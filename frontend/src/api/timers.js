import { apiFetch } from "./client";

export function fetchTimers() {
  return apiFetch("/timers/");
}

export function createTimer(durationSeconds, label = "") {
  return apiFetch("/timers/", {
    method: "POST",
    body: JSON.stringify({ duration_seconds: durationSeconds, label }),
  });
}

export function cancelTimer(timerId) {
  return apiFetch(`/timers/${timerId}/`, { method: "DELETE" });
}

export function dismissTimers() {
  return apiFetch("/timers/dismiss/", { method: "POST" });
}
