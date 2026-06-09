"use client";

import { useState } from "react";
import { Users } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { PersonCard } from "@/components/people/person-card";
import { PersonClipsDialog } from "@/components/people/person-clips-dialog";
import { useFacesAvailable, usePeople } from "@/lib/queries";
import type { Person } from "@personal-video-ai-search/shared";

export default function PeoplePage() {
  const { data: people = [], isLoading, error, refetch } = usePeople();
  const { data: avail } = useFacesAvailable();
  const [active, setActive] = useState<Person | null>(null);

  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5">
        <h1 className="page-title">People</h1>
        <p className="text-sm text-muted-foreground mt-1.5">
          Faces clustered across your whole archive — entirely on-device, no AI
          key. Name a person (&ldquo;Grandma&rdquo;) and browse every clip they
          appear in. Backed by a face-cluster index stored in Backblaze B2.
        </p>
      </div>

      {avail && !avail.available ? (
        <Card>
          <CardContent className="p-0">
            <EmptyState
              icon={Users}
              title="Face indexing not available"
              description="Install the local face stack (insightface + onnxruntime) listed in services/api/requirements.txt, then re-index a video on the Library page."
            />
          </CardContent>
        </Card>
      ) : isLoading ? (
        <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="aspect-square w-full" />
          ))}
        </div>
      ) : error ? (
        <Card>
          <CardContent className="p-0">
            <ErrorState error={error} onRetry={() => refetch()} />
          </CardContent>
        </Card>
      ) : people.length === 0 ? (
        <Card>
          <CardContent className="p-0">
            <EmptyState
              icon={Users}
              title="No people yet"
              description="Add a video on the Library page. Once it reaches “Ready”, the people detected in it appear here."
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 animate-fade-in-up">
          {people.map((person) => (
            <PersonCard
              key={person.cluster_id}
              person={person}
              onOpenClips={setActive}
            />
          ))}
        </div>
      )}

      <PersonClipsDialog person={active} onOpenChange={(o) => !o && setActive(null)} />
    </div>
  );
}
