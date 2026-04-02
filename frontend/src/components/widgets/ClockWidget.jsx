import { useState, useEffect } from "react";
import styles from "./ClockWidget.module.css";

const DEFAULT_SETTINGS = {
  primary: {
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    label: "Local",
  },
  aux: [],
  format: "12h",
};

function isValidTimezone(tz) {
  try {
    Intl.DateTimeFormat("en-US", { timeZone: tz });
    return true;
  } catch {
    return false;
  }
}

function getGreeting(hour) {
  if (hour >= 5 && hour < 12) return "Good Morning";
  if (hour >= 12 && hour < 17) return "Good Afternoon";
  return "Good Evening";
}

function formatTime(date, timezone, hour12) {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12,
    timeZone: timezone,
  }).format(date);
}

function formatAuxTime(date, timezone, hour12) {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12,
    timeZone: timezone,
  }).format(date);
}

function formatDate(date, timezone) {
  return new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: timezone,
  }).format(date);
}

function getHourInTimezone(date, timezone) {
  const parts = new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    hour12: false,
    timeZone: timezone,
  }).formatToParts(date);
  const hourPart = parts.find((p) => p.type === "hour");
  return parseInt(hourPart.value, 10);
}

export default function ClockWidget({ settings }) {
  const config = {
    ...DEFAULT_SETTINGS,
    ...settings,
    primary: { ...DEFAULT_SETTINGS.primary, ...settings?.primary },
    aux: (settings?.aux ?? DEFAULT_SETTINGS.aux).filter(
      (c) => c.timezone && isValidTimezone(c.timezone),
    ),
  };
  const hour12 = config.format !== "24h";
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const primaryTz = config.primary.timezone;
  const primaryHour = getHourInTimezone(now, primaryTz);
  const greeting = getGreeting(primaryHour);
  const timeStr = formatTime(now, primaryTz, hour12);
  const dateStr = formatDate(now, primaryTz);

  return (
    <div className={styles.clock}>
      <div className={styles.greeting}>{greeting}</div>
      <div className={styles.primaryTime}>{timeStr}</div>
      <div className={styles.primaryLabel}>{config.primary.label}</div>
      <div className={styles.date}>{dateStr}</div>

      {config.aux && config.aux.length > 0 && (
        <>
          <div className={styles.divider} />
          <div className={styles.auxRow}>
            {config.aux.map((clock) => (
              <div key={clock.timezone} className={styles.auxClock}>
                <div className={styles.auxLabel}>{clock.label}</div>
                <div className={styles.auxTime}>
                  {formatAuxTime(now, clock.timezone, hour12)}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
