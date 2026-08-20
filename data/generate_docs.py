import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent

def generate_kb_docs():
    kb_data = [
        {
            "id": "KB-AUTH-001",
            "category": "Authentication",
            "title": "Corporate Outlook Password Reset Procedure",
            "keywords": ["outlook", "password", "reset", "active directory", "mfa"],
            "solution": "1. Navigate to identity.company.com.\n2. Click 'Self-Service Password Reset'.\n3. Complete MFA challenge via Authenticator App.\n4. Enter new compliant password (16+ chars).\n5. Wait 5 minutes for AD synchronization."
        },
        {
            "id": "KB-AUTH-002",
            "category": "Authentication",
            "title": "SSO Token Expiration and Session Cache Clearance",
            "keywords": ["sso", "token", "okta", "saml", "login failed", "unauthorized"],
            "solution": "1. Clear browser cookies and local storage for domain *.company.com.\n2. Revoke active OAuth tokens via Okta dashboard.\n3. Execute 'kinit -R' on Linux workstations to refresh Kerberos tickets."
        },
        {
            "id": "KB-INFRA-001",
            "category": "Infrastructure",
            "title": "EC2 High CPU Remediation Playbook",
            "keywords": ["ec2", "cpu", "aws", "high utilization", "process lock"],
            "solution": "1. Run top/htop to identify rogue PID.\n2. Inspect CloudWatch metric granularities (1-min intervals).\n3. Scale ASG desired capacity by +1 if traffic surge.\n4. Capture thread dump if Java process, then issue SIGTERM."
        },
        {
            "id": "KB-CODE-001",
            "category": "Code",
            "title": "Java Spring Boot NullPointerException Troubleshooting",
            "keywords": ["java", "spring boot", "nullpointerexception", "npe", "exception"],
            "solution": "1. Inspect stack trace line number.\n2. Verify @Autowired dependencies are registered beans.\n3. Check Optional wrapper implementations on service layer queries.\n4. Enable debug log level: logging.level.org.springframework=DEBUG."
        },
        {
            "id": "KB-BILLING-001",
            "category": "Billing",
            "title": "AWS Cost Anomaly Investigation",
            "keywords": ["aws", "bill", "cost", "spike", "cloud", "budget"],
            "solution": "1. Access AWS Cost Explorer -> Anomaly Detection.\n2. Filter by UsageType to locate resource spikes (e.g., Unblended Cost).\n3. Check orphan EBS volumes, NAT Gateway egress, or unattached Elastic IPs."
        }
    ]
    with open(DATA_DIR / "kb.json", "w") as f:
        json.dump(kb_data, f, indent=2)

def generate_monitoring_docs():
    monitoring_data = {
        "metrics": [
            {
                "resource_id": "i-0a8f912c4b1112e",
                "resource_name": "prod-api-cluster-node-01",
                "type": "EC2 Instance",
                "metrics": {"cpu_utilization": "98.4%", "memory_used": "88.2%", "disk_iops": "14200"},
                "status": "CRITICAL",
                "alerts": ["CPUThresholdExceeded", "HighMemoryPaging"]
            },
            {
                "resource_id": "db-aurora-prod-writer",
                "resource_name": "production-aurora-pg-writer",
                "type": "RDS PostgreSQL",
                "metrics": {"cpu_utilization": "99.1%", "active_connections": "480/500", "read_latency": "140ms"},
                "status": "CRITICAL",
                "alerts": ["ConnectionPoolExhaustion", "LockWaitTimeout"]
            }
        ]
    }
    with open(DATA_DIR / "monitoring_telemetry.json", "w") as f:
        json.dump(monitoring_data, f, indent=2)

def generate_git_docs():
    git_data = {
        "repositories": [
            {
                "repo_name": "core-payment-service",
                "recent_commits": [
                    {
                        "commit_hash": "7a8f92b",
                        "author": "dev-user@company.com",
                        "message": "Refactor user authentication pipeline and remove null check",
                        "changed_files": ["src/main/java/com/company/auth/AuthService.java"]
                    }
                ]
            }
        ]
    }
    with open(DATA_DIR / "git_repositories.json", "w") as f:
        json.dump(git_data, f, indent=2)

def generate_billing_docs():
    billing_data = {
        "accounts": [
            {
                "account_id": "aws-prod-110293",
                "current_month_cost": "$142,500.00",
                "previous_month_cost": "$98,000.00",
                "variance": "+45.4%",
                "top_cost_drivers": [
                    {"service": "Amazon EC2", "cost": "$62,000.00", "increase_reason": "Provisioned m5.8xlarge instances"},
                    {"service": "AWS NAT Gateway", "cost": "$28,400.00", "increase_reason": "Cross-region data transfer spike"}
                ]
            }
        ]
    }
    with open(DATA_DIR / "billing_records.json", "w") as f:
        json.dump(billing_data, f, indent=2)

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generate_kb_docs()
    generate_monitoring_docs()
    generate_git_docs()
    generate_billing_docs()
    print("Successfully generated all mock data documents in 'data/' directory.")

if __name__ == "__main__":
    main()

