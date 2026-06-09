"use client";

import { Film } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { ClipCard } from "@/components/search/clip-card";
import { usePersonClips } from "@/lib/queries";
import type { Person } from "@personal-video-ai-search/shared";

export function PersonClipsDialog({
  person,
  onOpenChange,
}: {
  person: Person | null;
  onOpenChange: (open: boolean) => void;
}) {
  const { data: clips = [], isLoading, error, refetch } = usePersonClips(
    person?.cluster_id,
    !!person,
  );

  return (
    <Dialog open={!!person} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>{person?.name ?? "Unnamed person"}</DialogTitle>
          <DialogDescription>
            Every clip this person appears in, across your archive — playable
            inline by seeking the original in B2.
          </DialogDescription>
        </DialogHeader>
        <div className="max-h-[70vh] overflow-y-auto">
          {isLoading ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-56 w-full" />
              ))}
            </div>
          ) : error ? (
            <ErrorState error={error} onRetry={() => refetch()} />
          ) : clips.length === 0 ? (
            <EmptyState
              icon={Film}
              title="No clips"
              description="This person has no indexed appearances yet."
            />
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {clips.map((clip) => (
                <ClipCard key={`${clip.video_id}-${clip.scene_id}`} clip={clip} />
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
