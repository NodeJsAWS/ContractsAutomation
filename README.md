# ContractFlow: contract review in under 3 business days (GCP)

AI-assisted contract intake, triage, parallel department review, governance redlining and e-sign closure.
Role model: **governance** (view/edit/redline/approve), **stakeholder** (view only), **vendor** (upload only).

## Run locally (no GCP needed)
```bash
cd backend && pip install -r requirements.txt
LOCAL_MODE=true uvicorn app.main:app --reload     # API docs at /docs
LOCAL_MODE=true python -m pytest -q
open ../frontend/dashboard.html                    # demo UI, works standalone
```
## Cloud mode
Set `LOCAL_MODE=false`, `GCP_PROJECT`, `DOCAI_PROCESSOR`; `cd infra/terraform && terraform apply -var project=YOUR_ID`.
Run `terraform destroy` when done to avoid charges.

## How it hits 3 days
Auto-approve low risk, route flagged clauses only to the departments concerned in parallel, 24h SLA timers, single vendor thread, webhook-driven closure.

## Roadmap
Cloud SQL + pgvector persistence, Identity Platform JWT verification, Cloud Tasks SLA escalation, TipTap tracked-changes editor, extraction eval set.
