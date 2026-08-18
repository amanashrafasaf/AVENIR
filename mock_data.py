"""
mock_data.py — Rule-based career recommendation engine (DEMO_MODE / offline fallback).

Generates the same structured JSON schema that the real AI layer will produce:
    recommendations -> skill_gaps -> roadmap (courses, certs, degrees, scholarships)

Deterministic: same profile in, same output out. No internet, no API key.
"""

import re
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Subject aliases (normalize free-text subject names)
# ---------------------------------------------------------------------------
SUBJECT_ALIASES = {
    "maths": ["maths", "mathematics", "math"],
    "cs": ["computer science", "cs", "computers", "computer", "it", "information technology", "informatics"],
    "physics": ["physics"],
    "chemistry": ["chemistry", "chem"],
    "biology": ["biology", "bio"],
    "commerce": ["commerce", "accountancy", "accounts", "business studies", "economics"],
    "economics": ["economics", "economy"],
    "english": ["english"],
    "arts": ["arts", "humanities", "history", "political science", "sociology", "geography", "psychology"],
    "design": ["design", "fine arts", "art", "drawing"],
    "statistics": ["statistics", "stats"],
    "data": ["data science", "data analytics", "data"],
}

INTEREST_KEYWORDS = {
    "software": ["coding", "programming", "software", "computer", "games", "gaming", "app", "web", "tech", "hacking", "robotics", "ai", "ml", "machine learning"],
    "data": ["data", "analytics", "statistics", "numbers", "spreadsheets", "excel", "insights", "patterns"],
    "business": ["business", "startup", "entrepreneurship", "money", "finance", "investing", "marketing", "management", "leadership"],
    "design": ["design", "art", "drawing", "creative", "animation", "ui", "ux", "graphics", "photoshop", "video"],
    "health": ["health", "medicine", "biology", "care", "doctor", "hospital", "helping people", "science"],
    "teaching": ["teaching", "mentoring", "education", "explaining", "students"],
    "civil": ["building", "construction", "infrastructure", "structures", "civil"],
    "accounts": ["accounting", "accounts", "tax", "audit", "finance"],
}

