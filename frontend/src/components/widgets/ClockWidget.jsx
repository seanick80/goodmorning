import { useState, useEffect, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchTimers, cancelTimer, dismissTimers } from "../../api/timers";
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

function formatCountdown(secondsLeft) {
  const h = Math.floor(secondsLeft / 3600);
  const m = Math.floor((secondsLeft % 3600) / 60);
  const s = secondsLeft % 60;
  if (h > 0) {
    return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  }
  return `${m}:${String(s).padStart(2, "0")}`;
}

function TimerRow({ timer, now, onCancel }) {
  const expiresAt = new Date(timer.expires_at);
  const secondsLeft = Math.max(0, Math.ceil((expiresAt - now) / 1000));
  const isRinging = timer.status === "ringing" || secondsLeft === 0;
  const label = timer.label || "Timer";

  return (
    <div className={`${styles.timerItem} ${isRinging ? styles.timerRinging : ""}`}>
      <div className={styles.timerLabel}>{label}</div>
      <div className={styles.timerCountdown}>
        {isRinging ? "0:00" : formatCountdown(secondsLeft)}
      </div>
      <button
        className={styles.timerCancelBtn}
        onClick={() => onCancel(timer.id, isRinging)}
        title={isRinging ? "Dismiss" : "Cancel"}
      >
        {isRinging ? "Dismiss" : "\u00d7"}
      </button>
    </div>
  );
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

  const queryClient = useQueryClient();

  const { data: timers } = useQuery({
    queryKey: ["timers"],
    queryFn: fetchTimers,
    refetchInterval: 5000,
  });

  const cancelMutation = useMutation({
    mutationFn: cancelTimer,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["timers"] }),
  });

  const dismissMutation = useMutation({
    mutationFn: dismissTimers,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["timers"] }),
  });

  const handleCancel = useCallback(
    (timerId, isRinging) => {
      if (isRinging) {
        dismissMutation.mutate();
      } else {
        cancelMutation.mutate(timerId);
      }
    },
    [cancelMutation, dismissMutation],
  );

  const activeTimers = (timers || []).filter(
    (t) => t.status === "running" || t.status === "ringing",
  );
  const hasTimers = activeTimers.length > 0;

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

      {hasTimers ? (
        <>
          <div className={styles.divider} />
          <div className={styles.timerSection}>
            {activeTimers.map((timer) => (
              <TimerRow
                key={timer.id}
                timer={timer}
                now={now}
                onCancel={handleCancel}
              />
            ))}
          </div>
        </>
      ) : (
        config.aux &&
        config.aux.length > 0 && (
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
        )
      )}
    </div>
  );
}
