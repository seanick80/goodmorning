import { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchGoogleCalendars, patchDashboard } from "../api/auth";
import { useDashboard } from "../hooks/useDashboard";
import WidgetCard from "./WidgetCard";
import styles from "./CalendarPicker.module.css";

export default function CalendarPicker() {
  const queryClient = useQueryClient();
  const { data: dashboard } = useDashboard();
  const { data: calendars, isLoading, isError } = useQuery({
    queryKey: ["googleCalendars"],
    queryFn: fetchGoogleCalendars,
  });

  const savedIds = getSavedCalendarIds(dashboard);
  const [selected, setSelected] = useState(savedIds);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setSelected(getSavedCalendarIds(dashboard));
  }, [dashboard]);

  function handleToggle(calendarId) {
    const next = selected.includes(calendarId)
      ? selected.filter((id) => id !== calendarId)
      : [...selected, calendarId];
    setSelected(next);
    saveSelection(next);
  }

  function saveSelection(ids) {
    setSaving(true);
    const widgetLayout = dashboard?.widget_layout ?? [];
    const calWidget = widgetLayout.find((w) => w.widget === "calendar");
    const updatedSettings = { ...(calWidget?.settings ?? {}), google_calendar_ids: ids };
    const updatedLayout = widgetLayout.map((w) =>
      w.widget === "calendar" ? { ...w, settings: updatedSettings } : w
    );
    if (!calWidget) {
      updatedLayout.push({
        widget: "calendar",
        enabled: true,
        position: updatedLayout.length,
        settings: { google_calendar_ids: ids },
      });
    }
    patchDashboard({ widget_layout: updatedLayout })
      .then(() => queryClient.invalidateQueries({ queryKey: ["dashboard"] }))
      .finally(() => setSaving(false));
  }

  if (isLoading) {
    return (
      <WidgetCard title="Google Calendars">
        <div className={styles.loading}>Loading calendars...</div>
      </WidgetCard>
    );
  }

  if (isError || !calendars) {
    return null;
  }

  if (calendars.length === 0) {
    return (
      <WidgetCard title="Google Calendars">
        <div className={styles.empty}>No calendars found</div>
      </WidgetCard>
    );
  }

  return (
    <WidgetCard title="Google Calendars">
      <ul className={styles.list}>
        {calendars.map((cal) => (
          <li key={cal.id} className={styles.item}>
            <label className={styles.label}>
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
                {cal.primary && <span className={styles.primary}> (primary)</span>}
              </span>
            </label>
          </li>
        ))}
      </ul>
    </WidgetCard>
  );
}

function getSavedCalendarIds(dashboard) {
  if (!dashboard?.widget_layout) return [];
  const calWidget = dashboard.widget_layout.find((w) => w.widget === "calendar");
  return calWidget?.settings?.google_calendar_ids ?? [];
}
