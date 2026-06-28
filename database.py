# ╔══════════════════════════════════════════════════════════════════╗
# ║                  NSIM DATABASE — database.py                    ║
# ║                                                                  ║
# ║  This is the ONLY file you need to edit to update NSIM info.   ║
# ║  Add courses, change fees, update timings — all here.          ║
# ╚══════════════════════════════════════════════════════════════════╝

# ── BASIC INFO ──────────────────────────────────────────────────────
INSTITUTE_NAME    = "NSIM yani National School of Internet Marketing"
LOCATION          = "South Delhi, India"
WEBSITE           = "nsim.in"
CONTACT_NUMBER    = "9811020518"
WHATSAPP_NUMBER   = "919811020518"   # country code + number, no + sign

# ── COURSES ─────────────────────────────────────────────────────────
# Add as many courses as you want in this format:
COURSES = [
    {
        "name"    : "Digital Marketing Course",
        "duration": "teen mahine",         # 3 months
        "fees"    : "pandrah hazaar rupaye",  # ₹15,000
        "topics"  : "SEO, Google Ads, Facebook Ads, Instagram Marketing, Content Marketing",
    },
    {
        "name"    : "Data Science Course",
        "duration": "chhe mahine",         # 6 months
        "fees"    : "pachees hazaar rupaye", # ₹25,000
        "topics"  : "Python, Machine Learning, Data Analysis, Tableau, Power BI",
    },
    {
        "name"    : "Cyber Security Course",
        "duration": "char mahine",         # 4 months
        "fees"    : "bees hazaar rupaye",   # ₹20,000
        "topics"  : "Network Security, Ethical Hacking, Penetration Testing",
    },
    {
        "name"    : "Machine Learning Course",
        "duration": "chhe mahine",         # 6 months
        "fees"    : "tees hazaar rupaye",   # ₹30,000
        "topics"  : "Python, Deep Learning, Neural Networks, AI Projects",
    },
    {
        "name"    : "Web Development Course",
        "duration": "teen mahine",         # 3 months
        "fees"    : "baarah hazaar rupaye", # ₹12,000
        "topics"  : "HTML, CSS, JavaScript, React, Node.js",
    },
    # ── ADD MORE COURSES BELOW THIS LINE ──
    # {
    #     "name"    : "Course Name",
    #     "duration": "duration in Hindi words",
    #     "fees"    : "fees in Hindi words",
    #     "topics"  : "topic1, topic2, topic3",
    # },
]

# ── BATCH TIMINGS ────────────────────────────────────────────────────
BATCHES = [
    "Subah ki batch: das baje se dopahar ek baje tak",
    "Shaam ki batch: paanch baje se raat aath baje tak",
    "Weekend batch: Shanivaar aur Ravivar dono din",
    "Working professionals ke liye special evening batch bhi hai",
]

# ── KEY FEATURES ─────────────────────────────────────────────────────
FEATURES = [
    "Ikyavan hazaar se zyada students train ho chuke hain",
    "Sau pratishat yani 100 percent placement guarantee di jaati hai",
    "Live projects par real kaam karte hain",
    "Course complete hone par certificate milti hai",
    "Pehle free demo class le sakte hain",
    "Expert trainers se seedha seekhne ka mauka milta hai",
    "Small batch size taaki har student par dhyan diya ja sake",
]

# ── ADMISSION PROCESS ────────────────────────────────────────────────
ADMISSION_STEPS = [
    "Pehle free demo class ke liye 9811020518 par call karein",
    "Demo class attend karein aur course select karein",
    "Fees jama karein aur batch join karein",
    "Ya seedha nsim.in par jaayein aur online registration karein",
]

# ── FAQ — common questions and their answers ─────────────────────────
# Add any question-answer pair that callers often ask
FAQ = [
    {
        "question": "EMI ya installment mein fees de sakte hain kya",
        "answer"  : "Haan, installment ki suvidha bhi uplabdh hai. Is baare mein 9811020518 par call karein.",
    },
    {
        "question": "Kya online classes bhi hain",
        "answer"  : "Haan, online aur offline dono tarah ki classes available hain.",
    },
    {
        "question": "Certificate Google ya koi company accept karti hai kya",
        "answer"  : "NSIM ka certificate industry mein maanya hai aur placement mein madad karta hai.",
    },
    {
        "question": "Kitni umra mein yeh course kar sakte hain",
        "answer"  : "Koi bhi umar zyada nahi hoti seekhne ke liye. Students, working professionals, aur grihini sab yeh course kar sakte hain.",
    },
    # ── ADD MORE FAQs BELOW ──
    # {
    #     "question": "your question in Hindi",
    #     "answer"  : "your answer in Hindi",
    # },
]

# ── LEAD DETECTION KEYWORDS ──────────────────────────────────────────
# If caller uses any of these words, they are considered INTERESTED
# and a WhatsApp message will be sent to WHATSAPP_NUMBER
INTEREST_KEYWORDS = [
    # Hindi
    "admission", "lena hai", "join", "enroll", "registration",
    "fees dena", "apply", "start karna", "course lena", "batch join",
    "kab se", "aaj se", "abhi", "immediately", "jald",
    "demo", "free class", "try karna", "dekhna chahta",
    "interested", "chahiye", "chahiye mujhe", "haan bhai", "haan ji",
    # English
    "enroll", "register", "sign up", "book", "confirm",
    "yes", "sure", "definitely", "i want", "i am interested",
]


# ════════════════════════════════════════════════════════════════════
#  BUILD KNOWLEDGE STRING — used by AI as its knowledge base
#  (No need to edit this function)
# ════════════════════════════════════════════════════════════════════
def build_knowledge() -> str:
    lines = []
    lines.append(f"Institute: {INSTITUTE_NAME}")
    lines.append(f"Location: {LOCATION}")
    lines.append(f"Website: {WEBSITE}")
    lines.append(f"Phone: {CONTACT_NUMBER}")
    lines.append("")
    lines.append("Hamare courses:")
    for c in COURSES:
        lines.append(
            f"- {c['name']}: {c['duration']}, fees {c['fees']}. "
            f"Topics: {c['topics']}"
        )
    lines.append("")
    lines.append("Batch timings:")
    for b in BATCHES:
        lines.append(f"- {b}")
    lines.append("")
    lines.append("Khaas baatein:")
    for f in FEATURES:
        lines.append(f"- {f}")
    lines.append("")
    lines.append("Admission process:")
    for i, s in enumerate(ADMISSION_STEPS, 1):
        lines.append(f"{i}. {s}")
    lines.append("")
    lines.append("Aksar poochhe jaane wale sawaal:")
    for faq in FAQ:
        lines.append(f"Q: {faq['question']}")
        lines.append(f"A: {faq['answer']}")
    return "\n".join(lines)
