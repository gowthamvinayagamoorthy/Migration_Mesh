"""
MigrationMesh - Empirical Evaluation & Benchmark Suite
Evaluates deterministic gates on two distinct test suites:
1. Unit Cases (20 synthetic cases)
2. Real Terraform CLI Plans (8 real `terraform show -json` plan outputs)

Reports exact counts, metrics, and Wilson 95% Confidence Intervals.
"""

import os
import sys
import glob
import json
import math
from typing import Dict, Any, List, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.core.destructive_gate import TerraformPlanDestructiveGate
from packages.core.schema_validator import TerraformProviderSchemaValidator


def compute_wilson_confidence_interval(successes: int, total: int) -> Tuple[float, float]:
    """Computes Wilson 95% score confidence interval for binomial proportion."""
    if total == 0:
        return 0.0, 0.0
    z = 1.95996  # 95% confidence
    p = successes / total
    denominator = 1 + (z ** 2) / total
    centre_adjusted_probability = p + (z ** 2) / (2 * total)
    adjusted_standard_deviation = math.sqrt((p * (1 - p) + (z ** 2) / (4 * total)) / total)

    lower_bound = (centre_adjusted_probability - z * adjusted_standard_deviation) / denominator
    upper_bound = (centre_adjusted_probability + z * adjusted_standard_deviation) / denominator

    return max(0.0, round(lower_bound * 100, 1)), min(100.0, round(upper_bound * 100, 1))


class MigrationMeshHonestEvaluator:
    """
    Evaluator evaluating both Unit Cases and Real Terraform Plan JSON files.
    """

    def __init__(self):
        self.destructive_gate = TerraformPlanDestructiveGate()
        self.schema_validator = TerraformProviderSchemaValidator()
        self.unit_plans_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unit_test_plans.json")
        self.real_plans_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "real_plans")

    def evaluate_unit_cases(self) -> Dict[str, Any]:
        with open(self.unit_plans_path, "r") as f:
            cases = json.load(f)

        total = len(cases)
        tp, tn, fp, fn = 0, 0, 0, 0

        for case in cases:
            expected = case["expected_verdict"]  # "SAFE" or "FAULTY"
            is_approved, _ = self.destructive_gate.evaluate_plan_json(case["plan_data"])
            actual = "SAFE" if is_approved else "FAULTY"

            if expected == "FAULTY" and actual == "FAULTY":
                tp += 1
            elif expected == "SAFE" and actual == "SAFE":
                tn += 1
            elif expected == "SAFE" and actual == "FAULTY":
                fp += 1
            elif expected == "FAULTY" and actual == "SAFE":
                fn += 1

        accuracy_ci = compute_wilson_confidence_interval(tp + tn, total)
        detection_ci = compute_wilson_confidence_interval(tp, tp + fn) if (tp + fn) > 0 else (0.0, 0.0)

        return {
            "test_set_name": "Unit Cases (Handwritten)",
            "total_cases": total,
            "counts": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
            "accuracy": f"{tp + tn}/{total} ({round(((tp + tn) / total) * 100, 1)}%, 95% CI: [{accuracy_ci[0]}%, {accuracy_ci[1]}%])",
            "detection_rate_recall": f"{tp}/{tp + fn} ({round((tp / (tp + fn)) * 100, 1)}%, 95% CI: [{detection_ci[0]}%, {detection_ci[1]}%])",
            "false_positive_rate": f"{fp}/{fp + tn} ({round((fp / (fp + tn)) * 100, 1)}%)",
            "false_negative_rate": f"{fn}/{tp + fn} ({round((fn / (tp + fn)) * 100, 1)}%)"
        }

    def evaluate_real_terraform_plans(self) -> Dict[str, Any]:
        plan_files = sorted(glob.glob(os.path.join(self.real_plans_dir, "*.json")))
        total = len(plan_files)
        tp, tn, fp, fn = 0, 0, 0, 0

        # Ground truth mapping for real generated Terraform plan files
        ground_truth = {
            "real_plan_01_safe_create.json": "SAFE",
            "real_plan_02_aws_s3_create.json": "SAFE",
            "real_plan_03_rds_create.json": "SAFE",
            "real_plan_04_rds_cluster_delete.json": "FAULTY",
            "real_plan_05_rds_forced_replacement.json": "FAULTY",
            "real_plan_06_nested_module_db_replace.json": "FAULTY",
            "real_plan_07_data_source_read_safe.json": "SAFE",
            "real_plan_08_safe_in_place_update.json": "SAFE"
        }

        for pf in plan_files:
            bname = os.path.basename(pf)
            expected = ground_truth.get(bname, "SAFE")
            is_approved, _ = self.destructive_gate.evaluate_plan_json_file(pf)
            actual = "SAFE" if is_approved else "FAULTY"

            if expected == "FAULTY" and actual == "FAULTY":
                tp += 1
            elif expected == "SAFE" and actual == "SAFE":
                tn += 1
            elif expected == "SAFE" and actual == "FAULTY":
                fp += 1
            elif expected == "FAULTY" and actual == "SAFE":
                fn += 1

        accuracy_ci = compute_wilson_confidence_interval(tp + tn, total)
        detection_ci = compute_wilson_confidence_interval(tp, tp + fn) if (tp + fn) > 0 else (0.0, 0.0)

        return {
            "test_set_name": "Real Terraform CLI Plans (`terraform show -json`)",
            "total_cases": total,
            "counts": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
            "accuracy": f"{tp + tn}/{total} ({round(((tp + tn) / total) * 100, 1)}%, 95% CI: [{accuracy_ci[0]}%, {accuracy_ci[1]}%])",
            "detection_rate_recall": f"{tp}/{tp + fn} ({round((tp / (tp + fn)) * 100, 1)}%, 95% CI: [{detection_ci[0]}%, {detection_ci[1]}%])",
            "false_positive_rate": f"{fp}/{fp + tn} ({round((fp / (fp + tn)) * 100, 1)}%)",
            "false_negative_rate": f"{fn}/{tp + fn} ({round((fn / (tp + fn)) * 100, 1)}%)"
        }

    def run_all_evaluations(self) -> Dict[str, Any]:
        unit_res = self.evaluate_unit_cases()
        real_res = self.evaluate_real_terraform_plans()

        print("=" * 80)
        print("MIGRATIONMESH RIGOROUS EVALUATION REPORT")
        print("=" * 80)
        print(f"SET 1: {unit_res['test_set_name']} (N={unit_res['total_cases']})")
        print(f"  - Accuracy:               {unit_res['accuracy']}")
        print(f"  - Detection Rate:         {unit_res['detection_rate_recall']}")
        print(f"  - False Positive Rate:    {unit_res['false_positive_rate']}")
        print(f"  - False Negative Rate:    {unit_res['false_negative_rate']}")
        print("-" * 80)
        print(f"SET 2: {real_res['test_set_name']} (N={real_res['total_cases']})")
        print(f"  - Accuracy:               {real_res['accuracy']}")
        print(f"  - Detection Rate:         {real_res['detection_rate_recall']}")
        print(f"  - False Positive Rate:    {real_res['false_positive_rate']}")
        print(f"  - False Negative Rate:    {real_res['false_negative_rate']}")
        print("=" * 80)
        print("NOTE: Human engineering baseline savings (~40 hrs manual review estimate)")
        print("is an unmeasured assumption, not an empirically timed human study.")
        print("=" * 80)

        return {"unit_cases": unit_res, "real_plans": real_res}


if __name__ == "__main__":
    evaluator = MigrationMeshHonestEvaluator()
    evaluator.run_all_evaluations()
