import { useQuery } from "@tanstack/react-query";
import { fetchWeather } from "../api/weather";

export function useWeather() {
  return useQuery({
    queryKey: ["weather"],
    queryFn: fetchWeather,
    refetchInterval: 5 * 60 * 1000,
  });
}
