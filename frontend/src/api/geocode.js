import { apiFetch } from "./client";

export function searchLocations(query) {
  return apiFetch(`/geocode/?q=${encodeURIComponent(query)}`);
}

export function updateWeatherLocation(latitude, longitude, locationName) {
  return apiFetch("/weather/location/", {
    method: "POST",
    body: JSON.stringify({
      latitude,
      longitude,
      location_name: locationName,
    }),
  });
}
