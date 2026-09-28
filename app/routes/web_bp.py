# app/routes/web_bp.py
import json
import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, Response
from app.repositories.user_repository import UserRepository
from app.repositories.quiz_repository import QuizRepository
from app.repositories.submission_repository import SubmissionRepository
from app.services.auth_service import AuthService
from app.services.quiz_service import QuizService
from app.services.grading_service import GradingService
from app.routes.security import login_required, require_permission

web_bp = Blueprint("web", __name__)

user_repo = UserRepository()
quiz_repo = QuizRepository()
sub_repo = SubmissionRepository()

auth_service = AuthService(user_repo)
quiz_service = QuizService(quiz_repo, sub_repo)
grading_service = GradingService(quiz_repo, sub_repo)


@web_bp.route("/")
def index():
    if not session.get("user_id"):
        return redirect(url_for("web.list_quizzes"))
    
    roles = [r.lower() for r in session.get("roles", [])]
    if "admin" in roles:
        return redirect(url_for("web.admin_dashboard"))
    elif "teacher" in roles or "instructor" in roles:
        return redirect(url_for("web.teacher_dashboard"))
    return redirect(url_for("web.list_quizzes"))


# ==========================================
# Authentication & Demo Quick Login
# ==========================================

@web_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        try:
            user = auth_service.authenticate(username, password)
            session["user_id"] = user.id
            session["username"] = user.username
            session["roles"] = user.roles
            session["permissions"] = user.permissions

            flash(f"Welcome back, {user.username}!", "success")
            if user.is_admin:
                return redirect(url_for("web.admin_dashboard"))
            elif user.is_teacher:
                return redirect(url_for("web.teacher_dashboard"))
            return redirect(url_for("web.list_quizzes"))
        except PermissionError as err:
            flash(str(err), "danger")

    return render_template("auth/login.html")


