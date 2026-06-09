"use client";

import { useState } from "react";
import { KeyRound, Search as SearchIcon, Sparkles, Telescope } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { ClipCard } from "@/components/search/clip-card";
import { usePeople, useSearch } from "@/lib/queries";
import type { Clip } from "@personal-video-ai-search/shared";

const ANY_PERSON = "__any__";

export default function SearchPage() {
  const [question, setQuestion] = useState("");
  const [synthesize, setSynthesize] = useState(false);
  const [personId, setPersonId] = useState<string>(ANY_PERSON);
  const search = useSearch();
  const { data: people = [] } = usePeople();
  const namedPeople = people.filter((p) => p.name);

  const submit = () => {
    const q = question.trim();
    if (!q) return;
    search.mutate({
      question: q,
      synthesize,
      personId: personId === ANY_PERSON ? null : personId,
    });
  };

  const data = search.data;

  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5">
        <h1 className="page-title">Search</h1>
        <p className="text-sm text-muted-foreground mt-1.5">
          Ask in plain language — by what&apos;s said, what&apos;s on screen, or
          who&apos;s in it — and get back the exact clips, playable inline. Try
          &ldquo;the dog jumps in the pool&rdquo; or &ldquo;birthday cake&rdquo;.
        </p>
      </div>

      <Card>
        <CardContent className="p-5 space-y-4">
          <Textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. the dog jumps in the pool (⌘/Ctrl + Enter to search)"
            className="min-h-20"
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit();
            }}
          />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-4">
              {namedPeople.length > 0 && (
                <div className="flex items-center gap-2">
                  <Label className="text-muted-foreground">Person</Label>
                  <Select value={personId} onValueChange={setPersonId}>
                    <SelectTrigger className="h-8 w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={ANY_PERSON}>Anyone</SelectItem>
                      {namedPeople.map((p) => (
                        <SelectItem key={p.cluster_id} value={p.cluster_id}>
                          {p.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              <div className="flex items-center gap-2">
                <Switch
                  id="synthesize"
                  checked={synthesize}
                  onCheckedChange={setSynthesize}
                />
                <Label htmlFor="synthesize" className="text-muted-foreground">
                  <Sparkles className="h-3.5 w-3.5" />
                  Synthesize an answer (Claude)
                </Label>
              </div>
            </div>
            <Button onClick={submit} disabled={search.isPending || !question.trim()} size="sm">
              <SearchIcon className="h-3.5 w-3.5" />
              {search.isPending ? "Searching…" : "Search"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {search.isPending && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-64 w-full" />
          ))}
        </div>
      )}

      {search.error && !search.isPending && (
        <Card>
          <CardContent className="p-0">
            <ErrorState error={search.error} onRetry={submit} />
          </CardContent>
        </Card>
      )}

      {data && !search.isPending && (
        <SearchResults
          providerConfigured={data.provider_configured}
          answer={data.answer}
          clips={data.clips}
        />
      )}
    </div>
  );
}

function SearchResults({
  providerConfigured,
  answer,
  clips,
}: {
  providerConfigured: boolean;
  answer: string | null;
  clips: Clip[];
}) {
  if (!providerConfigured) {
    return (
      <Card>
        <CardContent className="p-0">
          <EmptyState
            icon={KeyRound}
            title="No AI provider configured"
            description="Set OPENAI_API_KEY in your .env and restart the API to enable multimodal search."
          />
        </CardContent>
      </Card>
    );
  }

  if (clips.length === 0) {
    return (
      <Card>
        <CardContent className="p-0">
          <EmptyState
            icon={Telescope}
            title="No matching clips"
            description="Add a video on the Library page, wait for it to reach “Ready”, then try a different query."
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {answer && (
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
              <Sparkles className="h-3.5 w-3.5" />
              Answer
            </div>
            <p className="text-sm whitespace-pre-wrap">{answer}</p>
          </CardContent>
        </Card>
      )}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {clips.map((clip) => (
          <ClipCard key={`${clip.video_id}-${clip.scene_id}`} clip={clip} />
        ))}
      </div>
    </div>
  );
}
