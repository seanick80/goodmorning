import { apiFetch } from "./client";

export function fetchDashboard() {
  return apiFetch("/dashboard/");
}
