"""Generates backend/data/sample_jobs.csv (600 rows, 5 scam types + hard negatives).
SYNTHETIC DEMO DATA written from templates - NOT real postings and NOT a substitute for EMSCAD."""
import csv, random
from pathlib import Path
R = random.Random(7)
ROLES = {"Software Engineer":"Java, Python and REST APIs","Data Analyst":"SQL, Excel and dashboards","Accountant":"GST filing and reconciliation","Mechanical Engineer":"CAD design and testing","Marketing Executive":"campaign planning and analytics","Staff Nurse":"patient care and documentation","HR Associate":"onboarding and payroll support","Sales Manager":"key account growth","Content Writer":"research and editing","School Teacher":"lesson planning and assessment","Civil Engineer":"site supervision and estimation","UI Designer":"Figma and design systems"}
COS = [("Infosys","infosys.com"),("Tata Consultancy Services","tcs.com"),("Wipro","wipro.com"),("Apollo Hospitals","apollohospitals.com"),("Larsen & Toubro","larsentoubro.com"),("Zoho","zoho.com"),("Mahindra","mahindra.com"),("HCLTech","hcltech.com"),("Asian Paints","asianpaints.com"),("Flipkart","flipkart.com")]
CITY = ["Bengaluru","Hyderabad","Pune","Chennai","Vijayawada","Mumbai","Delhi","Kolkata"]
FNAME = ["Global Online Solutions","Smart Earn Services","Dream Career Hub","Quick Jobs India","Alpha Work Group","Star Digital Network","Easy Income Pvt","Prime Hire Zone"]
def genuine():
    co,d = R.choice(COS); r = R.choice(list(ROLES)); y = R.randint(1,6)
    parts = [f"{co} is hiring a {r} in {R.choice(CITY)}.", f"Responsibilities include {ROLES[r]} and collaborating with cross-functional teams.", f"Requirements: bachelor degree and {y}+ years of experience.",
      R.choice(["Benefits include health insurance, provident fund and paid leave.","We offer competitive salary, gratuity and learning budget.","Standard benefits and annual performance bonus."]),
      R.choice(["Interview process: online assessment, technical round and HR round.","Selection involves two interview rounds and a background check.","Shortlisted candidates attend a panel interview."]),
      f"Apply through the careers page at {d}."]
    if R.random()<.2: parts.append(R.choice(["Immediate joining preferred.","Urgent requirement for our expanding team.","HR will contact you on WhatsApp only to schedule the interview.","Training is provided after joining."]))
    return dict(title=r,company=co,email=f"careers@{d}",website=f"https://www.{d}",salary=f"₹{R.randint(4,25)} LPA",description=" ".join(parts),label=0,scam_type="genuine")
def fake(kind):
    r = R.choice(list(ROLES)+["Data Entry Operator","Online Task Executive","Work From Home Agent"]); n = R.choice([500,999,1500,2000,2500]); fn = R.choice(FNAME)
    core = {"advance_fee":[f"Pay a refundable registration fee of Rs {n} to confirm your seat.",f"Security deposit of Rs {n} is required before joining.","Training charges to be paid via UPI."],
     "data_theft":["Send your Aadhaar, PAN and bank details on WhatsApp for verification.","Share your OTP to complete your profile activation.","Provide your debit card number for salary setup."],
     "task":["Like YouTube videos and rate products to earn daily payment.","Typing work and copy paste jobs, task based income.","Ad posting work, earn per task."],
     "mlm":["Recruit friends, build your downline and earn passive income.","Join our investment plan for financial freedom.","Network marketing opportunity, be your own boss."],
     "cheque":["We will send you a cheque; deposit it and buy equipment from our vendor.","Cash this cheque and wire transfer the balance via Western Union.","Purchase a laptop from our approved vendor, we reimburse later."]}[kind]
    parts = [R.choice([f"URGENT hiring for {r}!!!",f"{fn} requires {r} immediately.",f"We are looking for a {r}."]),
      R.choice(["No experience required, anyone can earn Rs 5000 per day from home.","Work from home, any qualification, guaranteed job.","100% placement guarantee, no interview, direct selection."]), R.choice(core)]
    if R.random()<.5: parts.append(R.choice(["Only 10 seats left, apply now!","Contact on Telegram or WhatsApp +91 98XXXXXX10.","Hurry, last date today!"]))
    if R.random()<.3: parts.append(f"Requirements: any degree. Responsibilities include {ROLES.get(r,'simple tasks')}.")   # polished-looking fake
    em = R.choice([f"hr.{fn.split()[0].lower()}@gmail.com",f"jobs{R.randint(10,99)}@yahoo.com","","apply@careers-"+fn.split()[0].lower()+"-hr.xyz"])
    return dict(title=r,company=R.choice([fn,"",fn]),email=em,website="",salary=R.choice([f"₹{R.randint(3,9)*1000} per day","₹30,000 per week",f"₹{R.randint(40,90)},000 per month"]),description=" ".join(parts),label=1,scam_type=kind)
rows = []
for i in range(600):
    rows.append(genuine() if i%2==0 else fake(R.choice(["advance_fee","data_theft","task","mlm","cheque"])))
R.shuffle(rows)
p = Path(__file__).parent/"data"; p.mkdir(exist_ok=True)
with open(p/"sample_jobs.csv","w",newline="",encoding="utf-8") as f:
    w = csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("wrote",len(rows),"rows")
