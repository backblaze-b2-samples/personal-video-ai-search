<!-- last_verified: 2026-06-25 -->
# Issue 1: Search Date And Event Filters

## Goal
Add inclusive `created_at` date range filters and an event-name filter to Search.

## Plan
1. Extend `SearchRequest` with optional date range and event-name fields.
2. Filter candidate videos in the search service before loading scene indexes.
3. Thread the options through the TypeScript API client, query mutation, and UI.
4. Add backend coverage for the new filters.
5. Update the Search feature docs and tech debt tracker.

## Verification
- `pnpm lint`
- `pnpm lint:api`
- `pnpm test:api`
- `pnpm check:structure`
- `pnpm build`
- Playwright smoke check for `/search` filter controls
