export type FileStatus = "uploading" | "complete" | "error";

export interface FileMetadata {
  key: string;
  filename: string;
  folder: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
  url: string | null;
}

export interface FileMetadataDetail {
  filename: string;
  size_bytes: number;
  size_human: string;
  mime_type: string;
  extension: string;
  md5: string;
  sha256: string;
  uploaded_at: string;
  // Video/audio probe (ffprobe)
  duration_seconds: number | null;
  width: number | null;
  height: number | null;
  fps: number | null;
  codec: string | null;
  bitrate: number | null;
}

export interface FileUploadResponse {
  key: string;
  filename: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
  url: string | null;
  metadata: FileMetadataDetail | null;
}

export interface DailyUploadCount {
  date: string;
  uploads: number;
}

export interface UploadStats {
  total_files: number;
  total_size_bytes: number;
  total_size_human: string;
  uploads_today: number;
  total_downloads: number;
}

// --- Video pipeline ---------------------------------------------------------

export type VideoStatus =
  | "uploading"
  | "uploaded"
  | "probing"
  | "transcribing"
  | "tagging"
  | "clustering"
  | "embedding"
  | "ready"
  | "failed";

export interface Video {
  video_id: string;
  title: string;
  status: VideoStatus;
  source_key: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  created_at: string;
  duration_seconds: number | null;
  width: number | null;
  height: number | null;
  fps: number | null;
  codec: string | null;
  scene_count: number | null;
  people_count: number | null;
  clip_count: number | null;
  error: string | null;
}

export interface PresignedPart {
  part_number: number;
  url: string;
}

export interface MultipartUpload {
  video_id: string;
  source_key: string;
  upload_id: string;
  part_size: number;
  parts: PresignedPart[];
}

export interface CompletedPart {
  part_number: number;
  etag: string;
}

// --- Search -----------------------------------------------------------------

export interface Clip {
  video_id: string;
  title: string;
  scene_id: string;
  timestamp: number;
  caption: string;
  tags: string[];
  score: number;
  thumb_url: string | null;
  playback_url: string | null;
  people: string[];
}

export interface SearchResponse {
  question: string;
  clips: Clip[];
  answer: string | null;
  provider_configured: boolean;
}

// --- People (face clusters) -------------------------------------------------

export interface Person {
  cluster_id: string;
  name: string | null;
  face_count: number;
  video_count: number;
  cover_thumb_url: string | null;
}
