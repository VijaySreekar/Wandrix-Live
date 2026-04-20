CURATED_DESTINATION_IMAGES: dict[str, str] = {
    "canary islands": "https://images.unsplash.com/photo-1511527661048-7fe73d85e9a4?auto=format&fit=crop&w=1600&q=80",
    "seville": "https://images.unsplash.com/photo-1562883676-8c7feb1c4d73?auto=format&fit=crop&w=1600&q=80",
    "malta": "https://images.unsplash.com/photo-1573152958734-1922c188fba3?auto=format&fit=crop&w=1600&q=80",
    "madeira": "https://images.unsplash.com/photo-1510097467424-192d713fd8b2?auto=format&fit=crop&w=1600&q=80",
    "marrakesh": "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1600&q=80",
    "marrakech": "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1600&q=80",
    "rome": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=1600&q=80",
    "athens": "https://images.unsplash.com/photo-1555993539-1732b0258235?auto=format&fit=crop&w=1600&q=80",
    "lisbon": "https://images.unsplash.com/photo-1513735492246-483525079686?auto=format&fit=crop&w=1600&q=80",
    "porto": "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?auto=format&fit=crop&w=1600&q=80",
    "valencia": "https://images.unsplash.com/photo-1543783207-ec64e4d95325?auto=format&fit=crop&w=1600&q=80",
    "dubai": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1600&q=80",
}

GENERIC_DESTINATION_IMAGE = (
    "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1600&q=80"
)
GENERIC_ISLAND_IMAGE = (
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1600&q=80"
)


def get_destination_hero_image(destination_name: str | None) -> str:
    normalized = (destination_name or "").strip().lower()
    if not normalized:
        return GENERIC_DESTINATION_IMAGE

    for key, image_url in CURATED_DESTINATION_IMAGES.items():
        if key in normalized:
            return image_url

    if "island" in normalized:
        return GENERIC_ISLAND_IMAGE

    return GENERIC_DESTINATION_IMAGE
