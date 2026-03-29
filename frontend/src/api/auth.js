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

export function patchDashboard(data) {
  return apiFetch("/dashboard/", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
