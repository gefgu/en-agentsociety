# import ray
# import torch
# from typing import Dict, Optional
# from transformers import AutoTokenizer, AutoModelForSequenceClassification
# import time
# from ..logger import get_logger
# import os
# import numpy as np


# @ray.remote(num_gpus=0.1)
# class ModernBERTRegressionActor:
#     """A Ray actor for ModernBERT model inference."""

#     def __init__(self, model_path: str, device: str = "cuda", num_labels: int = 4):
#         """
#         Initialize ModerBERT model.

#         :param model_path: Path to the pretrained ModernBERT model.
#         :param device: Device to load the model on ('cuda' or 'cpu').
#         :param num_labels: Number of regression labels.
#         """

#         get_logger().info(f"DEBUG: Checking path {model_path}")
#         if not os.path.exists(model_path):
#             get_logger().info(f"ERROR: Path does not exist: {model_path}")
#         else:
#             get_logger().info(f"DEBUG: Path exists. Contents: {os.listdir(model_path)}")

#         get_logger().info(f"Loading ModernBERT model from {model_path} on {device}...")
#         self.device = torch.device(device if torch.cuda.is_available() else "cpu")
#         self.tokenizer = AutoTokenizer.from_pretrained(
#             model_path, local_files_only=True
#         )
#         self.model = AutoModelForSequenceClassification.from_pretrained(
#             model_path,
#             num_labels=num_labels,
#             dtype=torch.bfloat16 if device == "cuda" else torch.float32,
#             local_files_only=True,
#         )
#         self.model.to(self.device)
#         self.model.eval()

#         self.label_names = [
#             "hunger_satisfaction",
#             "energy_satisfaction",
#             "social_satisfaction",
#             "fun_satisfaction",
#         ]

#         get_logger().info("ModernBERT model loaded successfully.")

#     def predict(self, text: str) -> Dict[str, float]:
#             """
#             Runs regression prediction on the input text.
#             """
#             start = time.perf_counter()

#             inputs = self.tokenizer(
#                 text,
#                 return_tensors="pt",
#                 truncation=True,
#                 padding=True,
#                 max_length=512,
#             )

#             # 1. FIX: Move inputs to GPU (Correct!)
#             inputs = {key: value.to(self.device) for key, value in inputs.items()}

#             with torch.no_grad():
#                 outputs = self.model(**inputs)
                
#                 # 2. FIX: Remove Sigmoid & Double conversion
#                 # - We likely want raw values for regression (MSE), not Sigmoid.
#                 # - We removed the second .cpu().numpy() call which would cause a crash.
#                 predictions = outputs.logits.squeeze().float().cpu().numpy()

#             # Optional: Clip values to [0, 1] if your data is strictly bounded
#             predictions = np.clip(predictions, 0.0, 1.0)

#             pred_dict = {
#                 name: float(pred)
#                 # predictions is already numpy, so we just zip it directly
#                 for name, pred in zip(self.label_names, predictions)
#             }

#             latency_ms = (time.perf_counter() - start) * 1000
            
#             return {
#                 "predictions": pred_dict,
#                 "latency_ms": latency_ms,
#                 # 3. FIX: Don't return raw GPU tensors (inputs); they break JSON serialization.
#                 # If you really need them for debug, convert to list:
#                 "input_tokens": len(inputs['input_ids'].cpu().tolist())
#             }


# class ModernBertRegressorPool:
#     """
#     A pool of ModernBERT regression actors for parallel inference.
#     """

#     def __init__(
#         self,
#         model_path: str,
#         num_actors: int = 2,
#         device: str = "cuda",
#         num_labels: int = 4,
#     ):
#         """
#         Initialize the pool of ModernBERT regression actors.

#         :param model_path: Path to the pretrained ModernBERT model.
#         :param num_actors: Number of Ray actors to create.
#         :param device: Device to load the model on ('cuda' or 'cpu').
#         :param num_labels: Number of regression labels.
#         """

#         self.actors = [
#             ModernBERTRegressionActor.remote(
#                 model_path=model_path, device=device, num_labels=num_labels
#             )
#             for _ in range(num_actors)
#         ]
#         self.next_actor_idx = 0
#         self.num_actors = num_actors

#     def predict(self, text: str) -> ray.ObjectRef:
#         """
#         Dispatch prediction request to the next available actor.

#         :param text: Input text for prediction.
#         :return: Ray ObjectRef for the prediction result.
#         """

#         actor = self.actors[self.next_actor_idx]
#         self.next_actor_idx = (self.next_actor_idx + 1) % self.num_actors
#         return actor.predict.remote(text)
