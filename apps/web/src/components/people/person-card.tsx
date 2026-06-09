"use client";

import { useState } from "react";
import { Check, Pencil, UserRound } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useNamePerson } from "@/lib/queries";
import type { Person } from "@personal-video-ai-search/shared";

export function PersonCard({
  person,
  onOpenClips,
}: {
  person: Person;
  onOpenClips: (person: Person) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(person.name ?? "");
  const rename = useNamePerson();

  const save = () => {
    rename.mutate(
      { clusterId: person.cluster_id, name: name.trim() },
      {
        onSuccess: () => {
          setEditing(false);
          toast.success(name.trim() ? `Named "${name.trim()}"` : "Name cleared");
        },
        onError: (e) =>
          toast.error(e instanceof Error ? e.message : "Could not save name"),
      },
    );
  };

  return (
    <Card className="overflow-hidden card-hover">
      <button
        type="button"
        onClick={() => onOpenClips(person)}
        className="block w-full aspect-square bg-muted"
        title="View clips"
      >
        {person.cover_thumb_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={person.cover_thumb_url}
            alt={person.name ?? "Unnamed person"}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center">
            <UserRound className="h-10 w-10 text-muted-foreground" />
          </div>
        )}
      </button>
      <CardContent className="p-3 space-y-2">
        {editing ? (
          <div className="flex items-center gap-1.5">
            <Input
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && save()}
              placeholder="e.g. Grandma"
              className="h-8"
            />
            <Button size="icon" className="h-8 w-8" onClick={save} disabled={rename.isPending}>
              <Check className="h-3.5 w-3.5" />
            </Button>
          </div>
        ) : (
          <div className="flex items-center justify-between gap-2">
            <span className="font-medium truncate">
              {person.name ?? "Unnamed person"}
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 shrink-0"
              title="Name this person"
              onClick={() => setEditing(true)}
            >
              <Pencil className="h-3.5 w-3.5" />
            </Button>
          </div>
        )}
        <p className="text-xs text-muted-foreground tabular-nums">
          {person.face_count} appearance{person.face_count === 1 ? "" : "s"} ·{" "}
          {person.video_count} video{person.video_count === 1 ? "" : "s"}
        </p>
      </CardContent>
    </Card>
  );
}
