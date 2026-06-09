<!-- last_verified: 2026-06-09 -->
# App Workflows

User journeys inside the application.

## Add a video (ingest)

- User navigates to `/library` and clicks **Add video**
- Drops or selects a video (any size up to `MAX_VIDEO_SIZE`, default 5 GiB)
- The browser opens a presigned multipart upload and PUTs each part **directly
  to B2** — the API never proxies the bytes; a progress bar shows % uploaded
- On completion the API finalizes the upload and schedules the index pipeline
- The new video appears in the Library immediately with a live status badge
- See: [Video Ingest](features/video-ingest.md)

## Watch a video get indexed

- On `/library`, each video shows its pipeline stage, polled live:
  `uploading → probing → transcribing → tagging → clustering → embedding → ready`
- Behind the scenes the pipeline: probes the file, transcribes the audio
  (Whisper), samples scene-change keyframes and captions/tags them (gpt-4o-mini),
  detects + clusters faces locally, then embeds every scene
- All artifacts (transcript, thumbnails, scene tags, embedding index, face
  index) are written to B2 — there is no database
- A row can be **re-indexed** or **deleted** (removes the whole video tree from B2)
- With no `OPENAI_API_KEY`, the video sits at `uploaded` with a "configure a
  provider" note instead of erroring
- See: [Video Library](features/video-library.md)

## Search the archive

- User navigates to `/search` and asks in plain language — e.g. "the dog jumps
  in the pool" or "birthday cake"
- Optional: filter by a named **person**, and/or toggle a Claude-synthesized
  answer over the top clips
- The API embeds the query, scores it against the B2 scene indexes across all
  ready videos, and returns ranked clips with thumbnails
- Each clip plays inline by seeking the original in B2 (presigned + Range);
  detected people and scene tags are shown as chips
- Empty / not-configured states are explicit, never a blank page
- See: [Cross-archive Search](features/search.md)

## Browse by person

- User navigates to `/people`
- Faces clustered across the whole archive show as cards (cover thumbnail +
  appearance/video counts)
- Click the pencil to **name** a cluster ("Grandma"); click a card to open every
  clip that person appears in
- All on-device — no AI key. If the local face stack isn't installed, a clear
  "not available" state is shown
- See: [People (Face Clustering)](features/people.md)

## View Dashboard

- User navigates to `/` (home)
- Stats cards show: videos indexed, hours of footage, people identified, storage used
- A B2 activity chart shows objects written over the last 7 days
- A recent-videos table shows the latest videos with pipeline status
- See: [Dashboard](features/dashboard.md)

## Browse the whole bucket (File Browser)

- User navigates to `/files`
- The full bucket (not just this sample's prefix) is shown as a tree
- Preview / download / delete any object
- See: [File Browser](features/file-browser.md)

## Upload a small asset (generic)

- User navigates to `/upload` for small assets (≤100 MB), proxied through the API
- Large archive videos use the multipart Ingest flow above instead
- See: [File Upload](features/file-upload.md)
