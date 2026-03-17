import { useState, useEffect } from "react";
import WidgetCard from "../WidgetCard";
import styles from "./ClockWidget.module.css";

function getGreeting(hour) {
  if (hour >= 5 && hour < 12) return "Good Morning";
  if (hour >= 12 && hour < 17) return "Good Afternoon";
  return "Good Evening";
}

export default function ClockWidget() {
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const timeStr = now.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  });

  const dateStr = now.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const greeting = getGreeting(now.getHours());

  return (
    <WidgetCard className={styles.clock}>
      <div className={styles.greeting}>{greeting}</div>
      <div className={styles.time}>{timeStr}</div>
      <div className={styles.date}>{dateStr}</div>
    </WidgetCard>
  );
}
