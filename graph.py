"""LangGraph pipeline: intake -> triage -> (auto-approve | parallel dept review)."""
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from ..services import ocr, llm
from .. import config

class ContractState(TypedDict, total=False):
    raw: bytes
    text: str
    risk: int
    flags: List[Dict]
    reviews: Dict[str, str]   # dept -> pending|approved
    stage: str

def intake(s):  return {"text": ocr.extract_text(s["raw"]), "stage": "OCR complete"}

def triage(s):
    r = llm.analyze(s["text"])
    return {"risk": r["risk"], "flags": r["flags"], "stage": "Triaged"}

def route(s):
    return "auto" if s["risk"] <= config.AUTO_APPROVE_MAX_RISK and not s["flags"] else "review"

def auto_approve(s):
    return {"reviews": {d: "approved" for d in config.DEPARTMENTS}, "stage": "Awaiting signature"}

def fan_out(s):
    # Only depts with flagged clauses must review; all others auto-approve. Runs in parallel in the UI/SLA timers.
    need = {f["dept"] for f in s["flags"]} | {"Legal"}
    return {"reviews": {d: ("pending" if d in need else "approved") for d in config.DEPARTMENTS},
            "stage": "In review"}

g = StateGraph(ContractState)
for name, fn in [("intake", intake), ("triage", triage), ("auto", auto_approve), ("review", fan_out)]:
    g.add_node(name, fn)
g.set_entry_point("intake"); g.add_edge("intake", "triage")
g.add_conditional_edges("triage", route, {"auto": "auto", "review": "review"})
g.add_edge("auto", END); g.add_edge("review", END)
pipeline = g.compile()
