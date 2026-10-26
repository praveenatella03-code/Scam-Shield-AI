"""Trains the scam-message classifier (TF-IDF + LR/RF, selected by F1). Uses data/sample_scams.csv (SYNTHETIC) unless data/scam_real.csv (text,label) exists."""
import json
from pathlib import Path
import joblib, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from app.ml import clean
D=Path(__file__).parent/"data"; M=Path(__file__).parent/"models"
real=D/"scam_real.csv"; df=pd.read_csv(real if real.exists() else D/"sample_scams.csv").fillna(""); src="REAL data (scam_real.csv)" if real.exists() else "SYNTHETIC DEMO DATA (sample_scams.csv)"
X=df["text"].map(clean); Xtr,Xte,ytr,yte=train_test_split(X,df["label"],test_size=.2,stratify=df["label"],random_state=42)
best,bf,res=None,-1,{}
for n,c in {"LogisticRegression":LogisticRegression(max_iter=1000,class_weight="balanced"),"RandomForest":RandomForestClassifier(n_estimators=200,class_weight="balanced",random_state=42,n_jobs=-1)}.items():
    p=Pipeline([("tfidf",TfidfVectorizer(ngram_range=(1,2),min_df=2,stop_words="english",sublinear_tf=True)),("clf",c)]).fit(Xtr,ytr); pr=p.predict(Xte); f=f1_score(yte,pr)
    res[n]=dict(precision=round(precision_score(yte,pr),4),recall=round(recall_score(yte,pr),4),f1=round(f,4),confusion_matrix=confusion_matrix(yte,pr).tolist())
    if f>bf: best,bf,bn=p,f,n
M.mkdir(exist_ok=True); joblib.dump(best,M/"scam_model.joblib")
(M/"scam_metrics.json").write_text(json.dumps(dict(selected_model=bn,data_source=src,n_samples=len(df),results=res,warning="Synthetic data gives optimistic metrics." if "SYNTH" in src else "Held-out metrics; uncalibrated."),indent=2)); print(bn,src,res[bn])
