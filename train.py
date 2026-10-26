"""Train + evaluate fake-job classifiers.
Real data : place EMSCAD 'fake_job_postings.csv' (Kaggle: shivamb/real-or-fake-fake-jobposting-prediction) at data/fake_job_postings.csv
Fallback  : a SYNTHETIC demo dataset (template-generated). Metrics on it are NOT real-world performance."""
import json, random, sys
from pathlib import Path
import joblib, numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from app.ml import clean
D = Path(__file__).parent/"data"; M = Path(__file__).parent/"models"; SEED = 42

def synthetic(n=600):
    rnd = random.Random(SEED)
    roles = ["Software Engineer","Data Analyst","Accountant","Mechanical Engineer","Marketing Executive","Nurse","HR Associate","Sales Manager","Content Writer","Teacher"]
    good = ["Responsibilities include {t} and collaborating with the team.","Requirements: bachelor degree and {y} years of experience.","We offer health insurance, provident fund and paid leave.","Our interview process has an HR round and a technical round.","Join our established company; apply through the official careers page.","Strong communication and problem solving skills are required.","Location: {c}. Full-time position with a clear reporting structure."]
    bad = ["URGENT hiring, apply now, only {y} seats left!!!","Pay a refundable registration fee to confirm your seat.","No experience required, earn Rs 5000 per day from home.","Send your Aadhaar and bank details on WhatsApp.","Guaranteed job, no interview, direct selection.","Deposit a security fee and buy equipment from our vendor.","Contact the recruiter on Telegram, work from home typing work.","Financial freedom with passive income, recruit friends.","Congratulations you have been selected, share your OTP."]
    tasks = ["testing software","preparing reports","managing accounts","designing parts","running campaigns","patient care","onboarding staff","closing deals","writing articles","teaching students"]
    rows = []
    for i in range(n):
        fake = i%2; r = rnd.choice(roles)
        pool = bad if fake else good
        parts = [rnd.choice(pool).format(t=rnd.choice(tasks),y=rnd.randint(2,9),c=rnd.choice(["Pune","Delhi","Hyderabad","Bengaluru"])) for _ in range(rnd.randint(2,4))]
        if fake and rnd.random()<.35: parts.append(rnd.choice(good).format(t="reports",y=3,c="Chennai"))   # noise
        if not fake and rnd.random()<.25: parts.append(rnd.choice(bad).format(t="x",y=5,c="y"))        # noise
        rows.append({"text":f"{r}. "+" ".join(parts),"fraudulent":fake})
    return pd.DataFrame(rows)

def load():
    p = D/"fake_job_postings.csv"
    if p.exists():
        df = pd.read_csv(p)
        cols = [c for c in ["title","company_profile","description","requirements","benefits"] if c in df]
        df[cols] = df[cols].fillna("")                       # missing-value handling
        df["text"] = df[cols].agg(" ".join,axis=1)
        return df[["text","fraudulent"]], "EMSCAD (real dataset)"
    q = D/"sample_jobs.csv"
    if q.exists():
        df = pd.read_csv(q).fillna(""); df["text"] = df["title"]+" "+df["description"]+" "+df["salary"].astype(str)
        return df[["text","label"]].rename(columns={"label":"fraudulent"}), "SYNTHETIC DEMO DATA: sample_jobs.csv (gen_data.py), not real-world evidence"
    return synthetic(), "SYNTHETIC DEMO DATA (not real-world evidence)"

def main():
    df, src = load(); df["text"] = df["text"].map(clean)
    X_tr,X_te,y_tr,y_te = train_test_split(df["text"],df["fraudulent"],test_size=.2,stratify=df["fraudulent"],random_state=SEED)
    cands = {"LogisticRegression":LogisticRegression(max_iter=1000,class_weight="balanced"),
             "RandomForest":RandomForestClassifier(n_estimators=200,class_weight="balanced",random_state=SEED,n_jobs=-1)}
    res, best, best_f1 = {}, None, -1
    for name,clf in cands.items():
        pipe = Pipeline([("tfidf",TfidfVectorizer(ngram_range=(1,2),min_df=2,max_features=30000,stop_words="english",sublinear_tf=True)),("clf",clf)]).fit(X_tr,y_tr)
        pr = pipe.predict(X_te); f1 = f1_score(y_te,pr)
        res[name] = {"precision":round(precision_score(y_te,pr),4),"recall":round(recall_score(y_te,pr),4),"f1":round(f1,4),"confusion_matrix":confusion_matrix(y_te,pr).tolist()}
        print(f"\n== {name} ==\n{classification_report(y_te,pr,digits=3)}")
        if f1>best_f1: best,best_f1,bn = pipe,f1,name
    M.mkdir(exist_ok=True); joblib.dump(best,M/"model.joblib")
    meta = {"selected_model":bn,"selection_metric":"F1 (fraud class) on held-out 20% test set","data_source":src,"n_samples":int(len(df)),
            "fraud_rate":round(float(df["fraudulent"].mean()),4),"results":res,
            "warning":"Metrics from synthetic demo data are optimistic and not real-world performance." if "SYNTHETIC" in src else "Held-out test metrics on EMSCAD; scores are uncalibrated."}
    (M/"metrics.json").write_text(json.dumps(meta,indent=2)); print("Selected:",bn,"| source:",src)
if __name__=="__main__": main()
