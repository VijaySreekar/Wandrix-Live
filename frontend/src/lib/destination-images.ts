"use client";

import type { DestinationSuggestionCard } from "@/types/trip-conversation";

const DESTINATION_IMAGE_CACHE = new Map<string, string>();
const DESTINATION_IMAGE_STORAGE_PREFIX = "wandrix.destination-image.";

const CURATED_DESTINATION_IMAGES: Record<string, string> = {
  "canary islands":
    "https://images.unsplash.com/photo-1511527661048-7fe73d85e9a4?auto=format&fit=crop&w=1600&q=80",
  seville:
    "https://images.unsplash.com/photo-1562883676-8c7feb1c4d73?auto=format&fit=crop&w=1600&q=80",
  malta:
    "https://images.unsplash.com/photo-1573152958734-1922c188fba3?auto=format&fit=crop&w=1600&q=80",
  madeira:
    "https://images.unsplash.com/photo-1510097467424-192d713fd8b2?auto=format&fit=crop&w=1600&q=80",
  marrakesh:
    "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1600&q=80",
  marrakech:
    "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1600&q=80",
  rome:
    "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=1600&q=80",
  athens:
    "https://images.unsplash.com/photo-1555993539-1732b0258235?auto=format&fit=crop&w=1600&q=80",
  lisbon:
    "https://images.unsplash.com/photo-1513735492246-483525079686?auto=format&fit=crop&w=1600&q=80",
  porto:
    "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?auto=format&fit=crop&w=1600&q=80",
  valencia:
    "https://images.unsplash.com/photo-1543783207-ec64e4d95325?auto=format&fit=crop&w=1600&q=80",
  dubai:
    "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1600&q=80",
};

const GENERIC_IMAGE_MARKERS = [
  "source.unsplash.com",
  "photo-1488646953014-85cb44e25828",
  "photo-1507525428034-b723cf961d3e",
];

export async function resolveDestinationSuggestionImage(
  card: DestinationSuggestionCard,
): Promise<string> {
  const cacheKey = buildCacheKey(card.destination_name, card.country_or_region);
  const cached = readCachedDestinationImage(cacheKey);
  if (cached) {
    return cached;
  }

  const curated = getCuratedDestinationImage(card.destination_name);
  if (curated) {
    writeCachedDestinationImage(cacheKey, curated);
    return curated;
  }

  const wikipediaImage = await resolveWikipediaDestinationImage(card);
  if (wikipediaImage) {
    writeCachedDestinationImage(cacheKey, wikipediaImage);
    return wikipediaImage;
  }

  const provided = normalizeProvidedImage(card.image_url);
  if (provided) {
    writeCachedDestinationImage(cacheKey, provided);
    return provided;
  }

  return getSafeFallbackDestinationImage(card.destination_name);
}

function buildCacheKey(destinationName: string, countryOrRegion: string) {
  return `${destinationName.trim().toLowerCase()}::${countryOrRegion
    .trim()
    .toLowerCase()}`;
}

function readCachedDestinationImage(cacheKey: string) {
  const memoryHit = DESTINATION_IMAGE_CACHE.get(cacheKey);
  if (memoryHit) {
    return memoryHit;
  }

  if (typeof window === "undefined") {
    return null;
  }

  const storageHit = window.sessionStorage.getItem(
    `${DESTINATION_IMAGE_STORAGE_PREFIX}${cacheKey}`,
  );
  if (!storageHit) {
    return null;
  }

  DESTINATION_IMAGE_CACHE.set(cacheKey, storageHit);
  return storageHit;
}

function writeCachedDestinationImage(cacheKey: string, imageUrl: string) {
  DESTINATION_IMAGE_CACHE.set(cacheKey, imageUrl);

  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(
    `${DESTINATION_IMAGE_STORAGE_PREFIX}${cacheKey}`,
    imageUrl,
  );
}

function getCuratedDestinationImage(destinationName: string) {
  const normalized = destinationName.trim().toLowerCase();

  for (const [key, imageUrl] of Object.entries(CURATED_DESTINATION_IMAGES)) {
    if (normalized.includes(key)) {
      return imageUrl;
    }
  }

  return null;
}

async function resolveWikipediaDestinationImage(card: DestinationSuggestionCard) {
  const titles = buildWikipediaTitleCandidates(card);

  for (const title of titles) {
    const image = await fetchWikipediaSummaryImage(title);
    if (image) {
      return image;
    }
  }

  return null;
}

function buildWikipediaTitleCandidates(card: DestinationSuggestionCard) {
  const destination = card.destination_name.trim();
  const country = card.country_or_region.trim();
  const candidates = new Set<string>();

  if (destination) {
    candidates.add(destination);
  }

  if (destination && country) {
    candidates.add(`${destination}, ${country}`);
    candidates.add(`${destination} ${country}`);
  }

  if (destination.toLowerCase().includes("canary islands")) {
    candidates.add("Canary Islands");
    candidates.add("Tenerife");
    candidates.add("Gran Canaria");
  }

  if (destination.toLowerCase() === "madeira") {
    candidates.add("Madeira");
    candidates.add("Funchal");
  }

  return [...candidates];
}

async function fetchWikipediaSummaryImage(title: string) {
  try {
    const response = await fetch(
      `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title)}`,
      {
        headers: {
          Accept: "application/json",
        },
      },
    );

    if (!response.ok) {
      return null;
    }

    const data = (await response.json()) as {
      originalimage?: { source?: string };
      thumbnail?: { source?: string };
      type?: string;
    };

    if (data.type === "disambiguation") {
      return null;
    }

    return (
      data.originalimage?.source ||
      data.thumbnail?.source ||
      null
    );
  } catch {
    return null;
  }
}

function normalizeProvidedImage(imageUrl: string | null | undefined) {
  const trimmed = imageUrl?.trim();
  if (!trimmed) {
    return null;
  }

  if (GENERIC_IMAGE_MARKERS.some((marker) => trimmed.includes(marker))) {
    return null;
  }

  return trimmed;
}

function getSafeFallbackDestinationImage(destinationName: string) {
  const normalized = destinationName.trim().toLowerCase();

  if (normalized.includes("island")) {
    return "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1600&q=80";
  }

  return "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1600&q=80";
}
