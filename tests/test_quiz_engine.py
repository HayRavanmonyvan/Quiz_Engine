import unittest
from app.models.question import Question, Option
from app.models.quiz import Quiz
from app.models.user import User
from app.models.submission import Submission
from app.services.grading_service import GradingService

class MockQuizRepository:
    def __init__(self, quiz_data=None):
        self.quiz_data = quiz_data or {}

    def get_by_id(self, quiz_id: int):
        return self.quiz_data.get(quiz_id)

class MockSubmissionRepository:
    def __init__(self):
        self.saved_submissions = []

    def save(self, submission: Submission):
        self.saved_submissions.append(submission)
        return len(self.saved_submissions)

class QuizEngineTestSuite(unittest.TestCase):
    def setUp(self):
        self.opt1 = Option(id=101, question_id=1, option_text="Encapsulation", is_correct=True)
        self.opt2 = Option(id=102, question_id=1, option_text="Global Variable", is_correct=False)
        self.q1 = Question(id=1, quiz_id=10, prompt="Which is an OOP pillar?", points=2, options=[self.opt1, self.opt2])

        self.opt3 = Option(id=103, question_id=2, option_text="1991", is_correct=True)
        self.opt4 = Option(id=104, question_id=2, option_text="2020", is_correct=False)
        self.q2 = Question(id=2, quiz_id=10, prompt="When was Python released?", points=3, options=[self.opt3, self.opt4])

        self.quiz = Quiz(id=10, title="Python OOP Quiz", description="Basic OOP", created_by=1, pass_percentage=60.0, questions=[self.q1, self.q2])

        self.mock_quiz_repo = MockQuizRepository({10: self.quiz})
        self.mock_sub_repo = MockSubmissionRepository()
        self.service = GradingService(self.mock_quiz_repo, self.mock_sub_repo)

    # 1. Domain Validation Tests
    def test_question_validation_success(self):
        self.assertTrue(self.q1.validate_structure())

    def test_question_validation_fails_no_options(self):
        empty_q = Question(id=3, quiz_id=10, prompt="Invalid?", points=1, options=[])
        self.assertFalse(empty_q.validate_structure())

    def test_question_validation_fails_multiple_correct_answers(self):
        o1 = Option(id=1, question_id=4, option_text="A", is_correct=True)
        o2 = Option(id=2, question_id=4, option_text="B", is_correct=True)
        invalid_q = Question(id=4, quiz_id=10, prompt="Multi correct?", points=1, options=[o1, o2])
        self.assertFalse(invalid_q.validate_structure())

    def test_quiz_max_possible_score_calculation(self):
        self.assertEqual(self.quiz.max_possible_score, 5)

    # 2. Grading Business Rule Tests
    def test_grading_perfect_score_passed(self):
        result = self.service.evaluate_and_record(10, 1, {1: 101, 2: 103})
        self.assertEqual(result.total_score, 5.0)
        self.assertTrue(result.passed)

    def test_grading_zero_score_failed(self):
        result = self.service.evaluate_and_record(10, 1, {1: 102, 2: 104})
        self.assertEqual(result.total_score, 0.0)
        self.assertFalse(result.passed)

    def test_grading_partial_score_threshold_fails(self):
        # 2 points out of 5 = 40%, passing threshold is 60%
        result = self.service.evaluate_and_record(10, 1, {1: 101, 2: 104})
        self.assertEqual(result.total_score, 2.0)
        self.assertFalse(result.passed)

    def test_grading_partial_score_threshold_passes(self):
        # 3 points out of 5 = 60%, passing threshold is 60%
        result = self.service.evaluate_and_record(10, 1, {1: 102, 2: 103})
        self.assertEqual(result.total_score, 3.0)
        self.assertTrue(result.passed)

    def test_grading_missing_answers_default_incorrect(self):
        result = self.service.evaluate_and_record(10, 1, {})
        self.assertEqual(result.total_score, 0.0)
        self.assertEqual(len(result.answers), 2)
        self.assertFalse(result.answers[0].is_correct)

    def test_grading_invalid_quiz_raises_error(self):
        with self.assertRaises(ValueError):
            self.service.evaluate_and_record(999, 1, {})

    def test_submission_persistence_record_count(self):
        self.service.evaluate_and_record(10, 1, {1: 101, 2: 103})
        self.assertEqual(len(self.mock_sub_repo.saved_submissions), 1)

if __name__ == "__main__":
    unittest.main()