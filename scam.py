"""General scam-message detector (phishing, OTP theft, lottery, loan apps, digital arrest, UPI refund...). Shared rules: data/scam_rules.json."""
import json, re
from pathlib import Path
import joblib
from .ml import clean
from .rules import FREE_MAIL, _host
BASE = Path(__file__).resolve().parent.parent
CFG = json.loads((BASE/"data/scam_rules.json").read_text(encoding="utf-8"))
for r in CFG["risk"]+CFG["good"]: r["rx"] = re.compile(r["re"], re.I)
NEG = re.compile(r"[^.!?\n]*\b(never|do not|don't|dont)\s+(share|disclose|give|reveal|click)[^.!?\n]*[.!?]?", re.I)
URL = re.compile(r"https?://[^\s]+|www\.[^\s]+", re.I); BAD = re.compile(r"\.(xyz|top|click|work|buzz|gq|tk|ml|cf|ga|icu|monster|rest)$")
ADV = {"Phishing":"Do not click links in the message. Open your bank's official app or type its website yourself.","Credentials":"Never share OTP, PIN, CVV or passwords with anyone, including 'bank staff'.","Prize":"You cannot win contests you did not enter. Ignore and delete.","Payment":"Never pay fees to receive a prize, loan or parcel.","Investment":"Guaranteed returns do not exist. Check SEBI registration before investing.","Loan app":"Use only RBI-registered lenders. Never allow apps access to contacts or photos.","Delivery":"Check delivery status only in the courier's official app.","Impersonation":"No agency arrests or interrogates anyone over call or video. Hang up and call 1930.","UPI":"You never need a PIN or QR scan to receive money.","Tech support":"Do not install remote apps for strangers. Disconnect and call the official support number.","Emotional":"Verify by calling the person on a known number before sending money.","Pressure":"Pause. Real organisations let you verify.","Link":"Do not open shortened or unfamiliar links."}
GEN = ["Do not reply, click links or call numbers in the message; use official apps and websites.","If you shared OTP/bank details or paid, call your bank immediately and report at cybercrime.gov.in or helpline 1930."]
_model = None
def _ml(t):
    global _model
    if _model is None:
        p = BASE/"models/scam_model.joblib"; _model = joblib.load(p) if p.exists() else False
    if not _model: return None
    return float(_model.predict_proba([clean(t)])[0][1])
def analyze(text, sender="", url=""):
    full = " ".join([text, sender, url]); neutral = NEG.sub(lambda m: " "*len(m.group(0)), full); sig, pos = [], []
    for r in CFG["risk"]:
        m = r["rx"].search(neutral)
        if m: sig.append(dict(category=r["cat"],weight=r["w"],critical=bool(r["crit"]),title=r["title"],explanation=r["expl"],scam_type=r["type"],evidence=m.group(0).strip()[:60]))
    urls = [_host(u) for u in URL.findall(full)] + ([_host(url)] if url else []); hosts = [h for h in urls if h]
    for h in dict.fromkeys(hosts):
        if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", h) or "xn--" in h or BAD.search(h) or h.count("-")>=2:
            sig.append(dict(category="Link",weight=18,critical=False,title="Suspicious link domain",explanation="Odd extension, IP address, look-alike or hyphen-heavy domain.",scam_type="",evidence=h))
    b = re.search(r"\b("+CFG["brands"]+r")\b", full, re.I)
    if b and hosts:
        key = re.sub(r"\s","",b.group(1).lower()); bad = [h for h in hosts if key not in h]
        if bad: sig.append(dict(category="Link",weight=22,critical=False,title="Link does not match the brand named",explanation=f"Message names '{b.group(1)}' but links to another domain.",scam_type="Phishing / bank KYC fraud",evidence=bad[0]))
    if sender and FREE_MAIL.search(sender): sig.append(dict(category="Link",weight=10,critical=False,title="Sender uses a free email domain",explanation="Organisations use official domains.",scam_type="",evidence=sender))
    for g in CFG["good"]:
        if g["rx"].search(full): pos.append(dict(title=g["title"],weight=g["w"]))
    raw = sum(s["weight"] for s in sig); rule = max(0,min(100,round(raw-min(25,sum(p["weight"] for p in pos))*(0.4 if raw>50 else 1))))
    p = _ml(text); score = round(.55*rule+.45*p*100) if p is not None else rule
    if len(sig)<2 and not any(s["critical"] for s in sig): score = min(score,45)
    score = max(0,min(100,score)); level = "Low" if score<30 else "Medium" if score<60 else "High"
    sig.sort(key=lambda s:-s["weight"]); cats = {}
    for s in sig: cats[s["category"]] = cats.get(s["category"],0)+s["weight"]
    return dict(kind="scam",prediction={"Low":"Likely Safe","Medium":"Suspicious","High":"Likely Scam"}[level],risk_score=score,risk_level=level,rule_score=rule,ml_score=None if p is None else round(p*100),
      scam_types=list(dict.fromkeys(s["scam_type"] for s in sig if s["scam_type"])),reasons=[f'{s["title"]}: {s["explanation"]}' for s in sig[:4]] or ["No strong scam indicators were detected."],
      warning_signs=sig,positive_indicators=pos,category_scores=cats,safety_steps=list(dict.fromkeys(ADV[s["category"]] for s in sig if s["category"] in ADV))+GEN,
      score_explanation="Risk = 55% rule score + 45% ML output (rules only if no model). Heuristic indicator, NOT a calibrated probability.",disclaimer="AI-generated risk assessment, not guaranteed verification.")
