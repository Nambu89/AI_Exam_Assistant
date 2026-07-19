import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: ({ signal }) => api.health(signal),
    staleTime: 60_000,
  });
}

export function useTopics() {
  return useQuery({
    queryKey: ["topics"],
    queryFn: ({ signal }) => api.topics(signal),
    staleTime: 5 * 60_000,
  });
}

export function useConceptMap(subject: string) {
  return useQuery({
    queryKey: ["concept-map", subject],
    queryFn: ({ signal }) => api.conceptMap(subject, 1, signal),
    staleTime: 5 * 60_000,
    enabled: Boolean(subject),
  });
}
