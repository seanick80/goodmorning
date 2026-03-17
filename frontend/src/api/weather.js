import { apiFetch } from "./client";

export function fetchWeather() {
  return apiFetch("/weather/");
}
