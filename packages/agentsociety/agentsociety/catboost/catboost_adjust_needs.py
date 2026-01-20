import re
import ray
import pandas as pd
from catboost import CatBoostRegressor
import joblib
from fastembed import TextEmbedding
from scipy.spatial.distance import mahalanobis
from sklearn.preprocessing import StandardScaler
import numpy as np

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


# @ray.remote(num_cpus=1)
# class CatBoostAdjustNeedsActor:
#     """A Ray actor for CatBoost model inference."""

#     def __init__(self, model_path: str):
#         """
#         Initialize CatBoost model.

#         :param model_path: Path to the pretrained CatBoost model.
#         """
#         self.model = CatBoostRegressor()
#         self.model.load_model(model_path)

#         self.feature_columns = [
#             "prompt",
#             "current_need",
#             "current_hunger",
#             "current_energy",
#             "current_safety",
#             "current_social",
#         ]

#     def predict(
#         self,
#         prompt,
#         current_need,
#         current_hunger,
#         current_energy,
#         current_safety,
#         current_social,
#     ) -> dict[str, float]:
#         """
#         Runs prediction on the input features.

#         :param features: A pandas DataFrame containing the input features.
#         :return: A pandas Series containing the predicted values.
#         """

#         input_data = pd.DataFrame(
#             [
#                 {
#                     "prompt": format_prompt(prompt, current_need),
#                     "current_need": current_need,
#                     "current_hunger": current_hunger,
#                     "current_energy": current_energy,
#                     "current_safety": current_safety,
#                     "current_social": current_social,
#                 }
#             ]
#         )

#         predictions = self.model.predict(input_data[self.feature_columns]).tolist()[0]

#         predictions = [max(0.0, min(1.0, pred)) for pred in predictions]

#         response = {
#             "hunger_satisfaction": float(predictions[0]),
#             "energy_satisfaction": float(predictions[1]),
#             "safety_satisfaction": float(predictions[2]),
#             "social_satisfaction": float(predictions[3]),
#         }

#         return response


class CatBoostAdjustNeedsLocal:
    """Local version of CatBoost model inference."""

    def __init__(
        self,
        model_path: str,
        pca_path: str,
        mahalanobis_params_path: str,
        embedding: TextEmbedding,
    ):
        """
        Initialize CatBoost model.

        :param model_path: Path to the pretrained CatBoost model.
        """
        self.model = CatBoostRegressor()
        self.model.load_model(model_path)

        self.pca = joblib.load(pca_path)
        self.mahalanobis_params = joblib.load(mahalanobis_params_path)
        self.embedding = embedding

        self.feature_columns = [
            "prompt",
            "current_need",
            "current_hunger",
            "current_energy",
            "current_safety",
            "current_social",
        ]

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

        embeddings = list(self.embedding.embed([format_prompt(prompt, current_need)]))
        reduced_embeddings = self.pca.transform(embeddings)

        mahal_dist = mahalanobis(
            reduced_embeddings[0],
            self.mahalanobis_params["mean_vector"],
            self.mahalanobis_params["inv_cov_matrix"],
        )

        if mahal_dist > self.mahalanobis_params["threshold"]:
            return False, {}

        # Step 4: Prepare features for CatBoost
        # Create feature array in the same order as training
        sample_features = np.array(
            [
                [
                    current_need,
                    current_hunger,
                    current_energy,
                    current_safety,
                    current_social,
                ]
            ]
        )

        # Combine categorical/numerical features with PCA embeddings
        sample_combined = np.hstack([sample_features, reduced_embeddings])

        # Step 5: Make CatBoost prediction
        prediction = self.model.predict(sample_combined)[0]

        # Step 6: Clamp predictions to valid range [0, 1]
        predictions = [max(0.0, min(1.0, pred)) for pred in prediction]

        # Step 7: Format response
        response = {
            "hunger_satisfaction": float(predictions[0]),
            "energy_satisfaction": float(predictions[1]),
            "safety_satisfaction": float(predictions[2]),
            "social_satisfaction": float(predictions[3]),
        }

        return True, response
