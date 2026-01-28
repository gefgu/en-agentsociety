import os
from ..logger import get_logger
import re
import ray
import pandas as pd
from catboost import CatBoostRegressor
import joblib
from fastembed import TextEmbedding
from scipy.spatial.distance import mahalanobis
from sklearn.preprocessing import StandardScaler
import numpy as np
from fastembed import TextEmbedding

N_CPUS = 4


# Patterns for extracting satisfaction values
hunger_pattern = r"(hunger_satisfaction):\s*([\d\.]+)"
energy_pattern = r"(energy_satisfaction):\s*([\d\.]+)"
safety_pattern = r"(safety_satisfaction):\s*([\d\.]+)"
social_pattern = r"(social_satisfaction):\s*([\d\.]+)"


def format_prompt(prompt, need):
    role_section_prompt = f"You are an evaluation system for an intelligent agent. The agent has performed the following actions to satisfy the {need} need:\n\n"
    pre_notes_section = f"\n\nPlease evaluate and adjust the value of {need} satisfaction based on the execution results above."
    notes_section_prompt = """\n\nNotes:\n1. Satisfaction values range from 0-1, where:\n   - 1 means the need is fully satisfied\n   - 0 means the need is completely unsatisfied \n   - Higher values indicate greater need satisfaction\n2. If the current need is not "whatever", only return the new value for the current need. Otherwise, return both safe and social need values.\n3. Ensure the return value is in valid JSON format, examples below:\n\nPlease response in json format for specific need (hungry here) adjustment (Do not return any other text), example:\n{\n    "hunger_satisfaction": new_hunger_satisfaction_value\n}\n\nPlease response in json format for whatever need adjustment (Do not return any other text), example:\n{\n    "safety_satisfaction": new_safety_satisfaction_value,\n    "social_satisfaction": new_social_satisfaction_value\n}"""

    # Remove the current satisfaction section using regex
    current_satisfaction_pattern = r"\n\nCurrent satisfaction:\s*\n-\s*hunger_satisfaction:.*?\n-\s*energy_satisfaction:.*?\n-\s*safety_satisfaction:.*?\n-\s*social_satisfaction:.*?(?=\n|$)"

    # Apply regex after the replacements
    cleaned = re.sub(
        current_satisfaction_pattern,
        "",
        prompt.replace(notes_section_prompt, "")
        .replace(role_section_prompt, "")
        .replace(pre_notes_section, ""),
    )

    return cleaned.strip()


@ray.remote(num_cpus=N_CPUS)
class CatBoostAdjustNeedsActor:
    """A Ray actor for CatBoost model inference."""

    def __init__(
        self,
        model_path_prefix: str,
        pca_path: str,
        # mahalanobis_params_path: str,
    ):
        """
        Initialize CatBoost model.

        :param model_path: Path to the pretrained CatBoost model.
        """
        os.environ["OMP_NUM_THREADS"] = str(N_CPUS)
        os.environ["MKL_NUM_THREADS"] = str(N_CPUS)
        os.environ["ONNXRUNTIME_INTRA_OP_NUM_THREADS"] = str(N_CPUS)
        self.needs = ["hungry", "tired", "safe", "social"]
        self.models = {}
        for need in self.needs:
            model_path = f"{model_path_prefix}_{need}.cbm"
            model = CatBoostRegressor()
            model.load_model(model_path)
            self.models[need] = model
        self.pca = joblib.load(pca_path)
        # self.mahalanobis_params = joblib.load(mahalanobis_params_path)
        self.embedding = TextEmbedding(threads=N_CPUS)

        self.needs_replacement = {
            "hungry": "hunger",
            "tired": "energy",
            "safe": "safety",
        }

    def predict(
        self,
        prompt,
        current_need,
        current_hunger,
        current_energy,
        current_safety,
        current_social,
    ) -> tuple[bool, dict[str, float]]:
        """
        Runs prediction on the input features.

        :param features: A pandas DataFrame containing the input features.
        :return: A pandas Series containing the predicted values.
        """
        if prompt is None or len(prompt.strip()) == 0:
            get_logger().warning("Empty prompt received for CatBoost prediction.")
            return False, {}

        embeddings = list(self.embedding.embed([(prompt, current_need)]))
        reduced_embeddings = self.pca.transform(embeddings)


        # mahal_dist = mahalanobis(
        #     reduced_embeddings[0],
        #     self.mahalanobis_params["mean_vector"],
        #     self.mahalanobis_params["inv_cov_matrix"],
        # )

        # if mahal_dist > self.mahalanobis_params["threshold"]:
        #     return False, {}

        # Step 3: Prepare input for CatBoost model
        model = self.models[current_need]
        current_need_map = {
            "hunger": current_hunger,
            "energy": current_energy,
            "safety": current_safety,
            "social": current_social,
        }

        current_need = self.needs_replacement.get(current_need, current_need)
        current_need_value = current_need_map[current_need]

        # Step 4: Prepare features for CatBoost
        # Create feature array in the same order as training
        sample_features = np.array(
            [
                [
                    current_need_value,
                ]
            ]
        )

        # Combine categorical/numerical features with PCA embeddings
        sample_combined = np.hstack([sample_features, reduced_embeddings])

        # Step 5: Make CatBoost prediction
        prediction = model.predict(sample_combined)[0]

        # Step 6: Clamp predictions to valid range [0, 1]
        pred = max(0.0, min(1.0, prediction))
        # predictions = [max(0.0, min(1.0, pred)) for pred in prediction]

        response = {
            "hunger_satisfaction": current_hunger,
            "energy_satisfaction": current_energy,
            "safety_satisfaction": current_safety,
            "social_satisfaction": current_social,
        }

        # Step 7: Format response
        response = response | {
            f"{current_need}_satisfaction": pred,
        }

        return True, response
