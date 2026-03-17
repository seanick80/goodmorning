import { useWeather } from "../../hooks/useWeather";
import WidgetCard from "../WidgetCard";
import styles from "./WeatherWidget.module.css";

function weatherEmoji(code) {
  if (code === 0) return "\u2600\uFE0F";
  if (code <= 3) return "\u26C5";
  if (code <= 49) return "\uD83C\uDF2B\uFE0F";
  if (code <= 59) return "\uD83C\uDF27\uFE0F";
  if (code <= 69) return "\uD83C\uDF28\uFE0F";
  if (code <= 79) return "\u2744\uFE0F";
  if (code <= 82) return "\uD83C\uDF27\uFE0F";
  if (code <= 86) return "\uD83C\uDF28\uFE0F";
  if (code <= 99) return "\u26C8\uFE0F";
  return "\uD83C\uDF24\uFE0F";
}

function formatHour(timeStr) {
  if (!timeStr) return "";
  try {
    const d = new Date(timeStr);
    return d.toLocaleTimeString("en-US", { hour: "numeric", hour12: true });
  } catch {
    return timeStr;
  }
}

function formatTime12(timeStr) {
  if (!timeStr) return "";
  try {
    // Handle "HH:MM:SS" time-only strings by prepending today's date
    const d = timeStr.includes("T") ? new Date(timeStr) : new Date(`1970-01-01T${timeStr}`);
    return d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
  } catch {
    return timeStr;
  }
}

export default function WeatherWidget() {
  const { data, isLoading, isError, error } = useWeather();

  if (isLoading) {
    return (
      <WidgetCard title="Weather">
        <div className={styles.loading}>Loading weather...</div>
      </WidgetCard>
    );
  }

  if (isError) {
    return (
      <WidgetCard title="Weather">
        <div className={styles.error}>
          Unable to load weather data
          {error?.status === 404 && " (no data yet)"}
        </div>
      </WidgetCard>
    );
  }

  const weather = Array.isArray(data) ? data[0] : data;

  if (!weather) {
    return (
      <WidgetCard title="Weather">
        <div className={styles.error}>No weather data available</div>
      </WidgetCard>
    );
  }

  const unit = weather.temperature_unit === "celsius" ? "\u00B0C" : "\u00B0F";
  const forecast = weather.hourly_forecast || [];
  // Show next 6 hours from current time
  const now = new Date();
  const upcomingForecast = forecast
    .filter((h) => new Date(h.time) >= now)
    .slice(0, 6);
  // Fall back to last 6 entries if all are in the past
  const displayForecast =
    upcomingForecast.length > 0 ? upcomingForecast : forecast.slice(-6);

  return (
    <WidgetCard title={weather.location_name || "Weather"}>
      <div className={styles.current}>
        <span className={styles.emoji}>
          {weatherEmoji(weather.weather_code)}
        </span>
        <div className={styles.temp}>
          {Math.round(weather.temperature)}
          <span className={styles.unit}>{unit}</span>
        </div>
        <div className={styles.currentDetails}>
          <span className={styles.description}>
            {weather.weather_description || ""}
          </span>
          <span className={styles.highLow}>
            {weather.daily_high != null &&
              `H:${Math.round(weather.daily_high)}${unit}`}
            {weather.daily_low != null &&
              ` L:${Math.round(weather.daily_low)}${unit}`}
          </span>
          {weather.feels_like != null && (
            <span className={styles.feelsLike}>
              Feels like {Math.round(weather.feels_like)}
              {unit}
            </span>
          )}
        </div>
      </div>

      {displayForecast.length > 0 && (
        <div className={styles.forecastBar}>
          {displayForecast.map((h, i) => (
            <div key={i} className={styles.forecastHour}>
              <span className={styles.forecastHourLabel}>
                {formatHour(h.time)}
              </span>
              <span className={styles.forecastHourEmoji}>
                {weatherEmoji(h.code ?? h.weather_code)}
              </span>
              <span className={styles.forecastHourTemp}>
                {Math.round(h.temp)}
                {unit}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className={styles.sunRow}>
        {weather.sunrise && <span>&#x1F305; {formatTime12(weather.sunrise)}</span>}
        {weather.sunset && <span>&#x1F307; {formatTime12(weather.sunset)}</span>}
        {weather.humidity != null && <span>&#x1F4A7; {weather.humidity}%</span>}
      </div>
    </WidgetCard>
  );
}
