from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np

from inference.feature_extractor import extract_feature_vector


class HarPredictor:
    def __init__(self, model_path: str | Path) -> None:
        self.model_path = Path(model_path)
        self.model = joblib.load(self.model_path)

        self.expected_dim = int(getattr(self.model, "n_features_in_", 561))

        classes = getattr(self.model, "classes_", None)
        self.classes = list(classes) if classes is not None else ["WALKING", "SITTING", "STANDING"]

    def _build_output(self, probabilities: np.ndarray) -> Dict[str, Any]:
        best_idx = int(np.argmax(probabilities))
        label = str(self.classes[best_idx])
        confidence = float(probabilities[best_idx])

        class_probabilities = {
            str(cls): float(probabilities[idx])
            for idx, cls in enumerate(self.classes)
        }

        return {
            "label": label,
            "confidence": confidence,
            "probabilities": class_probabilities,
        }

    def predict_from_window(self, window_matrix: np.ndarray) -> Dict[str, Any]:
        started = time.perf_counter()

        features = extract_feature_vector(window_matrix, expected_dim=self.expected_dim)
        batch = features.reshape(1, -1)
        probabilities = self.model.predict_proba(batch)[0]

        result = self._build_output(probabilities)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        result["processing_ms"] = round(elapsed_ms, 3)
        return result
