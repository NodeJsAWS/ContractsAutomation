import os
LOCAL_MODE = os.getenv("LOCAL_MODE", "true").lower() == "true"  # no GCP creds needed
GCP_PROJECT = os.getenv("GCP_PROJECT", "")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
DOCAI_PROCESSOR = os.getenv("DOCAI_PROCESSOR", "")  # projects/../processors/..
VERTEX_MODEL = os.getenv("VERTEX_MODEL", "gemini-1.5-pro")
SLA_HOURS = int(os.getenv("SLA_HOURS", "24"))
AUTO_APPROVE_MAX_RISK = int(os.getenv("AUTO_APPROVE_MAX_RISK", "25"))
DEPARTMENTS = ["Legal", "Marketing", "Sales", "Engineering", "Support"]
