import os
from pathlib import Path
from ..logger import get_logger
import re
import ray
import pandas as pd
from catboost import CatBoostClassifier
import joblib
from fastembed import TextEmbedding
from scipy.spatial.distance import mahalanobis
from sklearn.preprocessing import StandardScaler
import numpy as np
from fastembed import TextEmbedding

N_CPUS = 4

@ray.remote(num_cpus=N_CPUS)
class CatBoostDispatcherActor:
    """A Ray actor for CatBoost model inference."""

    def __init__(
        self,
        model_path_prefix: str,
    ):
        """
        Initialize CatBoost model.

        :param model_path: Path to the pretrained CatBoost model.
        """
        os.environ["OMP_NUM_THREADS"] = str(N_CPUS)
        os.environ["MKL_NUM_THREADS"] = str(N_CPUS)
        os.environ["ONNXRUNTIME_INTRA_OP_NUM_THREADS"] = str(N_CPUS)
        self.model_path_prefix = Path(model_path_prefix)
        self.blocks_handled_by_case = {}  # blocks: case_id
        self.models_by_case = {}  # case_id: model
        self.pca_by_case = {}  # case_id: {col_name: pca_transformer}

        # Find model files with various possible extensions
        model_files = list(self.model_path_prefix.glob("catboost_dispatcher_case_*.cbm"))
        
        if not model_files:
            get_logger().warning(
                f"No CatBoost dispatcher model files found in {model_path_prefix}. "
                f"Looking for files matching pattern 'catboost_dispatcher_case_*.cbm'. "
                f"CatBoostDispatcher will fallback to LLM for all predictions."
            )

        get_logger().info(f"Loading CatBoostDispatcher from {model_path_prefix}")

        for model_file in model_files:
            get_logger().info(f"Loading model from {model_file}")
            case_name = re.search(
                r"catboost_dispatcher_case_(.*).cbm", model_file.name
            ).group(1)
            model = CatBoostClassifier()
            model.load_model(model_file)
            self.models_by_case[case_name] = model
            self.blocks_handled_by_case[case_name] = self._load_blocks_for_case(
                case_name
            )
            pca_file = self.model_path_prefix / f"catboost_dispatcher_case_{case_name}_pca.joblib"
            if pca_file.exists():
                self.pca_by_case[case_name] = joblib.load(pca_file)


        get_logger().info(f"Loaded CatBoostDispatcher with cases: {self.blocks_handled_by_case}")

        self.embedding = TextEmbedding(threads=N_CPUS)
        

    def _load_blocks_for_case(self, case_name: str) -> list[str]:
        blocks_file = (
            self.model_path_prefix
            / f"catboost_dispatcher_case_{case_name}_metadata.json"
        )
        if not blocks_file.exists():
            get_logger().warning(f"Blocks file for case '{case_name}' not found.")
            return []
        try:
            df = pd.read_json(blocks_file)
            # Get the possible_blocks value - it should already be a list
            blocks_data = df["possible_blocks"].tolist()
            
            # If it's already a list, sort it; if it's a string, it means the data is malformed
            if isinstance(blocks_data, list):
                return sorted(blocks_data)
            else:
                get_logger().error(
                    f"Expected list for possible_blocks in {blocks_file}, got {type(blocks_data)}: {blocks_data}"
                )
                return []
        except Exception as e:
            get_logger().error(f"Error loading blocks from {blocks_file}: {e}")
            return []

    def _parse_temperature(self, temp_str: str) -> float:
        """Extracts numerical temperature from strings like '15C' or 'Temp is 22.5°'."""
        try:
            # Matches integers or decimals. Handles negative numbers.
            match = re.search(r"([-+]?\d*\.?\d+)", temp_str)
            return float(match.group(1)) if match else 0
        except (ValueError, AttributeError):
            return 0

    def predict(
        self,
        function_schema: dict,
        context: dict,
        agent_id: str = None,  # Added for logging
    ) -> (bool, str):
        """
        Runs prediction on the input features.

        :param function_schema: Schema containing possible blocks in enum
        :param context: Dictionary with context information
        :param agent_id: Agent ID for logging
        :return: Tuple of (success: bool, predicted_block: str)
        """

        try:
            # Extract possible blocks and find matching case
            possible_blocks = tuple(
                sorted(
                    function_schema["function"]["parameters"]["properties"][
                        "block_name"
                    ]["enum"]
                )
            )

            # Find the case_id for these blocks
            case_id = None
            for cid, blocks in self.blocks_handled_by_case.items():
                if tuple(sorted(blocks)) == possible_blocks:
                    case_id = cid
                    break

            if case_id is None:
                get_logger().warning(f"No model found for blocks: {possible_blocks}")
                return False, None

            model = self.models_by_case[case_id]

            # Extract and process features matching training
            text_cols_data = {
                "ctx_intention": context.get("current_intention", ""),
                "ctx_thought": context.get("current_thought", ""),
                "ctx_plan_target": context.get("plan_target", ""),
            }

            # Generate embeddings for text columns with PCA (32 components each)
            text_features = []
            for col_name, text_value in text_cols_data.items():
                # Embed single text
                embedding = list(
                    self.embedding.embed([str(text_value) if text_value else ""])
                )[0]
                emb_array = np.array(embedding).reshape(1, -1)

                # Apply PCA (you'll need to save and load PCA transformers per case)
                # For now, using raw embeddings - ideally load the fitted PCA
                # If you want exact match, save PCA in training and load here
                text_features.append(emb_array)

            # Process time features
            time_str = context.get("current_time", "00:00:00")
            try:
                dt = pd.to_datetime(time_str, format="%H:%M:%S")
                time_features = np.array([[dt.hour, dt.minute]])
            except:
                time_features = np.array([[0, 0]])

            # Categorical features
            emotion = str(context.get("current_emotion", ""))

            # Numerical features
            raw_temp_str = context.get("temperature", "0")
            temp_value = self._parse_temperature(raw_temp_str)

            # Combine features into DataFrame matching training structure
            # Note: You need to match the exact column names from training
            feature_dict = {}

            pca_transformers = self.pca_by_case.get(case_id, {})
            for col_name, emb in zip(text_cols_data.keys(), text_features):
                if col_name in pca_transformers:
                    emb_reduced = pca_transformers[col_name].transform(emb)
                    for j in range(emb_reduced.shape[1]):
                        feature_dict[f"{col_name}_pca_{j}"] = emb_reduced[0, j]

            # Add time features
            feature_dict["ctx_time_hour"] = time_features[0, 0]
            feature_dict["ctx_time_minute"] = time_features[0, 1]

            # Add categorical
            feature_dict["ctx_emotion"] = emotion

            # Add numerical
            feature_dict["ctx_temperature"] = temp_value

            # Create DataFrame
            X = pd.DataFrame([feature_dict])


            prediction = model.predict(X)
            # get_logger().info(
            #     f"CatBoostDispatcher prediction for agent_id={agent_id}, case_id={case_id}: {prediction}"
            # )
            # Predict
            predicted_block = prediction[0][0]

            return True, predicted_block

        except Exception as e:
            get_logger().error(f"Prediction failed: {e}")
            return False, None
