# Academic Project Specifications & Evaluation Rubric: Quiz Engine

## 1. System Overview & Core Objectives
Build a production-ready Web Quiz Assessment Engine built with Python (Flask) and MySQL[cite: 8]. The platform enforces strict Role-Based Access Control (RBAC) across three distinct user actors[cite: 8]:
- **Admin**: Complete system oversight, user role administration, status management, and master catalog control[cite: 8].
- **Teacher / Instructor**: Dynamic quiz creation, question/answer key management, response inspection, and score adjustment with qualitative feedback[cite: 8].
- **Student**: Quiz discovery, interactive assessment taking, automated instant grading, and historical attempt review[cite: 8].

---

## 2. Architectural Requirements (Decoupled Layered Architecture)
The application must adhere to a strict layered design[cite: 8]:
- **Domain Layer (`app/models/`)**: Python dataclasses encapsulating state, validation rules, and core domain behaviors (`User`, `Quiz`, `Question`, `QuestionOption`, `Submission`, `SubmissionAnswer`)[cite: 8]. No database queries or framework imports inside models[cite: 8].
- **Data Access Layer (`app/repositories/`)**: Encapsulates all raw MySQL interactions using secure parameterized queries (`%s`)[cite: 8]. Must strictly implement atomic database transactions (`conn.begin()`, `conn.commit()`, and `conn.rollback()`) for multi-entity creation and cascading operations[cite: 8].
- **Business Logic Layer (`app/services/`)**: Orchestrates domain models and repositories[cite: 8]. Handles user authorization resolution, password hashing/salting, dynamic quiz evaluation, pass threshold calculations, and teacher grade modifications[cite: 8].
- **Web & Security Layer (`app/routes/`)**: Flask blueprints (`web_bp`, `auth_bp`)[cite: 8]. Enforces endpoint guards via custom Python decorators (`@login_required`, `@require_permission`)[cite: 8]. Routes must remain thin controllers that validate inputs and delegate work entirely to services[cite: 8].

---

## 3. Database Schema & RBAC Specifications
The relational schema must enforce a decoupled 5-table RBAC standard with zero redundant role columns on the primary user record[cite: 8]:
1. `users`: `id`, `username`, `email`, `password_hash`, `is_active`, `created_at` (Must NOT contain a static `role_id`)[cite: 8].
2. `roles`: `id`, `name`, `description`.
3. `permissions`: `id`, `name`, `description`.
4. `user_roles`: `user_id`, `role_id` (Composite PK, foreign keys with `ON DELETE CASCADE`)[cite: 8].
5. `role_permissions`: `role_id`, `permission_id` (Composite PK, foreign keys with `ON DELETE CASCADE`)[cite: 8].

### Core Assessment Tables:
6. `quizzes`: `id`, `title`, `description`, `pass_percentage`, `created_by`, `created_at`[cite: 8].
7. `questions`: `id`, `quiz_id`, `prompt`, `points`, `order_num`[cite: 8].
8. `question_options`: `id`, `question_id`, `option_text`, `is_correct`[cite: 8].
9. `submissions`: `id`, `quiz_id`, `student_id`, `total_score`, `max_score`, `passed`, `teacher_feedback`, `submitted_at`[cite: 8].
10. `submission_answers`: `id`, `submission_id`, `question_id`, `selected_option_id`, `is_correct`[cite: 8].

### Seed Data & Roles
- **Standardized Roles**: `Admin` (ID: 1), `Teacher` (ID: 2), `Student` (ID: 3)[cite: 8].
- **Granular Permissions**:
  - `user:manage`: View, create, update, and toggle user accounts[cite: 8].
  - `quiz:create`, `quiz:edit`, `quiz:delete`: Manage question banks and quizzes[cite: 8].
  - `quiz:score`: View submissions and modify grades/feedback[cite: 8].
  - `quiz:view`: Inspect public quiz catalogs[cite: 8].
  - `quiz:submit`: Execute assessments and record answer choices[cite: 8].
  - `report:view_all`: Teacher/Admin analytics and submission breakdown[cite: 8].
  - `report:view_own`: Student personal attempt history[cite: 8].
- **Demo Seed Credentials**:
  - All default accounts use password: `Password@123`[cite: 8]
  - Admin: `admin`[cite: 8]
  - Teachers: `teacher_jane`, `instructor_socheat`[cite: 8]
  - Students: `student_john`, `student_alice`[cite: 8]

---

## 4. UI/UX Design Standards (Google Forms Aesthetic)
- Signature purple accent palette (`#673ab7`) with subtle card shadows, clean borders, and floating containers[cite: 8].
- **Authentication**: Quick Demo Role Switcher to swap between Admin, Teacher, and Student personas for evaluation[cite: 8].
- **Quiz Taking View**: Card-based question layout with points indicators (`1 pt`, `2 pts`), clear active selection, and floating submit controls[cite: 8].
- **Teacher Quiz Builder**: Visual builder supporting dynamic question addition, point assignment, and radio-click answer key marking[cite: 8].
- **Responses View**: Google Forms-inspired summary dashboard displaying aggregate KPIs (average score, pass rate, completion count) and student response cards[cite: 8].

---

## 5. Testing & Verification Standards
- Maintain automated unit tests covering domain rules, service calculations, and permission guards[cite: 8].
- Verify that `User.has_permission()` accurately accounts for the Admin wildcard bypass[cite: 8].
- Verify that `QuizRepository` rollbacks are triggered whenever child question or option insertions fail[cite: 8].
- Ensure 403 Forbidden enforcement on restricted endpoints when accessed by unauthorized roles[cite: 8].

---

## 6. Academic Deliverables & Defense Expectations
- Fully functional, bug-free codebase with complete setup instructions[cite: 8].
- Comprehensive project documentation/report detailing system architecture, entity-relationship diagrams (ERD), layered class hierarchies, and RBAC security flows[cite: 8].
- Defense presentation covering architectural design justifications, transaction integrity, and live software demonstration[cite: 8].