from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "employee_clean.csv"


@dataclass(frozen=True)
class DatasetProfile:
    rows: int
    attrition_rate: float
    average_salary: float
    average_tenure: float


def load_employee_data(csv_path: Path | None = None) -> pd.DataFrame:
    path = csv_path or DATA_PATH
    frame = pd.read_csv(path)
    frame["department"] = frame["department"].astype(str).str.strip().str.title()
    frame["left_company"] = frame["left_company"].astype(int)
    frame["perf_was_missing"] = frame["perf_was_missing"].astype(int)
    return frame


def profile_dataset(frame: pd.DataFrame) -> DatasetProfile:
    return DatasetProfile(
        rows=int(len(frame)),
        attrition_rate=float(frame["left_company"].mean()),
        average_salary=float(frame["salary"].mean()),
        average_tenure=float(frame["tenure_years"].mean()),
    )
