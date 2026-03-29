import ClockWidget from "./widgets/ClockWidget";
import WeatherWidget from "./widgets/WeatherWidget";
import StocksWidget from "./widgets/StocksWidget";
import CalendarWidget from "./widgets/CalendarWidget";
import NewsWidget from "./widgets/NewsWidget";
import AuthStatus from "./AuthStatus";
import CalendarPicker from "./CalendarPicker";
import AlbumPicker from "./AlbumPicker";
import { useDashboard } from "../hooks/useDashboard";
import { useAuth } from "../hooks/useAuth";
import styles from "./Dashboard.module.css";

export default function Dashboard() {
  const { data: dashboard } = useDashboard();
  const { data: auth } = useAuth();
  const clockSettings = dashboard?.clock_settings ?? undefined;
  const googleConnected = auth?.authenticated && auth?.google_connected;

  return (
    <div className={styles.wrapper}>
      <header className={styles.header}>
        <AuthStatus />
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
          {googleConnected && <CalendarPicker />}
          {googleConnected && <AlbumPicker />}
        </div>
      </div>
    </div>
  );
}
