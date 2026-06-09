<!-- last_verified: 2026-06-09 -->
# Feature: Dashboard

## Purpose
Give an at-a-glance overview of the video archive: what's indexed, how much
footage, who's in it, and how much B2 storage it uses.

## Used By
- UI: `/` page (dashboard home)
- API: `GET /videos`, `GET /people`, `GET /files/stats`, `GET /files/stats/activity`

## Core Functions
- `apps/web/src/components/dashboard/stats-cards.tsx` — videos indexed, hours of footage, people identified, storage used
- `apps/web/src/components/dashboard/recent-videos-table.tsx` — last 8 videos + pipeline status
- `apps/web/src/components/dashboard/upload-chart.tsx` — B2 objects written per day
- `apps/web/src/lib/queries.ts` — `useVideos()`, `usePeople()`, `useFileStats()`, `useUploadActivity()`
- `services/api/app/service/videos.py` — `list_videos()` (status + counts from B2 meta.json)

## Canonical Files
- Stats: `apps/web/src/components/dashboard/stats-cards.tsx`
- Aggregation source: `services/api/app/service/videos.py`

## Inputs
- None (dashboard loads data automatically)

## Outputs
- `GET /videos` → `Video[]` (drives "videos indexed", "hours of footage", recent table)
- `GET /people` → `Person[]` (drives "people identified")
- `GET /files/stats` → `UploadStats` (drives "storage used")
- `GET /files/stats/activity?days=7` → `DailyUploadCount[]` (B2 activity chart)

## Flow
- Page loads → parallel TanStack Query hooks fetch videos, people, stats, activity
- Stats cards compute videos-ready, total duration in hours, people count, B2 storage
- `useVideos` polls every 4s while any video is mid-pipeline so counts stay live
- Recent videos table shows the latest 8 with a status badge and length

## Edge Cases
- API unavailable → inline `ErrorState` with retry (not a silent zero)
- No videos → empty states on cards/table; chart shows "no activity yet"
- Many objects → stats endpoint paginates with `ContinuationToken`

## UX States
- Loading: skeleton placeholders for cards and table
- Empty: "No videos yet" / "No activity yet"
- Loaded: populated cards, chart, table

## Verification
- Test files: `services/api/tests/test_upload_activity.py`, `services/api/tests/test_recent_files.py`
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: pytest green, no ruff violations

## Related Docs
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [App Workflows](../app-workflows.md)
