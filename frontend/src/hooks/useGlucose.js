import { useQuery } from "@tanstack/react-query";
import { fetchGlucose } from "../api/glucose";

export function useGlucose() {
  return useQuery({
    queryKey: ["glucose"],
    queryFn: fetchGlucose,
    refetchInterval: 60 * 1000,
  });
}
