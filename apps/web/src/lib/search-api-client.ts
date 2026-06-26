import type { SearchResponse } from "@personal-video-ai-search/shared";

import { ApiError, apiFetch, getHealth } from "@/lib/api-client";

export const SEARCH_FILTERS_ENABLED =
  process.env.NEXT_PUBLIC_SEARCH_FILTERS_ENABLED === "true";

let searchFilterSupportCheck: Promise<void> | null = null;

export type LocalDateString = `${number}-${number}-${number}`;

export interface SearchOptions {
  videoId?: string | null;
  personId?: string | null;
  // YYYY-MM-DD values from local calendar-day controls. The API receives
  // timezone-aware instants generated from the user's selected days.
  createdAtFrom?: LocalDateString | null;
  createdAtTo?: LocalDateString | null;
  eventName?: string | null;
  topK?: number;
  synthesize?: boolean;
}

interface SearchRequestPayload {
  question: string;
  video_id: string | null;
  person_id: string | null;
  top_k: number;
  synthesize: boolean;
  created_at_from?: string | null;
  created_at_to?: string | null;
  event_name?: string | null;
}

async function ensureSearchFiltersSupported() {
  searchFilterSupportCheck ??= getHealth()
    .then((health) => {
      if (health.features?.search_filters !== true) {
        throw new ApiError("Search filter support is not available on the API", 409);
      }
    })
    .catch((error) => {
      searchFilterSupportCheck = null;
      throw error;
    });

  return searchFilterSupportCheck;
}

function localDayInstant(
  dateValue: LocalDateString | null | undefined,
  fieldName: string,
  endOfDay = false,
) {
  if (!dateValue) return null;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateValue)) {
    throw new ApiError(`${fieldName} must use YYYY-MM-DD`, 400);
  }
  const [year, month, day] = dateValue.split("-").map(Number);
  if (!year || !month || !day) {
    throw new ApiError(`${fieldName} must be a valid calendar date`, 400);
  }
  const local = endOfDay
    ? new Date(year, month - 1, day, 23, 59, 59, 999)
    : new Date(year, month - 1, day, 0, 0, 0, 0);
  if (
    local.getFullYear() !== year ||
    local.getMonth() !== month - 1 ||
    local.getDate() !== day
  ) {
    throw new ApiError(`${fieldName} must be a valid calendar date`, 400);
  }
  const instant = local.toISOString();
  return endOfDay ? instant.replace(/\.999Z$/, ".999999Z") : instant;
}

export async function searchVideos(question: string, opts: SearchOptions = {}) {
  const eventName = opts.eventName?.trim() || null;
  const hasRequestedFilters = Boolean(
    opts.createdAtFrom || opts.createdAtTo || eventName,
  );

  if (hasRequestedFilters && !SEARCH_FILTERS_ENABLED) {
    throw new ApiError("Search filters are disabled in this deployment", 409);
  }

  const createdAtFrom = SEARCH_FILTERS_ENABLED
    ? localDayInstant(opts.createdAtFrom, "createdAtFrom")
    : null;
  const createdAtTo = SEARCH_FILTERS_ENABLED
    ? localDayInstant(opts.createdAtTo, "createdAtTo", true)
    : null;

  if (createdAtFrom || createdAtTo || eventName) {
    await ensureSearchFiltersSupported();
  }

  const body: SearchRequestPayload = {
    question,
    video_id: opts.videoId ?? null,
    person_id: opts.personId ?? null,
    top_k: opts.topK ?? 8,
    synthesize: opts.synthesize ?? false,
  };

  if (SEARCH_FILTERS_ENABLED) {
    body.created_at_from = createdAtFrom;
    body.created_at_to = createdAtTo;
    body.event_name = eventName;
  }

  return apiFetch<SearchResponse>("/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
