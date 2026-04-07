import { apiFetch } from "./client";

export function fetchWordOfTheDay(today) {
  return apiFetch(`/word-of-the-day/?date=${today}`);
}
