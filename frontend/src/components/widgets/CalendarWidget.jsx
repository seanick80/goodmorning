import { useCalendar } from "../../hooks/useCalendar";
import StaleIndicator from "../StaleIndicator";
import WidgetCard from "../WidgetCard";
import styles from "./CalendarWidget.module.css";

function formatTime(isoStr) {
  if (!isoStr) return "";
  try {
    return new Date(isoStr).toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  } catch {
    return isoStr;
  }
}

export default function CalendarWidget() {
  const { data, isLoading, isError } = useCalendar();

  if (isLoading) {
    return (
      <WidgetCard title="Today's Schedule">
        <div className={styles.loading}>Loading calendar...</div>
      </WidgetCard>
    );
  }

  if (isError) {
    return (
      <WidgetCard title="Today's Schedule">
        <div className={styles.error}>Unable to load calendar</div>
      </WidgetCard>
    );
  }

  const events = Array.isArray(data) ? data : [];

  if (events.length === 0) {
    return (
      <WidgetCard title="Today's Schedule">
        <div className={styles.empty}>No events today</div>
      </WidgetCard>
    );
  }

  return (
    <WidgetCard title="Today's Schedule" titleExtra={<StaleIndicator fetchedAt={events[0]?.fetched_at} />}>
      {events.map((event, i) => (
        <div key={i} className={styles.event}>
          <span className={styles.time}>
            {event.all_day ? "All day" : `${formatTime(event.start)} – ${formatTime(event.end)}`}
          </span>
          <span className={styles.title}>{event.title}</span>
          {event.location && (
            <span className={styles.location}>{event.location}</span>
          )}
        </div>
      ))}
    </WidgetCard>
  );
}
