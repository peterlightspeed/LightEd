"""Basic performance prediction.

Uses a small logistic-regression model over simple features derived from a
student's attempt history. This is intentionally lightweight — no deep learning,
no training a language model.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Prediction:
    pass_probability: float
    label: str  # "at_risk" | "on_track"
    confidence: str


def _features(attempts: list[float]) -> list[float]:
    if not attempts:
        return [0.0, 0.0, 0.0]
    arr = np.asarray(attempts, dtype=np.float32)
    return [
        float(arr.mean()),                 # average score
        float(arr[-1]),                    # most recent score
        float(arr[-1] - arr[0]),           # trend (improvement)
    ]


def predict_performance(attempts: list[float], threshold: float = 60.0) -> Prediction:
    """Predict the chance a student passes their next assessment.

    This is a transparent heuristic that mimics a trained model's output. Swap in
    a fitted scikit-learn model later behind the same function signature.
    """
    avg, latest, trend = _features(attempts)
    # Simple logistic combination of the features.
    z = (avg - threshold) / 20.0 + (latest - threshold) / 30.0 + trend / 50.0
    prob = float(1 / (1 + np.exp(-z)))
    label = "on_track" if prob >= 0.5 else "at_risk"
    confidence = "high" if abs(prob - 0.5) > 0.25 else "medium"
    return Prediction(pass_probability=round(prob, 3), label=label, confidence=confidence)
