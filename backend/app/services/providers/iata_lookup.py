from dataclasses import dataclass
from typing import Literal

from app.integrations.amadeus.client import create_amadeus_client


CITY_IATA_ALIASES: dict[str, str] = {
    "london": "LON",
    "manchester": "MAN",
    "birmingham": "BHX",
    "edinburgh": "EDI",
    "glasgow": "GLA",
    "barcelona": "BCN",
    "madrid": "MAD",
    "lisbon": "LIS",
    "porto": "OPO",
    "valencia": "VLC",
    "seville": "SVQ",
    "malaga": "AGP",
    "paris": "PAR",
    "rome": "ROM",
    "milan": "MIL",
    "athens": "ATH",
    "amsterdam": "AMS",
    "berlin": "BER",
    "prague": "PRG",
    "budapest": "BUD",
    "dubai": "DXB",
    "marrakesh": "RAK",
    "marrakech": "RAK",
    "tokyo": "TYO",
    "osaka": "OSA",
    "kyoto": "OSA",
    "kyto": "OSA",
    "new york": "NYC",
    "san francisco": "SFO",
    "los angeles": "LAX",
}

GatewayRole = Literal["origin", "destination"]


@dataclass(frozen=True)
class FlightGateway:
    requested_location: str
    search_iata: str
    gateway_label: str
    ground_transfer_label: str | None = None

    @property
    def uses_ground_transfer(self) -> bool:
        return bool(self.ground_transfer_label)

    def planning_note(self, role: GatewayRole) -> str | None:
        if not self.ground_transfer_label:
            return None
        if role == "origin":
            return (
                f"Start with a ground transfer from {self.requested_location} to "
                f"{self.ground_transfer_label} before flying from {self.search_iata}."
            )
        return (
            f"{self.requested_location} is reached by flying into "
            f"{self.ground_transfer_label}, then continuing by ground transfer."
        )


FLIGHT_GATEWAY_ALIASES: dict[str, tuple[str, str, str]] = {
    "kyoto": ("OSA", "Osaka gateway", "Osaka/Kansai or Itami"),
    "kyto": ("OSA", "Osaka gateway", "Osaka/Kansai or Itami"),
    "amalfi coast": ("NAP", "Naples gateway", "Naples"),
    "positano": ("NAP", "Naples gateway", "Naples"),
    "lake como": ("MIL", "Milan gateway", "Milan"),
    "cinque terre": ("PSA", "Pisa gateway", "Pisa"),
    "interlaken": ("ZRH", "Zurich gateway", "Zurich"),
    "st moritz": ("ZRH", "Zurich gateway", "Zurich"),
    "saint moritz": ("ZRH", "Zurich gateway", "Zurich"),
    "banff": ("YYC", "Calgary gateway", "Calgary"),
    "tulum": ("CUN", "Cancun gateway", "Cancun"),
}


def resolve_flight_gateway(keyword: str) -> FlightGateway | None:
    cleaned_keyword = keyword.strip()
    if not cleaned_keyword:
        return None

    gateway_match = _match_flight_gateway_alias(cleaned_keyword)
    if gateway_match:
        search_iata, gateway_label, ground_transfer_label = gateway_match
        return FlightGateway(
            requested_location=cleaned_keyword,
            search_iata=search_iata,
            gateway_label=gateway_label,
            ground_transfer_label=ground_transfer_label,
        )

    iata_code = resolve_location_iata(cleaned_keyword)
    if not iata_code:
        return None

    return FlightGateway(
        requested_location=cleaned_keyword,
        search_iata=iata_code,
        gateway_label=cleaned_keyword,
    )


def _match_flight_gateway_alias(keyword: str) -> tuple[str, str, str] | None:
    normalized_keyword = _normalize_location_key(keyword)
    direct_match = FLIGHT_GATEWAY_ALIASES.get(normalized_keyword)
    if direct_match:
        return direct_match

    for alias, gateway in FLIGHT_GATEWAY_ALIASES.items():
        if normalized_keyword.startswith(f"{alias} "):
            return gateway
    return None


def _normalize_location_key(keyword: str) -> str:
    normalized = keyword.lower()
    for character in [",", ".", "(", ")", "/", "-"]:
        normalized = normalized.replace(character, " ")
    return " ".join(normalized.split())


def resolve_location_iata(keyword: str) -> str | None:
    if not keyword.strip():
        return None

    cleaned_keyword = keyword.strip()
    if len(cleaned_keyword) == 3 and cleaned_keyword.isalpha():
        return cleaned_keyword.upper()

    alias_match = CITY_IATA_ALIASES.get(cleaned_keyword.lower())
    if alias_match:
        return alias_match

    try:
        with create_amadeus_client() as client:
            response = client.get(
                "/v1/reference-data/locations",
                params={
                    "subType": "CITY,AIRPORT",
                    "keyword": cleaned_keyword[:20],
                    "page[limit]": 5,
                },
            )
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return None

    candidates = payload.get("data") or []
    if not candidates:
        return None

    city_candidate = next(
        (
            item
            for item in candidates
            if item.get("subType") == "CITY" and item.get("iataCode")
        ),
        None,
    )
    if city_candidate:
        return city_candidate["iataCode"]

    first_candidate = candidates[0]
    iata_code = first_candidate.get("iataCode")
    return iata_code if isinstance(iata_code, str) else None
