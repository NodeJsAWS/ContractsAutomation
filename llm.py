"""Clause extraction + playbook risk scoring (Vertex AI or rule-based mock)."""
import json, re
from .. import config

PLAYBOOK = {
    "Legal": [(r"unlimited liability", 40, "Unlimited liability"),
              (r"auto(matic)?(ally)? renew", 15, "Auto-renewal")],
    "Sales": [(r"exclusiv", 20, "Exclusivity clause")],
    "Engineering": [(r"source code|escrow", 15, "Source-code / escrow terms"),
                    (r"uptime.{0,20}(9[0-8]\.|[0-8]\d)%", 15, "Weak uptime SLA")],
    "Marketing": [(r"use of (name|logo)|publicity", 10, "Publicity rights")],
    "Support": [(r"response time.{0,30}(\d{2,}) ?(hours|days)", 10, "Slow support SLA")],
}

def analyze(text: str) -> dict:
    if config.LOCAL_MODE:
        return _rules(text)
    import vertexai
    from vertexai.generative_models import GenerativeModel
    vertexai.init(project=config.GCP_PROJECT, location=config.GCP_REGION)
    prompt = ("You are a contract analyst. Return ONLY JSON: "
              '{"risk":0-100,"flags":[{"dept":str,"clause":str,"rationale":str,"suggested_redline":str}]}\n\n'
              + text[:30000])
    out = GenerativeModel(config.VERTEX_MODEL).generate_content(prompt).text
    return json.loads(re.sub(r"```json|```", "", out).strip())

def _rules(text: str) -> dict:
    flags, risk = [], 0
    for dept, rules in PLAYBOOK.items():
        for pat, pts, name in rules:
            if re.search(pat, text, re.I):
                risk += pts
                flags.append({"dept": dept, "clause": name,
                              "rationale": f"Deviates from playbook ({pts} pts)",
                              "suggested_redline": f"Replace '{name}' with standard fallback language."})
    return {"risk": min(risk, 100), "flags": flags}
