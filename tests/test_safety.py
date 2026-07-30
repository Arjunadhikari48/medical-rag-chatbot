from app.services.safety import has_emergency_language


def test_emergency_phrase_is_detected() -> None:
    assert has_emergency_language("I have chest pain and cannot breathe") is True


def test_regular_question_is_not_emergency() -> None:
    assert has_emergency_language("What is vitamin D?") is False
