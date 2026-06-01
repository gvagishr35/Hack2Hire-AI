def difficulty_for_index(index: int, total: int) -> str:
    """Initial difficulty curve: early questions easy, later questions harder."""
    if total <= 1:
        return "easy"
    ratio = index / max(total - 1, 1)
    if ratio < 0.4:
        return "easy"
    if ratio < 0.8:
        return "medium"
    return "hard"
