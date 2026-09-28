# app/models/question.py
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class QuestionOption:
    """Represents an answer choice for a quiz question."""
    id: Optional[int]
    question_id: Optional[int]
    option_text: str
    is_correct: bool = False

# Alias for backward compatibility with existing tests and modules
Option = QuestionOption

@dataclass
class Question:
    """Represents a question entity with validation rules."""
    id: Optional[int]
    quiz_id: Optional[int]
    prompt: str
    points: int = 1
    order_num: int = 0
    options: List[QuestionOption] = field(default_factory=list)

    def validate_structure(self) -> bool:
        """
        Validates structural integrity:
        1. Prompt must not be empty.
        2. Must have at least 2 options.
        3. Must have exactly one correct option.
        """
        if not self.prompt or not self.prompt.strip():
            return False
        if len(self.options) < 2:
            return False
        correct_count = sum(1 for opt in self.options if opt.is_correct)
        return correct_count == 1