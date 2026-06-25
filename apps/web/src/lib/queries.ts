"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ApiError,
  deleteFile,
  deleteVideo,
  getFacesAvailable,
  getFiles,
  getFileStats,
  getPeople,
  getPersonClips,
  getPreviewUrl,
  getUploadActivity,
  getVideoPlayback,
  getVideos,
  ingestVideo,
  namePerson,
  reindexVideo,
  searchVideos,
  type SearchOptions,
} from "@/lib/api-client";
import type { FileMetadata, Person, Video } from "@personal-video-ai-search/shared";

// Single source of truth for query keys. Keep these tightly scoped so that
// invalidating "files" doesn't blow away unrelated caches, and so an IDE
// "find usages" of `qk.files` reveals every consumer.
export const qk = {
  all: ["b2"] as const,
  files: (prefix?: string, limit?: number) =>
    [...qk.all, "files", prefix ?? "", limit ?? 100] as const,
  stats: () => [...qk.all, "stats"] as const,
  uploadActivity: (days: number) =>
    [...qk.all, "stats", "activity", days] as const,
  preview: (key: string) => [...qk.all, "preview", key] as const,
  videos: () => [...qk.all, "videos"] as const,
  video: (id: string) => [...qk.all, "videos", id] as const,
  videoPlayback: (id: string) => [...qk.all, "videos", id, "playback"] as const,
  people: () => [...qk.all, "people"] as const,
  facesAvailable: () => [...qk.all, "people", "available"] as const,
  personClips: (id: string) => [...qk.all, "people", id, "clips"] as const,
};

export function useFiles(prefix = "", limit = 100) {
  return useQuery<FileMetadata[], ApiError>({
    queryKey: qk.files(prefix, limit),
    queryFn: () => getFiles(prefix, limit),
  });
}

export function useFileStats() {
  return useQuery({
    queryKey: qk.stats(),
    queryFn: getFileStats,
  });
}

export function useUploadActivity(days = 7) {
  return useQuery({
    queryKey: qk.uploadActivity(days),
    queryFn: () => getUploadActivity(days),
  });
}

// Presigned preview URL — only fetched when `enabled` is true (e.g., when
// the dialog opens for a specific file). Kept short-lived (60s) because
// the URL itself has a presigned expiry and is cheap to regenerate.
export function usePreviewUrl(key: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: qk.preview(key ?? ""),
    queryFn: () => getPreviewUrl(key as string),
    enabled: enabled && !!key,
    staleTime: 60_000,
  });
}

export function useDeleteFile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (fileKey: string) => deleteFile(fileKey),
    // After delete, blow away every cached file list + stats. Cheap and
    // correct — the dashboard re-fetches lazily as components remount.
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.all });
    },
  });
}

// --- Video pipeline ---------------------------------------------------------

const PROCESSING: ReadonlySet<string> = new Set([
  "uploading",
  "probing",
  "transcribing",
  "tagging",
  "clustering",
  "embedding",
]);

export function useVideos() {
  return useQuery<Video[], ApiError>({
    queryKey: qk.videos(),
    queryFn: getVideos,
    // Poll while anything is mid-pipeline so the Library reflects progress.
    refetchInterval: (query) =>
      query.state.data?.some((v) => PROCESSING.has(v.status)) ? 4000 : false,
  });
}

export function useIngestVideo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { file: File; onProgress?: (percent: number) => void }) =>
      ingestVideo(vars.file, vars.onProgress),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.videos() }),
  });
}

export function useDeleteVideo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (videoId: string) => deleteVideo(videoId),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.all }),
  });
}

// Presigned playback URL for a video's original source in B2 — fetched only
// while the player dialog is open (`enabled`). Kept short-lived (60s) because
// the URL carries its own presigned expiry and is cheap to regenerate. The
// <video> element streams it over Range requests, so seeking pulls only the
// bytes it needs rather than downloading the whole (multi-GB) source.
export function useVideoPlayback(videoId: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: qk.videoPlayback(videoId ?? ""),
    queryFn: () => getVideoPlayback(videoId as string),
    enabled: enabled && !!videoId,
    staleTime: 60_000,
  });
}

export function useReindexVideo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (videoId: string) => reindexVideo(videoId),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.videos() }),
  });
}

export function useSearch() {
  return useMutation({
    mutationFn: ({ question, ...opts }: SearchOptions & { question: string }) =>
      searchVideos(question, opts),
  });
}

// --- People (face clusters) -------------------------------------------------

export function usePeople() {
  return useQuery<Person[], ApiError>({
    queryKey: qk.people(),
    queryFn: getPeople,
  });
}

export function useFacesAvailable() {
  return useQuery({
    queryKey: qk.facesAvailable(),
    queryFn: getFacesAvailable,
    staleTime: Infinity,
  });
}

export function usePersonClips(clusterId: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: qk.personClips(clusterId ?? ""),
    queryFn: () => getPersonClips(clusterId as string),
    enabled: enabled && !!clusterId,
  });
}

export function useNamePerson() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { clusterId: string; name: string }) =>
      namePerson(vars.clusterId, vars.name),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.people() }),
  });
}
