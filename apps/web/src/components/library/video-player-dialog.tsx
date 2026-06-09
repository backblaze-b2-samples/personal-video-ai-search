"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useVideoPlayback } from "@/lib/queries";
import type { Video } from "@personal-video-ai-search/shared";

/**
 * Watch an ingested video inline. Fetches a presigned GET URL for the original
 * in B2 (only while open) and streams it through a native <video> element —
 * the browser issues Range requests, so seeking pulls just the bytes it needs
 * rather than downloading the whole (multi-GB) source. The same presigned,
 * Range-capable read path the Search/People clip players use, here for the
 * full source instead of a seek-to-timestamp.
 */
export function VideoPlayerDialog({
  video,
  onOpenChange,
}: {
  video: Video | null;
  onOpenChange: (open: boolean) => void;
}) {
  const { data, isLoading, error, refetch } = useVideoPlayback(
    video?.video_id,
    !!video,
  );

  return (
    <Dialog open={!!video} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle className="truncate pr-6">{video?.title}</DialogTitle>
        </DialogHeader>
        {isLoading ? (
          <Skeleton className="aspect-video w-full rounded-md" />
        ) : error ? (
          <ErrorState error={error} onRetry={() => refetch()} />
        ) : data?.url ? (
          <video
            autoPlay
            controls
            preload="metadata"
            className="aspect-video w-full rounded-md border border-border bg-black"
            src={data.url}
          />
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
