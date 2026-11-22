"""Pure OCR value-selection helpers; intentionally independent of the GUI."""

def select_ratio_candidate(
    parsed: list[tuple[int, int, str]],
) -> tuple[int | None, int | None, str]:
    """Select one OCR ratio from a single screenshot.

    A single complete ratio is provisional, not final: _scan_game_state()
    independently captures the game twice and requires exact agreement.
    Multiple conflicting complete ratios in one screenshot remain ambiguous.
    """
    if not parsed:
        return None, None, ""

    denominator_votes: dict[int, int] = {}
    for _, maximum, _ in parsed:
        denominator_votes[maximum] = denominator_votes.get(maximum, 0) + 1

    best_max, votes = max(denominator_votes.items(), key=lambda item: item[1])
    confirmed = [item for item in parsed if item[1] == best_max]

    if votes < 2:
        # A lone full match such as 292/700 is acceptable as one half of the
        # outer two-screenshot confirmation. Never accept a lone fragment.
        if len(parsed) == 1:
            current, maximum, raw = parsed[0]
            return current, maximum, f"{raw} (предварительно; жду совпадение второго снимка)"

        raw_values = "; ".join(item[2] for item in parsed)
        return None, None, f"{raw_values} (противоречивые OCR-варианты)"

    # When one denominator wins, keep the largest matching numerator to avoid
    # losing leading digits if a weaker pass reads 70 instead of 1270.
    current, maximum, raw = max(confirmed, key=lambda item: item[0])
    return current, maximum, raw
