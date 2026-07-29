from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.contracts import (
    load_test_policy,
    validate_execution_result,
    validate_task_contract,
    validate_test_waiver,
)
from tests.helpers import FRAMEWORK_ROOT, full_contract, full_result


class TaskContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_test_policy(FRAMEWORK_ROOT)

    def test_complete_contract_is_valid(self) -> None:
        self.assertEqual([], validate_task_contract(full_contract(), self.policy))

    def test_file_outside_scope_is_rejected(self) -> None:
        result = full_result()
        result["changes"]["files_modified"].append("app/auth.py")
        issues = validate_execution_result(full_contract(), result, self.policy)
        self.assertIn("file-out-of-scope", {item["code"] for item in issues})

    def test_acceptance_criterion_without_evidence_is_rejected(self) -> None:
        result = full_result()
        result["acceptance_evidence"]["AC-02"] = []
        issues = validate_execution_result(full_contract(), result, self.policy)
        self.assertIn(
            "acceptance-evidence-missing", {item["code"] for item in issues}
        )

    def test_red_green_trace_is_executable_policy(self) -> None:
        result = full_result()
        result["verification"]["commands_run"] = [
            item
            for item in result["verification"]["commands_run"]
            if item["stage"] != "red"
        ]
        issues = validate_execution_result(full_contract(), result, self.policy)
        self.assertIn("red-missing", {item["code"] for item in issues})

    def test_valid_waiver_requires_specific_alternative_evidence(self) -> None:
        waiver = {
            "reason": "CSS-only visual alignment with no executable behavior",
            "approved_by": "framework-policy",
            "alternative_evidence": [
                "desktop screenshot",
                "mobile screenshot",
                "browser console clean",
            ],
        }
        self.assertEqual([], validate_test_waiver(waiver))

    def test_invalid_generic_waiver_is_rejected(self) -> None:
        waiver = {
            "reason": "Não foi possível testar",
            "approved_by": "framework-policy",
            "alternative_evidence": [],
        }
        issues = validate_test_waiver(waiver)
        self.assertEqual(
            {"waiver-reason", "waiver-evidence"},
            {item["code"] for item in issues},
        )

    def test_executor_cannot_claim_verified(self) -> None:
        result = full_result()
        result["task"]["result"] = "verified"
        issues = validate_execution_result(full_contract(), result, self.policy)
        self.assertIn("executor-authority", {item["code"] for item in issues})


if __name__ == "__main__":
    unittest.main()

