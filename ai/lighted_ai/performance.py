
"""Production-oriented student performance prediction.

Training rows must contain historical attempt scores and the known
pass/fail outcome of the NEXT assessment.

Example training row:
    {
        "attempts": [45, 52, 61],
        "passed": True,
        "threshold": 60.0,
    }

A prediction is only as reliable as the training data, calibration,
evaluation and similarity between training and production students.
"""
from __future__ import annotations

import math
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from numbers import Real
from pathlib import Path
from typing import Literal, Any

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


MODEL_VERSION = 1
FEATURE_VERSION = 1
DEFAULT_PASS_THRESHOLD = 60.0
DEFAULT_RISK_PROBABILITY_THRESHOLD = 0.5
DEFAULT_MODEL_PATH = Path("models") / "performance_model.joblib"
MODEL_PATH_ENV_VAR = "LIGHTED_PERFORMANCE_MODEL_PATH"

FEATURE_NAMES = (
    "mean_score",
    "latest_score",
    "recent_mean",
    "trend_slope",
    "score_std",
    "log_attempt_count",
    "pass_threshold",
)

PredictionLabel = Literal["at_risk", "on_track"]
ConfidenceLevel = Literal["low", "medium", "high"]


class PredictionError(ValueError):
    """Invalid input for performance prediction."""


class ModelNotReadyError(RuntimeError):
    """No compatible trained prediction model is available."""


class ModelArtifactError(RuntimeError):
    """The saved prediction model is invalid or incompatible."""


@dataclass(frozen=True, slots=True)
class Prediction:
    pass_probability: float
    label: PredictionLabel
    confidence: ConfidenceLevel
    attempts_used: int
    model_version: int


def _validate_threshold(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise PredictionError(f"{name} must be a numeric percentage.")

    result = float(value)

    if not math.isfinite(result) or not 0.0 <= result <= 100.0:
        raise PredictionError(f"{name} must be between 0 and 100.")

    return result


def _validate_probability_threshold(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise PredictionError(
            "risk_probability_threshold must be a number between 0 and 1."
        )

    result = float(value)

    if not math.isfinite(result) or not 0.0 < result < 1.0:
        raise PredictionError(
            "risk_probability_threshold must be greater than 0 "
            "and less than 1."
        )

    return result


def _validate_attempts(attempts: Sequence[float]) -> np.ndarray:
    if isinstance(attempts, (str, bytes)):
        raise PredictionError("attempts must be a sequence of numeric scores.")

    try:
        values = list(attempts)
    except TypeError as exc:
        raise PredictionError("attempts must be a sequence.") from exc

    if not values:
        raise PredictionError(
            "At least one completed assessment is required for prediction."
        )

    scores: list[float] = []

    for index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, Real):
            raise PredictionError(
                f"Attempt score at index {index} must be numeric."
            )

        score = float(value)

        if not math.isfinite(score) or not 0.0 <= score <= 100.0:
            raise PredictionError(
                f"Attempt score at index {index} must be finite "
                "and between 0 and 100."
            )

        scores.append(score)

    return np.asarray(scores, dtype=np.float64)


def _features(
    attempts: Sequence[float],
    threshold: float = DEFAULT_PASS_THRESHOLD,
) -> np.ndarray:
    """Build a stable, versioned feature vector from past scores.

    Trend is the least-squares slope over chronological attempt positions.
    Recent mean uses up to the last three assessments.
    """
    scores = _validate_attempts(attempts)
    pass_threshold = _validate_threshold(threshold, "threshold")

    count = len(scores)
    positions = np.arange(count, dtype=np.float64)

    centered_positions = positions - positions.mean()
    denominator = float(np.dot(centered_positions, centered_positions))

    trend = (
        float(np.dot(centered_positions, scores - scores.mean()) / denominator)
        if denominator > 0
        else 0.0
    )

    recent_mean = float(scores[-min(3, count):].mean())

    features = np.asarray(
        [
            float(scores.mean()),
            float(scores[-1]),
            recent_mean,
            trend,
            float(scores.std(ddof=0)),
            math.log1p(count),
            pass_threshold,
        ],
        dtype=np.float64,
    )

    if features.shape != (len(FEATURE_NAMES),):
        raise PredictionError("Internal feature schema mismatch.")

    if not np.isfinite(features).all():
        raise PredictionError("Feature extraction produced non-finite values.")

    return features


def _training_row_features(row: Mapping[str, Any]) -> np.ndarray:
    if "attempts" not in row:
        raise PredictionError("Training row is missing 'attempts'.")

    threshold = row.get("threshold", DEFAULT_PASS_THRESHOLD)

    return _features(
        row["attempts"],
        threshold=threshold,
    )


def train_model(
    training_rows: Sequence[Mapping[str, Any]],
) -> CalibratedClassifierCV:
    """Fit a calibrated classifier from labelled historical outcomes.

    Each row must have:
        attempts: historical numeric scores
        passed: bool, indicating the NEXT assessment's outcome
        threshold: optional pass-score threshold

    Requires at least five examples from EACH outcome class for the
    five-fold calibration procedure. Use separate held-out data to
    evaluate the resulting model before deployment.
    """
    if len(training_rows) < 10:
        raise PredictionError(
            "At least 10 labelled rows are required, with at least "
            "five examples in each outcome class. More data is normally "
            "needed for reliable production predictions."
        )

    features: list[np.ndarray] = []
    labels: list[int] = []

    for index, row in enumerate(training_rows):
        if not isinstance(row, Mapping):
            raise PredictionError(
                f"Training row {index} must be a mapping."
            )

        if "passed" not in row or not isinstance(row["passed"], bool):
            raise PredictionError(
                f"Training row {index} must contain a boolean 'passed'."
            )

        try:
            vector = _training_row_features(row)
        except PredictionError as exc:
            raise PredictionError(
                f"Invalid training row {index}: {exc}"
            ) from exc

        features.append(vector)
        labels.append(int(row["passed"]))

    X = np.vstack(features)
    y = np.asarray(labels, dtype=np.int64)

    class_counts = np.bincount(y, minlength=2)

    if np.any(class_counts < 5):
        raise PredictionError(
            "Calibrated training requires at least five pass examples "
            "and five fail examples. Collect more labelled outcomes."
        )

    base_pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )

    # Sigmoid calibration improves probability estimates when supported
    # by representative, sufficiently large training data.
    model = CalibratedClassifierCV(
        estimator=base_pipeline,
        method="sigmoid",
        cv=5,
    )
    model.fit(X, y)

    return model


