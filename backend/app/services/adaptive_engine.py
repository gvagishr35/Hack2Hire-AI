"""Adaptive difficulty rules for interview progression."""

from app.core.settings import settings

DIFFICULTY_ORDER = ["easy", "medium", "hard"]


def next_difficulty(current: str, answer_score: float) -> str:
    """Adjust difficulty for the next question based on answer performance."""
    idx = DIFFICULTY_ORDER.index(current) if current in DIFFICULTY_ORDER else 1

    if answer_score >= 80 and idx < 2:
        return DIFFICULTY_ORDER[idx + 1]
    if answer_score < 45 and idx > 0:
        return DIFFICULTY_ORDER[idx - 1]
    return current


def should_terminate_early(scored_answers: list[float]) -> tuple[bool, str | None]:
    """Determine if interview should end early due to poor performance."""
    if len(scored_answers) < settings.interview_early_termination_min_answers:
        return False, None

    average = sum(scored_answers) / len(scored_answers)
    if average < settings.interview_early_termination_avg:
        return True, (
            f"Interview ended early: average answer score ({average:.0f}%) is below "
            f"the minimum threshold ({settings.interview_early_termination_avg:.0f}%)."
        )

    if scored_answers[-1] < settings.interview_single_answer_fail_threshold:
        return True, (
            f"Interview ended early: last answer scored {scored_answers[-1]:.0f}%, "
            f"indicating insufficient preparation for this role."
        )

    return False, None
