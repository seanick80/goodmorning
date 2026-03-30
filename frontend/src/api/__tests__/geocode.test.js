import { describe, it, expect, vi } from 'vitest';
import { apiFetch } from '../client';
import { searchLocations, updateWeatherLocation } from '../geocode';

vi.mock('../client', () => ({
  apiFetch: vi.fn(),
}));

describe('geocode API', () => {
  it('searchLocations encodes the query parameter', () => {
    searchLocations('New York');
    expect(apiFetch).toHaveBeenCalledWith('/geocode/?q=New%20York');
  });

  it('searchLocations handles special characters', () => {
    searchLocations('München & Zürich');
    expect(apiFetch).toHaveBeenCalledWith(
      '/geocode/?q=M%C3%BCnchen%20%26%20Z%C3%BCrich',
    );
  });

  it('updateWeatherLocation sends POST with lat/lon/name', () => {
    updateWeatherLocation(47.6, -122.3, 'Seattle');
    expect(apiFetch).toHaveBeenCalledWith('/weather/location/', {
      method: 'POST',
      body: JSON.stringify({
        latitude: 47.6,
        longitude: -122.3,
        location_name: 'Seattle',
      }),
    });
  });
});
