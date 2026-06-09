import { Loader2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { VideoStatus } from "@personal-video-ai-search/shared";

const PROCESSING = new Set<VideoStatus>([
  "uploading",
  "probing",
  "transcribing",
  "tagging",
  "clustering",
  "embedding",
]);

const LABELS: Record<VideoStatus, string> = {
  uploading: "Uploading",
  uploaded: "Uploaded",
  probing: "Probing",
  transcribing: "Transcribing",
  tagging: "Tagging scenes",
  clustering: "Clustering faces",
  embedding: "Embedding",
  ready: "Ready",
  failed: "Failed",
};

function variantFor(status: VideoStatus): "default" | "secondary" | "destructive" {
  if (status === "ready") return "default";
  if (status === "failed") return "destructive";
  return "secondary";
}

export function StatusBadge({ status }: { status: VideoStatus }) {
  return (
    <Badge variant={variantFor(status)}>
      {PROCESSING.has(status) && <Loader2 className="animate-spin" />}
      {LABELS[status]}
    </Badge>
  );
}
