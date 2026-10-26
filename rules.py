"""Rule-based scam signal detector. Signals are RISK INDICATORS, not proof of fraud."""
import re
from urllib.parse import urlparse
FREE_MAIL = re.compile(r"@(gmail|yahoo|ymail|hotmail|outlook|rediffmail|protonmail|aol|live|icloud)\.", re.I)
F = re.IGNORECASE
# (id, category, weight, critical, regex, title, explanation)
RISK = [
 ("fee","Payment",35,True,r"(registration|security|refundable|processing|training|joining|application|kit|uniform)\s*(fee|fees|charges?|deposit)|pay\s+(a\s+)?(fee|deposit)|deposit\s+(of\s+)?(rs\.?|₹|\$)","Upfront payment requested","Genuine employers do not charge candidates to hire them."),
 ("transfer","Payment",30,True,r"gift\s*cards?|bitcoin|western union|wire\s+transfer|money\s+transfer|(cash|deposit)\s+(this\s+)?che(que|ck)|buy\s+(your\s+)?(equipment|laptop|software)|purchase\s+(equipment|laptop)","Money transfer / equipment purchase","Cheque-cashing and equipment-purchase schemes are common scams."),
 ("sensitive","Privacy",30,True,r"(send|share|provide|submit)\s+(your\s+)?(aadhaar|aadhar|pan|passport|ssn|social\s+security|bank\s+(account|details)|debit\s+card|credit\s+card|cvv|otp|pin)","Sensitive data requested","Never share ID, bank or OTP details before a verified offer."),
 ("urgent","Pressure",12,False,r"urgent(ly)?\s+(hiring|required|need)|apply\s+(now|immediately)|limited\s+(seats|slots)|only\s+\d+\s+(seats|slots|positions)|hurry|last\s+date\s+today|accept\s+(the\s+)?offer\s+(today|immediately)","Urgency / pressure","Scammers rush people so they skip verification."),
 ("guarantee","Pressure",12,False,r"100%\s*(job\s*)?(guarantee|placement|selection)|guaranteed\s+(job|income|selection)","Guaranteed job or income","No honest recruiter can guarantee selection."),
 ("nointerview","Content",14,False,r"no\s+interview|without\s+(an\s+)?interview|direct\s+(selection|joining)|selected\s+(directly|instantly)|you\s+have\s+been\s+selected","No interview / instant selection","Real hiring includes screening."),
 ("noskill","Content",14,False,r"no\s+(experience|qualification|skills?)\s*(needed|required)|anyone\s+can\s+(apply|earn)|any\s+qualification","No skills needed (with high pay)","Unrealistic combination of low effort and high reward."),
 ("tasks","Content",12,False,r"(like|share|rate|subscribe)\s+(youtube|videos?|products?|apps?)|typing\s+work|copy\s*paste\s+(work|job)|task[-\s]based|ad\s+posting","Task-based 'earn at home' work","A frequent pattern in online job scams."),
 ("mlm","Content",12,False,r"network\s+marketing|\bmlm\b|downline|recruit\s+(others|friends)|investment\s+(plan|scheme)|passive\s+income|financial\s+freedom","MLM / investment language","Not a genuine employment offer."),
 ("chat","Contact",10,False,r"whats\s*app|telegram|wa\.me|t\.me","Hiring via WhatsApp/Telegram","Official hiring is rarely only on chat apps."),
 ("shortlink","Contact",12,False,r"\b(bit\.ly|tinyurl\.com|goo\.gl|cutt\.ly|rb\.gy)\S*","Shortened link","Hides the real destination."),
]
GOOD = [
 (8,r"\b(responsibilit(y|ies)|requirements?|qualifications?)\b","Describes responsibilities and requirements"),
 (6,r"\b(health insurance|provident fund|gratuity|paid leave|esop|benefits)\b","Mentions standard employee benefits"),
 (6,r"\b(bachelor|b\.?tech|b\.?e\b|mba|degree|\d\+?\s*years?)\b","Specific education / experience criteria"),
 (6,r"\b(interview\s+(rounds?|process)|technical\s+round|hr\s+round|assessment)\b","Describes an interview process"),
]
def _host(u):
    try: return (urlparse(u if "//" in u else "//"+u).hostname or "").lower().removeprefix("www.")
    except Exception: return ""

def analyze_rules(d: dict) -> dict:
    text = " ".join(str(d.get(k) or "") for k in ("title","description","qualifications","salary","recruiter_email","application_url"))
    signals, positives, cats = [], [], {}
    def add(cat,w,crit,title,expl,ev=None): signals.append({"category":cat,"weight":w,"critical":crit,"title":title,"explanation":expl,"evidence":ev})
    for _i,cat,w,crit,rx,title,expl in RISK:
        m = re.search(rx,text,F)
        if m: add(cat,w,crit,title,expl,m.group(0).strip()[:60])
    email, site, comp = (d.get("recruiter_email") or "").strip(), _host(d.get("company_website") or ""), (d.get("company") or "").strip()
    if email and FREE_MAIL.search(email): add("Contact",16,False,"Recruiter uses a free email domain","Companies normally use an official domain.",email)
    elif email and site and "@" in email:
        ed = email.split("@")[1].lower()
        if not (ed.endswith(site) or site.endswith(ed)): add("Contact",14,False,"Email domain differs from company website","Check whether the recruiter really belongs to this company.",email)
    if not comp: add("Company",14,False,"Company name missing","Anonymous employers are hard to verify.")
    if not site and not email: add("Company",8,False,"No website or recruiter contact","Verifiable details are missing.")
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?",(d.get("salary") or "").replace(",",""))]
    s, mx = (d.get("salary") or "").lower(), max(nums or [0])
    if (re.search(r"day|daily",s) and mx>=2000) or (re.search(r"week",s) and mx>=10000) or (re.search(r"hour",s) and mx>=2000):
        add("Content",16,False,"Salary looks unrealistic","Pay rate is far above typical for this kind of role.",d.get("salary"))
    desc = d.get("description") or ""
    if len(desc.split())<30: add("Content",10,False,"Very short or vague description","Genuine ads usually describe duties clearly.")
    letters = re.sub(r"[^A-Za-z]","",desc)
    if len(letters)>40 and sum(c.isupper() for c in letters)/len(letters)>.35: add("Pressure",8,False,"Excessive capital letters","Shouting style is common in spam.")
    if desc.count("!")>=3: add("Pressure",6,False,"Too many exclamation marks","Unprofessional tone.")
    for w,rx,t in GOOD:
        if re.search(rx,text,F): positives.append({"title":t,"weight":w})
    if site: positives.append({"title":"Company website provided","weight":6})
    if email and not FREE_MAIL.search(email): positives.append({"title":"Recruiter uses a non-free email domain","weight":6})
    raw = sum(x["weight"] for x in signals); bonus = min(25,sum(p["weight"] for p in positives))
    score = max(0,min(100,round(raw-bonus*(0.4 if raw>50 else 1))))
    for x in signals: cats[x["category"]] = cats.get(x["category"],0)+x["weight"]
    return {"rule_score":score,"signals":signals,"positives":positives,"categories":cats}
