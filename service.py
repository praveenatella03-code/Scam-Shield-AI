from . import ml
from .rules import analyze_rules
ADVICE = {"Payment":"Never pay money to get a job. Do not transfer anything.","Privacy":"Do not share ID, bank details or OTPs until the offer is verified in writing.",
 "Contact":"Check the recruiter's email domain and find the company's official HR contact yourself.","Pressure":"Take your time. Genuine employers allow you to verify the offer.",
 "Company":"Search the company on LinkedIn, Google Maps and its official website.","Content":"Ask for a detailed job description, interview process and written offer letter."}
GENERAL = ["Verify the company through its official website.","Confirm the job independently using contact details you found yourself.","Report suspected scams at cybercrime.gov.in or helpline 1930 (India), or your local authority."]
def run(d):
    r = analyze_rules(d)
    prob, terms = ml.predict(" ".join(str(d.get(k) or "") for k in ("title","description","qualifications")))
    meta = ml.info(); rule = r["rule_score"]
    score = round(0.6*rule+0.4*prob*100) if prob is not None else rule
    if len(r["signals"])<2 and not any(s["critical"] for s in r["signals"]): score = min(score,45)  # one weak sign never suffices
    score = max(0,min(100,score))
    pred,level = ("Likely Genuine","Low") if score<30 else ("Suspicious","Medium") if score<60 else ("Potentially Fake","High")
    sig = sorted(r["signals"],key=lambda s:-s["weight"])
    reasons = [f'{s["title"]}: {s["explanation"]}' for s in sig[:4]]
    if terms: reasons.append("Words pushing the ML model toward 'fraudulent': "+", ".join(terms))
    if not reasons: reasons = ["No strong scam indicators were detected."]
    steps = [ADVICE[c] for c in dict.fromkeys(s["category"] for s in sig)]+GENERAL
    return {"prediction":pred,"risk_score":score,"risk_level":level,"reasons":reasons,"warning_signs":sig,
     "positive_indicators":r["positives"],"category_scores":r["categories"],"safety_steps":steps,"rule_score":rule,
     "ml_score":None if prob is None else round(prob*100),
     "model":{"available":meta is not None,"name":meta and meta["selected_model"],"data_source":meta and meta["data_source"]},
     "score_explanation":"Risk score = 60% rule-based scam-signal score + 40% ML model output (rule score only if no model is loaded). It is a heuristic risk indicator, NOT a calibrated or verified probability of fraud.",
     "disclaimer":"AI-generated risk assessment, not guaranteed verification. Always verify employers independently."}
