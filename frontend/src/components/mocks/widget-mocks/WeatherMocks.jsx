import WidgetCard from "../../WidgetCard";
import { mockWeather, mockHourlyForecast } from "../mockData";
import styles from "./WeatherMocks.module.css";

const unit = mockWeather.temperature_unit === "celsius" ? "\u00B0C" : "\u00B0F";

function weatherEmoji(code) {
  if (code === 0) return "\u2600\uFE0F";
  if (code <= 3) return "\u26C5";
  if (code <= 49) return "\uD83C\uDF2B\uFE0F";
  if (code <= 59) return "\uD83C\uDF27\uFE0F";
  return "\uD83C\uDF24\uFE0F";
}

function VariantCompact() {
  const w = mockWeather;
  return (
    <WidgetCard title="Weather">
      <div className={styles.compactMain}>
        <span className={styles.compactEmoji}>{weatherEmoji(w.weather_code)}</span>
        <div className={styles.compactTemp}>
          {Math.round(w.temperature)}
          <span className={styles.compactUnit}>{unit}</span>
        </div>
      </div>
      <div className={styles.compactDesc}>{w.weather_description}</div>
      <div className={styles.compactDetails}>
        <span>H: {Math.round(w.daily_high)}{unit}</span>
        <span>L: {Math.round(w.daily_low)}{unit}</span>
        <span>Humidity: {w.humidity}%</span>
      </div>
    </WidgetCard>
  );
}

function VariantFullPanel() {
  const w = mockWeather;
  return (
    <WidgetCard title="Weather">
      <div className={styles.fullMain}>
        <span className={styles.fullEmoji}>{weatherEmoji(w.weather_code)}</span>
        <div className={styles.fullTempBlock}>
          <div className={styles.fullTemp}>
            {Math.round(w.temperature)}
            <span className={styles.fullUnit}>{unit}</span>
          </div>
          <div className={styles.fullDesc}>{w.weather_description}</div>
        </div>
      </div>
      <div className={styles.fullGrid}>
        <div className={styles.fullDetail}>
          <span className={styles.fullDetailLabel}>Feels Like</span>
          <span className={styles.fullDetailValue}>{Math.round(w.feels_like)}{unit}</span>
        </div>
        <div className={styles.fullDetail}>
          <span className={styles.fullDetailLabel}>Humidity</span>
          <span className={styles.fullDetailValue}>{w.humidity}%</span>
        </div>
        <div className={styles.fullDetail}>
          <span className={styles.fullDetailLabel}>Sunrise</span>
          <span className={styles.fullDetailValue}>{w.sunrise}</span>
        </div>
        <div className={styles.fullDetail}>
          <span className={styles.fullDetailLabel}>Sunset</span>
          <span className={styles.fullDetailValue}>{w.sunset}</span>
        </div>
        <div className={styles.fullDetail}>
          <span className={styles.fullDetailLabel}>High</span>
          <span className={styles.fullDetailValue}>{Math.round(w.daily_high)}{unit}</span>
        </div>
        <div className={styles.fullDetail}>
          <span className={styles.fullDetailLabel}>Low</span>
          <span className={styles.fullDetailValue}>{Math.round(w.daily_low)}{unit}</span>
        </div>
      </div>
    </WidgetCard>
  );
}

function VariantMinimalStrip() {
  const w = mockWeather;
  return (
    <WidgetCard>
      <div className={styles.stripRow}>
        <span className={styles.stripEmoji}>{weatherEmoji(w.weather_code)}</span>
        <span className={styles.stripTemp}>{Math.round(w.temperature)}{unit}</span>
        <span className={styles.stripDesc}>{w.weather_description}</span>
        <span className={styles.stripHighLow}>
          {Math.round(w.daily_high)}{unit} / {Math.round(w.daily_low)}{unit}
        </span>
      </div>
    </WidgetCard>
  );
}

function VariantForecast() {
  const w = mockWeather;
  return (
    <WidgetCard title="Weather">
      <div className={styles.forecastCurrent}>
        <span className={styles.forecastEmoji}>{weatherEmoji(w.weather_code)}</span>
        <div className={styles.forecastTemp}>
          {Math.round(w.temperature)}
          <span className={styles.forecastUnit}>{unit}</span>
        </div>
        <div className={styles.forecastDesc}>{w.weather_description}</div>
      </div>
      <div className={styles.forecastBar}>
        {mockHourlyForecast.map((h, i) => (
          <div key={i} className={styles.forecastHour}>
            <span className={styles.forecastHourLabel}>{h.time}</span>
            <span className={styles.forecastHourEmoji}>{weatherEmoji(h.code)}</span>
            <span className={styles.forecastHourTemp}>{h.temp}{unit}</span>
          </div>
        ))}
      </div>
      <div className={styles.forecastSun}>
        <span>&#x1F305; {w.sunrise}</span>
        <span>&#x1F307; {w.sunset}</span>
      </div>
    </WidgetCard>
  );
}

export default function WeatherMocks() {
  return (
    <div className={styles.grid}>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant A: Compact Card</div>
        <VariantCompact />
      </div>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant B: Full Panel</div>
        <VariantFullPanel />
      </div>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant C: Minimal Strip</div>
        <VariantMinimalStrip />
      </div>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant D: Forecast Focus</div>
        <VariantForecast />
      </div>
    </div>
  );
}
