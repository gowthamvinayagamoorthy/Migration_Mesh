"""
MigrationMesh - Fast Real Terraform Plan Generator
Uses official HashiCorp Terraform CLI to generate real `terraform show -json` plan outputs:
1. Safe Create (local_file)
2. Safe Create (aws_s3_bucket)
3. Safe Update (in-place tag change)
4. Safe Module Create (module.networking.aws_vpc)
5. Safe Data Source Read (data.aws_iam_policy_document)
6. Destructive Drop (aws_rds_cluster delete)
7. Destructive Forced Replacement (aws_rds_cluster requires_new via cluster_identifier)
8. Destructive Nested Module Replacement (module.database.aws_db_instance requires_new)
9. Destructive S3 Bucket Delete (aws_s3_bucket delete)
10. Destructive EBS Volume Delete (aws_ebs_volume delete)
"""

import os
import shutil
import json
import subprocess

BIN_TF = "/Users/gowthamv/Desktop/sem_proj_v/bin/terraform"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLANS_DIR = os.path.join(BASE_DIR, "real_plans")
SRC_DIR = os.path.join(BASE_DIR, "real_plans_src")
os.makedirs(PLANS_DIR, exist_ok=True)

AWS_CACHED_DIR = os.path.join(SRC_DIR, "aws_plan_safe")


def copy_cached_provider(target_dir: str):
    os.makedirs(target_dir, exist_ok=True)
    src_dot_tf = os.path.join(AWS_CACHED_DIR, ".terraform")
    src_lock = os.path.join(AWS_CACHED_DIR, ".terraform.lock.hcl")
    tgt_dot_tf = os.path.join(target_dir, ".terraform")
    tgt_lock = os.path.join(target_dir, ".terraform.lock.hcl")

    if os.path.exists(src_dot_tf) and not os.path.exists(tgt_dot_tf):
        shutil.copytree(src_dot_tf, tgt_dot_tf)
    if os.path.exists(src_lock) and not os.path.exists(tgt_lock):
        shutil.copy2(src_lock, tgt_lock)


def create_state_file(target_dir: str, resources: list):
    state_payload = {
        "version": 4,
        "terraform_version": "1.10.5",
        "serial": 1,
        "lineage": "mesh-test-lineage-2026",
        "outputs": {},
        "resources": resources
    }
    with open(os.path.join(target_dir, "terraform.tfstate"), "w") as f:
        json.dump(state_payload, f, indent=2)


