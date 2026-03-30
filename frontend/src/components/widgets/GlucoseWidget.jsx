import { useState, useEffect } from "react";
import { useGlucose } from "../../hooks/useGlucose";
import StaleIndicator from "../StaleIndicator";
import WidgetCard from "../WidgetCard";
import styles from "./GlucoseWidget.module.css";

function getRangeClass(value) {
  if (value < 55 || value > 250) return styles.urgentRange;
  if (value < 70 || value > 180) return styles.highRange;
  return styles.inRange;
}

function Sparkline({ history }) {
  if (!history || history.length < 2) return null;

  const values = history.map((r) => r.value).reverse();
  const min = Math.min(...values, 40);
  const max = Math.max(...values, 300);
  const width = 200;
  const height = 40;
  const padding = 2;

  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * (width - padding * 2) + padding;
    const y =
      height -
      padding -
      ((v - min) / (max - min)) * (height - padding * 2);
    return `${x},${y}`;
  });

  // In-range band (70-180 mg/dL)
  const bandTop =
    height -
    padding -
    ((180 - min) / (max - min)) * (height - padding * 2);
  const bandBottom =
    height -
    padding -
    ((70 - min) / (max - min)) * (height - padding * 2);

  return (
    <svg
      className={styles.sparkline}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
    >
      <rect
        className={styles.rangeBand}
        x={padding}
        y={Math.max(bandTop, padding)}
        width={width - padding * 2}
        height={Math.min(bandBottom, height - padding) - Math.max(bandTop, padding)}
      />
      <polyline className={styles.sparklinePath} points={points.join(" ")} />
    </svg>
  );
}

function formatTime(dateStr) {
  try {
    const d = new Date(dateStr);
    return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  } catch {
    return "";
  }
}

export default function GlucoseWidget() {
  const { data, isLoading, isError } = useGlucose();
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 30_000);
    return () => clearInterval(id);
  }, []);

  if (isLoading) {
    return (
      <WidgetCard title="Glucose">
        <div className={styles.loading}>Loading glucose...</div>
      </WidgetCard>
    );
  }

  if (isError || !data?.current) {
    return (
      <WidgetCard title="Glucose">
        <div className={styles.error}>No glucose data</div>
      </WidgetCard>
    );
  }

  const { current, history } = data;
  const rangeClass = getRangeClass(current.value);

  // Check if reading is stale (>15 minutes old)
  const recordedAt = new Date(current.recorded_at);
  const ageMinutes = (now - recordedAt.getTime()) / 60000;
  const isStale = ageMinutes > 15;

  return (
    <WidgetCard
      title="Glucose"
      titleExtra={<StaleIndicator fetchedAt={current.fetched_at} />}
    >
      <div className={styles.content}>
        <span className={`${styles.value} ${rangeClass}`}>{current.value}</span>
        <span className={styles.unit}>mg/dL</span>
        <span className={`${styles.trend} ${rangeClass}`}>
          {current.trend_arrow}
        </span>
      </div>
      {isStale && (
        <div className={styles.stale}>
          {Math.round(ageMinutes)} min ago
        </div>
      )}
      <div className={styles.timestamp}>{formatTime(current.recorded_at)}</div>
      <Sparkline history={history} />
    </WidgetCard>
  );
}