@web_bp.route("/register", methods=["GET", "POST"])
def register():
    """Student Self-Registration (Sign Up)."""
    if session.get("user_id"):
        return redirect(url_for("web.list_quizzes"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        try:
            user = auth_service.register_student(
                username=username,
                email=email,
                password=password,
                confirm_password=confirm_password
            )
            # Automatically log into session upon successful registration
            session["user_id"] = user.id
            session["username"] = user.username
            session["roles"] = user.roles
            session["permissions"] = user.permissions

            flash(f"Welcome, {user.username}! Your student account has been created successfully.", "success")
            return redirect(url_for("web.list_quizzes"))
        except ValueError as err:
            flash(str(err), "danger")
            return render_template("auth/register.html", username=username, email=email)

    return render_template("auth/register.html")


@web_bp.route("/demo-login/<role_name>")
def demo_login(role_name: str):
    """Convenience endpoint to instantly sign in as a demo user for quick role verification."""
    role_map = {
        "admin": "admin",
        "teacher": "teacher_jane",
        "student": "student_john"
    }
    username = role_map.get(role_name.lower())
    if not username:
        flash("Unknown demo role.", "danger")
        return redirect(url_for("web.login"))

    try:
        user = auth_service.authenticate(username, "Password@123")
        session["user_id"] = user.id
        session["username"] = user.username
        session["roles"] = user.roles
        session["permissions"] = user.permissions

        flash(f"Quick signed in as {user.username} (Role: {user.primary_role})", "info")
        if user.is_admin:
            return redirect(url_for("web.admin_dashboard"))
        elif user.is_teacher:
            return redirect(url_for("web.teacher_dashboard"))
        return redirect(url_for("web.list_quizzes"))
    except Exception as err:
        flash(f"Demo login failed: {err}", "danger")
        return redirect(url_for("web.login"))


@web_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("web.login"))


@web_bp.route("/break-glass", methods=["GET", "POST"])
def break_glass():
    """Emergency administrative override access for disaster recovery & staff absence."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        reason = request.form.get("reason", "").strip()
        ip_address = request.remote_addr

        try:
            user = auth_service.emergency_break_glass_login(username, password, reason=reason, ip_address=ip_address)
            session["user_id"] = user.id
            session["username"] = user.username
            session["roles"] = user.roles
            session["permissions"] = user.permissions
            session["is_emergency_session"] = True
            session["emergency_reason"] = reason

            flash("🚨 BREAK-GLASS EMERGENCY OVERRIDE AUTHORIZED. Session is being actively logged.", "danger")
            return redirect(url_for("web.admin_dashboard"))
        except (ValueError, PermissionError) as err:
            flash(f"Emergency Access Rejected: {err}", "danger")
            return render_template("auth/break_glass.html", username=username)

    return render_template("auth/break_glass.html")


# ==========================================
# Student Views & Quiz Taking (Google Form style)
# ==========================================

@web_bp.route("/quizzes")
@require_permission("quiz:view")
def list_quizzes():
    quizzes = quiz_service.list_available_quizzes()
    return render_template("student/quizzes.html", quizzes=quizzes)


@web_bp.route("/quizzes/<int:quiz_id>")
@require_permission("quiz:view")
def take_quiz(quiz_id: int):
    quiz = quiz_service.get_public_quiz_view(quiz_id)
    if not quiz:
        flash("Quiz not found.", "danger")
        return redirect(url_for("web.list_quizzes"))

    return render_template("student/take_quiz.html", quiz=quiz)


@web_bp.route("/quizzes/<int:quiz_id>/submit", methods=["POST"])
@require_permission("quiz:submit")
def submit_quiz(quiz_id: int):
    student_id = session.get("user_id")

    # Extract answers from submitted form: name format is 'question_<id>'
    answers_map = {}
    for key, value in request.form.items():
        if key.startswith("question_"):
            try:
                q_id = int(key.replace("question_", ""))
                answers_map[q_id] = int(value)
            except ValueError:
                continue

    try:
        submission = grading_service.evaluate_and_record(quiz_id, student_id, answers_map)
        flash("Assessment submitted successfully!", "success")
        return redirect(url_for("web.view_submission", submission_id=submission.id))
    except ValueError as err:
        flash(str(err), "danger")
        return redirect(url_for("web.take_quiz", quiz_id=quiz_id))


@web_bp.route("/submissions/<int:submission_id>")
@login_required
def view_submission(submission_id: int):
    submission = grading_service.get_submission_detail(submission_id)
    if not submission:
        flash("Submission not found.", "danger")
        return redirect(url_for("web.list_quizzes"))

    # Permission check: Student can only view their own submission; Teacher and Admin can view any
    user_roles = [r.lower() for r in session.get("roles", [])]
    is_staff = any(r in ("admin", "teacher", "instructor") for r in user_roles)
    if not is_staff and submission.student_id != session.get("user_id"):
        flash("Access Denied: You cannot view another student's submission.", "danger")
        return redirect(url_for("web.my_submissions"))

    return render_template("student/result.html", submission=submission)


@web_bp.route("/student/my-submissions")
@require_permission("report:view_own")
def my_submissions():
    student_id = session.get("user_id")
    submissions = grading_service.list_student_submissions(student_id)
    return render_template("student/my_submissions.html", submissions=submissions)


# ==========================================
# Teacher Views & Google Form Builder
# ==========================================

@web_bp.route("/teacher/dashboard")
@require_permission("report:view_all")
def teacher_dashboard():
    user = user_repo.get_by_id(session.get("user_id"))
    quizzes = quiz_service.list_available_quizzes()
    return render_template("teacher/dashboard.html", quizzes=quizzes, current_user=user)


@web_bp.route("/teacher/quizzes/new", methods=["GET", "POST"])
@require_permission("quiz:create")
def new_quiz():
    """Google Form visual quiz builder."""
    if request.method == "POST":
        # Check if submitted as JSON or standard Form with quiz_data
        if request.is_json:
            data = request.get_json() or {}
        else:
            raw_payload = request.form.get("quiz_data")
            data = json.loads(raw_payload) if raw_payload else {}

        try:
            quiz_id = quiz_service.create_quiz(data, creator_id=session.get("user_id"))
            if request.is_json:
                return jsonify({"status": "success", "quiz_id": quiz_id, "redirect": url_for("web.teacher_dashboard")}), 201
            flash("Quiz created successfully!", "success")
            return redirect(url_for("web.teacher_dashboard"))
        except ValueError as err:
            if request.is_json:
                return jsonify({"error": str(err)}), 400
            flash(str(err), "danger")

    return render_template("teacher/quiz_builder.html", quiz=None, is_edit=False)


@web_bp.route("/teacher/quizzes/<int:quiz_id>/edit", methods=["GET", "POST"])
@require_permission("quiz:edit")
def edit_quiz(quiz_id: int):
    """Google Form visual quiz editor."""
    user = user_repo.get_by_id(session.get("user_id"))
    quiz = quiz_service.get_quiz_by_id(quiz_id)
    if not quiz:
        flash("Quiz not found.", "danger")
        return redirect(url_for("web.teacher_dashboard"))

    if request.method == "POST":
        if request.is_json:
            data = request.get_json() or {}
        else:
            raw_payload = request.form.get("quiz_data")
            data = json.loads(raw_payload) if raw_payload else {}

        try:
            quiz_service.update_quiz(quiz_id, data, user=user)
            if request.is_json:
                return jsonify({"status": "success", "redirect": url_for("web.teacher_dashboard")}), 200
            flash("Quiz updated successfully!", "success")
            return redirect(url_for("web.teacher_dashboard"))
        except (ValueError, PermissionError) as err:
            if request.is_json:
                return jsonify({"error": str(err)}), 400
            flash(str(err), "danger")

    return render_template("teacher/quiz_builder.html", quiz=quiz, is_edit=True)


@web_bp.route("/teacher/quizzes/<int:quiz_id>/delete", methods=["POST"])
@require_permission("quiz:delete")
def delete_quiz(quiz_id: int):
    user = user_repo.get_by_id(session.get("user_id"))
    try:
        quiz_service.delete_quiz(quiz_id, user=user)
        flash("Quiz deleted successfully.", "success")
    except (ValueError, PermissionError) as err:
        flash(str(err), "danger")

    return redirect(url_for("web.teacher_dashboard"))


@web_bp.route("/teacher/quizzes/<int:quiz_id>/responses")
@require_permission("report:view_all")
def quiz_responses(quiz_id: int):
    """Google Form Responses tab (Analytics + Submissions list)."""
    try:
        overview = quiz_service.get_responses_overview(quiz_id)
        return render_template(
            "teacher/quiz_responses.html",
            quiz=overview["quiz"],
            stats=overview["stats"],
            submissions=overview["submissions"],
            question_stats=overview.get("question_stats", [])
        )
    except ValueError as err:
        flash(str(err), "danger")
        return redirect(url_for("web.teacher_dashboard"))


@web_bp.route("/teacher/quizzes/<int:quiz_id>/export-csv")
@require_permission("report:view_all")
def export_quiz_csv(quiz_id: int):
    """Export all student responses and scores for a quiz as CSV."""
    try:
        overview = quiz_service.get_responses_overview(quiz_id)
        quiz = overview["quiz"]
        submissions = overview["submissions"]

        output = io.StringIO()
        writer = csv.writer(output)

        # CSV Header
        writer.writerow([
            "Submission ID",
            "Quiz ID",
            "Quiz Title",
            "Student Username",
            "Total Score",
            "Max Score",
            "Percentage",
            "Result",
            "Teacher Feedback",
            "Submitted At"
        ])

        # Data Rows
        for sub in submissions:
            writer.writerow([
                sub.id,
                quiz.id,
                quiz.title,
                sub.student_username,
                sub.total_score,
                sub.max_score,
                f"{sub.percentage}%",
                "PASSED" if sub.passed else "FAILED",
                sub.teacher_feedback or "",
                sub.submitted_at
            ])

        csv_content = output.getvalue()
        output.close()

        safe_title = "".join(c if c.isalnum() else "_" for c in quiz.title).strip("_")
        filename = f"quiz_{quiz.id}_{safe_title}_responses.csv"

        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as err:
        flash(str(err), "danger")
        return redirect(url_for("web.teacher_dashboard"))


@web_bp.route("/teacher/submissions/<int:submission_id>/grade", methods=["GET", "POST"])
@require_permission("quiz:score")
def grade_submission(submission_id: int):
    submission = grading_service.get_submission_detail(submission_id)
    if not submission:
        flash("Submission not found.", "danger")
        return redirect(url_for("web.teacher_dashboard"))

    if request.method == "POST":
        try:
            new_score = float(request.form.get("total_score", submission.total_score))
            feedback = request.form.get("teacher_feedback", "").strip()
            grading_service.adjust_score_and_feedback(submission_id, new_score, feedback)
            flash("Submission score and feedback updated successfully.", "success")
            return redirect(url_for("web.quiz_responses", quiz_id=submission.quiz_id))
        except ValueError as err:
            flash(str(err), "danger")

    return render_template("teacher/grade_submission.html", submission=submission)


# ==========================================
# Admin Views & User Management
# ==========================================

@web_bp.route("/admin/dashboard")
@require_permission("user:manage")
def admin_dashboard():
    users = auth_service.list_all_users()
    roles = auth_service.get_available_roles()
    quizzes = quiz_service.list_available_quizzes()
    all_submissions = grading_service.list_all_submissions()
    audit_logs = auth_service.get_audit_logs(limit=25)

    return render_template(
        "admin/dashboard.html",
        users=users,
        roles=roles,
        quizzes=quizzes,
        submissions=all_submissions,
        audit_logs=audit_logs
    )


@web_bp.route("/admin/users/create", methods=["POST"])
@require_permission("user:manage")
def admin_create_user():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    role_name = request.form.get("role_name", "Student").strip()

    try:
        auth_service.register_user(username, email, password, role_name=role_name)
        flash(f"User '{username}' created successfully as {role_name}.", "success")
    except ValueError as err:
        flash(str(err), "danger")

    return redirect(url_for("web.admin_dashboard"))


@web_bp.route("/admin/users/<int:user_id>/role", methods=["POST"])
@require_permission("user:manage")
def admin_update_user_role(user_id: int):
    new_role = request.form.get("role_name")
    try:
        auth_service.update_user_role(user_id, new_role)
        flash("User role updated successfully.", "success")
    except Exception as err:
        flash(str(err), "danger")

    return redirect(url_for("web.admin_dashboard"))


@web_bp.route("/admin/users/<int:user_id>/toggle", methods=["POST"])
@require_permission("user:manage")
def admin_toggle_user_status(user_id: int):
    if user_id == session.get("user_id"):
        flash("You cannot deactivate your own administrative account.", "warning")
        return redirect(url_for("web.admin_dashboard"))

    user = user_repo.get_by_id(user_id)
    if user:
        new_status = not user.is_active
        auth_service.toggle_user_status(user_id, new_status)
        flash(f"User '{user.username}' status set to {'Active' if new_status else 'Inactive'}.", "info")

    return redirect(url_for("web.admin_dashboard"))


@web_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@require_permission("user:manage")
def admin_delete_user(user_id: int):
    if user_id == session.get("user_id"):
        flash("You cannot delete your own administrative account.", "danger")
        return redirect(url_for("web.admin_dashboard"))

    try:
        auth_service.delete_user(user_id)
        flash("User deleted successfully.", "success")
    except Exception as err:
        flash(str(err), "danger")

    return redirect(url_for("web.admin_dashboard"))