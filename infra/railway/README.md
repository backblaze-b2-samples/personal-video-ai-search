# Railway Deployment

Deploy both services (web + api) on Railway.

## Setup

1. Create a new Railway project
2. Add two services from the same repo:

### Web Service (Next.js)
- **Root Directory**: `apps/web`
- **Build Command**: `pnpm install && pnpm build`
- **Start Command**: `pnpm start`
- **Port**: `3000`

### API Service (FastAPI)
- **Root Directory**: `services/api`
- **Build Command**: `apt-get update && apt-get install -y ffmpeg && pip install -r requirements.txt`
  (the index pipeline shells out to `ffmpeg`/`ffprobe`)
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

> The first ingest with face indexing downloads the local face model weights
> (insightface) once; give the API service a persistent volume if you want to
> avoid re-downloading them on each cold start.

## Environment Variables

Set these on the API service:

| Variable | Value |
|----------|-------|
| `B2_ENDPOINT` | Your B2 S3 endpoint |
| `B2_APPLICATION_KEY_ID` | Your B2 application key ID |
| `B2_APPLICATION_KEY` | Your B2 application key |
| `B2_BUCKET_NAME` | Your bucket name |
| `B2_REGION` | Your bucket region (e.g., `us-west-004`) |
| `OPENAI_API_KEY` | OpenAI key — Whisper + gpt-4o-mini vision + embeddings (leave unset to run B2-only) |
| `ANTHROPIC_API_KEY` | *(optional)* Claude key for the synthesized answer over clips |
| `API_CORS_ORIGINS` | Your web service URL (e.g., `https://web-production-xxx.up.railway.app`) |

Set this on the Web service:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | Your API service URL (e.g., `https://api-production-xxx.up.railway.app`) |
| `NEXT_PUBLIC_SEARCH_FILTERS_ENABLED` | `false` by default. Set to `true` only after every API instance has the Search filter backend and old instances are drained. |

### Search Filter Rollout

The Search date/event filters are gated from the Web service because old API
instances silently ignore unknown JSON fields. For rolling deploys:

1. Deploy the API service first.
2. Wait until old API instances are drained and `/health` reports
   `features.search_filters: true` everywhere.
3. Rebuild/redeploy the Web service with
   `NEXT_PUBLIC_SEARCH_FILTERS_ENABLED=true`.
