from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from .data import load_employee_data, profile_dataset
from .model import AttritionModel


class EmployeeIntelligenceService:
    def __init__(self) -> None:
        self.frame = load_employee_data()
        self.profile = profile_dataset(self.frame)
        self.model = AttritionModel()
        self.artifacts = self.model.fit(self.frame)
        self.scored = self.frame.copy()
        self.scored["attrition_risk"] = self.model.predict_proba(self.frame).round(4)
        self.critical_threshold = float(self.scored["attrition_risk"].quantile(0.82))
        self.elevated_threshold = float(self.scored["attrition_risk"].quantile(0.62))
        self.scored["risk_band"] = self.scored["attrition_risk"].apply(self._risk_band)

    def _risk_band(self, score: float) -> str:
        if score >= self.critical_threshold:
            return "critical"
        if score >= self.elevated_threshold:
            return "elevated"
        return "stable"

    def summary(self) -> dict:
        profile = asdict(self.profile)
        metrics = asdict(self.artifacts.metrics)
        return {
            "profile": profile,
            "model_metrics": metrics,
            "critical_count": int((self.scored["risk_band"] == "critical").sum()),
            "elevated_count": int((self.scored["risk_band"] == "elevated").sum()),
            "stable_count": int((self.scored["risk_band"] == "stable").sum()),
        }

    def department_breakdown(self) -> list[dict]:
        grouped = (
            self.scored.groupby("department")
            .agg(
                headcount=("employee_id", "count"),
                attrition_rate=("left_company", "mean"),
                avg_risk=("attrition_risk", "mean"),
                avg_salary=("salary", "mean"),
                avg_tenure=("tenure_years", "mean"),
            )
            .reset_index()
            .sort_values("avg_risk", ascending=False)
        )
        return grouped.round(4).to_dict(orient="records")

    def risk_distribution(self) -> list[dict]:
        distribution = (
            self.scored.groupby("risk_band")
            .agg(employees=("employee_id", "count"), left_company_rate=("left_company", "mean"))
            .reset_index()
        )
        order = {"critical": 0, "elevated": 1, "stable": 2}
        distribution["sort_order"] = distribution["risk_band"].map(order)
        distribution = distribution.sort_values("sort_order").drop(columns=["sort_order"])
        return distribution.round(4).to_dict(orient="records")

    def top_employees(self, limit: int = 12) -> list[dict]:
        ranked = self.scored.sort_values(["attrition_risk", "salary"], ascending=[False, False]).head(limit)
        rows = []
        for _, row in ranked.iterrows():
            rows.append(
                {
                    "employee_id": row["employee_id"],
                    "department": row["department"],
                    "attrition_risk": round(float(row["attrition_risk"]), 4),
                    "risk_band": row["risk_band"],
                    "salary": round(float(row["salary"]), 2),
                    "tenure_years": round(float(row["tenure_years"]), 1),
                    "performance_score": round(float(row["performance_score"]), 1),
                    "left_company": int(row["left_company"]),
                    "drivers": self.model.explain_row(row),
                }
            )
        return rows

    def risk_vs_tenure(self) -> list[dict]:
        return (
            self.scored[["employee_id", "department", "tenure_years", "salary", "attrition_risk", "risk_band"]]
            .sort_values("attrition_risk", ascending=False)
            .round(4)
            .to_dict(orient="records")
        )

    def driver_summary(self) -> list[dict]:
        weights = list(zip(self.artifacts.feature_names, self.artifacts.weights))
        top = sorted(weights, key=lambda item: abs(item[1]), reverse=True)[:8]
        output = []
        for feature, weight in top:
            direction = "raises risk" if weight > 0 else "reduces risk"
            output.append(
                {
                    "feature": feature.replace("department_", "").replace("_", " "),
                    "weight": round(float(weight), 4),
                    "direction": direction,
                }
            )
        return output

    def dashboard_payload(self) -> dict:
        return {
            "summary": self.summary(),
            "department_breakdown": self.department_breakdown(),
            "risk_distribution": self.risk_distribution(),
            "top_employees": self.top_employees(),
            "risk_vs_tenure": self.risk_vs_tenure(),
            "driver_summary": self.driver_summary(),
        }

    def predict(self, payload: dict) -> dict:
        required = {
            "age",
            "salary",
            "department",
            "tenure_years",
            "performance_score",
            "perf_was_missing",
        }
        missing = sorted(required.difference(payload))
        if missing:
            raise ValueError(f"Missing fields: {', '.join(missing)}")

        frame = pd.DataFrame([payload])
        frame["department"] = frame["department"].astype(str).str.title()
        frame["perf_was_missing"] = frame["perf_was_missing"].astype(int)
        for column in ["age", "salary", "tenure_years", "performance_score"]:
            frame[column] = pd.to_numeric(frame[column], errors="raise")
        probability = float(self.model.predict_proba(frame)[0])
        explanation = self.model.explain_row(frame.iloc[0])
        return {
            "attrition_risk": round(probability, 4),
            "risk_band": self._risk_band(probability),
            "drivers": explanation,
        }
