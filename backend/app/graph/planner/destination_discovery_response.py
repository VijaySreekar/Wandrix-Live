from app.schemas.conversation import ConversationBoardAction
from app.schemas.trip_conversation import (
    DestinationSuggestionCard,
    TripConversationState,
)


def build_destination_discovery_response(
    *,
    conversation: TripConversationState,
    greeting_name: str | None,
    action: ConversationBoardAction | None,
) -> str:
    cards = conversation.suggestion_board.cards[:6]
    greeting_prefix = f"Hey {greeting_name}. " if greeting_name else ""
    leading_card = next(
        (card for card in cards if card.selection_status == "leading"),
        None,
    )
    if action and action.type == "select_destination_suggestion" and leading_card:
        destination = _destination_label(leading_card)
        fit_line = leading_card.recommendation_note or leading_card.short_reason
        return (
            f"{greeting_prefix}Nice, I’d make **{destination}** the front-runner for now.\n\n"
            f"**Why it fits**\n{fit_line}\n\n"
            "**Before I lock it**\nWant me to lock it as the destination, or should we keep comparing it with the others?"
        )

    cleaned_source_context = conversation.suggestion_board.source_context
    source_line = (
        f"{cleaned_source_context.rstrip('.!?')}. "
        if cleaned_source_context
        else ""
    )
    correction_line = (
        "If you are not actually leaving from around there, tell me your real departure point and I will switch the shortlist. "
        if conversation.suggestion_board.source_context
        else ""
    )
    count_word = _number_word(len(cards))
    turn_kind = conversation.suggestion_board.discovery_turn_kind
    if turn_kind == "pivot":
        opening = f"{greeting_prefix}Got it. I’ve shifted the shortlist around that new direction."
    elif turn_kind in {"refine", "narrow"}:
        opening = f"{greeting_prefix}That helps. I’ve tightened the shortlist around the new preference."
    elif turn_kind == "expand":
        opening = f"{greeting_prefix}I’ve widened the options while keeping the original brief in view."
    elif turn_kind == "compare":
        opening = f"{greeting_prefix}Here’s the clean comparison I’d use."
    else:
        opening = f"{greeting_prefix}I’d start with these {count_word} destination directions."

    summary_line = (
        conversation.suggestion_board.comparison_summary.strip()
        if conversation.suggestion_board.comparison_summary
        else ""
    )
    quick_read = _build_quick_read(cards, summary_line)
    comparison_lines = [
        _format_destination_row(card)
        for card in cards
    ]
    comparison_block = "\n".join(comparison_lines)
    lean_line = (
        conversation.suggestion_board.leading_recommendation.strip()
        if conversation.suggestion_board.leading_recommendation
        else _fallback_leading_recommendation(cards)
    )
    correction_block = (
        f"\n\n**Small note**\n{correction_line.strip()}"
        if correction_line
        else ""
    )
    context_block = f"**Context**\n{source_line.strip()}\n\n" if source_line else ""
    quick_read_block = f"{quick_read}\n\n" if quick_read else ""

    return (
        f"{opening}\n\n"
        f"{context_block}"
        f"{quick_read_block}"
        f"{comparison_block}\n\n"
        f"My lean: {lean_line}\n\n"
        "I’ve updated the cards on the right. Tap one to make it the front-runner, or tell me the taste you want me to optimize for."
        f"{correction_block}"
    )


def _format_destination_row(card: DestinationSuggestionCard) -> str:
    strength = _format_strength(
        card.best_for or card.fit_label or card.short_reason
    )
    tradeoff = card.tradeoffs[0] if card.tradeoffs else None
    verdict = card.recommendation_note

    line = f"- **{_destination_label(card)}**: {strength}."
    if tradeoff:
        line += f" Worth knowing: {_compact_sentence(tradeoff)}."
    if verdict:
        line += f" {_compact_sentence(verdict)}."
    return line


def _fallback_leading_recommendation(cards: list[DestinationSuggestionCard]) -> str:
    if not cards:
        return "I’d keep comparing before locking anything."
    first = cards[0]
    return (
        f"{_destination_label(first)} looks strongest for now because "
        f"{(first.recommendation_note or first.short_reason).rstrip('.')}."
    )


def _destination_label(card: DestinationSuggestionCard) -> str:
    return ", ".join(
        value
        for value in [card.destination_name, card.country_or_region]
        if value
    )


def _compact_cell(value: str) -> str:
    normalized = " ".join(value.strip().split())
    return normalized[:117] + "..." if len(normalized) > 120 else normalized


def _compact_sentence(value: str) -> str:
    return _compact_cell(value).rstrip(".")


def _format_strength(value: str | None) -> str:
    compacted = _compact_cell(value or "a strong fit for the brief").rstrip(".")
    lowered = compacted.lower()
    if lowered.startswith(("best for", "strongest for", "good for", "ideal for")):
        return compacted[:1].lower() + compacted[1:]
    return f"best for {compacted[:1].lower() + compacted[1:]}"


def _build_quick_read(
    cards: list[DestinationSuggestionCard],
    summary_line: str | None,
) -> str | None:
    if summary_line and not _summary_sounds_internal(summary_line):
        return summary_line
    if not cards:
        return None

    lead = cards[0]
    lead_strength = _compact_cell(
        lead.best_for or lead.fit_label or lead.short_reason
    ).rstrip(".")
    comparison_cards = cards[1:3]
    if not comparison_cards:
        return (
            f"{lead.destination_name} is the main option I’d focus on for "
            f"{lead_strength}."
        )

    comparisons = [
        f"{card.destination_name} for {_compact_cell(card.best_for or card.fit_label or card.short_reason).rstrip('.')}"
        for card in comparison_cards
    ]
    if len(comparisons) == 1:
        comparison_text = comparisons[0]
    else:
        comparison_text = f"{comparisons[0]}, and {comparisons[1]}"

    return (
        f"{lead.destination_name} brings {lead_strength}. "
        f"I’d mainly weigh it against {comparison_text}."
    )


def _summary_sounds_internal(value: str) -> bool:
    lowered = value.lower()
    return any(
        marker in lowered
        for marker in [
            "the user",
            "should be compared against",
            "compare against",
            "new direction",
            "visible shortlist",
        ]
    )


def _number_word(value: int) -> str:
    words = {
        2: "two",
        3: "three",
        4: "four",
        5: "five",
        6: "six",
    }
    return words.get(value, str(value))
