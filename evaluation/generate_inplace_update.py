import os
import json
import subprocess

BIN_TF = "/Users/gowthamv/Desktop/sem_proj_v/bin/terraform"
p1_dir = "evaluation/real_plans_src/plan1_safe"

# 1. Apply plan1 to create local state
subprocess.run([BIN_TF, "apply", "-auto-approve", "tfplan"], cwd=p1_dir, check=True)

# 2. Modify permissions in main.tf (which is an in-place update for local_file)
with open(os.path.join(p1_dir, "main.tf"), "w") as f:
    f.write("""
terraform {
  required_providers {
    local = { source = "hashicorp/local", version = "~> 2.5" }
  }
}
resource "local_file" "app_config" {
  content         = "application_mode = production\\nversion = 1.0.0"
  filename        = "${path.module}/app_config.txt"
  file_permission = "0644"
}
""")

subprocess.run([BIN_TF, "plan", "-out=tfplan_update", "-no-color"], cwd=p1_dir, check=True)
out_json = subprocess.check_output([BIN_TF, "show", "-json", "tfplan_update"], cwd=p1_dir).decode("utf-8")

with open("evaluation/real_plans/real_plan_08_safe_in_place_update.json", "w") as f:
    f.write(out_json)

# Remove old mismatched file if exists
if os.path.exists("evaluation/real_plans/real_plan_08_safe_in_place_tag_update.json"):
    os.remove("evaluation/real_plans/real_plan_08_safe_in_place_tag_update.json")

d = json.loads(out_json)
print("Actions for plan 8 in-place update:", d["resource_changes"][0]["change"]["actions"])
