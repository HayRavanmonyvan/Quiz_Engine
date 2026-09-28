# app/models/submission.py
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class SubmissionAnswer:
    question_id: int
    selected_option_id: Optional[int]
    is_correct: bool
    question_prompt: Optional[str] = None
    selected_option_text: Optional[str] = None
    correct_option_text: Optional[str] = None
    points_awarded: float = 0.0

@dataclass
class Submission:
    id: Optional[int]
    quiz_id: int
    student_id: int
    total_score: float
    max_score: float
    passed: bool
    answers: List[SubmissionAnswer] = field(default_factory=list)
    teacher_feedback: Optional[str] = None
    student_username: Optional[str] = None
    quiz_title: Optional[str] = None
    submitted_at: Optional[str] = None

    @property
    def percentage(self) -> float:
        if self.max_score > 0:
            return round((self.total_score / self.max_score) * 100.0, 1)
        return 0.0