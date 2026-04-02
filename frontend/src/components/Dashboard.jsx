import { useState, useCallback, useRef, useEffect } from "react";
import ClockWidget from "./widgets/ClockWidget";
import WeatherWidget from "./widgets/WeatherWidget";
import GlucoseWidget from "./widgets/GlucoseWidget";
import StocksWidget from "./widgets/StocksWidget";
import CalendarWidget from "./widgets/CalendarWidget";
import NewsWidget from "./widgets/NewsWidget";
import WordOfTheDayWidget from "./widgets/WordOfTheDayWidget";
import AuthStatus from "./AuthStatus";
import SettingsPanel from "./SettingsPanel";
import BackgroundSlideshow from "./BackgroundSlideshow";
import { useDashboard } from "../hooks/useDashboard";
import styles from "./Dashboard.module.css";

function getDashboardFlashFreq(dashboard) {
  if (!dashboard?.widget_layout) return 4;
  const widget = dashboard.widget_layout.find((w) => w.widget === "photos");
  return widget?.settings?.dashboard_flash_frequency ?? 4;
}

function getDashboardFlashDuration(dashboard) {
  if (!dashboard?.widget_layout) return 15;
  const widget = dashboard.widget_layout.find((w) => w.widget === "photos");
  return widget?.settings?.dashboard_flash_seconds ?? 15;
}

const WIDGET_MAP = {
  clock: ClockWidget,
  weather: WeatherWidget,
  glucose: GlucoseWidget,
  stocks: StocksWidget,
  calendar: CalendarWidget,
  news: NewsWidget,
  wordoftheday: WordOfTheDayWidget,
};

const DEFAULT_PANEL = {
  clock: "left",
  weather: "left",
  glucose: "right",
  stocks: "right",
  calendar: "right",
  news: "right",
  wordoftheday: "left",
  photos: "right",
};

function getWidgetsForPanel(widgetLayout, panel) {
  return (widgetLayout || [])
    .filter((w) => w.enabled !== false && (w.panel || DEFAULT_PANEL[w.widget]) === panel)
    .sort((a, b) => (a.position ?? 0) - (b.position ?? 0));
}

export default function Dashboard() {
  const { data: dashboard } = useDashboard();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [photoFrameMode, setPhotoFrameMode] = useState(false);
  const [kioskMode, setKioskMode] = useState(
    () => localStorage.getItem("kiosk_mode") === "true"
  );

  const handleToggleKiosk = useCallback(() => {
    setKioskMode((v) => {
      localStorage.setItem("kiosk_mode", String(!v));
      return !v;
    });
  }, []);
  const [dashboardFlash, setDashboardFlash] = useState(false);
  const tickRef = useRef(0);
  const flashTimerRef = useRef(null);

  const flashFreq = getDashboardFlashFreq(dashboard);
  const flashDuration = getDashboardFlashDuration(dashboard);

  const onAdvance = useCallback(() => {
    if (!photoFrameMode) return;
    tickRef.current += 1;
    if (flashFreq > 0 && tickRef.current % flashFreq === 0) {
      setDashboardFlash(true);
      clearTimeout(flashTimerRef.current);
      flashTimerRef.current = setTimeout(() => {
        setDashboardFlash(false);
      }, flashDuration * 1000);
    }
  }, [photoFrameMode, flashFreq, flashDuration]);

  const slideshowPaused = photoFrameMode && dashboardFlash;

  const handleTogglePhotoFrame = useCallback(() => {
    setPhotoFrameMode((v) => !v);
    tickRef.current = 0;
    setDashboardFlash(false);
    clearTimeout(flashTimerRef.current);
  }, []);

  // Clean up flash timer on unmount
  useEffect(() => () => clearTimeout(flashTimerRef.current), []);

  const showWidgets = !photoFrameMode || dashboardFlash;

  return (
    <div className={styles.wrapper}>
      <BackgroundSlideshow onAdvance={onAdvance} paused={slideshowPaused} />
      {photoFrameMode && (
        <button
          type="button"
          className={styles.exitFrameButton}
          onClick={handleTogglePhotoFrame}
          aria-label="Exit photo frame mode"
          title="Exit photo frame"
        >
          {"\u2716"}
        </button>
      )}

      <div
        className={`${styles.dashboardContent} ${showWidgets ? styles.dashboardVisible : styles.dashboardHidden}`}
      >
        <header className={styles.header}>
          <AuthStatus />
          <button
            type="button"
            className={styles.settingsButton}
            onClick={() => setSettingsOpen(true)}
            aria-label="Open settings"
            title="Settings"
          >
            {"\u2699"}
          </button>
        </header>

        <div className={styles.hero}>
          <div className={styles.leftPanel}>
            {getWidgetsForPanel(dashboard?.widget_layout, "left").map((w) => {
              const Component = WIDGET_MAP[w.widget];
              if (!Component) return null;
              const props = (w.widget === "clock" || w.widget === "news" || w.widget === "wordoftheday") ? { settings: w.settings } : {};
              return <Component key={w.widget} {...props} kioskMode={kioskMode} />;
            })}
          </div>

          <div className={styles.rightPanel}>
            {getWidgetsForPanel(dashboard?.widget_layout, "right").map((w) => {
              const Component = WIDGET_MAP[w.widget];
              if (!Component) return null;
              const props = (w.widget === "clock" || w.widget === "news" || w.widget === "wordoftheday") ? { settings: w.settings } : {};
              return <Component key={w.widget} {...props} kioskMode={kioskMode} />;
            })}
          </div>
        </div>
      </div>

      {settingsOpen && (
        <SettingsPanel
          onClose={() => setSettingsOpen(false)}
          photoFrameMode={photoFrameMode}
          onTogglePhotoFrame={handleTogglePhotoFrame}
          kioskMode={kioskMode}
          onToggleKiosk={handleToggleKiosk}
        />
      )}
    </div>
  );
}
