"use client";

import type { DestinationSuggestionCard } from "@/types/trip-conversation";

const DESTINATION_IMAGE_CACHE = new Map<string, string>();
const DESTINATION_IMAGE_STORAGE_PREFIX = "wandrix.destination-image.v4.";
const TRUSTED_DESTINATION_IMAGE_HOSTS = new Set([
  "upload.wikimedia.org",
]);
const GENERIC_CITY_IMAGE =
  "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1600&q=80";
const GENERIC_COAST_IMAGE =
  "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1600&q=80";
const GENERIC_HERITAGE_IMAGE =
  "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=1600&q=80";

const UNSTABLE_IMAGE_MARKERS = [
  "source.unsplash.com",
];
const GENERIC_IMAGE_MARKERS = [
  "photo-1488646953014-85cb44e25828",
  "photo-1449824913935-59a10b8d2000",
  "photo-1507525428034-b723cf961d3e",
  "photo-1524231757912-21f4fe3a7200",
];
const NON_DESTINATION_IMAGE_MARKERS = [
  "special_marker",
  "location_map",
  "locator_map",
  "map_of_",
  "_map.",
  "flag_of_",
  ".svg",
  "coat_of_arms",
  "seal_of_",
  "emblem",
  "logo",
];

export async function resolveDestinationSuggestionImage(
  card: DestinationSuggestionCard,
): Promise<string> {
  const cacheKey = buildCacheKey(card.destination_name, card.country_or_region);
  const cached = readCachedDestinationImage(cacheKey);
  if (cached) {
    return cached;
  }

  const provided = normalizeProvidedImage(card.image_url);
  if (provided) {
    writeCachedDestinationImage(cacheKey, provided);
    return provided;
  }

  const wikipediaImage = await resolveWikipediaDestinationImage(card);
  if (wikipediaImage) {
    writeCachedDestinationImage(cacheKey, wikipediaImage);
    return wikipediaImage;
  }

  return getSafeFallbackDestinationImage(card);
}

export function getDestinationSuggestionImagePreview(
  card: DestinationSuggestionCard,
): string {
  return (
    normalizeProvidedImage(card.image_url) ||
    getSafeFallbackDestinationImage(card)
  );
}

export function getDestinationSuggestionImageFallback(
  card: DestinationSuggestionCard,
): string {
  return getSafeFallbackDestinationImage(card);
}

function buildCacheKey(destinationName: string, countryOrRegion: string) {
  return `${destinationName.trim().toLowerCase()}::${countryOrRegion
    .trim()
    .toLowerCase()}`;
}

function readCachedDestinationImage(cacheKey: string) {
  const memoryHit = DESTINATION_IMAGE_CACHE.get(cacheKey);
  const normalizedMemoryHit = normalizeProvidedImage(memoryHit);
  if (normalizedMemoryHit) {
    return normalizedMemoryHit;
  }
  if (memoryHit) {
    DESTINATION_IMAGE_CACHE.delete(cacheKey);
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

  const normalizedStorageHit = normalizeProvidedImage(storageHit);
  if (!normalizedStorageHit) {
    window.sessionStorage.removeItem(
      `${DESTINATION_IMAGE_STORAGE_PREFIX}${cacheKey}`,
    );
    return null;
  }

  DESTINATION_IMAGE_CACHE.set(cacheKey, normalizedStorageHit);
  return normalizedStorageHit;
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
  const destinationVariants = expandDestinationTitleVariants(destination);

  for (const variant of destinationVariants) {
    candidates.add(variant);
  }

  if (country) {
    for (const variant of destinationVariants) {
      candidates.add(`${variant}, ${country}`);
      candidates.add(`${variant} ${country}`);
    }
  }

  return [...candidates];
}

function expandDestinationTitleVariants(destination: string) {
  const normalized = destination.trim();
  if (!normalized) {
    return [];
  }

  const variants = new Set([normalized]);
  const parenthetical = normalized.match(/^(.+?)\s*\((.+?)\)\s*$/);
  if (parenthetical) {
    variants.add(parenthetical[1].trim());
    variants.add(parenthetical[2].trim());
  }

  return [...variants].filter(Boolean);
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

  if (UNSTABLE_IMAGE_MARKERS.some((marker) => trimmed.includes(marker))) {
    return null;
  }

  try {
    const parsed = new URL(trimmed);
    if (
      parsed.protocol !== "https:" ||
      !TRUSTED_DESTINATION_IMAGE_HOSTS.has(parsed.hostname)
    ) {
      return null;
    }
  } catch {
    return null;
  }

  const normalized = trimmed.toLowerCase();
  if (GENERIC_IMAGE_MARKERS.some((marker) => normalized.includes(marker))) {
    return null;
  }
  if (NON_DESTINATION_IMAGE_MARKERS.some((marker) => normalized.includes(marker))) {
    return null;
  }

  return trimmed;
}

function getSafeFallbackDestinationImage(card: DestinationSuggestionCard) {
  const normalized = [
    card.destination_name,
    card.country_or_region,
    card.short_reason,
    card.practicality_label,
    card.fit_label,
    card.best_for,
    card.recommendation_note,
    card.change_note,
    ...(card.tradeoffs ?? []),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  if (
    [
      "beach",
      "beaches",
      "coast",
      "coastal",
      "sea",
      "ocean",
      "island",
      "riviera",
      "harbour",
      "harbor",
      "waterfront",
    ].some((marker) => normalized.includes(marker))
  ) {
    return GENERIC_COAST_IMAGE;
  }

  if (
    [
      "ancient",
      "heritage",
      "historic",
      "history",
      "old town",
      "palace",
      "fort",
      "temple",
      "monument",
      "museum",
    ].some((marker) => normalized.includes(marker))
  ) {
    return GENERIC_HERITAGE_IMAGE;
  }

  return GENERIC_CITY_IMAGE;
}
