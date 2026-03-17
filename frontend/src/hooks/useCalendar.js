import { useQuery } from "@tanstack/react-query";
import { fetchCalendar } from "../api/calendar";

export function useCalendar() {
  return useQuery({
    queryKey: ["calendar"],
    queryFn: fetchCalendar,
    refetchInterval: 10 * 60 * 1000,
  });
}
