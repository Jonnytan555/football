import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from modelling.python.features import build_features

MODEL_PATH = Path(__file__).parent.parent.parent / "football_data" / "model.pkl"

FEATURE_COLS = [
    "home_roll_win", "home_roll_draw", "home_roll_loss", "home_roll_gf", "home_roll_ga", "home_roll_points",
    "away_roll_win", "away_roll_draw", "away_roll_loss", "away_roll_gf", "away_roll_ga", "away_roll_points",
    "home_venue_roll_win", "home_venue_roll_gf", "home_venue_roll_ga",
    "away_venue_roll_win", "away_venue_roll_gf", "away_venue_roll_ga",
    "home_days_rest", "away_days_rest",
    "h2h_home_win_rate", "h2h_meetings",
]

LABEL_MAP = {0: "Home Win", 1: "Draw", 2: "Away Win"}

CANDIDATES = {
    "logistic": (
        LogisticRegression(max_iter=1000, multi_class="multinomial"),
        {"model__C": [0.01, 0.1, 1, 10]},
    ),
    "random_forest": (
        RandomForestClassifier(random_state=42),
        {"model__n_estimators": [100, 200], "model__max_depth": [3, 5, None]},
    ),
    "gradient_boosting": (
        GradientBoostingClassifier(random_state=42),
        {"model__n_estimators": [100, 200], "model__max_depth": [3, 4], "model__learning_rate": [0.05, 0.1]},
    ),
    "svm": (
        SVC(probability=True),
        {"model__C": [0.1, 1, 10], "model__kernel": ["rbf", "linear"]},
    ),
}


class FootballPredictor:

    def __init__(self, estimator=None):
        estimator = estimator or GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42)
        self.pipeline = Pipeline([("scaler", StandardScaler()), ("model", estimator)])
        self.trained = False

    def train(self, df: pd.DataFrame) -> dict:
        cutoff = df["utc_date"].quantile(0.8)
        train = df[df["utc_date"] <= cutoff]
        test = df[df["utc_date"] > cutoff]
        X_train, y_train = train[FEATURE_COLS].fillna(0), train["target"]
        X_test, y_test = test[FEATURE_COLS].fillna(0), test["target"]

        self.pipeline.fit(X_train, y_train)
        self.trained = True

        preds = self.pipeline.predict(X_test)
        acc = accuracy_score(y_test, preds)
        report = classification_report(y_test, preds, target_names=list(LABEL_MAP.values()))
        logging.info("Test accuracy: %.3f\n%s", acc, report)
        return {"accuracy": acc, "train_rows": len(train), "test_rows": len(test)}

    def save(self, path: Path = MODEL_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, path)
        logging.info("Model saved to %s", path)

    @classmethod
    def load(cls, path: Path = MODEL_PATH) -> "FootballPredictor":
        instance = cls()
        instance.pipeline = joblib.load(path)
        instance.trained = True
        logging.info("Model loaded from %s", path)
        return instance

    def predict_match(self, home_stats: dict, away_stats: dict, h2h_rate: float, h2h_meetings: int) -> dict:
        if not self.trained:
            raise RuntimeError("Call train() before predict()")
        row = pd.DataFrame([{**home_stats, **away_stats, "h2h_home_win_rate": h2h_rate, "h2h_meetings": h2h_meetings}])
        probs = self.pipeline.predict_proba(row[FEATURE_COLS].fillna(0))[0]
        return {LABEL_MAP[i]: round(float(p), 3) for i, p in enumerate(probs)}


def compare_models(df: pd.DataFrame) -> str | None:
    """Grid search all candidates with TimeSeriesSplit CV. Saves and returns the best model name."""
    cutoff = df["utc_date"].quantile(0.8)
    train, test = df[df["utc_date"] <= cutoff], df[df["utc_date"] > cutoff]
    X_train, y_train = train[FEATURE_COLS].fillna(0), train["target"]
    X_test, y_test = test[FEATURE_COLS].fillna(0), test["target"]

    tscv = TimeSeriesSplit(n_splits=5)
    best_acc, best_pipeline, best_name = -1, None, None

    for name, (estimator, param_grid) in CANDIDATES.items():
        logging.info("Tuning %s...", name)
        pipeline = Pipeline([("scaler", StandardScaler()), ("model", estimator)])
        search = GridSearchCV(pipeline, param_grid, cv=tscv, scoring="accuracy", n_jobs=-1)
        search.fit(X_train, y_train)
        acc = accuracy_score(y_test, search.best_estimator_.predict(X_test))
        logging.info("  %s — CV: %.3f  Test: %.3f  Params: %s", name, search.best_score_, acc, search.best_params_)
        if acc > best_acc:
            best_acc, best_pipeline, best_name = acc, search.best_estimator_, name

    logging.info("Best: %s (%.3f)", best_name, best_acc)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_pipeline, MODEL_PATH)
    logging.info("Saved to %s", MODEL_PATH)
    return best_name


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    df = build_features()
    print(f"Dataset: {len(df)} matches")
    if "--compare" in sys.argv:
        compare_models(df)
    else:
        p = FootballPredictor()
        stats = p.train(df)
        p.save()
        print(f"Accuracy: {stats['accuracy']:.1%}")
