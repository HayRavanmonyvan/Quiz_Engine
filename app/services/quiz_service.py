# app/services/quiz_service.py
from typing import List, Optional, Dict, Any
from app.models.quiz import Quiz
from app.models.question import Question, Option
from app.models.user import User
from app.repositories.quiz_repository import QuizRepository
from app.repositories.submission_repository import SubmissionRepository

class QuizService:
    def __init__(self, quiz_repo: QuizRepository, sub_repo: Optional[SubmissionRepository] = None):
        self.quiz_repo = quiz_repo
        self.sub_repo = sub_repo or SubmissionRepository()

    def get_public_quiz_view(self, quiz_id: int) -> Optional[dict]:
        """Fetch quiz details with `is_correct` answers redacted for student test-taking."""
        quiz = self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            return None

        return {
            "id": quiz.id,
            "title": quiz.title,
            "description": quiz.description,
            "pass_percentage": quiz.pass_percentage,
            "time_limit_minutes": getattr(quiz, "time_limit_minutes", 0) or 0,
            "max_possible_score": quiz.max_possible_score,
            "questions": [
                {
                    "id": q.id,
                    "prompt": q.prompt,
                    "points": q.points,
                    "options": [{"id": opt.id, "text": opt.option_text} for opt in q.options]
                }
                for q in quiz.questions
            ]
        }

    def get_quiz_by_id(self, quiz_id: int) -> Optional[Quiz]:
        return self.quiz_repo.get_by_id(quiz_id)

    def list_available_quizzes(self) -> List[Quiz]:
        return self.quiz_repo.list_all()

    def list_quizzes_by_teacher(self, teacher_id: int) -> List[Quiz]:
        return self.quiz_repo.list_by_creator(teacher_id)

    def parse_quiz_form_data(self, form_data: Dict[str, Any], creator_id: int, quiz_id: Optional[int] = None) -> Quiz:
        """
        Parses Google Form-style dynamic builder payload into OOP Quiz, Question, and Option domain objects.
        Validates domain rules (non-empty prompts, >= 2 options, exactly 1 correct answer per question).
        """
        title = form_data.get("title", "").strip()
        description = form_data.get("description", "").strip()
        pass_percentage = float(form_data.get("pass_percentage", 50.0))
        try:
            time_limit_minutes = int(form_data.get("time_limit_minutes", 0) or 0)
            if time_limit_minutes < 0:
                time_limit_minutes = 0
        except (ValueError, TypeError):
            time_limit_minutes = 0

        if not title:
            raise ValueError("Quiz title is required.")

        questions_list: List[Question] = []
        raw_questions = form_data.get("questions", [])

        if not raw_questions:
            raise ValueError("Quiz must contain at least one question.")

        for q_idx, q_data in enumerate(raw_questions):
            prompt = q_data.get("prompt", "").strip()
            points = int(q_data.get("points", 1))
            if points < 1:
                points = 1

            options_list: List[Option] = []
            raw_options = q_data.get("options", [])

            for opt_idx, opt_data in enumerate(raw_options):
                opt_text = opt_data.get("text", "").strip()
                if not opt_text:
                    continue
                is_correct = bool(opt_data.get("is_correct", False))
                options_list.append(Option(id=None, question_id=None, option_text=opt_text, is_correct=is_correct))

            question = Question(id=None, quiz_id=quiz_id, prompt=prompt, points=points, options=options_list)
            
            if not question.validate_structure():
                raise ValueError(
                    f"Question {q_idx + 1} is invalid: must have a prompt, at least 2 options, and exactly 1 correct answer selected."
                )

            questions_list.append(question)

        return Quiz(
            id=quiz_id,
            title=title,
            description=description,
            created_by=creator_id,
            pass_percentage=pass_percentage,
            time_limit_minutes=time_limit_minutes,
            questions=questions_list
        )

    def create_quiz(self, form_data: Dict[str, Any], creator_id: int) -> int:
        quiz = self.parse_quiz_form_data(form_data, creator_id=creator_id)
        return self.quiz_repo.create(quiz)

    def update_quiz(self, quiz_id: int, form_data: Dict[str, Any], user: User) -> bool:
        existing = self.quiz_repo.get_by_id(quiz_id)
        if not existing:
            raise ValueError("Quiz not found.")

        # Admin can edit any quiz; Teachers can edit their own quizzes
        if not (user.is_admin or existing.created_by == user.id):
            raise PermissionError("You are not authorized to edit this quiz.")

        quiz = self.parse_quiz_form_data(form_data, creator_id=existing.created_by, quiz_id=quiz_id)
        return self.quiz_repo.update(quiz)

    def delete_quiz(self, quiz_id: int, user: User) -> bool:
        existing = self.quiz_repo.get_by_id(quiz_id)
        if not existing:
            raise ValueError("Quiz not found.")

        if not (user.is_admin or existing.created_by == user.id):
            raise PermissionError("You are not authorized to delete this quiz.")

        return self.quiz_repo.delete(quiz_id)

    def get_responses_overview(self, quiz_id: int) -> Dict[str, Any]:
        quiz = self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise ValueError("Quiz not found.")

        stats = self.quiz_repo.get_stats(quiz_id)
        submissions = self.sub_repo.list_by_quiz(quiz_id)
        question_stats = self.quiz_repo.get_question_breakdown(quiz_id)

        return {
            "quiz": quiz,
            "stats": stats,
            "submissions": submissions,
            "question_stats": question_stats
        }