def main():
    print("Generating Real Terraform Plans using Terraform CLI:", BIN_TF)

    # 1. Plan 4: Real RDS Cluster Delete
    p4_dir = os.path.join(SRC_DIR, "plan4_destroy")
    copy_cached_provider(p4_dir)
    with open(os.path.join(p4_dir, "main.tf"), "w") as f:
        f.write("""
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.40" }
  }
}
provider "aws" {
  region = "us-east-1"
  access_key = "mock"
  secret_key = "mock"
  skip_credentials_validation = true
  skip_requesting_account_id = true
}
""")
    create_state_file(p4_dir, [
        {
            "mode": "managed",
            "type": "aws_rds_cluster",
            "name": "aurora_postgres",
            "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
            "instances": [
                {
                    "schema_version": 0,
                    "attributes": {
                        "id": "prod-aurora-db",
                        "cluster_identifier": "prod-aurora-db",
                        "engine": "aurora-postgresql"
                    }
                }
            ]
        }
    ])
    subprocess.run([BIN_TF, "init", "-plugin-dir=" + os.path.join(AWS_CACHED_DIR, ".terraform/providers")], cwd=p4_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([BIN_TF, "plan", "-out=tfplan", "-no-color", "-refresh=false"], cwd=p4_dir, check=True)
    out_json = subprocess.check_output([BIN_TF, "show", "-json", "tfplan"], cwd=p4_dir).decode("utf-8")
    with open(os.path.join(PLANS_DIR, "real_plan_04_rds_cluster_delete.json"), "w") as f:
        f.write(out_json)
    print(" -> Generated real_plan_04_rds_cluster_delete.json")

    # 2. Plan 5: Real RDS Cluster Forced Replacement (requires_new)
    p5_dir = os.path.join(SRC_DIR, "plan5_replace")
    copy_cached_provider(p5_dir)
    with open(os.path.join(p5_dir, "main.tf"), "w") as f:
        f.write("""
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.40" }
  }
}
provider "aws" {
  region = "us-east-1"
  access_key = "mock"
  secret_key = "mock"
  skip_credentials_validation = true
  skip_requesting_account_id = true
}
resource "aws_rds_cluster" "aurora_postgres" {
  cluster_identifier = "new-changed-cluster-id"
  engine = "aurora-postgresql"
  skip_final_snapshot = true
}
""")
    create_state_file(p5_dir, [
        {
            "mode": "managed",
            "type": "aws_rds_cluster",
            "name": "aurora_postgres",
            "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
            "instances": [
                {
                    "schema_version": 0,
                    "attributes": {
                        "id": "old-cluster-id",
                        "cluster_identifier": "old-cluster-id",
                        "engine": "aurora-postgresql",
                        "engine_mode": "provisioned"
                    }
                }
            ]
        }
    ])
    subprocess.run([BIN_TF, "init", "-plugin-dir=" + os.path.join(AWS_CACHED_DIR, ".terraform/providers")], cwd=p5_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([BIN_TF, "plan", "-out=tfplan", "-no-color", "-refresh=false"], cwd=p5_dir, check=True)
    out_json = subprocess.check_output([BIN_TF, "show", "-json", "tfplan"], cwd=p5_dir).decode("utf-8")
    with open(os.path.join(PLANS_DIR, "real_plan_05_rds_forced_replacement.json"), "w") as f:
        f.write(out_json)
    print(" -> Generated real_plan_05_rds_forced_replacement.json")

    # 3. Plan 6: Real Nested Module Database Replacement
    p6_dir = os.path.join(SRC_DIR, "plan6_module")
    copy_cached_provider(p6_dir)
    os.makedirs(os.path.join(p6_dir, "modules", "db"), exist_ok=True)
    with open(os.path.join(p6_dir, "modules", "db", "main.tf"), "w") as f:
        f.write("""
terraform {
  required_providers {
    aws = { source = "hashicorp/aws" }
  }
}
resource "aws_db_instance" "postgres" {
  identifier = "new-db-name"
  instance_class = "db.t3.micro"
  engine = "postgres"
  skip_final_snapshot = true
}
""")
    with open(os.path.join(p6_dir, "main.tf"), "w") as f:
        f.write("""
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.40" }
  }
}
provider "aws" {
  region = "us-east-1"
  access_key = "mock"
  secret_key = "mock"
  skip_credentials_validation = true
  skip_requesting_account_id = true
}
module "database_tier" {
  source = "./modules/db"
}
""")
    create_state_file(p6_dir, [
        {
            "module": "module.database_tier",
            "mode": "managed",
            "type": "aws_db_instance",
            "name": "postgres",
            "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
            "instances": [
                {
                    "schema_version": 1,
                    "attributes": {
                        "id": "old-db-name",
                        "identifier": "old-db-name",
                        "instance_class": "db.t3.micro",
                        "engine": "postgres"
                    }
                }
            ]
        }
    ])
    subprocess.run([BIN_TF, "init", "-plugin-dir=" + os.path.join(AWS_CACHED_DIR, ".terraform/providers")], cwd=p6_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([BIN_TF, "plan", "-out=tfplan", "-no-color", "-refresh=false"], cwd=p6_dir, check=True)
    out_json = subprocess.check_output([BIN_TF, "show", "-json", "tfplan"], cwd=p6_dir).decode("utf-8")
    with open(os.path.join(PLANS_DIR, "real_plan_06_nested_module_db_replace.json"), "w") as f:
        f.write(out_json)
    print(" -> Generated real_plan_06_nested_module_db_replace.json")

    # 4. Plan 7: Real Data Source Read (Must be ignored by gate)
    p7_dir = os.path.join(SRC_DIR, "plan7_data_source")
    copy_cached_provider(p7_dir)
    with open(os.path.join(p7_dir, "main.tf"), "w") as f:
        f.write("""
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.40" }
  }
}
provider "aws" {
  region = "us-east-1"
  access_key = "mock"
  secret_key = "mock"
  skip_credentials_validation = true
  skip_requesting_account_id = true
}
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"
    principals {
      type = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}
""")
    subprocess.run([BIN_TF, "init", "-plugin-dir=" + os.path.join(AWS_CACHED_DIR, ".terraform/providers")], cwd=p7_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([BIN_TF, "plan", "-out=tfplan", "-no-color"], cwd=p7_dir, check=True)
    out_json = subprocess.check_output([BIN_TF, "show", "-json", "tfplan"], cwd=p7_dir).decode("utf-8")
    with open(os.path.join(PLANS_DIR, "real_plan_07_data_source_read_safe.json"), "w") as f:
        f.write(out_json)
    print(" -> Generated real_plan_07_data_source_read_safe.json")

    # 5. Plan 8: Real In-Place Tag Update (Safe update)
    p8_dir = os.path.join(SRC_DIR, "plan8_tag_update")
    copy_cached_provider(p8_dir)
    with open(os.path.join(p8_dir, "main.tf"), "w") as f:
        f.write("""
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.40" }
  }
}
provider "aws" {
  region = "us-east-1"
  access_key = "mock"
  secret_key = "mock"
  skip_credentials_validation = true
  skip_requesting_account_id = true
}
resource "aws_rds_cluster" "aurora_postgres" {
  cluster_identifier = "prod-aurora-db"
  engine = "aurora-postgresql"
  tags = { Environment = "production-v2" }
  skip_final_snapshot = true
}
""")
    create_state_file(p8_dir, [
        {
            "mode": "managed",
            "type": "aws_rds_cluster",
            "name": "aurora_postgres",
            "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
            "instances": [
                {
                    "schema_version": 0,
                    "attributes": {
                        "id": "prod-aurora-db",
                        "cluster_identifier": "prod-aurora-db",
                        "engine": "aurora-postgresql",
                        "tags": { "Environment": "production-v1" }
                    }
                }
            ]
        }
    ])
    subprocess.run([BIN_TF, "init", "-plugin-dir=" + os.path.join(AWS_CACHED_DIR, ".terraform/providers")], cwd=p8_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([BIN_TF, "plan", "-out=tfplan", "-no-color", "-refresh=false"], cwd=p8_dir, check=True)
    out_json = subprocess.check_output([BIN_TF, "show", "-json", "tfplan"], cwd=p8_dir).decode("utf-8")
    with open(os.path.join(PLANS_DIR, "real_plan_08_safe_in_place_tag_update.json"), "w") as f:
        f.write(out_json)
    print(" -> Generated real_plan_08_safe_in_place_tag_update.json")


if __name__ == "__main__":
    main()
