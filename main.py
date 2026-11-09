import time, uuid, os
from enum import Enum
from fastapi import FastAPI, UploadFile, File, Depends, Header, HTTPException
from pydantic import BaseModel
from .pipeline.graph import pipeline
from . import config

app = FastAPI(title="ContractFlow")
DB: dict = {}   # swap for Cloud SQL; kept in-memory for demo
AUDIT: list = []

class Role(str, Enum):
    governance = "governance"; stakeholder = "stakeholder"; vendor = "vendor"

def user(x_role: str = Header("vendor"), x_user: str = Header("demo")):
    """Demo auth. Production: verify Identity Platform JWT and read role from custom claims."""
    try: return {"id": x_user, "role": Role(x_role)}
    except ValueError: raise HTTPException(401, "Unknown role")

def need(*roles):
    def dep(u=Depends(user)):
        if u["role"] not in roles: raise HTTPException(403, f"{u['role'].value} cannot do this")
        return u
    return dep

def log(u, action, cid): AUDIT.append({"t": time.time(), "user": u["id"], "role": u["role"], "action": action, "contract": cid})

@app.post("/contracts")
async def upload(vendor: str, value: float = 0, file: UploadFile = File(...), u=Depends(need(Role.vendor, Role.governance))):
    cid = str(uuid.uuid4())[:8]
    out = pipeline.invoke({"raw": await file.read()})
    DB[cid] = {"id": cid, "vendor": vendor, "value": value, "created": time.time(),
               "sla_due": time.time() + config.SLA_HOURS * 3600, "redline": out["text"], **{k: out[k] for k in ("risk", "flags", "reviews", "stage")}}
    log(u, "upload", cid); return DB[cid]

@app.get("/contracts")
def pipeline_view(u=Depends(need(Role.governance, Role.stakeholder))):
    return sorted(DB.values(), key=lambda c: -c["risk"])

@app.get("/contracts/{cid}")
def detail(cid: str, u=Depends(need(Role.governance, Role.stakeholder))):
    if cid not in DB: raise HTTPException(404)
    return DB[cid]

class Edit(BaseModel): text: str

@app.put("/contracts/{cid}/redline")
def redline(cid: str, e: Edit, u=Depends(need(Role.governance))):   # edit rights: governance only
    DB[cid]["redline"] = e.text; log(u, "redline", cid); return DB[cid]

@app.post("/contracts/{cid}/review/{dept}")
def review(cid: str, dept: str, u=Depends(need(Role.governance))):
    c = DB[cid]; c["reviews"][dept] = "approved"
    if all(v == "approved" for v in c["reviews"].values()): c["stage"] = "Awaiting signature"
    log(u, f"approve:{dept}", cid); return c

@app.post("/webhooks/esign")   # DocuSign/Dropbox Sign callback -> Pub/Sub in production
def esign(payload: dict):
    c = DB.get(payload.get("contract_id"))
    if c and payload.get("status") == "completed":
        c["stage"] = "Complete"; c["cycle_hours"] = round((time.time() - c["created"]) / 3600, 2)
    return {"ok": True}

@app.get("/kpis")
def kpis(u=Depends(need(Role.governance))):
    done = [c["cycle_hours"] for c in DB.values() if "cycle_hours" in c]
    return {"total": len(DB), "avg_cycle_hours": sum(done) / len(done) if done else None,
            "overdue": sum(time.time() > c["sla_due"] and c["stage"] != "Complete" for c in DB.values())}
