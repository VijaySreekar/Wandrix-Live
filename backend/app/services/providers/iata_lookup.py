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
    "new york": "NYC",
    "san francisco": "SFO",
    "los angeles": "LAX",
}


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
