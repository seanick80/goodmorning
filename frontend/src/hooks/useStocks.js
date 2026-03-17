import { useQuery } from "@tanstack/react-query";
import { fetchStocks } from "../api/stocks";

export function useStocks() {
  return useQuery({
    queryKey: ["stocks"],
    queryFn: fetchStocks,
    refetchInterval: 60 * 1000,
  });
}
