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

function weatherDescription(code) {
  if (code === 0) return "Clear sky";
  if (code === 1) return "Mainly clear";
  if (code === 2) return "Partly cloudy";
  if (code === 3) return "Overcast";
  if (code <= 49) return "Foggy";
  if (code <= 59) return "Drizzle";
  if (code <= 69) return "Rain";
  if (code <= 79) return "Snow";
  if (code <= 82) return "Rain showers";
  if (code <= 86) return "Snow showers";
  if (code <= 99) return "Thunderstorm";
  return "Unknown";
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

  return (
    <WidgetCard title="Weather">
      <div className={styles.main}>
        <span className={styles.emoji}>
          {weatherEmoji(weather.weather_code)}
        </span>
        <div className={styles.temp}>
          {Math.round(weather.temperature)}
          <span className={styles.unit}>{unit}</span>
        </div>
      </div>

      <div className={styles.description}>
        {weather.weather_description ||
          weatherDescription(weather.weather_code)}
      </div>

      <div className={styles.details}>
        <div className={styles.detail}>
          <span className={styles.detailLabel}>Feels like</span>
          <span className={styles.detailValue}>
            {weather.feels_like != null
              ? `${Math.round(weather.feels_like)}${unit}`
              : "--"}
          </span>
        </div>
        <div className={styles.detail}>
          <span className={styles.detailLabel}>High / Low</span>
          <span className={styles.detailValue}>
            {weather.daily_high != null && weather.daily_low != null
              ? `${Math.round(weather.daily_high)}${unit} / ${Math.round(weather.daily_low)}${unit}`
              : "--"}
          </span>
        </div>
        <div className={styles.detail}>
          <span className={styles.detailLabel}>Humidity</span>
          <span className={styles.detailValue}>
            {weather.humidity != null ? `${weather.humidity}%` : "--"}
          </span>
        </div>
        {weather.sunrise && (
          <div className={styles.detail}>
            <span className={styles.detailLabel}>Sunrise / Sunset</span>
            <span className={styles.detailValue}>
              {weather.sunrise} / {weather.sunset || "--"}
            </span>
          </div>
        )}
      </div>
    </WidgetCard>
  );
}
