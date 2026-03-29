import { apiFetch } from "./client";

export function fetchAuthStatus() {
  return apiFetch("/auth/status/");
}

export function fetchGoogleCalendars() {
  return apiFetch("/auth/google/calendars/");
}

export function fetchGooglePhotosAlbums() {
  return apiFetch("/auth/google/photos/albums/");
}

export function createPhotosPickerSession() {
  return apiFetch("/auth/google/photos/picker/", { method: "POST" });
}

export function pollPhotosPickerSession(sessionId) {
  return apiFetch(`/auth/google/photos/picker/${sessionId}/`);
}

export function fetchPhotosPickerMedia(sessionId) {
  return apiFetch(`/auth/google/photos/picker/${sessionId}/media/`);
}

export function patchDashboard(data) {
  return apiFetch("/dashboard/", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
