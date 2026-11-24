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
    # A lone value equal to the denominator could be the denominator itself.
    # Refuse that ambiguous case; a full "700/700" ratio is parsed above.
    if expected_max >= min_max and 0 <= current < expected_max:
        parsed.append((current, expected_max, f"{raw} (ранее подтверждён максимум {expected_max})"))
    return parsed


def confirm_income_pair(
    current_a: int | None,
    maximum_a: int | None,
    current_b: int | None,
    maximum_b: int | None,
) -> tuple[int | None, int | None, str]:
    """Reconcile two adjacent income reads while allowing tiny passive increments.

    The game can add a few income points between screenshots even before the
    hammer loop begins. Accept only the same confirmed target and a small
    difference; return the larger reading so the worker never underestimates
    progress. Large changes and target mismatches remain unconfirmed.
    """
    if (
        current_a is None or current_b is None
        or maximum_a is None or maximum_b is None
        or maximum_a != maximum_b
        or maximum_a <= 0
    ):
        return None, None, "доход не подтверждён: отсутствует значение или различается целевой лимит"

    tolerance = max(6, min(25, round(maximum_a * 0.01)))
    difference = abs(current_b - current_a)
    if difference > tolerance:
        return (
            None,
            None,
            f"доход скачет сильнее допустимого: {current_a}/{maximum_a} → "
            f"{current_b}/{maximum_b} (допуск {tolerance})",
        )

    selected = max(current_a, current_b)
    if difference:
        return (
            selected,
            maximum_a,
            f"{current_a} → {current_b}; принято {selected}/{maximum_a} "
            f"(небольшое изменение за время сканирования, допуск {tolerance})",
        )
    return selected, maximum_a, f"{selected}/{maximum_a}; два снимка совпали"


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



def visual_change_ratio(before, after, region, *, pixel_delta: int = 30) -> float:
    """Return the fraction of pixels changed meaningfully inside a client-area region.

    Small cursor/particle changes should not be sufficient to confirm a reward
    transition. The before/after images must be full client-area screenshots.
    """
    from PIL import ImageChops

    if before.size != after.size:
        return 0.0
    left, top, right, bottom = (int(value) for value in region)
    left = max(0, min(before.width, left))
    right = max(left, min(before.width, right))
    top = max(0, min(before.height, top))
    bottom = max(top, min(before.height, bottom))
    if right <= left or bottom <= top:
        return 0.0

    before_crop = before.crop((left, top, right, bottom)).convert("RGB")
    after_crop = after.crop((left, top, right, bottom)).convert("RGB")
    difference = ImageChops.difference(before_crop, after_crop).convert("L")
    changed = sum(difference.histogram()[pixel_delta + 1:])
    total = (right - left) * (bottom - top)
    return changed / total if total else 0.0
