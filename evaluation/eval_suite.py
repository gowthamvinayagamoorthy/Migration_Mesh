"""
MigrationMesh - Empirical Evaluation & Benchmark Suite
Evaluates deterministic gates on an independent, held-out dataset of 20 realistic Terraform Plan JSON cases.
Reports True Positives, True Negatives, False Positives, False Negatives, Precision, Recall, and real elapsed timers.
"""

import os
import sys
import json
import time
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.core.destructive_gate import TerraformPlanDestructiveGate
from packages.core.schema_validator import TerraformProviderSchemaValidator
from packages.policy_engine.python_policy_checker import PythonPolicyChecker
from packages.audit_ledger.hmac_hash_chain import HMACHashChain


class MigrationMeshHonestEvaluator:
    """
    Honest Evaluation Harness:
    Evaluates a held-out test suite of 20 independent Terraform plan cases
    (10 Safe plans, 10 Faulty/Destructive plans).
    """

    def __init__(self, dataset_path: Optional[str] = None):
        self.dataset_path = dataset_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "held_out_plans.json"
        )
        self.destructive_gate = TerraformPlanDestructiveGate()
        self.schema_validator = TerraformProviderSchemaValidator()
        self.policy_checker = PythonPolicyChecker()

    def run_held_out_evaluation(self) -> Dict[str, Any]:
        with open(self.dataset_path, "r") as f:
            cases = json.load(f)

        total_cases = len(cases)
        tp = 0  # Faulty plan correctly identified and blocked
        tn = 0  # Safe plan correctly approved
        fp = 0  # Safe plan erroneously blocked (false alarm)
        fn = 0  # Faulty plan missed and allowed through

        case_results = []
        start_timer = time.perf_counter()

        for case in cases:
            case_id = case["id"]
            case_name = case["name"]
            expected = case["expected_verdict"]  # "SAFE" or "FAULTY"
            plan_data = case["plan_data"]

            t0 = time.perf_counter()
            is_approved, violations = self.destructive_gate.evaluate_plan_json(plan_data)
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)

            actual = "SAFE" if is_approved else "FAULTY"

            if expected == "FAULTY" and actual == "FAULTY":
                tp += 1
                classification = "TRUE_POSITIVE"
            elif expected == "SAFE" and actual == "SAFE":
                tn += 1
                classification = "TRUE_NEGATIVE"
            elif expected == "SAFE" and actual == "FAULTY":
                fp += 1
                classification = "FALSE_POSITIVE"
            elif expected == "FAULTY" and actual == "SAFE":
                fn += 1
                classification = "FALSE_NEGATIVE"

            case_results.append({
                "id": case_id,
                "name": case_name,
                "expected": expected,
                "actual": actual,
                "classification": classification,
                "latency_ms": elapsed_ms,
                "violations_count": len(violations)
            })

        total_eval_time_sec = time.perf_counter() - start_timer
        avg_eval_time_ms = (total_eval_time_sec / total_cases) * 1000.0

        # Compute Metrics
        detection_rate_recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        false_positive_rate = (fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        false_negative_rate = (fn / (tp + fn)) if (tp + fn) > 0 else 0.0
        precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        accuracy = ((tp + tn) / total_cases) if total_cases > 0 else 0.0

        summary = {
            "evaluation_type": "HELD_OUT_INDEPENDENT_TEST_SET",
            "test_set_size": total_cases,
            "counts": {
                "total_cases": total_cases,
                "true_positives": tp,
                "true_negatives": tn,
                "false_positives": fp,
                "false_negatives": fn
            },
            "metrics": {
                "accuracy": f"{tp + tn}/{total_cases} ({round(accuracy * 100, 1)}%)",
                "detection_rate_recall": f"{tp}/{tp + fn} ({round(detection_rate_recall * 100, 1)}%)",
                "precision": f"{tp}/{tp + fp} ({round(precision * 100, 1)}%)",
                "false_positive_rate": f"{fp}/{fp + tn} ({round(false_positive_rate * 100, 1)}%)",
                "false_negative_rate": f"{fn}/{tp + fn} ({round(false_negative_rate * 100, 1)}%)"
            },
            "timing_measurements": {
                "total_evaluation_elapsed_seconds": round(total_eval_time_sec, 4),
                "average_plan_gate_latency_ms": round(avg_eval_time_ms, 3),
                "measurement_method": "real timer (time.perf_counter)"
            },
            "human_baseline_comparison": {
                "human_time_baseline": "Assumption, unmeasured (Estimated 40.0 hours for manual review & verification of a 3-tier architecture)",
                "note": "Net engineering time savings are projected relative to estimated human baseline, not an empirically timed human cohort study."
            },
            "detailed_case_results": case_results
        }

        self._print_summary_report(summary)
        return summary

    def _print_summary_report(self, summary: Dict[str, Any]):
        print("=" * 80)
        print("MIGRATIONMESH HONEST EVALUATION REPORT (HELD-OUT DATASET)")
        print("=" * 80)
        print(f"Dataset Size: {summary['test_set_size']} independent test plans")
        print(f"True Positives (Faulty blocked):   {summary['counts']['true_positives']}/10")
        print(f"True Negatives (Safe allowed):     {summary['counts']['true_negatives']}/10")
        print(f"False Positives (Safe blocked):    {summary['counts']['false_positives']}/10 (FPR: {summary['metrics']['false_positive_rate']})")
        print(f"False Negatives (Faulty missed):   {summary['counts']['false_negatives']}/10 (FNR: {summary['metrics']['false_negative_rate']})")
        print(f"Plan Gate Precision:              {summary['metrics']['precision']}")
        print(f"Detection Rate (Recall):          {summary['metrics']['detection_rate_recall']}")
        print(f"Avg Plan Gate Latency:            {summary['timing_measurements']['average_plan_gate_latency_ms']} ms (measured)")
        print(f"Human Baseline Status:            {summary['human_baseline_comparison']['human_time_baseline']}")
        print("=" * 80)


if __name__ == "__main__":
    evaluator = MigrationMeshHonestEvaluator()
    evaluator.run_held_out_evaluation()
