import os, re
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from . import db, ml, service
class JobIn(BaseModel):
    title: str = Field(min_length=2,max_length=200)
    company: str = Field(default="",max_length=200)
    company_website: str = Field(default="",max_length=300)
    description: str = Field(min_length=20,max_length=20000)
    qualifications: str = Field(default="",max_length=5000)
    salary: str = Field(default="",max_length=200)
    employment_type: str = Field(default="",max_length=60)
    location: str = Field(default="",max_length=200)
    recruiter_email: str = Field(default="",max_length=200)
    application_url: str = Field(default="",max_length=500)
    @field_validator("*",mode="before")
    @classmethod
    def clean(cls,v): return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]","",v).strip() if isinstance(v,str) else v
    @field_validator("recruiter_email")
    @classmethod
    def email_ok(cls,v):
        if v and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",v): raise ValueError("Recruiter email format is invalid")
        return v
@asynccontextmanager
async def lifespan(app):
    db.init(); ml.load(); yield
app = FastAPI(title="JobShield AI",version="1.0",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=os.getenv("ALLOWED_ORIGINS","http://localhost:5173").split(","),allow_methods=["GET","POST","DELETE"],allow_headers=["Content-Type"])
@app.get("/api/health")
def health(): return {"status":"ok","model_loaded":ml.info() is not None}
@app.get("/api/model")
def model_info(): return ml.info() or {"selected_model":None,"note":"No model trained. Run train.py. Rule-based baseline in use."}
@app.post("/api/analyze")
def analyze(job: JobIn):
    try:
        res = service.run(job.model_dump()); res["id"] = db.save(job.title,job.company,res); return res
    except Exception:
        raise HTTPException(500,"Analysis failed. Please try again.")
@app.get("/api/history")
def history(): return db.all_()
@app.delete("/api/history/{item_id}")
def delete(item_id: int):
    if not db.delete(item_id): raise HTTPException(404,"History entry not found")
    return {"deleted":item_id}

class BatchIn(BaseModel):
    jobs: list[JobIn] = Field(min_length=1, max_length=20)
@app.post("/api/batch")
def batch(b: BatchIn):
    out = []
    for j in b.jobs:
        r = service.run(j.model_dump()); db.save(j.title, j.company, r)
        out.append({"title": j.title, "prediction": r["prediction"], "risk_score": r["risk_score"], "risk_level": r["risk_level"]})
    return out
@app.get("/api/stats")
def stats():
    items = db.all_(); lv = {"Low": 0, "Medium": 0, "High": 0}
    for i in items: lv[i["risk_level"]] = lv.get(i["risk_level"], 0) + 1
    return {"total": len(items), "by_level": lv, "avg_risk": round(sum(i["risk_score"] for i in items)/len(items), 1) if items else 0}

class ScamIn(BaseModel):
    text: str = Field(min_length=10, max_length=5000)
    sender: str = Field(default="", max_length=200)
    url: str = Field(default="", max_length=500)
    @field_validator("*", mode="before")
    @classmethod
    def clean_(cls, v): return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", v).strip() if isinstance(v, str) else v
from . import scam
@app.post("/api/scam/analyze")
def scam_analyze(s: ScamIn):
    try:
        res = scam.analyze(s.text, s.sender, s.url); res["id"] = db.save("Message scan", s.sender, res); return res
    except Exception:
        raise HTTPException(500, "Analysis failed. Please try again.")
