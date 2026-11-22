"""Pure OCR value-selection helpers; intentionally independent of the GUI."""

import re


def parse_ratio_text(
    raw: str,
    *,
    expected_max: int | None = None,
    min_max: int = 1,
) -> list[tuple[int, int, str]]:
    """Parse full ratios, or a lone numerator when its denominator is trusted.

    A numerator-only reading is allowed only after an independent scan has
    established the static maximum for the current event. Multiple numbers
    without a slash remain ambiguous and are never promoted to a ratio.
    """
    compact = re.sub(r"[^0-9/]", "", raw)
    parsed: list[tuple[int, int, str]] = []

    for match in re.finditer(r"(\d{1,6})/(\d{1,6})", compact):
        current, maximum = int(match.group(1)), int(match.group(2))
        if maximum < min_max or maximum <= 0 or current > maximum:
            continue
        if expected_max is not None and maximum != expected_max:
            continue
        parsed.append((current, maximum, raw))

    if parsed or expected_max is None:
        return parsed

    digit_tokens = re.findall(r"\d{1,6}", raw)
    if len(digit_tokens) != 1:
        return parsed

    current = int(digit_tokens[0])
    if 0 <= current <= expected_max:
        parsed.append((current, expected_max, f"{raw} (ранее подтверждён максимум {expected_max})"))
    return parsed


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
