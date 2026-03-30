import { apiFetch } from "./client";

export function fetchGlucose() {
  return apiFetch("/glucose/");
}
