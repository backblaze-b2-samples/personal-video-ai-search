from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Backblaze B2 (S3-compatible) ---
    # Standardized B2_* names. This differs from the upstream starter kit,
    # which used B2_KEY_ID and had no region — both corrected here so the
    # boto3 client gets an explicit region (no hardcoded region in source).
    b2_endpoint: str = "https://s3.us-west-004.backblazeb2.com"
    b2_application_key_id: str = ""
    b2_application_key: str = ""
    b2_bucket_name: str = ""
    b2_region: str = "us-west-004"
    b2_public_url: str = ""

    # --- AI providers (multimodal index pipeline) ---
    # Empty keys = the indexing features are disabled and degrade gracefully:
    # the API returns a clear "provider not configured" state instead of
    # crashing, and the generic B2 surfaces (upload, files, dashboard) keep
    # working. One key (OPENAI_API_KEY) covers all three paid signals.
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # OpenAI model tier (newest cost-efficient, not flagship).
    transcription_model: str = "whisper-1"
    vision_model: str = "gpt-4o-mini"  # keyframe captions + scene tags
    embedding_model: str = "text-embedding-3-small"
    # Anthropic, optional — only used for the synthesized answer over clips.
    answer_model: str = "claude-haiku-4-5"

    # --- Sample namespace + ingest limits ---
    # All of this sample's objects live under this prefix so the bucket can
    # be shared with other samples (and the full-bucket File Browser) without
    # collisions. The Library is scoped to this prefix; Files is not.
    video_prefix: str = "personal-video-ai-search/"
    max_video_size: int = 5 * 1024 * 1024 * 1024  # 5 GiB
    multipart_part_size: int = 64 * 1024 * 1024  # 64 MB per multipart part

    # Visual indexing caps — keep one demo run well under the $1 ceiling.
    max_keyframes_per_video: int = 8
    scene_threshold: float = 0.30  # ffmpeg scene-change sensitivity (0..1)

    # Local face clustering (no API cost). Cosine distance below this merges
    # two faces into the same cluster; a face must appear at least
    # min_faces_per_cluster times to surface as a named-able person.
    face_cluster_threshold: float = 0.55
    min_faces_per_cluster: int = 1

    # --- API / generic upload ---
    api_port: int = 8000
    # Explicit allowlist by default — covers Next on :3000 and the
    # fallback :3001 it picks if 3000 is busy. Production deploys should
    # override with the exact frontend origin.
    api_cors_origins: str = "http://localhost:3000,http://localhost:3001"
    # Optional dev-only escape hatch: a regex that matches additional
    # allowed origins. Empty by default. NEVER ship this to production.
    api_cors_origin_regex: str = ""

    # Generic /upload cap (small assets proxied through the API). Large video
    # never flows through the API — it uses presigned multipart, browser → B2.
    max_file_size: int = 100 * 1024 * 1024  # 100 MB

    # Small durable counters (plays/downloads, etc). Point at a persistent
    # volume in production if you care about surviving restarts.
    download_count_file: str = "data/download_count.json"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",")]


settings = Settings()