def save_model(
    model: CalibratedClassifierCV,
    path: str | Path,
) -> Path:
    """Persist a fitted model and its feature schema."""
    if not hasattr(model, "predict_proba"):
        raise ModelArtifactError("Model does not support predict_proba().")

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    artifact = {
        "model_version": MODEL_VERSION,
        "feature_version": FEATURE_VERSION,
        "feature_names": FEATURE_NAMES,
        "model": model,
    }

    # Only load model artifacts from trusted sources: joblib uses pickle.
    joblib.dump(artifact, destination)
    _load_model_cached.cache_clear()

    return destination


@lru_cache(maxsize=4)
def _load_model_cached(
    resolved_path: str,
    modified_ns: int,
) -> dict[str, Any]:
    """Load and cache an artifact; modification time invalidates the cache."""
    del modified_ns  # Included in the cache key intentionally.

    try:
        artifact = joblib.load(resolved_path)
    except Exception as exc:
        raise ModelArtifactError(
            f"Could not load prediction model: {resolved_path}"
        ) from exc

    if not isinstance(artifact, dict):
        raise ModelArtifactError("Model artifact must be a dictionary.")

    if artifact.get("model_version") != MODEL_VERSION:
        raise ModelArtifactError("Unsupported model artifact version.")

    if artifact.get("feature_version") != FEATURE_VERSION:
        raise ModelArtifactError("Unsupported feature schema version.")

    if tuple(artifact.get("feature_names", ())) != FEATURE_NAMES:
        raise ModelArtifactError("Model feature names do not match this code.")

    model = artifact.get("model")

    if not hasattr(model, "predict_proba"):
        raise ModelArtifactError("Saved model has no predict_proba() method.")

    return artifact


def load_model(path: str | Path | None = None) -> Any:
    """Load the configured model or raise a clear readiness error."""
    configured_path = path or os.getenv(
        MODEL_PATH_ENV_VAR,
        str(DEFAULT_MODEL_PATH),
    )
    model_path = Path(configured_path).expanduser().resolve()

    if not model_path.is_file():
        raise ModelNotReadyError(
            f"No trained performance model found at {model_path}. "
            "Train and evaluate a model before enabling predictions."
        )

    try:
        modified_ns = model_path.stat().st_mtime_ns
    except OSError as exc:
        raise ModelArtifactError(
            f"Cannot inspect model artifact: {model_path}"
        ) from exc

    artifact = _load_model_cached(str(model_path), modified_ns)
    return artifact["model"]


def _confidence(probability: float) -> ConfidenceLevel:
    """Describe decision margin, NOT a statistical confidence interval."""
    margin = abs(probability - 0.5)

    if margin >= 0.35:
        return "high"
    if margin >= 0.15:
        return "medium"
    return "low"


