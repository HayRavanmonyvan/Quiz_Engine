# app/models/quiz.py
from dataclasses import dataclass, field
from typing import List, Optional
from app.models.question import Question

@dataclass
class Quiz:
    id: Optional[int]
    title: str
    description: str
    created_by: int
    pass_percentage: float = 50.0
    time_limit_minutes: int = 0
    questions: List[Question] = field(default_factory=list)
    creator_username: Optional[str] = None
    created_at: Optional[str] = None

    @property
    def max_possible_score(self) -> int:
        return sum(q.points for q in self.questions)

    @property
    def question_count(self) -> int:
        return len(self.questions)