import { useState } from "react";
import ClockWidget from "./widgets/ClockWidget";
import WeatherWidget from "./widgets/WeatherWidget";
import GlucoseWidget from "./widgets/GlucoseWidget";
import StocksWidget from "./widgets/StocksWidget";
import CalendarWidget from "./widgets/CalendarWidget";
import NewsWidget from "./widgets/NewsWidget";
import AuthStatus from "./AuthStatus";
import SettingsPanel from "./SettingsPanel";
import BackgroundSlideshow from "./BackgroundSlideshow";
import { useDashboard } from "../hooks/useDashboard";
import styles from "./Dashboard.module.css";

export default function Dashboard() {
  const { data: dashboard } = useDashboard();
  const clockSettings = dashboard?.clock_settings ?? undefined;
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [photoFrameMode, setPhotoFrameMode] = useState(false);

  return (
    <div className={styles.wrapper}>
      <BackgroundSlideshow />
      {photoFrameMode ? (
        <button
          type="button"
          className={styles.exitFrameButton}
          onClick={() => setPhotoFrameMode(false)}
          aria-label="Exit photo frame mode"
          title="Exit photo frame"
        >
          {"\u2716"}
        </button>
      ) : (
        <>
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
              <ClockWidget settings={clockSettings} />
              <WeatherWidget />
            </div>

            <div className={styles.rightPanel}>
              <GlucoseWidget />
              <StocksWidget />
              <CalendarWidget />
              <NewsWidget />
            </div>
          </div>
        </>
      )}

      {settingsOpen && (
        <SettingsPanel
          onClose={() => setSettingsOpen(false)}
          photoFrameMode={photoFrameMode}
          onTogglePhotoFrame={() => setPhotoFrameMode((v) => !v)}
        />
      )}
    </div>
  );
}
