import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import WeatherWidget from "../WeatherWidget";

vi.mock("../../../hooks/useWeather", () => ({
  useWeather: vi.fn(),
}));
vi.mock("../../StaleIndicator", () => ({
  default: () => null,
}));
vi.mock("../LocationSelector", () => ({
  default: () => null,
}));

import { useWeather } from "../../../hooks/useWeather";

const mockWeather = {
  location_name: "Seattle",
  temperature: 58.2,
  temperature_unit: "fahrenheit",
  feels_like: 55.0,
  humidity: 72,
  wind_speed: 8,
  wind_direction: 180,
  weather_code: 0,
  weather_description: "Clear sky",
  precipitation_probability: 10,
  sunrise: "06:30:00",
  sunset: "19:45:00",
  daily_high: 62,
  daily_low: 48,
  hourly_forecast: [],
  fetched_at: new Date().toISOString(),
};

describe("WeatherWidget", () => {
  it("shows loading state", () => {
    (useWeather as ReturnType<typeof vi.fn>).mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
    });
    render(<WeatherWidget />);
    expect(screen.getByText("Loading weather...")).toBeInTheDocument();
  });

  it("shows error state", () => {
    (useWeather as ReturnType<typeof vi.fn>).mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: {},
    });
    render(<WeatherWidget />);
    expect(screen.getByText(/Unable to load weather/)).toBeInTheDocument();
  });

  it("renders current temperature", () => {
    (useWeather as ReturnType<typeof vi.fn>).mockReturnValue({
      data: mockWeather,
      isLoading: false,
      isError: false,
    });
    render(<WeatherWidget />);
    expect(screen.getByText("58")).toBeInTheDocument();
    expect(screen.getByText("°F")).toBeInTheDocument();
  });

  it("renders location name as title", () => {
    (useWeather as ReturnType<typeof vi.fn>).mockReturnValue({
      data: mockWeather,
      isLoading: false,
      isError: false,
    });
    render(<WeatherWidget />);
    expect(screen.getByText("Seattle")).toBeInTheDocument();
  });

  it("renders high/low temperatures", () => {
    (useWeather as ReturnType<typeof vi.fn>).mockReturnValue({
      data: mockWeather,
      isLoading: false,
      isError: false,
    });
    render(<WeatherWidget />);
    expect(screen.getByText(/H:62°F/)).toBeInTheDocument();
    expect(screen.getByText(/L:48°F/)).toBeInTheDocument();
  });

  it("renders feels like", () => {
    (useWeather as ReturnType<typeof vi.fn>).mockReturnValue({
      data: mockWeather,
      isLoading: false,
      isError: false,
    });
    render(<WeatherWidget />);
    expect(screen.getByText(/Feels like 55/)).toBeInTheDocument();
  });

  it("renders sun emoji for clear sky (code 0)", () => {
    (useWeather as ReturnType<typeof vi.fn>).mockReturnValue({
      data: { ...mockWeather, weather_code: 0 },
      isLoading: false,
      isError: false,
    });
    render(<WeatherWidget />);
    expect(screen.getByText("☀️")).toBeInTheDocument();
  });

  it("renders cloud emoji for cloudy (code 2)", () => {
    (useWeather as ReturnType<typeof vi.fn>).mockReturnValue({
      data: { ...mockWeather, weather_code: 2 },
      isLoading: false,
      isError: false,
    });
    render(<WeatherWidget />);
    expect(screen.getByText("⛅")).toBeInTheDocument();
  });

  it("renders humidity", () => {
    (useWeather as ReturnType<typeof vi.fn>).mockReturnValue({
      data: mockWeather,
      isLoading: false,
      isError: false,
    });
    render(<WeatherWidget />);
    expect(screen.getByText("72% humidity")).toBeInTheDocument();
  });

  it("handles array data format", () => {
    (useWeather as ReturnType<typeof vi.fn>).mockReturnValue({
      data: [mockWeather],
      isLoading: false,
      isError: false,
    });
    render(<WeatherWidget />);
    expect(screen.getByText("58")).toBeInTheDocument();
  });
});
