import { useQuery } from "@tanstack/react-query";
import { fetchAuthStatus } from "../api/auth";

export function useAuth() {
  return useQuery({
    queryKey: ["authStatus"],
    queryFn: fetchAuthStatus,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}
