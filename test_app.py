import os, tempfile
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(),"t.db")
from fastapi.testclient import TestClient
from app.main import app
GOOD = dict(title="Backend Engineer",company="Infosys Ltd",company_website="https://www.infosys.com",recruiter_email="careers@infosys.com",
 description="Responsibilities: design REST APIs, write tests and collaborate with product teams. Requirements: B.Tech in CS and 3+ years of experience. Benefits include health insurance and provident fund. Interview process: assessment, technical round and HR round. "*2,qualifications="B.Tech",salary="12-18 LPA")
FAKE = dict(title="Data Entry",company="Global Online",recruiter_email="hr.global@gmail.com",salary="Rs 5000 per day",
 description="URGENT hiring!!! No experience required. Pay Rs 1500 registration fee (refundable) to confirm seat. Send your Aadhaar and bank details on WhatsApp. No interview, guaranteed job!")
def test_all():
    with TestClient(app) as c:
        assert c.get("/api/health").json()["status"]=="ok"
        g = c.post("/api/analyze",json=GOOD).json(); assert g["risk_level"]=="Low", g
        f = c.post("/api/analyze",json=FAKE).json(); assert f["risk_level"]=="High", f
        assert c.post("/api/analyze",json={}).status_code==422                      # empty form
        m = c.post("/api/analyze",json=dict(title="Clerk",description="Need clerk for office work in town please apply soon")).json()
        assert m["risk_level"] in ("Low","Medium")                                  # missing info is not auto-fake
        long = c.post("/api/analyze",json=dict(GOOD,description=GOOD["description"]*40)); assert long.status_code==200
        s = c.post("/api/analyze",json=dict(FAKE,recruiter_email="x@gmail.com",description="Contact us on Telegram t.me/job and bit.ly/apply for easy work from home task based income")).json(); assert s["warning_signs"]
        h = c.get("/api/history").json(); assert len(h)>=4
        assert c.delete(f"/api/history/{h[0]['id']}").status_code==200; assert c.delete("/api/history/99999").status_code==404
