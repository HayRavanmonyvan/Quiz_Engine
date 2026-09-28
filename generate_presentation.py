"""
Automated PowerPoint Presentation Generator for:
Quiz Engine R&D Project Proposal & Final Defense
Aligns with Lecturer Sek Socheat's Advanced OOP Presentation Template.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

# ---------------------------------------------------------
# CONSTANTS & PALETTE
# ---------------------------------------------------------
COLOR_PRIMARY = RGBColor(103, 58, 183)    # Google Purple #673ab7
COLOR_DARK = RGBColor(33, 33, 33)         # Dark Gray / Off-black
COLOR_MUTED = RGBColor(117, 117, 117)     # Muted Gray
COLOR_BG_CARD = RGBColor(245, 243, 250)   # Light Purple Tint Card
COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_SUCCESS = RGBColor(46, 125, 50)     # Green

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]


def add_header(slide, title_text, category="ADVANCED OOP R&D PROJECT PROPOSAL"):
    """Adds standard header bar with category and title."""
    header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(1.1))
    tf = header_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_cat = tf.paragraphs[0]
    p_cat.text = category.upper()
    p_cat.font.size = Pt(11)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COLOR_PRIMARY

    p_title = tf.add_paragraph()
    p_title.text = title_text
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_DARK
    p_title.space_before = Pt(4)


def add_card(slide, left, top, width, height, title, body_bullets, bg_color=COLOR_BG_CARD):
    """Creates a card container with title and bullet points."""
    shape = slide.shapes.add_shape(1, left, top, width, height)  # 1 = MSO_SHAPE.RECTANGLE
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.color.rgb = COLOR_PRIMARY
    shape.line.width = Pt(1)

    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.25)
    tf.margin_top = Inches(0.2)

    p0 = tf.paragraphs[0]
    p0.text = title
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_PRIMARY

    for bullet in body_bullets:
        p = tf.add_paragraph()
        p.text = f"• {bullet}"
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_DARK
        p.space_before = Pt(5)


def add_notes(slide, notes_text):
    """Adds faculty defense speaker script into presenter notes."""
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = notes_text


# =========================================================
# SLIDE 1: Title & Metadata
# =========================================================
slide1 = prs.slides.add_slide(blank_layout)

# Accent Top Bar
top_bar = slide1.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(0.2))
top_bar.fill.solid()
top_bar.fill.fore_color.rgb = COLOR_PRIMARY
top_bar.line.fill.background()

title_box = slide1.shapes.add_textbox(Inches(1.0), Inches(1.2), Inches(11.3), Inches(2.2))
tf1 = title_box.text_frame
tf1.word_wrap = True

p_main = tf1.paragraphs[0]
p_main.text = "Autonomous RBAC Assessment Engine"
p_main.font.size = Pt(36)
p_main.font.bold = True
p_main.font.color.rgb = COLOR_PRIMARY

p_sub = tf1.add_paragraph()
p_sub.text = "A Decoupled Layered Architecture with 5-Table Access Control & Google Forms UX"
p_sub.font.size = Pt(18)
p_sub.font.color.rgb = COLOR_DARK
p_sub.space_before = Pt(8)

p_meta = tf1.add_paragraph()
p_meta.text = "Course: Advanced Object-Oriented Programming (Python + Flask + MySQL) | Lecturer: Sek Socheat"
p_meta.font.size = Pt(13)
p_meta.font.color.rgb = COLOR_MUTED
p_meta.space_before = Pt(14)

roles = [
    ("Systems Lead & Analyst", ["Project scope & requirements", "Architecture & evaluation metrics", "Proposal & defense preparation"]),
    ("Backend & OOP Designer", ["Dataclass domain models", "Auth & Grading services", "Business rule isolation"]),
    ("Database & Security", ["5-Table RBAC schema", "Parameterized repository queries", "ACID transaction rollbacks"]),
    ("UI & Test Automation", ["Google Forms card UI", "Countdown timer & CSV export", "Automated unittest suite (36/36)"])
]

for i, (r_title, r_items) in enumerate(roles):
    left = Inches(1.0 + (i * 2.88))
    add_card(slide1, left, Inches(4.0), Inches(2.7), Inches(2.6), r_title, r_items)

add_notes(slide1, "Good morning Lecturer Sek Socheat and committee members. Today we present our project proposal: an Autonomous, Google Forms-inspired Quiz Engine built on a 5-layer decoupled architecture with enterprise-grade Role-Based Access Control. Our goal is to solve the architectural vulnerabilities, tight coupling, and data integrity failures found in standard educational web tools.")


# =========================================================
# SLIDE 2: Problem Statement & Industry Context
# =========================================================
slide2 = prs.slides.add_slide(blank_layout)
add_header(slide2, "Problem Statement: Architectural Anti-Patterns in Web Assessment")

table_shape2 = slide2.shapes.add_table(5, 3, Inches(0.8), Inches(1.8), Inches(11.73), Inches(4.8))
table2 = table_shape2.table
table2.columns[0].width = Inches(2.6)
table2.columns[1].width = Inches(4.5)
table2.columns[2].width = Inches(4.63)

headers2 = ["Failure Dimension", "Ad-Hoc / Monolithic Web Apps", "Our Engineering Solution"]
for col_idx, text in enumerate(headers2):
    cell = table2.cell(0, col_idx)
    cell.fill.solid()
    cell.fill.fore_color.rgb = COLOR_PRIMARY
    p = cell.text_frame.paragraphs[0]
    p.text = text
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = COLOR_WHITE

rows2 = [
    ("Code Organization", "Monolithic app.py with routes, SQL, and business logic tightly coupled in one God file.", "Strict 5-layer decoupled architecture (Models, Repositories, Services, Blueprints, Templates)."),
    ("Access Control", "Hardcoded boolean flags (is_admin) or static role_id columns leading to privilege leaks.", "Dynamic 5-Table RBAC standard (users, roles, permissions, user_roles, role_permissions)."),
    ("Data Integrity", "Multi-table quiz inserts performed without transactions, leaving orphaned questions.", "Atomic MySQL transactions with explicit conn.rollback() on any child insert error."),
    ("Assessment Control", "Untimed forms vulnerable to browser tampering and lacking response exports.", "Client/server countdown timer, auto-submit on timeout, and class CSV export.")
]

for row_idx, data in enumerate(rows2, start=1):
    for col_idx, val in enumerate(data):
        cell = table2.cell(row_idx, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_WHITE if row_idx % 2 == 0 else COLOR_BG_CARD
        p = cell.text_frame.paragraphs[0]
        p.text = val
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_DARK
        if col_idx == 0:
            p.font.bold = True

add_notes(slide2, "Data analysis of student web projects reveals recurring anti-patterns: monolithic God-files inside app.py, SQL injection risks, and static role assignments. When an application hardcodes an is_admin boolean, expanding permissions requires dangerous schema migrations. Furthermore, non-transactional quiz creation leaves orphaned records in the database. Our project replaces these failure points with a normalized, tested, and defendable architecture.")


# =========================================================
# SLIDE 3: Objectives & Scope Boundaries
# =========================================================
slide3 = prs.slides.add_slide(blank_layout)
add_header(slide3, "Measurable Objectives & Engineering Scope Boundaries")

add_card(slide3, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8), "In-Scope Core Deliverables", [
    "5-Table Normalized RBAC: Dynamic user-role and role-permission bridge resolution.",
    "Decoupled Architecture: Independent domain models, repositories, services, and route guards.",
    "ACID Transaction Safety: Atomic inserts for quizzes, questions, and options.",
    "Google Forms UX: Signature purple header, floating cards, answer key radio select.",
    "Assessment Engine: Duration countdown timers, auto-submit on expiry, instant evaluation.",
    "Data Export: Administrative and teacher response export to structured CSV files."
])

add_card(slide3, Inches(6.9), Inches(1.8), Inches(5.6), Inches(4.8), "Out-of-Scope (Deliberate Trade-Offs)", [
    "Third-Party OAuth / Social Login: Focus kept on internal 5-table RBAC traversal.",
    "External SMTP Email Verification: Avoids external network dependencies and demo failures.",
    "Live Video Proctoring / WebRTC: High overhead non-essential to core OOP database rubric.",
    "Payment Gateway / Monetization: Irrelevant to educational assessment workflow.",
    "Mobile Native App: Addressed via responsive CSS flexbox/card layouts on web."
])

add_notes(slide3, "To ensure our R&D project remains achievable within the semester timeline, we have defined strict boundaries. We prioritize depth over width: instead of adding fragile third-party mail APIs, we focus heavily on core computer science fundamentals—data persistence, atomic transactions, domain model encapsulation, and permission checking.")


# =========================================================
# SLIDE 4: User Personas & RBAC Matrix
# =========================================================
slide4 = prs.slides.add_slide(blank_layout)
add_header(slide4, "User Personas & Fine-Grained Authorization Matrix")

table_shape4 = slide4.shapes.add_table(8, 5, Inches(0.8), Inches(1.8), Inches(11.73), Inches(4.8))
table4 = table_shape4.table
table4.columns[0].width = Inches(2.5)
table4.columns[1].width = Inches(1.6)
table4.columns[2].width = Inches(1.6)
table4.columns[3].width = Inches(1.6)
table4.columns[4].width = Inches(4.43)

headers4 = ["Permission Token", "Admin", "Teacher", "Student", "System Action & Architectural Guard"]
for col_idx, text in enumerate(headers4):
    cell = table4.cell(0, col_idx)
    cell.fill.solid()
    cell.fill.fore_color.rgb = COLOR_PRIMARY
    p = cell.text_frame.paragraphs[0]
    p.text = text
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_WHITE

perms4 = [
    ("user:manage", "Bypass", "Blocked (403)", "Blocked (403)", "Full user administration, role reassignment, status toggle."),
    ("quiz:create", "Bypass", "Allowed", "Blocked (403)", "Author quizzes, questions, points, and duration limits."),
    ("quiz:edit / delete", "Bypass", "Allowed", "Blocked (403)", "Update assessments or cascade delete quiz trees."),
    ("quiz:score", "Bypass", "Allowed", "Blocked (403)", "Inspect student submissions and apply qualitative feedback."),
    ("quiz:view", "Bypass", "Allowed", "Allowed", "Browse published quizzes in the active catalog."),
    ("quiz:submit", "Bypass", "Blocked (403)", "Allowed", "Submit quiz responses and trigger automated grading."),
    ("report:view_all", "Bypass", "Allowed", "Blocked (403)", "View class analytics, pass rates, and export CSV files.")
]

for row_idx, data in enumerate(perms4, start=1):
    for col_idx, val in enumerate(data):
        cell = table4.cell(row_idx, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_WHITE if row_idx % 2 == 0 else COLOR_BG_CARD
        p = cell.text_frame.paragraphs[0]
        p.text = val
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_DARK
        if col_idx == 0:
            p.font.bold = True

add_notes(slide4, "Our RBAC system does not evaluate raw role strings inside our routes. Instead, it resolves discrete permissions hydrated during login. A student cannot access the quiz builder because their session lacks quiz:create. If a student tries to post a submission to a teacher endpoint, the web security decorator intercepts the request, returning a clean 403 Forbidden or security redirect.")


# =========================================================
# SLIDE 5: OOP Domain Layer & SOLID Design
# =========================================================
slide5 = prs.slides.add_slide(blank_layout)
add_header(slide5, "Object-Oriented Domain Layer: Single Responsibility & State Safety")

models5 = [
    ("User (Dataclass)", [
        "Attributes: id, username, email, roles: List[str], permissions: List[str]",
        "Methods: has_role(role_name), has_permission(permission_name)",
        "Admin bypass logic: User.has_permission() returns True if 'Admin' in roles"
    ]),
    ("Quiz & Question (Dataclasses)", [
        "Quiz: title, description, time_limit_minutes, pass_percentage, questions",
        "Encapsulation: Quiz.max_score() calculates sum of question points",
        "Question: prompt, points, order_num, options: List[QuestionOption]"
    ]),
    ("Submission & Grading", [
        "Submission: student_id, quiz_id, total_score, max_score, passed, feedback",
        "GradingService: orchestrates business rules without SQL pollution",
        "Polymorphic score percentage calculation and threshold verification"
    ])
]

for i, (m_title, m_bullets) in enumerate(models5):
    left = Inches(0.8 + (i * 3.95))
    add_card(slide5, left, Inches(1.8), Inches(3.75), Inches(4.8), m_title, m_bullets)

add_notes(slide5, "To satisfy our OOP rubric, our classes exhibit high cohesion and single responsibility. The Quiz model calculates its own maximum possible score and verifies question structural validity before touching the database. The User entity encapsulates role hierarchy logic—for example, automatically evaluating wildcard admin bypasses inside User.has_permission().")


# =========================================================
# SLIDE 6: Decoupled Multi-Layer Architecture
# =========================================================
slide6 = prs.slides.add_slide(blank_layout)
add_header(slide6, "Decoupled 5-Tier Flask Architecture")

layers6 = [
    ("Presentation Tier (Templates / UI)", [
        "Google Forms card layout with purple accent (#673ab7).",
        "Dynamic JS form builder and floating assessment countdown timer.",
        "Quick demo login switcher for rapid role evaluation."
    ]),
    ("Routing & Security Tier (Blueprints)", [
        "Routes: web_bp.py (views), auth_bp.py (authentication).",
        "Thin controllers: zero direct SQL queries, delegates to services.",
        "Guards: @login_required, @require_permission(perm_token)."
    ]),
    ("Business Logic Tier (Services)", [
        "AuthService: manages password hashing, session hydration, user CRUD.",
        "QuizService: validates quiz models, payload parsing, time limits.",
        "GradingService: evaluates answers, determines pass/fail thresholds."
    ]),
    ("Persistence Tier (Repositories & MySQL)", [
        "UserRepository, QuizRepository, SubmissionRepository.",
        "100% Parameterized queries (%s) preventing SQL injection.",
        "Atomic multi-table inserts with explicit rollback on failure."
    ])
]

for i, (l_title, l_bullets) in enumerate(layers6):
    top = Inches(1.7 + (i * 1.25))
    add_card(slide6, Inches(0.8), top, Inches(11.73), Inches(1.15), l_title, l_bullets)

add_notes(slide6, "Our architecture complies with Lecturer Sek Socheat's design rule: routes must call services, services must coordinate business rules, and repositories must handle database access. Notice the complete absence of SQL queries within our route blueprints. If we switch our database or change UI layouts, our core business rules in GradingService remain untouched.")


# =========================================================
# SLIDE 7: Database Architecture & ACID Transactions
# =========================================================
slide7 = prs.slides.add_slide(blank_layout)
add_header(slide7, "Database Design: 5-Table RBAC Standard & Atomic Transactions")

add_card(slide7, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8), "5-Table Relational RBAC (3NF)", [
    "users: id (PK), username, email, password_hash, is_active, created_at. (Zero static role_id).",
    "roles: id (PK), name ('Admin', 'Teacher', 'Student'), description.",
    "permissions: id (PK), name ('quiz:create', 'report:view_all'), description.",
    "user_roles: user_id (FK), role_id (FK) -> Many-to-many bridge.",
    "role_permissions: role_id (FK), permission_id (FK) -> Many-to-many bridge.",
    "Pure Junction Tables: Allows users to have dynamic, multiple roles without altering schema."
])

add_card(slide7, Inches(6.9), Inches(1.8), Inches(5.6), Inches(4.8), "Assessment Tables & ACID Transactions", [
    "quizzes: id, title, description, pass_percentage, time_limit_minutes, created_by.",
    "questions & question_options: Hierarchical foreign keys with ON DELETE CASCADE.",
    "submissions & submission_answers: Records student selections and score snapshots.",
    "Atomic Transaction Block in QuizRepository.create():",
    "  1. conn.autocommit = False",
    "  2. Insert quiz -> Insert questions -> Insert options",
    "  3. conn.commit() on success",
    "  4. except Exception -> conn.rollback() (Zero orphaned questions!)"
])

add_notes(slide7, "Our database implements the full 5-table RBAC standard without compromises. We dropped the redundant role_id column from users to maintain a single source of truth. Roles and permissions are joined dynamically across user_roles and role_permissions. Furthermore, all inserts across questions and options are transactional: either the complete assessment commits, or everything rolls back cleanly.")


# =========================================================
# SLIDE 8: R&D Timeline & Risk Management
# =========================================================
slide8 = prs.slides.add_slide(blank_layout)
add_header(slide8, "R&D Timeline, Sprint Milestones & Technical Risk Mitigation")

table_shape8 = slide8.shapes.add_table(5, 4, Inches(0.8), Inches(1.8), Inches(11.73), Inches(4.8))
table8 = table_shape8.table
table8.columns[0].width = Inches(2.2)
table8.columns[1].width = Inches(1.8)
table8.columns[2].width = Inches(1.5)
table8.columns[3].width = Inches(6.23)

headers8 = ["Identified Risk", "Severity", "Probability", "Applied Engineering Mitigation"]
for col_idx, text in enumerate(headers8):
    cell = table8.cell(0, col_idx)
    cell.fill.solid()
    cell.fill.fore_color.rgb = COLOR_PRIMARY
    p = cell.text_frame.paragraphs[0]
    p.text = text
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_WHITE

risks8 = [
    ("Privilege Escalation", "High", "Low", "Enforce @require_permission decorators on all mutating endpoints; server-side session checks."),
    ("Orphaned Data / Partial Inserts", "High", "Low", "InnoDB foreign keys with CASCADE + atomic transactions with explicit rollback."),
    ("Client-Side Timer Tampering", "Medium", "Medium", "Server records start_time in session; auto-grading validates elapsed time on submission."),
    ("SQL Injection Attacks", "Critical", "Low", "100% Parameterized queries (%s) in repositories; zero string concatenation.")
]

for row_idx, data in enumerate(risks8, start=1):
    for col_idx, val in enumerate(data):
        cell = table8.cell(row_idx, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_WHITE if row_idx % 2 == 0 else COLOR_BG_CARD
        p = cell.text_frame.paragraphs[0]
        p.text = val
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_DARK
        if col_idx == 0:
            p.font.bold = True

add_notes(slide8, "Our timeline mirrors the R&D project lifecycle outlined in the syllabus. By addressing data security and transaction risks during Weeks 4 through 8, we ensure that the testing phase in Weeks 9 and 10 validates established business logic rather than diagnosing architectural flaws.")


# =========================================================
# SLIDE 9: Automated Verification & Empirical Results
# =========================================================
slide9 = prs.slides.add_slide(blank_layout)
add_header(slide9, "Empirical Verification: 36/36 Automated Tests Passing (1.013s)")

kpis9 = [
    ("Total Tests", "36", "Unit, integration & E2E tests"),
    ("Pass Rate", "100%", "0 Failures / 0 Errors"),
    ("Runtime", "1.013s", "Sub-second test execution")
]

for i, (k_title, k_val, k_sub) in enumerate(kpis9):
    left = Inches(0.8 + (i * 3.95))
    shape = slide9.shapes.add_shape(1, left, Inches(1.8), Inches(3.75), Inches(1.4))
    shape.fill.solid()
    shape.fill.fore_color.rgb = COLOR_BG_CARD
    shape.line.color.rgb = COLOR_SUCCESS
    shape.line.width = Pt(1.5)
    tf = shape.text_frame
    tf.word_wrap = True
    p0 = tf.paragraphs[0]
    p0.text = k_title.upper()
    p0.font.size = Pt(10)
    p0.font.color.rgb = COLOR_MUTED
    p1 = tf.add_paragraph()
    p1.text = k_val
    p1.font.size = Pt(28)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_SUCCESS
    p2 = tf.add_paragraph()
    p2.text = k_sub
    p2.font.size = Pt(10)
    p2.font.color.rgb = COLOR_DARK

suites9 = [
    ("Domain & Scoring (14 Tests)", [
        "Question validation (prompt, >=2 options, single answer key).",
        "Dynamic max_score calculation.",
        "Pass/fail boundary score grading."
    ]),
    ("RBAC & Security (16 Tests)", [
        "Admin bypass validation on all permissions.",
        "403 Forbidden on unauthorized endpoint access.",
        "QuizRepository rollback verification."
    ]),
    ("Live E2E Flows (6 Tests)", [
        "Sequential row index & user ID badges.",
        "Timer countdown & auto-submit.",
        "Teacher CSV class response export."
    ])
]

for i, (s_title, s_bullets) in enumerate(suites9):
    left = Inches(0.8 + (i * 3.95))
    add_card(slide9, left, Inches(3.4), Inches(3.75), Inches(3.2), s_title, s_bullets)

add_notes(slide9, "We follow test-driven principles. As demonstrated in our test results, 36 automated test cases pass in just over 1 second. We test business rules, transaction safety, and security limits: students are confirmed to receive 403 Forbidden on admin endpoints, and database rollbacks are verified to work when faulty records are inserted.")


# =========================================================
# SLIDE 10: Deliverables & Live Demonstration Strategy
# =========================================================
slide10 = prs.slides.add_slide(blank_layout)
add_header(slide10, "Deliverables & Live Demonstration Defense Flow")

demo_steps = [
    ("1. Clean Seed Initialization", "Execute python -m database.init_db to seed Admin, Teacher, and Student personas."),
    ("2. Role Navigation & RBAC", "Log in as student_john; demonstrate 403 intercept when accessing /admin/dashboard."),
    ("3. Visual Quiz Building", "Log in as teacher_jane; build a timed quiz with dynamic points and radio answer keys."),
    ("4. Timed Assessment Attempt", "Log in as student_john; complete assessment with live countdown timer and instant scorecard."),
    ("5. Manual Grading & Feedback", "Teacher reviews student attempt, overrides score, and submits qualitative feedback."),
    ("6. Response Data Export", "Teacher exports the complete class response ledger to CSV format.")
]

for i, (d_title, d_desc) in enumerate(demo_steps):
    top = Inches(1.7 + (i * 0.85))
    shape = slide10.shapes.add_shape(1, Inches(0.8), top, Inches(11.73), Inches(0.75))
    shape.fill.solid()
    shape.fill.fore_color.rgb = COLOR_BG_CARD
    shape.line.color.rgb = COLOR_PRIMARY
    shape.line.width = Pt(1)
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.2)
    tf.margin_top = Inches(0.1)
    p0 = tf.paragraphs[0]
    p0.text = d_title
    p0.font.size = Pt(12)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_PRIMARY
    p1 = tf.add_paragraph()
    p1.text = d_desc
    p1.font.size = Pt(10)
    p1.font.color.rgb = COLOR_DARK

add_notes(slide10, "During our final defense, we will follow the faculty demo checklist: starting from a seeded database, switching between personas, creating quizzes through the Google Forms builder, taking an assessment with countdown timers, and exporting student response datasets to CSV. Every technical design decision is backed by modular code that our team can explain.")


# =========================================================
# SLIDE 11: Technical Defense & Faculty Q&A
# =========================================================
slide11 = prs.slides.add_slide(blank_layout)
add_header(slide11, "Technical Defense: Architectural Decisions & Faculty Q&A")

qas11 = [
    ("Q1: Why use 5 tables instead of a static 'role' column on the User table?", [
        "A static column violates 3NF normalization and creates schema rigidity.",
        "The 5-table schema (users, roles, permissions, user_roles, role_permissions) supports multiple roles per user and dynamic permission adjustments without database migrations.",
        "Enables fine-grained permission-based decorators (@require_permission) rather than coarse role strings."
    ]),
    ("Q2: How does your system prevent orphaned records if a quiz creation query fails?", [
        "QuizRepository.create() wraps the entire creation lifecycle in an explicit atomic transaction.",
        "Sets conn.autocommit = False. Inserts the quiz record, iterates questions, and inserts options.",
        "If an error occurs on any child insert, conn.rollback() is invoked, guaranteeing zero orphaned records in MySQL."
    ]),
    ("Q3: Why separate the Repository layer from the Service layer?", [
        "Enforces the Single Responsibility Principle (SRP) and enables isolated unit testing.",
        "GradingService can be tested with mock data in 1.013 seconds without spinning up a live MySQL connection.",
        "Decouples SQL syntax from business grading rules and web HTTP request handling."
    ])
]

for i, (q_title, q_bullets) in enumerate(qas11):
    top = Inches(1.7 + (i * 1.7))
    add_card(slide11, Inches(0.8), top, Inches(11.73), Inches(1.55), q_title, q_bullets)

add_notes(slide11, "Thank you Lecturer Sek Socheat and committee members. We have designed this system around maintainability, clean object-oriented design, and verifiable security. We now welcome your questions and feedback.")


# Save Presentation
output_filename = "Quiz_Engine_Proposal_Defense.pptx"
prs.save(output_filename)
print(f"[SUCCESS] Presentation generated successfully: {output_filename}")