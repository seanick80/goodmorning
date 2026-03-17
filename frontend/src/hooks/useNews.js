import { useQuery } from "@tanstack/react-query";
import { fetchNews } from "../api/news";

export function useNews() {
  return useQuery({
    queryKey: ["news"],
    queryFn: fetchNews,
    refetchInterval: 5 * 60 * 1000,
  });
}