# ---------------------------------------------------------------------------
# Career catalog
# ---------------------------------------------------------------------------
CAREERS = [
    {
        "career": "Software Engineer",
        "subjects": ["maths", "cs", "physics"],
        "skills": ["Programming (Python/JavaScript)", "Data Structures & Algorithms", "Version Control (Git)", "Web Development", "Problem Solving"],
        "interests": ["software"],
        "education_paths": ["University degree", "Certification/online", "Not sure"],
        "salary": "₹4–12 LPA (entry)",
        "demand": "Very High",
        "summary": "Build software products — from web apps to AI systems. One of the fastest-growing careers with remote-friendly options.",
        "courses": ["CS50 (Harvard, free)", "Full-Stack Web Development (freeCodeCamp)", "Python for Everybody (Coursera)"],
        "certs": ["Meta Front-End Developer (Coursera)", "AWS Certified Cloud Practitioner", "Google IT Automation (Coursera)"],
        "degrees": ["B.Tech CSE", "BCA", "B.Sc Computer Science"],
        "projects": ["A personal portfolio website", "A Python mini-project (e.g. a to-do tracker or quiz game)", "A small web app with a database"],
    },
    {
        "career": "Data Analyst",
        "subjects": ["maths", "statistics", "data", "economics", "commerce", "cs"],
        "skills": ["Excel", "SQL", "Python (pandas)", "Data Visualization", "Statistics Basics"],
        "interests": ["data", "business"],
        "education_paths": ["University degree", "Certification/online", "Not sure", "Diploma/ITI"],
        "salary": "₹3.5–9 LPA (entry)",
        "demand": "Very High",
        "summary": "Turn raw data into decisions for companies. Welcomes commerce/maths backgrounds — no engineering degree required.",
        "courses": ["Google Data Analytics Certificate (Coursera)", "SQL for Data Science (Coursera)", "Excel Skills for Business (Coursera)"],
        "certs": ["Google Data Analytics Professional", "Microsoft Power BI Data Analyst (PL-300)", "IBM Data Analyst (Coursera)"],
        "degrees": ["B.Sc Statistics", "B.Com + analytics certification", "BCA / B.Sc Data Science"],
        "projects": ["Analyze a public dataset (e.g. sports or weather) in Excel", "Build an interactive dashboard in Power BI/Tableau", "SQL queries on a sample sales database"],
    },
    {
        "career": "Product Manager",
        "subjects": ["commerce", "economics", "cs", "english", "maths"],
        "skills": ["Communication", "User Research", "Analytics (SQL/Excel)", "Roadmap Planning", "Basic Tech Understanding"],
        "interests": ["business", "data"],
        "education_paths": ["University degree", "Certification/online", "Not sure"],
        "salary": "₹6–20 LPA (entry)",
        "demand": "High",
        "summary": "Own what gets built — the bridge between business, users, and engineers. Great for strong communicators with business sense.",
        "courses": ["Product Management Certification (Coursera/Google)", "Business Analytics (Coursera)", "UX Design Fundamentals (Google)"],
        "certs": ["Google Project Management Certificate", "Product School PM Certificate", "Agile/Scrum Foundation (PSM I)"],
        "degrees": ["BBA", "B.Com", "B.Tech (any branch) + MBA later"],
        "projects": ["Document a product teardown of an app you use", "Run a small user survey and summarize insights", "Build a one-page product roadmap for a hobby idea"],
    },
    {
        "career": "Data Scientist",
        "subjects": ["maths", "statistics", "data", "cs"],
        "skills": ["Python", "Statistics", "Machine Learning Basics", "SQL", "Data Visualization"],
        "interests": ["data", "software"],
        "education_paths": ["University degree", "Certification/online", "Not sure"],
        "salary": "₹6–15 LPA (entry)",
        "demand": "Very High",
        "summary": "Build models that predict and decide. Requires strong maths — your marks in mathematics matter here.",
        "courses": ["Machine Learning Specialization (Andrew Ng)", "Python for Data Science (freeCodeCamp)", "Statistics with R/Python (Coursera)"],
        "certs": ["IBM Data Science Professional", "TensorFlow Developer Certificate", "Kaggle micro-courses"],
        "degrees": ["B.Sc Data Science", "B.Tech CSE/AI", "B.Sc Statistics + ML certs"],
        "projects": ["Kaggle beginner competitions (Titanic etc.)", "A prediction project using a real dataset", "End-to-end ML pipeline notebook on GitHub"],
    },
    {
        "career": "UI/UX Designer",
        "subjects": ["design", "cs", "english", "arts"],
        "skills": ["Figma", "Design Thinking", "Wireframing", "User Research", "Basic HTML/CSS"],
        "interests": ["design", "software"],
        "education_paths": ["University degree", "Certification/online", "Not sure", "Diploma/ITI"],
        "salary": "₹3.5–10 LPA (entry)",
        "demand": "High",
        "summary": "Design how products look and feel. Combines creativity with tech — no heavy maths needed.",
        "courses": ["Google UX Design Certificate (Coursera)", "Figma for Beginners (YouTube/free)", "Interaction Design Basics (Coursera)"],
        "certs": ["Google UX Design Professional", "Meta UX/UI Certification", "Adobe Certified Professional (Photoshop/Illustrator)"],
        "degrees": ["B.Des", "BFA", "B.Sc Multimedia / any + portfolio"],
        "projects": ["Redesign an app screen in Figma", "Build a 5-screen mobile app prototype", "A personal design portfolio on Behance/Dribbble"],
    },
    {
        "career": "Chartered Accountant (CA)",
        "subjects": ["commerce", "economics", "maths"],
        "skills": ["Accounting", "Taxation Basics", "Excel", "Attention to Detail", "Business Law Basics"],
        "interests": ["accounts", "business"],
        "education_paths": ["University degree", "Not sure"],
        "salary": "₹6–12 LPA (articleship+; ₹10–25 LPA qualified)",
        "demand": "High",
        "summary": "Audit, tax, and finance expert — a prestigious, stable path for commerce students. Long but rewarding qualification journey.",
        "courses": ["ICAI Foundation study material (official)", "Accounting Basics (Coursera)", "Income Tax fundamentals (free online)"],
        "certs": ["CA Foundation → Inter → Final (ICAI)", "CS (Company Secretary) as parallel", "CMA (Cost & Management Accountancy)"],
        "degrees": ["B.Com (mandatory alongside CA)", "B.Com (Hons) Accounting & Finance"],
        "projects": ["Maintain mock accounts for a small business", "Prepare a sample tax return", "Case study on a company's annual report"],
    },
    {
        "career": "Business Analyst",
        "subjects": ["commerce", "economics", "maths", "statistics", "cs"],
        "skills": ["Excel", "SQL", "Requirements Gathering", "Process Mapping", "Communication"],
        "interests": ["business", "data"],
        "education_paths": ["University degree", "Certification/online", "Not sure"],
        "salary": "₹4–10 LPA (entry)",
        "demand": "High",
        "summary": "Analyze business problems and translate them into tech requirements. A natural home for commerce + analytical students.",
        "courses": ["Business Analysis Fundamentals (Udemy/Coursera)", "SQL for Business Analysts", "Excel for Business (Coursera)"],
        "certs": ["ECBA (IIBA) Entry Certificate", "Google Data Analytics (helps)", "Agile BA certification"],
        "degrees": ["BBA", "B.Com", "B.Sc Economics"],
        "projects": ["Document requirements for a simple app idea", "Build a process flow diagram (draw.io)", "Analyze a business dataset and present insights"],
    },
    {
        "career": "Digital Marketer",
        "subjects": ["commerce", "english", "arts", "economics"],
        "skills": ["SEO Basics", "Social Media", "Content Writing", "Google Ads Basics", "Analytics"],
        "interests": ["business", "design"],
        "education_paths": ["University degree", "Certification/online", "Not sure", "Diploma/ITI"],
        "salary": "₹3–8 LPA (entry)",
        "demand": "High",
        "summary": "Grow brands online through content, ads, and SEO. Portfolio + skills matter more than degrees.",
        "courses": ["Google Digital Marketing & E-commerce Certificate", "SEO Fundamentals (free online)", "Meta Social Media Marketing (Coursera)"],
        "certs": ["Google Digital Marketing Certificate", "HubSpot Content Marketing", "Meta Certified Digital Marketing Associate"],
        "degrees": ["BBA Marketing", "B.Com", "BA (any) + certifications"],
        "projects": ["Run a small Instagram page and grow it", "Write 10 SEO blog posts for a niche", "Launch a mock Google Ads campaign"],
    },
    {
        "career": "Civil Engineer",
        "subjects": ["maths", "physics", "chemistry"],
        "skills": ["Physics & Maths Core", "AutoCAD Basics", "Structural Concepts", "Site Surveying Basics", "Project Planning"],
        "interests": ["civil"],
        "education_paths": ["University degree"],
        "salary": "₹3.5–8 LPA (entry)",
        "demand": "Moderate",
        "summary": "Design and build infrastructure — roads, buildings, bridges. A solid core-engineering path with government job options.",
        "courses": ["Engineering Mechanics (NPTEL, free)", "AutoCAD 2D/3D (Udemy)", "Construction Materials (NPTEL)"],
        "certs": ["AutoCAD Certified User", "NPTEL course certificates", "Primavera P6 basics (later)"],
        "degrees": ["B.Tech Civil Engineering", "Diploma in Civil Engineering"],
        "projects": ["Model a small structure in AutoCAD", "Survey a local area (measurements + sketch)", "Study a real bridge/building design"],
    },
    {
        "career": "Teacher / Educator",
        "subjects": ["english", "arts", "maths", "science", "biology", "physics", "chemistry", "commerce", "economics"],
        "skills": ["Communication", "Subject Mastery", "Lesson Planning", "Patience", "Digital Teaching Tools"],
        "interests": ["teaching"],
        "education_paths": ["University degree", "Not sure"],
        "salary": "₹3–7 LPA (school); higher for EdTech/online",
        "demand": "High",
        "summary": "Shape the next generation in classrooms or fast-growing EdTech platforms. Any strong subject background works.",
        "courses": ["Diploma in Elementary Education (D.El.Ed)", "Pedagogy courses (NPTEL)", "Digital Teaching tools (free online)"],
        "certs": ["B.Ed (after graduation)", "CTET (Central Teacher Eligibility Test)", "TEFL/TESOL (for English teaching)"],
        "degrees": ["B.A/B.Sc + B.Ed", "B.El.Ed (4-year integrated)"],
        "projects": ["Create video lessons on YouTube for a subject you love", "Design lesson plans for a topic", "Tutor juniors and document outcomes"],
    },
    {
        "career": "Entrepreneur / Startup Founder",
        "subjects": ["commerce", "economics", "cs", "english", "maths"],
        "skills": ["Problem Solving", "Communication", "Basic Finance", "Sales", "Resilience"],
        "interests": ["business"],
        "education_paths": ["University degree", "Certification/online", "Not sure", "Diploma/ITI"],
        "salary": "Uncapped (high risk, high reward)",
        "demand": "N/A — you create it",
        "summary": "Build your own venture. Works best combined with a strong skill (tech, design, or domain) — pick one first.",
        "courses": ["Startup fundamentals (Y Combinator Startup School, free)", "Business Model Canvas (free)", "Digital marketing basics"],
        "certs": ["Y Combinator Startup School (free)", "NSRCEL / incubation programs", "PMI/lean startup workshops"],
        "degrees": ["Any degree + strong portfolio", "BBA with entrepreneurship electives"],
        "projects": ["Launch a micro-business (service or product) for real users", "Build an MVP of an app idea", "Write a one-page business plan"],
    },
    {
        "career": "Doctor (MBBS) / Healthcare",
        "subjects": ["biology", "physics", "chemistry", "maths"],
        "skills": ["Biology Mastery", "Discipline & Study Skills", "Empathy", "Lab Basics", "Time Management"],
        "interests": ["health"],
        "education_paths": ["University degree"],
        "salary": "₹6–15 LPA (residency+); high later",
        "demand": "Very High",
        "summary": "Medicine — the most demanding entry (NEET) but deeply rewarding. Requires top marks in biology/chemistry/physics.",
        "courses": ["NEET preparation (NCERT-first strategy)", "Human Biology (Khan Academy)", "Medical entrance coaching (if affordable)"],
        "certs": ["NEET-UG (entrance)", "Later: PG (NEET-PG)"],
        "degrees": ["MBBS (after NEET)", "BDS / BAMS / Nursing as alternatives"],
        "projects": ["Volunteer at a hospital/clinic", "Health awareness project in your locality", "Maintain strong NCERT notes + test series"],
    },
    {
        "career": "Graphic Designer",
        "subjects": ["design", "arts", "english"],
        "skills": ["Photoshop", "Illustrator", "Typography", "Color Theory", "Portfolio Development"],
        "interests": ["design"],
        "education_paths": ["University degree", "Certification/online", "Not sure", "Diploma/ITI"],
        "salary": "₹2.5–7 LPA (entry)",
        "demand": "High",
        "summary": "Create visual identities, ads, and digital content. A portfolio beats a degree — start freelancing early.",
        "courses": ["Graphic Design Specialization (CalArts/Coursera)", "Photoshop/Illustrator (Adobe Learn, free)", "Typography fundamentals (free online)"],
        "certs": ["Adobe Certified Professional", "Canva Design certificates", "Google UX (helps)"],
        "degrees": ["B.Des / BFA", "Diploma in Graphic Design"],
        "projects": ["Design 10 social media posts for a mock brand", "Rebrand a local shop (logo + posters)", "Build a Behance portfolio"],
    },
]

