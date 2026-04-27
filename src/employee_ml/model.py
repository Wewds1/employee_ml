from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


NUMERIC_COLUMNS = ["age", "salary", "tenure_years", "performance_score", "perf_was_missing"]
CATEGORICAL_COLUMNS = ["department"]
TARGET_COLUMN = "left_company"


def sigmoid(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values, -35.0, 35.0)
    return 1.0 / (1.0 + np.exp(-clipped))


@dataclass
class ModelMetrics:
    accuracy: float
    precision: float
    recall: float
    f1_score: float


@dataclass
class TrainingArtifacts:
    feature_names: list[str]
    means: np.ndarray
    stds: np.ndarray
    weights: np.ndarray
    bias: float
    metrics: ModelMetrics


class AttritionModel:
    def __init__(self, learning_rate: float = 0.08, epochs: int = 2500) -> None:
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.artifacts: TrainingArtifacts | None = None

    def _prepare_features(
        self, frame: pd.DataFrame, fit: bool
    ) -> tuple[np.ndarray, list[str], np.ndarray, np.ndarray]:
        numeric = frame[NUMERIC_COLUMNS].astype(float).copy()
        numeric_matrix = numeric.to_numpy(dtype=float)

        if fit or self.artifacts is None:
            means = numeric_matrix.mean(axis=0)
            stds = numeric_matrix.std(axis=0)
            stds[stds == 0] = 1.0
        else:
            means = self.artifacts.means
            stds = self.artifacts.stds

        numeric_scaled = (numeric_matrix - means) / stds

        dummies = pd.get_dummies(frame[CATEGORICAL_COLUMNS], columns=CATEGORICAL_COLUMNS)
        if fit or self.artifacts is None:
            feature_names = NUMERIC_COLUMNS + list(dummies.columns)
        else:
            feature_names = self.artifacts.feature_names
            for feature in feature_names[len(NUMERIC_COLUMNS) :]:
                if feature not in dummies:
                    dummies[feature] = 0
            dummies = dummies[[name for name in feature_names if name not in NUMERIC_COLUMNS]]

        matrix = np.column_stack([numeric_scaled, dummies.to_numpy(dtype=float)])
        return matrix, feature_names, means, stds

    def fit(self, frame: pd.DataFrame) -> TrainingArtifacts:
        matrix, feature_names, means, stds = self._prepare_features(frame, fit=True)
        target = frame[TARGET_COLUMN].to_numpy(dtype=float)

        weights = np.zeros(matrix.shape[1], dtype=float)
        bias = 0.0

        for _ in range(self.epochs):
            logits = matrix @ weights + bias
            predictions = sigmoid(logits)
            error = predictions - target

            gradient_w = matrix.T @ error / len(matrix)
            gradient_b = float(error.mean())

            weights -= self.learning_rate * gradient_w
            bias -= self.learning_rate * gradient_b

        predicted_labels = (sigmoid(matrix @ weights + bias) >= 0.5).astype(int)
        metrics = compute_metrics(target.astype(int), predicted_labels)

        self.artifacts = TrainingArtifacts(
            feature_names=feature_names,
            means=means,
            stds=stds,
            weights=weights,
            bias=bias,
            metrics=metrics,
        )
        return self.artifacts

    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        if self.artifacts is None:
            raise RuntimeError("Model must be fitted before inference.")

        matrix, _, _, _ = self._prepare_features(frame, fit=False)
        return sigmoid(matrix @ self.artifacts.weights + self.artifacts.bias)

    def explain_row(self, row: pd.Series) -> list[dict[str, float | str]]:
        if self.artifacts is None:
            raise RuntimeError("Model must be fitted before explanation.")

        row_frame = pd.DataFrame([row])
        matrix, _, _, _ = self._prepare_features(row_frame, fit=False)
        contributions = matrix[0] * self.artifacts.weights

        explanation = [
            {"feature": feature, "impact": float(impact)}
            for feature, impact in zip(self.artifacts.feature_names, contributions)
            if abs(float(impact)) > 0.02
        ]
        explanation.sort(key=lambda item: abs(float(item["impact"])), reverse=True)
        return explanation[:5]


def compute_metrics(actual: np.ndarray, predicted: np.ndarray) -> ModelMetrics:
    true_positive = int(((actual == 1) & (predicted == 1)).sum())
    true_negative = int(((actual == 0) & (predicted == 0)).sum())
    false_positive = int(((actual == 0) & (predicted == 1)).sum())
    false_negative = int(((actual == 1) & (predicted == 0)).sum())

    accuracy = (true_positive + true_negative) / max(len(actual), 1)
    precision = true_positive / max(true_positive + false_positive, 1)
    recall = true_positive / max(true_positive + false_negative, 1)
    f1_score = 2 * precision * recall / max(precision + recall, 1e-9)

    return ModelMetrics(
        accuracy=float(accuracy),
        precision=float(precision),
        recall=float(recall),
        f1_score=float(f1_score),
    )
