from __future__ import annotations

import calendar
import re
from datetime import date, timedelta

from app.schemas.trip_conversation import AdvancedDateOptionCard
from app.schemas.trip_planning import TripConfiguration


_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def build_advanced_date_options(
    configuration: TripConfiguration,
    *,
    today: date | None = None,
) -> list[AdvancedDateOptionCard]:
    current_day = today or date.today()
    rough_timing = (configuration.travel_window or "").strip()
    rough_length = (configuration.trip_length or "").strip()
    weekend_mode = _has_weekend_signal(rough_timing, rough_length)
    target_month = _resolve_target_month(rough_timing, current_day)
    target_year = _resolve_target_year(
        rough_timing=rough_timing,
        today=current_day,
        target_month=target_month,
    )
    nights = _resolve_nights(rough_timing=rough_timing, rough_length=rough_length)
    start_dates = (
        _build_weekend_start_dates(year=target_year, month=target_month)
        if weekend_mode
        else _build_general_start_dates(
            year=target_year,
            month=target_month,
            rough_timing=rough_timing,
        )
    )
    recommended_index = _recommended_option_index(
        rough_timing=rough_timing,
        weekend_mode=weekend_mode,
    )
    reason_labels = _build_reason_labels(
        rough_timing=rough_timing,
        rough_length=rough_length,
        weekend_mode=weekend_mode,
    )
    cards: list[AdvancedDateOptionCard] = []

    for index, start_day in enumerate(start_dates[:3]):
        end_day = start_day + timedelta(days=nights)
        cards.append(
            AdvancedDateOptionCard(
                id=f"date_option_{start_day.isoformat()}_{end_day.isoformat()}",
                title=_build_option_title(
                    start_day=start_day,
                    end_day=end_day,
                    weekend_mode=weekend_mode,
                ),
                start_date=start_day,
                end_date=end_day,
                nights=nights,
                reason=reason_labels[index],
                recommended=index == recommended_index,
                cta_label="Use this trip window",
            )
        )

    return cards


def _has_weekend_signal(rough_timing: str, rough_length: str) -> bool:
    combined = f"{rough_timing} {rough_length}".lower()
    return "weekend" in combined


def _resolve_target_month(rough_timing: str, today: date) -> int:
    normalized = rough_timing.lower()
    for month_name, month_number in _MONTHS.items():
        if month_name in normalized:
            return month_number

    if "next month" in normalized:
        return 1 if today.month == 12 else today.month + 1

    return today.month


def _resolve_target_year(
    *,
    rough_timing: str,
    today: date,
    target_month: int,
) -> int:
    year_match = re.search(r"\b(20\d{2})\b", rough_timing)
    if year_match:
        return int(year_match.group(1))

    if target_month < today.month:
        return today.year + 1

    return today.year


def _resolve_nights(*, rough_timing: str, rough_length: str) -> int:
    combined = f"{rough_timing} {rough_length}".lower()
    nights_match = re.search(r"(\d+)\s*nights?", combined)
    if nights_match:
        return max(1, min(14, int(nights_match.group(1))))

    days_match = re.search(r"(\d+)\s*days?", combined)
    if days_match:
        return max(1, min(14, int(days_match.group(1)) - 1))

    if "long weekend" in combined:
        return 3

    if "weekend" in combined:
        return 2

    if "week" in combined:
        return 6

    return 4


def _build_weekend_start_dates(*, year: int, month: int) -> list[date]:
    last_day = calendar.monthrange(year, month)[1]
    fridays = [
        date(year, month, day)
        for day in range(1, last_day + 1)
        if date(year, month, day).weekday() == 4
    ]
    if len(fridays) >= 3:
        midpoint = max(0, (len(fridays) // 2) - 1)
        selected = fridays[midpoint : midpoint + 3]
        if len(selected) == 3:
            return selected

    while len(fridays) < 3:
        fallback = fridays[-1] + timedelta(days=7) if fridays else date(year, month, 1)
        fridays.append(fallback)
    return fridays[:3]


def _build_general_start_dates(
    *,
    year: int,
    month: int,
    rough_timing: str,
) -> list[date]:
    qualifier = rough_timing.lower()
    if "early" in qualifier:
        candidates = [4, 8, 12]
    elif "mid" in qualifier:
        candidates = [10, 14, 18]
    elif "late" in qualifier:
        candidates = [18, 22, 26]
    else:
        candidates = [7, 13, 19]

    last_day = calendar.monthrange(year, month)[1]
    return [date(year, month, min(day, last_day)) for day in candidates]


def _recommended_option_index(*, rough_timing: str, weekend_mode: bool) -> int:
    if weekend_mode:
        return 1

    normalized = rough_timing.lower()
    if "early" in normalized:
        return 0
    return 1


def _build_reason_labels(
    *,
    rough_timing: str,
    rough_length: str,
    weekend_mode: bool,
) -> list[str]:
    timing_text = rough_timing.lower()
    if weekend_mode:
        return [
            "Earlier clean weekend interpretation",
            "Best weekend interpretation",
            "Later weekend option if you want more flexibility",
        ]

    if "late march" in timing_text:
        return [
            "Earlier late-March fit",
            "Cleanest late-March fit",
            "Latest workable late-March option",
        ]

    if "early" in timing_text:
        return [
            "Closest early-window fit",
            "Best balance inside the early window",
            "Slightly later if you want extra breathing room",
        ]

    if "mid" in timing_text:
        return [
            "Earlier mid-window interpretation",
            "Best mid-window balance",
            "Later mid-window option",
        ]

    if "late" in timing_text:
        return [
            "Earlier late-window option",
            "Strongest late-window balance",
            "Later option if you want to stretch the window",
        ]

    if rough_length:
        return [
            f"Earlier option for {rough_length}",
            f"Strongest balance for {rough_length}",
            "Later option for smoother onward planning",
        ]

    return [
        "Earlier workable option",
        "Strongest balance for onward planning",
        "Later workable option",
    ]


def _build_option_title(
    *,
    start_day: date,
    end_day: date,
    weekend_mode: bool,
) -> str:
    if weekend_mode:
        return f"{start_day.strftime('%a %d %b')} - {end_day.strftime('%a %d %b')}"
    return f"{start_day.strftime('%d %b')} - {end_day.strftime('%d %b')}"
