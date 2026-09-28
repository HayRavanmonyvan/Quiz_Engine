# app/routes/quiz_bp.py
from flask import Blueprint, jsonify, request, session
from app.routes.security import require_permission
from app.repositories.user_repository import UserRepository
from app.repositories.quiz_repository import QuizRepository
from app.repositories.submission_repository import SubmissionRepository
from app.services.quiz_service import QuizService
from app.services.grading_service import GradingService

quiz_bp = Blueprint("quiz", __name__, url_prefix="/api/quizzes")

user_repo = UserRepository()
quiz_repo = QuizRepository()
sub_repo = SubmissionRepository()
quiz_service = QuizService(quiz_repo, sub_repo)
grading_service = GradingService(quiz_repo, sub_repo)

# 1. View Quiz: Accessible by Students, Teachers, and Admins (quiz:view)
@quiz_bp.route("/<int:quiz_id>", methods=["GET"])
@require_permission("quiz:view")
def get_quiz(quiz_id: int):
    payload = quiz_service.get_public_quiz_view(quiz_id)
    if not payload:
        return jsonify({"error": "Quiz not found."}), 404
    return jsonify(payload), 200

# 2. Submit Quiz: Accessible by Students and Admins (quiz:submit)
@quiz_bp.route("/<int:quiz_id>/submit", methods=["POST"])
@require_permission("quiz:submit")
def submit_quiz(quiz_id: int):
    student_id = session["user_id"]
    data = request.get_json() or {}
    answers = {int(k): int(v) for k, v in data.get("answers", {}).items()}

    try:
        result = grading_service.evaluate_and_record(quiz_id, student_id, answers)
        return jsonify({
            "submission_id": result.id,
            "total_score": result.total_score,
            "max_score": result.max_score,
            "passed": result.passed
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

# 3. Create Quiz: Teachers and Admins (quiz:create)
@quiz_bp.route("", methods=["POST"])
@require_permission("quiz:create")
def create_quiz():
    creator_id = session["user_id"]
    data = request.get_json() or {}
    try:
        quiz_id = quiz_service.create_quiz(data, creator_id=creator_id)
        return jsonify({"message": "Quiz created successfully.", "quiz_id": quiz_id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

# 4. Edit Quiz: Teachers and Admins (quiz:edit)
@quiz_bp.route("/<int:quiz_id>", methods=["PUT"])
@require_permission("quiz:edit")
def update_quiz(quiz_id: int):
    user = user_repo.get_by_id(session["user_id"])
    data = request.get_json() or {}
    try:
        quiz_service.update_quiz(quiz_id, data, user=user)
        return jsonify({"message": "Quiz updated successfully."}), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 400

# 5. Delete Quiz: Teachers and Admins (quiz:delete)
@quiz_bp.route("/<int:quiz_id>", methods=["DELETE"])
@require_permission("quiz:delete")
def delete_quiz(quiz_id: int):
    user = user_repo.get_by_id(session["user_id"])
    try:
        quiz_service.delete_quiz(quiz_id, user=user)
        return jsonify({"message": "Quiz deleted successfully."}), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 400

# 6. Responses & Analytics: Teachers and Admins (report:view_all)
@quiz_bp.route("/<int:quiz_id>/responses", methods=["GET"])
@require_permission("report:view_all")
def view_quiz_responses(quiz_id: int):
    try:
        summary = quiz_service.get_responses_overview(quiz_id)
        return jsonify({
            "quiz_id": quiz_id,
            "title": summary["quiz"].title,
            "stats": summary["stats"],
            "submissions_count": len(summary["submissions"])
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# 7. Score / Adjust Submission: Teachers and Admins (quiz:score)
@quiz_bp.route("/submissions/<int:submission_id>/grade", methods=["POST"])
@require_permission("quiz:score")
def grade_submission(submission_id: int):
    data = request.get_json() or {}
    new_score = float(data.get("score", 0.0))
    feedback = data.get("feedback", "").strip()
    try:
        grading_service.adjust_score_and_feedback(submission_id, new_score, feedback)
        return jsonify({"message": "Submission score and feedback updated."}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400