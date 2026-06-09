"use client";

import { Clock, Film, HardDrive, Users } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { useFileStats, usePeople, useVideos } from "@/lib/queries";

export function StatsCards() {
  const { data: videos = [], isLoading: videosLoading, error, refetch } = useVideos();
  const { data: stats, isLoading: statsLoading } = useFileStats();
  const { data: people = [] } = usePeople();

  // Surface fetch failures inline rather than rendering zeros — that would
  // lie about the archive state when the API is really just unreachable.
  if (error) {
    return (
      <Card>
        <CardContent className="p-0">
          <ErrorState error={error} onRetry={() => refetch()} />
        </CardContent>
      </Card>
    );
  }

  const ready = videos.filter((v) => v.status === "ready").length;
  const hours = (
    videos.reduce((sum, v) => sum + (v.duration_seconds ?? 0), 0) / 3600
  ).toFixed(1);

  const cards = [
    { title: "Videos Indexed", value: ready, icon: Film, loading: videosLoading },
    {
      title: "Hours of Footage",
      value: hours,
      icon: Clock,
      loading: videosLoading,
    },
    {
      title: "People Identified",
      value: people.length,
      icon: Users,
      loading: videosLoading,
    },
    {
      title: "Storage Used",
      value: stats?.total_size_human ?? "0 B",
      icon: HardDrive,
      loading: statsLoading,
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card, i) => (
        <Card
          key={card.title}
          className={`card-hover animate-fade-in-up stagger-${i + 1}`}
        >
          <CardHeader className="flex flex-row items-center justify-between pt-4 pb-2 px-4 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground">
              {card.title}
            </CardTitle>
            <div className="stat-icon-wrap">
              <card.icon className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent className="pb-5 px-4">
            {card.loading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <div className="stat-value">{card.value}</div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
