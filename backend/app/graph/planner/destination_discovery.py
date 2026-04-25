from app.graph.planner.turn_models import (
    ConversationOptionCandidate,
    DestinationSuggestionCandidate,
    TripTurnUpdate,
)
from app.schemas.conversation import ConversationBoardAction
from app.schemas.trip_conversation import (
    DestinationSuggestionCard,
    TripConversationState,
    TripSuggestionBoardState,
)
from app.schemas.trip_planning import TripConfiguration
from app.utils.destination_images import get_destination_card_image


def build_destination_mentioned_options(
    suggestions: list[DestinationSuggestionCandidate],
) -> list[ConversationOptionCandidate]:
    return [
        ConversationOptionCandidate(
            kind="destination",
            value=f"{suggestion.destination_name}, {suggestion.country_or_region}",
        )
        for suggestion in suggestions
    ]


def resolve_destination_cards(
    *,
    current: TripConversationState,
    current_board: TripSuggestionBoardState,
    llm_suggestions: list[DestinationSuggestionCandidate],
    action: ConversationBoardAction | None,
) -> list[DestinationSuggestionCard]:
    if action and action.type == "own_choice":
        return []

    if llm_suggestions:
        cards = [
            DestinationSuggestionCard(
                id=suggestion.id,
                destination_name=suggestion.destination_name,
                country_or_region=suggestion.country_or_region,
                image_url=get_destination_card_image(
                    suggestion.destination_name,
                    country_or_region=suggestion.country_or_region,
                    provided_image_url=suggestion.image_url,
                ),
                short_reason=suggestion.short_reason,
                practicality_label=suggestion.practicality_label,
                fit_label=suggestion.fit_label,
                best_for=suggestion.best_for,
                tradeoffs=suggestion.tradeoffs,
                recommendation_note=suggestion.recommendation_note,
                change_note=suggestion.change_note,
                selection_status="suggested",
            )
            for suggestion in llm_suggestions
        ]
        cards = _filter_rejected_destination_cards(cards, current)
    else:
        cards = current_board.cards

    if not cards:
        return []

    if action and action.type in {
        "select_destination_suggestion",
        "confirm_destination_suggestion",
    }:
        updated_cards: list[DestinationSuggestionCard] = []
        for card in cards:
            is_selected = (
                action.suggestion_id == card.id
                or (
                    action.destination_name
                    and card.destination_name.lower() == action.destination_name.lower()
                )
            )
            updated_cards.append(
                card.model_copy(
                    update={
                        "selection_status": (
                            "confirmed"
                            if action.type == "confirm_destination_suggestion"
                            and is_selected
                            else "leading"
                            if is_selected
                            else "suggested"
                        )
                    }
                )
            )
        return updated_cards

    return cards


def should_show_destination_suggestions(
    *,
    configuration: TripConfiguration,
    llm_update: TripTurnUpdate,
    action: ConversationBoardAction | None,
    next_cards: list[DestinationSuggestionCard],
) -> bool:
    if configuration.to_location:
        return False
    if action and action.type in {"own_choice", "confirm_destination_suggestion"}:
        return False
    if llm_update.to_location:
        return False
    return bool(next_cards)


def resolve_unconfirmed_destination_options(
    *,
    current: TripConversationState,
    llm_update: TripTurnUpdate,
) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    rejected_keys = {
        key
        for option in current.memory.rejected_options
        if option.kind == "destination"
        for key in _destination_option_keys(option.value)
    }

    candidates = [
        *llm_update.mentioned_options,
        *[
            ConversationOptionCandidate(kind=option.kind, value=option.value)
            for option in current.memory.mentioned_options
        ],
    ]

    for candidate in candidates:
        if candidate.kind != "destination":
            continue
        option_keys = _destination_option_keys(candidate.value)
        if option_keys.intersection(rejected_keys):
            continue
        normalized = _normalize_destination_value(candidate.value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        values.append(candidate.value.strip())

    return values[:3]


def build_unresolved_destination_title(options: list[str]) -> str:
    if len(options) == 2:
        return f"{options[0]} and {options[1]} are both still in play"
    return f"{', '.join(options[:-1])}, and {options[-1]} are still in play"


def _filter_rejected_destination_cards(
    cards: list[DestinationSuggestionCard],
    current: TripConversationState,
) -> list[DestinationSuggestionCard]:
    rejected_destination_keys = {
        key
        for option in current.memory.rejected_options
        if option.kind == "destination"
        for key in _destination_option_keys(option.value)
    }
    seen_destination_keys: set[str] = set()
    filtered: list[DestinationSuggestionCard] = []

    for card in cards:
        card_keys = _destination_option_keys(
            f"{card.destination_name}, {card.country_or_region}"
        )
        if rejected_destination_keys.intersection(card_keys):
            continue

        primary_key = _normalize_destination_value(card.destination_name)
        if primary_key in seen_destination_keys:
            continue

        seen_destination_keys.add(primary_key)
        filtered.append(card)

    return filtered


def _destination_option_keys(value: str) -> set[str]:
    normalized = _normalize_destination_value(value)
    if not normalized:
        return set()

    keys = {normalized}
    primary = normalized.split(",")[0].strip()
    if primary:
        keys.add(primary)
    return keys


def _normalize_destination_value(value: str) -> str:
    return " ".join(value.strip().lower().split())
