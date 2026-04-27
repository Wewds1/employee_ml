import unittest

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from employee_ml.service import EmployeeIntelligenceService  # noqa: E402


class EmployeeIntelligenceServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = EmployeeIntelligenceService()

    def test_dashboard_payload_contains_expected_sections(self) -> None:
        payload = self.service.dashboard_payload()
        self.assertIn("summary", payload)
        self.assertIn("department_breakdown", payload)
        self.assertIn("top_employees", payload)
        self.assertGreater(len(payload["department_breakdown"]), 0)

    def test_prediction_returns_bounded_probability(self) -> None:
        prediction = self.service.predict(
            {
                "age": 31.0,
                "salary": 58000.0,
                "department": "Engineering",
                "tenure_years": 1.6,
                "performance_score": 2.0,
                "perf_was_missing": 0,
            }
        )
        self.assertGreaterEqual(prediction["attrition_risk"], 0.0)
        self.assertLessEqual(prediction["attrition_risk"], 1.0)
        self.assertIn(prediction["risk_band"], {"stable", "elevated", "critical"})


if __name__ == "__main__":
    unittest.main()
