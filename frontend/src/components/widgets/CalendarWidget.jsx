import { useCalendar } from "../../hooks/useCalendar";
import WidgetCard from "../WidgetCard";
import styles from "./CalendarWidget.module.css";

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
    <WidgetCard title="Today's Schedule">
      {events.map((event, i) => (
        <div key={i} className={styles.event}>
          <span className={styles.time}>
            {event.start} - {event.end}
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
