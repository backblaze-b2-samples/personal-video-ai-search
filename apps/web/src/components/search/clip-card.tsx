"use client";

import { useState } from "react";
import { Play, Users } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { formatTimestamp } from "@/lib/utils";
import type { Clip } from "@personal-video-ai-search/shared";

export function ClipCard({ clip }: { clip: Clip }) {
  const [playing, setPlaying] = useState(false);

  // Media fragment (#t=start) tells the browser to seek straight to this
  // moment in the original — no clip file is generated; we seek the source
  // video in B2 over a presigned, Range-capable URL.
  const src = clip.playback_url
    ? `${clip.playback_url}#t=${clip.timestamp.toFixed(2)}`
    : null;

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4 space-y-3">
        <div className="flex items-center justify-between gap-2">
          <span className="font-medium truncate">{clip.title}</span>
          <Badge variant="secondary" className="font-mono tabular-nums shrink-0">
            {formatTimestamp(clip.timestamp)}
          </Badge>
        </div>

        {playing && src ? (
          <video
            autoPlay
            controls
            preload="metadata"
            className="w-full rounded-md border border-border bg-black aspect-video"
            src={src}
          />
        ) : (
          <button
            type="button"
            onClick={() => src && setPlaying(true)}
            disabled={!src}
            className="group relative block w-full overflow-hidden rounded-md border border-border bg-muted aspect-video disabled:cursor-not-allowed"
          >
            {clip.thumb_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={clip.thumb_url}
                alt={clip.caption || "scene thumbnail"}
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="h-full w-full" />
            )}
            <span className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 transition-opacity group-hover:opacity-100">
              <Play className="h-8 w-8 text-white" />
            </span>
          </button>
        )}

        {clip.caption && (
          <p className="text-sm text-muted-foreground line-clamp-3">{clip.caption}</p>
        )}

        <div className="flex flex-wrap gap-1.5">
          {clip.people.map((name) => (
            <Badge key={name} variant="outline" className="gap-1">
              <Users className="h-3 w-3" />
              {name}
            </Badge>
          ))}
          {clip.tags.slice(0, 4).map((tag) => (
            <Badge key={tag} variant="secondary" className="font-normal">
              {tag}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
