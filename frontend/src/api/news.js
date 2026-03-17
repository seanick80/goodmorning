import { apiFetch } from "./client";

export function fetchNews() {
  return apiFetch("/news/");
}
