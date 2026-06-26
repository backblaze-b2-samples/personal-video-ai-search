<!-- last_verified: 2026-06-25 -->
# Issue 1 and 3: Search Date And Event Filters

## Goal
Add inclusive, timezone-aware `created_at` range filters and an event-name
filter to Search, including frontend date input bounds that prevent inverted
date ranges before submit.

## Plan
1. Extend `SearchRequest` with optional date range and event-name fields.
2. Filter candidate videos in the search service before loading scene indexes.
3. Gate frontend controls and request fields behind
   `NEXT_PUBLIC_SEARCH_FILTERS_ENABLED` for backend-first rolling deploys.
4. Thread the options through the TypeScript API client, query mutation, and UI.
5. Add backend and e2e coverage for the new filters and date bounds.
6. Update the Search feature docs and tech debt tracker.

## Verification
- `pnpm lint`
- `pnpm lint:api`
- `pnpm test:api`
- `pnpm check:structure`
- `pnpm build`
- Playwright Search filter date-bound coverage