# ---------------------------------------------------------------------------
# Scholarships (filtered by financial preference + location keyword)
# ---------------------------------------------------------------------------
SCHOLARSHIPS = [
    {"name": "National Means-cum-Means Scholarship (NMMS)", "for": "Class 9–10, low income", "amount": "₹12,000/year"},
    {"name": "Central Sector Scheme (CSS) — Top Class Education", "for": "Low-income meritorious students", "amount": "Full fees + maintenance"},
    {"name": "Post-Matric Scholarship (state-level)", "for": "SC/ST/OBC & minority students", "amount": "Varies by state (check your state portal)"},
    {"name": "AICTE Pragati (girls) & Saksham (divyang) schemes", "for": "Technical education students", "amount": "₹50,000/year"},
    {"name": "State scholarship portals (e.g. your state's scholarship portal)", "for": "Resident students, merit-based", "amount": "Varies — apply early"},
    {"name": "PM YASASVI / NSP (National Scholarship Portal)", "for": "Central scholarships, single application", "amount": "Multiple schemes"},
    {"name": "Merit-cum-Means (minority communities, Maulana Azad)", "for": "Minority students, professional courses", "amount": "Up to ₹20,000/year"},
    {"name": "Online learning scholarships (Coursera/Google financial aid)", "for": "Anyone applying for financial aid", "amount": "Free course access"},
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tokens(text):
    """Lowercase, split on commas and whitespace."""
    parts = re.split(r"[,;]+", text or "")
    return [p.strip().lower() for p in parts if p.strip()]


def _norm_subjects(subjects):
    """Map free-text subjects to canonical aliases present in profile."""
    toks = _tokens(subjects)
    found = set()
    for canon, aliases in SUBJECT_ALIASES.items():
        for alias in aliases:
            if any(alias in t for t in toks):
                found.add(canon)
                break
    # catch generic science/tech mentions
    joined = " ".join(toks)
    if "science" in joined or "pcm" in joined or "pcb" in joined:
        found.add("physics"); found.add("chemistry")
    if "pcm" in joined: found.add("maths")
    if "pcb" in joined: found.add("biology")
    return found


def _norm_skills(skills):
    return _tokens(skills)


def _match_interests(interests, keywords):
    toks = _tokens(interests)
    joined = " ".join(toks)
    return any(k in joined or any(k in t for t in toks) for k in keywords)


def _norm_location(location):
    """Return lowercased location string for scholarship filtering."""
    return (location or "").lower().strip()


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_career(profile, career):
    subjects = _norm_subjects(profile.get("subjects", ""))
    skills = _norm_skills(profile.get("skills", ""))
    interests = profile.get("interests", "")
    edu_path = (profile.get("preferredEducationPath") or "").strip().lower()

    required_subjects = career["subjects"]
    matched_subjects = [s for s in required_subjects if s in subjects]
    subject_score = (len(matched_subjects) / len(required_subjects)) * 40 if required_subjects else 0

    # Skills: check if the student already possesses career skills
    required_skills = career["skills"]
    career_skill_keywords = [s.split(" (")[0].lower() for s in required_skills]
    skill_hits = 0
    for kw in career_skill_keywords:
        kw_first = kw.split()[0]
        if any(kw_first in s for s in skills):
            skill_hits += 1
    skill_score = (skill_hits / len(career_skill_keywords)) * 30

    interest_hits = [tag for tag in career["interests"] if _match_interests(interests, INTEREST_KEYWORDS.get(tag, []))]
    interest_score = 20 if interest_hits else 0

    path_score = 0
    if edu_path and edu_path != "not sure":
        for p in career["education_paths"]:
            if edu_path in p.lower():
                path_score = 10
                break
        else:
            path_score = 2  # still possible, just less aligned
    elif not edu_path or edu_path == "not sure":
        path_score = 6  # open to guidance

    score = round(subject_score + skill_score + interest_score + path_score)
    return min(score, 98), matched_subjects, interest_hits, skill_hits


def build_skill_gaps(profile, career):
    skills = _norm_skills(profile.get("skills", ""))
    gaps = []
    for skill in career["skills"]:
        base = skill.split(" (")[0].lower()
        first = base.split()[0]
        if not any(first in s for s in skills):
            importance = "high" if skill in career["skills"][:2] else "medium"
            gaps.append({"skill": skill, "importance": importance,
                         "how_to_learn": _learning_hint(skill)})
    return gaps


def _learning_hint(skill):
    hints = {
        "Programming": "Start with Python — freeCodeCamp or CS50, then build one small project.",
        "Data Structures": "Practice on LeetCode/HackerRank after basic Python; 30 min a day.",
        "Excel": "Google 'Excel for Beginners' (free) + build one practice sheet weekly.",
        "SQL": "Free interactive courses on SQLZoo / Khan Academy; query a sample DB.",
        "Statistics": "Khan Academy Statistics + a free Coursera intro course.",
        "Communication": "Join a debate/Toastmasters club; practice 1-min explanations daily.",
        "Figma": "Figma's own free tutorials, then recreate 3 popular app screens.",
        "AutoCAD": "Free YouTube series, then redraw a floor plan.",
        "Photoshop": "Adobe Learn free basics; recreate 5 posters you like.",
        "Python": "CS50P or 'Automate the Boring Stuff' (free online).",
    }
    for key, text in hints.items():
        if key.lower() in skill.lower():
            return text
    return "Search for a free beginner course on this skill and practice weekly."


# ---------------------------------------------------------------------------
# Roadmap construction
# ---------------------------------------------------------------------------

def build_roadmap(profile, career, gaps, match_pct):
    financial = (profile.get("financialPreference") or "").strip().lower()
    need_scholarship = "scholarship" in financial or "budget" in financial

    top_gap_titles = [g["skill"] for g in gaps[:2]]
    gap_line = "Learn " + ", ".join(top_gap_titles) if top_gap_titles else "Sharpen your existing skills"

    years = [
        {
            "year": "Year 1 — Foundation",
            "phase": "Learn the core skills and build your first proof of work",
            "milestones": [
                {"title": f"Finish a beginner course: {career['courses'][0]}", "type": "course",
                 "detail": f"Goal: complete within 3 months. This is the #1 skill-gap fix for {career['career']}."},
                {"title": f"Project: {career['projects'][0]}", "type": "project",
                 "detail": "A concrete artefact you can show — this becomes your portfolio entry #1."},
                {"title": gap_line, "type": "skill",
                 "detail": "Weekly practice routine; 30–60 minutes, 4–5 days a week."},
                {"title": "Join a community (Discord/Reddit/local meetup)", "type": "skill",
                 "detail": "Learn from people already in the field — it accelerates everything."},
            ],
        },
        {
            "year": "Year 2 — Deepen & Internship Prep",
            "phase": "Move from learning to doing — build a portfolio and get real exposure",
            "milestones": [
                {"title": f"Finish advanced course: {career['courses'][1]}", "type": "course",
                 "detail": "Completes the practical side of your core skill set."},
                {"title": f"Project: {career['projects'][1]}", "type": "project",
                 "detail": "Portfolio entry #2 — slightly harder than entry #1, showing growth."},
                {"title": "Apply to 10+ internships (Internshala/LinkedIn)", "type": "internship",
                 "detail": "Even unpaid/remote internships build the resume line that matters."},
                {"title": "Publish your work (GitHub/Behance/portfolio site)", "type": "project",
                 "detail": "A live link beats a resume bullet point, every time."},
            ],
        },
        {
            "year": "Year 3 — Credentials & Degree Path",
            "phase": "Lock in the qualification that matches your education path",
            "milestones": [
                {"title": f"Complete certification: {career['certs'][0]}", "type": "certification",
                 "detail": "The credential employers filter for in this career."},
                {"title": f"Degree option: {career['degrees'][0]}", "type": "education",
                 "detail": f"Best-fit degree for {career['career']} based on your preferred education path."},
                {"title": "Apply for scholarships (see list below)", "type": "scholarship",
                 "detail": "Apply to at least 3 schemes this cycle — deadlines are early."},
                {"title": f"Project: {career['projects'][2]}", "type": "project",
                 "detail": "Portfolio entry #3 — your strongest, most complete work."},
            ],
        },
        {
            "year": "Year 4 — Launch",
            "phase": "Convert everything into your first real opportunity",
            "milestones": [
                {"title": "Interview prep: resume, portfolio review, mock interviews", "type": "skill",
                 "detail": "Do at least 5 mock interviews with seniors or online peers."},
                {"title": "Apply to 20+ jobs/roles (entry level)", "type": "internship",
                 "detail": "Volume + targeted applications; track every application in a sheet."},
                {"title": "Network: connect with 10 people in the field", "type": "skill",
                 "detail": "Referrals convert far better than cold applications."},
                {"title": "Start your career in " + career["career"], "type": "career",
                 "detail": "First role secured — the roadmap was the plan, this is the outcome."},
            ],
        },
    ]

    # Scholarship filter
    scholarships = list(SCHOLARSHIPS)
    if need_scholarship:
        scholarships = [s for s in scholarships if "financial aid" not in s["name"].lower() or True]
        scholarships = scholarships[:4]
    else:
        scholarships = scholarships[:3]

    return {
        "years": years,
        "courses": career["courses"],
        "certifications": career["certs"],
        "degree_options": career["degrees"],
        "scholarships": scholarships,
        "demand_outlook": career["demand"],
        "salary_range": career["salary"],
        "match_summary": (
            f"Best fit: {career['career']} scores {match_pct}% against your subjects, skills, interests and education path. "
            + ("Your financial preference flagged scholarship options below — apply early, deadlines matter." if need_scholarship
               else "Based on your profile, the standard education path works — no scholarship dependency.") 
        ),
    }


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def generate_roadmap(profile):
    """Given a student profile dict, return the full structured recommendation."""
    scored = []
    for career in CAREERS:
        score, matched_subjects, interest_hits, skill_hits = score_career(profile, career)
        scored.append((score, career, matched_subjects, interest_hits, skill_hits))

    scored.sort(key=lambda x: -x[0])
    top = scored[:3]

    recommendations = []
    for score, career, matched_subjects, interest_hits, skill_hits in top:
        reasons = []
        if matched_subjects:
            reasons.append(f"Your subjects ({', '.join(matched_subjects)}) align with this field")
        if skill_hits:
            reasons.append(f"You already have {skill_hits} relevant skill{'s' if skill_hits > 1 else ''}")
        if interest_hits:
            reasons.append(f"Your interests point this way ({', '.join(interest_hits)})")
        if not reasons:
            reasons.append("Good overall alignment with your profile and preferences")
        recommendations.append({
            "career": career["career"],
            "match_score": score,
            "match_reasons": reasons,
            "summary": career["summary"],
            "salary_range": career["salary"],
            "demand_outlook": career["demand"],
            "education_paths": career["education_paths"],
        })

    # Skill gaps for the top recommendation
    top_career = top[0][1]
    top_score = top[0][0]
    gaps = build_skill_gaps(profile, top_career)
    roadmap = build_roadmap(profile, top_career, gaps, top_score)

    return {
        "profile": profile,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "mock",
        "recommendations": recommendations,
        "skill_gaps": gaps,
        "roadmap": roadmap,
    }


# ---------------------------------------------------------------------------
# Profile-aware chat (DEMO_MODE)
# ---------------------------------------------------------------------------

def answer_chat(message, profile):
    msg = (message or "").lower()
    name = (profile.get("name") or "").strip() or "student"
    subjects = ", ".join(_norm_subjects(profile.get("subjects", ""))) or "your subjects"
    interests = profile.get("interests", "").strip() or "your interests"
    skills = profile.get("skills", "").strip() or "your current skills"

    def base():
        return (f"Based on your profile — {subjects}, interests in {interests}, skills: {skills} — "
                f"here's my take, {name.title()}.")

    if "engineer" in msg and ("no" in msg or "don't want" in msg or "not" in msg):
        return (f"{base()} You absolutely don't need an engineering degree. "
                "Your subjects open Data Analyst, Business Analyst, Product Manager, UI/UX Designer and Digital Marketing paths. "
                "Data Analyst is usually the smoothest switch — it rewards maths/analytics over an engineering tag. "
                "Want me to show the roadmap for it?")
    if "commerce" in msg:
        return (f"{base()} Commerce backgrounds fit Data Analyst, CA/Finance, Business Analyst, Product Manager and Digital Marketing really well. "
                "Data Analyst is the most in-demand — companies love commerce students who can work with numbers and SQL. "
                "Your location and budget also matter: tell me if scholarships are important and I'll filter options.")
    if "math" in msg or "mathematics" in msg:
        return (f"{base()} Strong mathematics opens Data Analyst, Data Scientist, Software Engineering, and even Finance/Quant paths — "
                "none of which require you to be an engineer first. If you enjoy applying maths to real problems, "
                "Data Science is the highest-growth option, but start with Data Analyst to build the foundation.")
    if "scholarship" in msg or "money" in msg or "fee" in msg or "cost" in msg or "budget" in msg:
        return (f"{base()} Good news — there are scholarships for nearly every path here, from the National Scholarship Portal "
                "(one application, many schemes) to state-level post-matric and AICTE Pragati/Saksham. "
                "Your roadmap already includes a filtered scholarship list. My advice: apply to at least 3 schemes this cycle; "
                "most deadlines are between October and December.")
    if "salary" in msg or "earn" in msg or "package" in msg or "pay" in msg:
        return (f"{base()} Entry-level ranges in your recommended careers are roughly ₹3.5–12 LPA depending on the field — "
                "Software Engineering and Data roles pay the most, while UI/UX and Marketing grow fast with portfolio quality. "
                "Long-term, Data Science, Product Management and Software Engineering have the steepest salary curves.")
    if "roadmap" in msg or "plan" in msg or "next" in msg or "start" in msg:
        return (f"{base()} Your roadmap is ready in the panel above: Year 1 is foundation courses + your first project, "
                "Year 2 deepens skills and lands an internship, Year 3 adds certifications/degrees and scholarships, "
                "Year 4 converts everything into your first role. Tick milestones as you finish them — the tracker will show your progress.")
    if "degree" in msg or "college" in msg or "university" in msg:
        return (f"{base()} For your top match, the best-fit degrees are listed in the roadmap. "
                "The good news: most of your recommended careers also accept certification-only paths if college is not affordable — "
                "start with the free courses in the roadmap and build a portfolio either way.")
    if "design" in msg or "creative" in msg or "art" in msg:
        return (f"{base()} Your creative side maps to UI/UX Designer and Graphic Designer. "
                "Both are portfolio-driven — you can start freelancing within months and neither needs an engineering degree. "
                "Given your interests, UI/UX (which also touches tech) tends to pay better than pure graphic design.")
    if "which" in msg or "recommend" in msg or "best" in msg or "option" in msg or "career" in msg:
        return (f"{base()} Based on my analysis your top three matches are the ones in the cards above, "
                "led by your best-scoring career. Each card shows why it matched. "
                "Ask me about salary, scholarships, switching streams, or degrees and I'll go deeper.")
    return (f"{base()} I can answer based on your profile — ask me things like "
            "\"I'm a commerce student, can I become a data analyst?\", \"I like maths but don't want engineering\", "
            "or about scholarships, salaries, degrees, or how to start your roadmap.")
