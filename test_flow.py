from fastapi.testclient import TestClient
from app.main import app
c = TestClient(app)
LOW = b"Standard services agreement. Governing law: Texas."
HIGH = b"Vendor accepts unlimited liability. Contract will auto renew. Exclusive supplier. Escrow of source code."

def up(body, role="vendor"):
    return c.post("/contracts?vendor=Acme", files={"file": ("a.pdf", body)}, headers={"x-role": role})

def test_low_risk_auto_approves():
    assert up(LOW).json()["stage"] == "Awaiting signature"

def test_high_risk_routes_to_review():
    r = up(HIGH).json(); assert r["stage"] == "In review" and r["risk"] > 25

def test_rbac():
    cid = up(HIGH).json()["id"]
    assert c.put(f"/contracts/{cid}/redline", json={"text": "x"}, headers={"x-role": "stakeholder"}).status_code == 403
    assert c.put(f"/contracts/{cid}/redline", json={"text": "x"}, headers={"x-role": "governance"}).status_code == 200
    assert c.get("/contracts", headers={"x-role": "vendor"}).status_code == 403