def predict_performance(
    attempts: Sequence[float],
    threshold: float = DEFAULT_PASS_THRESHOLD,
    *,
    risk_probability_threshold: float = DEFAULT_RISK_PROBABILITY_THRESHOLD,
    model: Any | None = None,
    model_path: str | Path | None = None,
) -> Prediction:
    """Predict the probability of passing the next assessment.

    `threshold` is the score required to pass an assessment.
    `risk_probability_threshold` is the probability cutoff for the label.

    Pass a previously loaded model to avoid repeated model lookup.
    No heuristic probability is returned if a trained model is missing.
    """
    pass_threshold = _validate_threshold(threshold, "threshold")
    risk_cutoff = _validate_probability_threshold(
        risk_probability_threshold
    )

    vector = _features(attempts, threshold=pass_threshold).reshape(1, -1)
    predictor = model if model is not None else load_model(model_path)

    if not hasattr(predictor, "predict_proba"):
        raise ModelArtifactError("Predictor must implement predict_proba().")

    try:
        probabilities = np.asarray(
            predictor.predict_proba(vector),
            dtype=np.float64,
        )
        classes = np.asarray(predictor.classes_)
    except Exception as exc:
        raise ModelArtifactError("Model prediction failed.") from exc

    if (
        probabilities.ndim != 2
        or probabilities.shape != (1, len(classes))
        or not np.isfinite(probabilities).all()
        or np.any(probabilities < 0)
        or np.any(probabilities > 1)
        or not np.isclose(probabilities.sum(axis=1)[0], 1.0, atol=1e-6)
    ):
        raise ModelArtifactError("Model returned invalid probabilities.")

    if not np.any(classes == 1):
        raise ModelArtifactError(
            "Model must be trained with both fail (0) and pass (1) labels."
        )

    passed_indices = np.flatnonzero(classes == 1)

    if len(passed_indices) != 1:
        raise ModelArtifactError(
            "Model must be trained with both fail (0) and pass (1) labels."
        )

    probability = float(probabilities[0, passed_indices[0]])

    label: PredictionLabel = (
        "on_track" if probability >= risk_cutoff else "at_risk"
    )

    return Prediction(
        pass_probability=round(probability, 4),
        label=label,
        confidence=_confidence(probability),
        attempts_used=len(attempts),
        model_version=MODEL_VERSION,
    )


def train_demo_model() -> CalibratedClassifierCV:
    """Build a small synthetic model for demos and smoke tests.

    This is only intended for local validation when no real student dataset is
    available yet. Production use should replace it with a model trained on a
    real, representative dataset.
    """
    demo_rows = [
        {"attempts": [35, 42, 48], "passed": False, "threshold": 60.0},
        {"attempts": [40, 45, 50], "passed": False, "threshold": 60.0},
        {"attempts": [48, 52, 57], "passed": False, "threshold": 60.0},
        {"attempts": [50, 54, 58], "passed": False, "threshold": 60.0},
        {"attempts": [52, 58, 63], "passed": True, "threshold": 60.0},
        {"attempts": [55, 60, 68], "passed": True, "threshold": 60.0},
        {"attempts": [58, 63, 72], "passed": True, "threshold": 60.0},
        {"attempts": [60, 66, 75], "passed": True, "threshold": 60.0},
        {"attempts": [42, 49, 55], "passed": False, "threshold": 60.0},
        {"attempts": [45, 51, 60], "passed": True, "threshold": 60.0},
    ]
    return train_model(demo_rows)


def evaluate_model(
    model: Any,
    evaluation_rows: Sequence[Mapping[str, Any]],
) -> dict[str, float]:
    """Evaluate on held-out labelled outcomes, not training rows."""
    if not evaluation_rows:
        raise PredictionError("Evaluation data cannot be empty.")

    X = np.vstack([
        _training_row_features(row)
        for row in evaluation_rows
    ])

    y = np.asarray([
        int(row["passed"])
        if isinstance(row.get("passed"), bool)
        else -1
        for row in evaluation_rows
    ])

    if np.any((y != 0) & (y != 1)):
        raise PredictionError(
            "Every evaluation row must contain a boolean 'passed'."
        )

    probabilities = np.asarray(model.predict_proba(X), dtype=np.float64)
    classes = np.asarray(model.classes_)
    passed_indices = np.flatnonzero(classes == 1)

    if len(passed_indices) != 1:
        raise ModelArtifactError("Model has no unique pass class (1).")

    pass_probabilities = probabilities[:, passed_indices[0]]

    metrics = {
        "brier_score": float(brier_score_loss(y, pass_probabilities)),
    }

    if len(np.unique(y)) == 2:
        metrics["roc_auc"] = float(
            roc_auc_score(y, pass_probabilities)
        )

    return metrics
