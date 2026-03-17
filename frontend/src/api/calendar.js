import { apiFetch } from "./client";

export function fetchCalendar() {
  return apiFetch("/calendar/");
}
