import json, re
from pathlib import Path
import joblib
MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
_model = None; _meta = None
def clean(t):
    t = re.sub(r"<[^>]+>"," ",str(t or "")).lower()
    t = re.sub(r"https?://\S+"," url ",t)
    t = re.sub(r"[^a-z0-9₹$% ]"," ",t)
    return re.sub(r"\s+"," ",t).strip()
def load():
    global _model,_meta
    p = MODEL_DIR/"model.joblib"
    if p.exists():
        _model = joblib.load(p); _meta = json.loads((MODEL_DIR/"metrics.json").read_text())
    return _meta
def info(): return _meta
def predict(text):
    """(probability of 'fraudulent' class 0-1, top terms) or (None, [])."""
    if _model is None: return None, []
    vec, clf = _model.named_steps["tfidf"], _model.named_steps["clf"]
    x = vec.transform([clean(text)]); prob = float(clf.predict_proba(x)[0][1]); terms = []
    if hasattr(clf,"coef_"):
        names = vec.get_feature_names_out(); idx = x.nonzero()[1]
        c = sorted(((float(x[0,i]*clf.coef_[0][i]),names[i]) for i in idx),reverse=True)
        terms = [t for v,t in c[:6] if v>0]
    return prob, terms
