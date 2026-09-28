# app/services/grading_service.py
from typing import Dict, List, Optional
from app.models.submission import Submission, SubmissionAnswer
from app.repositories.quiz_repository import QuizRepository
from app.repositories.submission_repository import SubmissionRepository

class GradingService:
    def __init__(self, quiz_repo: QuizRepository, submission_repo: SubmissionRepository):
        self.quiz_repo = quiz_repo
        self.submission_repo = submission_repo

    def evaluate_and_record(self, quiz_id: int, student_id: int, answers_map: Dict[int, int]) -> Submission:
        """
        Evaluates submitted student answers against the quiz's answer key,
        computes total score, passing status, and commits the submission record.
        """
        quiz = self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise ValueError(f"Quiz with ID {quiz_id} does not exist.")
        if not quiz.questions:
            raise ValueError("Cannot submit an empty quiz.")

        earned_points = 0.0
        max_points = float(quiz.max_possible_score)
        answer_records = []

        for question in quiz.questions:
            selected_opt_id = answers_map.get(question.id)
            is_correct = False

            # Find matching correct option
            correct_option = next((opt for opt in question.options if opt.is_correct), None)
            if correct_option and selected_opt_id == correct_option.id:
                is_correct = True
                earned_points += float(question.points)

            answer_records.append(
                SubmissionAnswer(
                    question_id=question.id,
                    selected_option_id=selected_opt_id,
                    is_correct=is_correct
                )
            )

        calculated_pct = (earned_points / max_points * 100.0) if max_points > 0 else 0.0
        has_passed = calculated_pct >= quiz.pass_percentage

        submission = Submission(
            id=None,
            quiz_id=quiz_id,
            student_id=student_id,
            total_score=round(earned_points, 2),
            max_score=round(max_points, 2),
            passed=has_passed,
            answers=answer_records
        )

        submission_id = self.submission_repo.save(submission)
        submission.id = submission_id
        return submission

    def get_submission_detail(self, submission_id: int) -> Optional[Submission]:
        return self.submission_repo.get_by_id(submission_id)

    def list_student_submissions(self, student_id: int) -> List[Submission]:
        return self.submission_repo.list_by_student(student_id)

    def list_all_submissions(self) -> List[Submission]:
        return self.submission_repo.list_all()

    def adjust_score_and_feedback(self, submission_id: int, new_score: float, feedback: str) -> bool:
        """Teacher/Admin manual score adjustment and feedback comments."""
        if new_score < 0:
            raise ValueError("Score cannot be negative.")
        return self.submission_repo.update_score_and_feedback(submission_id, new_score, feedback)