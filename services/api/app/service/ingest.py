"""Ingest pipeline: probe → transcribe (Whisper) → sample keyframes + caption
/tag (vision) → cluster faces (local) → embed every scene → persist the index
to B2. Runs as a FastAPI BackgroundTask (no external job queue — see
docs/RELIABILITY.md).

Status is persisted to meta.json at every stage so the Library reflects
progress, and the whole thing degrades gracefully: with no OPENAI_API_KEY the
video stays ``uploaded`` with a clear "configure a provider" message instead of
crashing; the generic B2 surfaces keep working regardless."""

import logging

from app.repo import (
    ProviderNotConfiguredError,
    embeddings,
    media,
    transcription,
    video_store,
    vision,
)
from app.service import people as people_svc
from app.service import scenes as scenes_svc
from app.service import videos as videos_svc
from app.types import SceneEmbedding, SceneIndex, Transcript, VideoStatus

logger = logging.getLogger(__name__)


def run_pipeline(video_id: str) -> None:
    video = videos_svc.try_get(video_id)
    if not video:
        logger.warning("Pipeline: video %s not found", video_id)
        return

    # The three paid signals all key off OPENAI_API_KEY. Without it, surface a
    # clear state instead of failing.
    if not (vision.is_configured() and embeddings.is_configured()):
        videos_svc.update_status(
            video_id,
            VideoStatus.uploaded,
            error="AI provider not configured — set OPENAI_API_KEY to index "
            "this video (transcript + scene tags + searchable embeddings).",
        )
        logger.info("Pipeline skipped for %s: provider not configured", video_id)
        return

    try:
        _run(video_id, video.source_key)
    except ProviderNotConfiguredError as e:
        videos_svc.update_status(video_id, VideoStatus.uploaded, error=str(e))
    except Exception as e:  # pipeline must never crash the background worker
        logger.exception("Pipeline failed for %s", video_id)
        videos_svc.update_status(video_id, VideoStatus.failed, error=str(e)[:300])


def _run(video_id: str, source_key: str) -> None:
    videos_svc.update_status(video_id, VideoStatus.probing)
    local_video = media.download_to_temp(source_key)
    probe = media.probe(local_video)
    videos_svc.update_status(video_id, VideoStatus.probing, probe=probe)

    # --- 1. Transcript (audio) -------------------------------------------
    videos_svc.update_status(video_id, VideoStatus.transcribing, probe=probe)
    transcript = _transcribe(video_id, local_video, probe)

    # --- 2. Visual scene tags (sampled keyframes) ------------------------
    videos_svc.update_status(video_id, VideoStatus.tagging, probe=probe)
    scenes = scenes_svc.build_scenes(video_id, local_video, transcript)
    video_store.put_json(
        video_store.scenes_key(video_id),
        {"video_id": video_id, "scenes": [s.model_dump(mode="json") for s in scenes]},
    )

    # --- 3. Faces (local detect + embed + cluster across the archive) ----
    videos_svc.update_status(
        video_id, VideoStatus.clustering, probe=probe, scene_count=len(scenes)
    )
    people_count = people_svc.index_video_faces(video_id, scenes)

    # --- 4. Embed every scene → the searchable multimodal index ----------
    videos_svc.update_status(
        video_id,
        VideoStatus.embedding,
        probe=probe,
        scene_count=len(scenes),
        people_count=people_count,
    )
    documents = [scenes_svc.scene_document(s) for s in scenes]
    vectors = embeddings.embed_texts(documents) if documents else []
    index = SceneIndex(
        video_id=video_id,
        model=embeddings.model_name(),
        dim=len(vectors[0]) if vectors else 0,
        scenes=[
            SceneEmbedding(
                scene_id=s.scene_id,
                timestamp=s.timestamp,
                thumb_key=s.thumb_key,
                caption=s.caption,
                tags=s.tags,
                text=doc,
                vector=vec,
            )
            for s, doc, vec in zip(scenes, documents, vectors, strict=False)
        ],
    )
    video_store.put_json(
        video_store.embeddings_key(video_id), index.model_dump(mode="json")
    )

    videos_svc.update_status(
        video_id,
        VideoStatus.ready,
        probe=probe,
        scene_count=len(scenes),
        people_count=people_count,
        clip_count=len(index.scenes),
    )
    logger.info(
        "Pipeline complete for %s: %d scenes, %d people",
        video_id,
        len(scenes),
        people_count,
    )


def _transcribe(video_id: str, local_video: str, probe: dict) -> Transcript:
    """Transcribe the audio track. Returns an empty transcript on failure so the
    visual + face signals still index (audio is one of three signals)."""
    try:
        audio_path = media.extract_audio(local_video)
        raw = transcription.transcribe(audio_path)
    except Exception:
        logger.warning("Transcription failed for %s; indexing visual signals only",
                       video_id, exc_info=True)
        return Transcript(
            video_id=video_id,
            duration_seconds=probe.get("duration_seconds"),
            segments=[],
        )
    transcript = Transcript(
        video_id=video_id,
        language=raw.get("language"),
        duration_seconds=raw.get("duration") or probe.get("duration_seconds"),
        segments=raw.get("segments", []),
    )
    video_store.put_json(
        video_store.transcript_key(video_id), transcript.model_dump(mode="json")
    )
    return transcript
