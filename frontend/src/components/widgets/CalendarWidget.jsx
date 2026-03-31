import { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCalendar } from "../../hooks/useCalendar";
import { fetchGoogleCalendars, patchDashboard } from "../../api/auth";
import { useAuth } from "../../hooks/useAuth";
import { useDashboard } from "../../hooks/useDashboard";
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

function getSavedCalendarIds(dashboard) {
  if (!dashboard?.widget_layout) return [];
  const calWidget = dashboard.widget_layout.find((w) => w.widget === "calendar");
  return calWidget?.settings?.google_calendar_ids ?? [];
}

function CalendarConfigure({ onClose }) {
  const queryClient = useQueryClient();
  const { data: dashboard } = useDashboard();
  const { data: auth } = useAuth();
  const googleConnected = auth?.authenticated && auth?.google_connected;

  const { data: calendars, isLoading, isError } = useQuery({
    queryKey: ["googleCalendars"],
    queryFn: fetchGoogleCalendars,
    enabled: !!googleConnected,
  });

  const savedIds = getSavedCalendarIds(dashboard);
  const [selected, setSelected] = useState(savedIds);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setSelected(getSavedCalendarIds(dashboard));
  }, [dashboard]);

  function handleToggle(calendarId) {
    setSelected((prev) =>
      prev.includes(calendarId)
        ? prev.filter((id) => id !== calendarId)
        : [...prev, calendarId]
    );
  }

  function handleSave() {
    setSaving(true);
    const widgetLayout = dashboard?.widget_layout ?? [];
    const calWidget = widgetLayout.find((w) => w.widget === "calendar");
    const updatedSettings = { ...(calWidget?.settings ?? {}), google_calendar_ids: selected };
    const updatedLayout = widgetLayout.map((w) =>
      w.widget === "calendar" ? { ...w, settings: updatedSettings } : w
    );
    if (!calWidget) {
      updatedLayout.push({
        widget: "calendar",
        enabled: true,
        position: updatedLayout.length,
        settings: { google_calendar_ids: selected },
      });
    }
    patchDashboard({ widget_layout: updatedLayout })
      .then(() => {
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
        queryClient.invalidateQueries({ queryKey: ["calendar"] });
        onClose();
      })
      .finally(() => setSaving(false));
  }

  if (!googleConnected) {
    return (
      <div className={styles.configure}>
        <a href="/accounts/google/login/" className={styles.connectLink}>
          Connect Google Account
        </a>
      </div>
    );
  }

  if (isLoading) {
    return <div className={styles.configure}>Loading calendars...</div>;
  }

  if (isError || !calendars || calendars.length === 0) {
    return <div className={styles.configure}>No calendars found</div>;
  }

  return (
    <div className={styles.configure}>
      <ul className={styles.calendarList}>
        {calendars.map((cal) => (
          <li key={cal.id} className={styles.calendarItem}>
            <label className={styles.calendarLabel}>
              <input
                type="checkbox"
                checked={selected.includes(cal.id)}
                onChange={() => handleToggle(cal.id)}
                disabled={saving}
                className={styles.checkbox}
              />
              {cal.background_color && (
                <span
                  className={styles.colorDot}
                  style={{ backgroundColor: cal.background_color }}
                />
              )}
              <span className={styles.calName}>
                {cal.summary}
                {cal.primary && <span className={styles.primaryBadge}> (primary)</span>}
              </span>
            </label>
          </li>
        ))}
      </ul>
      <div className={styles.configureActions}>
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className={styles.saveButton}
        >
          {saving ? "Saving..." : "Save"}
        </button>
        <button
          type="button"
          onClick={onClose}
          className={styles.cancelButton}
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

export default function CalendarWidget() {
  const [configOpen, setConfigOpen] = useState(false);
  const { data, isLoading, isError } = useCalendar();

  const gearButton = (
    <button
      type="button"
      className={styles.gearButton}
      onClick={() => setConfigOpen((v) => !v)}
      aria-label="Configure calendar"
      title="Configure calendars"
    >
      {"\u2699"}
    </button>
  );

  if (configOpen) {
    return (
      <WidgetCard title="Today's Schedule" titleExtra={gearButton}>
        <CalendarConfigure onClose={() => setConfigOpen(false)} />
      </WidgetCard>
    );
  }

  if (isLoading) {
    return (
      <WidgetCard title="Today's Schedule" titleExtra={gearButton}>
        <div className={styles.loading}>Loading calendar...</div>
      </WidgetCard>
    );
  }

  if (isError) {
    return (
      <WidgetCard title="Today's Schedule" titleExtra={gearButton}>
        <div className={styles.error}>Unable to load calendar</div>
      </WidgetCard>
    );
  }

  const events = Array.isArray(data) ? data : [];

  if (events.length === 0) {
    return (
      <WidgetCard title="Today's Schedule" titleExtra={gearButton}>
        <div className={styles.empty}>No events today</div>
      </WidgetCard>
    );
  }

  return (
    <WidgetCard
      title="Today's Schedule"
      titleExtra={
        <>
          <StaleIndicator fetchedAt={events[0]?.fetched_at} />
          {gearButton}
        </>
      }
    >
      {events.map((event, i) => {
        // Strip recurring instance suffix (e.g. _20260331T034500Z) to get base event ID
        const baseUid = event.uid?.replace(/_\d{8}T\d{6}Z?$/, "") ?? "";
        const calUrl = baseUid
          ? `https://calendar.google.com/calendar/r/eventedit/${baseUid}`
          : null;
        return (
          <a
            key={i}
            className={styles.event}
            href={calUrl ?? undefined}
            target="_blank"
            rel="noopener noreferrer"
          >
            <span className={styles.time}>
              {event.all_day ? "All day" : `${formatTime(event.start)} – ${formatTime(event.end)}`}
            </span>
            <span className={styles.title}>{event.title}</span>
            {event.location && (
              <span className={styles.location}>{event.location}</span>
            )}
          </a>
        );
      })}
    </WidgetCard>
  );
}
