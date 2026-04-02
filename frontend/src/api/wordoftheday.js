import { apiFetch } from "./client";

export function fetchWordOfTheDay() {
  return apiFetch("/word-of-the-day/");
}
