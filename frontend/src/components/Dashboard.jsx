import { useState } from "react";
import ClockWidget from "./widgets/ClockWidget";
import WeatherWidget from "./widgets/WeatherWidget";
import StocksWidget from "./widgets/StocksWidget";
import CalendarWidget from "./widgets/CalendarWidget";
import NewsWidget from "./widgets/NewsWidget";
import AuthStatus from "./AuthStatus";
import SettingsPanel from "./SettingsPanel";
import { useDashboard } from "../hooks/useDashboard";
import styles from "./Dashboard.module.css";

export default function Dashboard() {
  const { data: dashboard } = useDashboard();
  const clockSettings = dashboard?.clock_settings ?? undefined;
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <div className={styles.wrapper}>
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
          <StocksWidget />
          <CalendarWidget />
          <NewsWidget />
        </div>
      </div>

      {settingsOpen && <SettingsPanel onClose={() => setSettingsOpen(false)} />}
    </div>
  );
}
