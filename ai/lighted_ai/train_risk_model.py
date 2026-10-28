"""Prototype ML risk model (PDF §11): Random Forest on SYNTHETIC data.

⚠️  Results from synthetic data are NOT real-world performance (see PDF §10.2). This script proves the
workflow (features -> train -> validate -> save) so it can be re-run on real platform data later.
The live API still uses the transparent rule-based score in apps/api/app/services/analytics.py.

Run:  python -m lighted_ai.train_risk_model            (from the ai/ folder)
Out:  models/risk_model.joblib  + printed precision / recall / F1 / ROC-AUC
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import cross_val_score, train_test_split

FEATURES = ["avg_score", "recent_avg", "score_trend", "completion", "days_inactive", "attempts"]


def make_synthetic(n: int = 2000, seed: int = 7) -> pd.DataFrame:
    """Students whose risk depends on low scores, falling trend, low completion and inactivity (+ noise)."""
    rng = np.random.default_rng(seed)
    avg = np.clip(rng.normal(68, 18, n), 5, 100)
    recent = np.clip(avg + rng.normal(0, 10, n), 0, 100)
    df = pd.DataFrame({
        "avg_score": avg,
        "recent_avg": recent,
        "score_trend": recent - avg,
        "completion": np.clip(rng.normal(55, 28, n), 0, 100),
        "days_inactive": rng.exponential(6, n).round(),
        "attempts": rng.integers(0, 25, n),
    })
    logit = (-0.07 * (df.avg_score - 60) - 0.05 * (df.recent_avg - 60) - 0.02 * df.completion
             + 0.06 * df.days_inactive - 0.04 * df.attempts + rng.normal(0, 0.8, n) + 1.2)
    df["at_risk"] = (1 / (1 + np.exp(-logit)) > 0.5).astype(int)  # 1 = will score below pass mark
    return df


def main() -> None:
    df = make_synthetic()
    X_train, X_test, y_train, y_test = train_test_split(df[FEATURES], df["at_risk"], test_size=0.25, stratify=df["at_risk"], random_state=1)
    model = RandomForestClassifier(n_estimators=200, max_depth=8, class_weight="balanced", random_state=1)
    print("5-fold CV ROC-AUC:", cross_val_score(model, X_train, y_train, cv=5, scoring="roc_auc").mean().round(3))
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    print(classification_report(y_test, model.predict(X_test), target_names=["ok", "at-risk"]))
    print("Held-out ROC-AUC:", round(roc_auc_score(y_test, proba), 3), "(targets: recall>=0.70, AUC>=0.75)")
    print("Feature importance:", dict(zip(FEATURES, model.feature_importances_.round(3))))
    out = Path(__file__).resolve().parents[1] / "models"
    out.mkdir(exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES, "synthetic": True}, out / "risk_model.joblib")
    print("Saved ->", out / "risk_model.joblib")


if __name__ == "__main__":
    main()
