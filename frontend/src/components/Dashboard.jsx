import ClockWidget from "./widgets/ClockWidget";
import WeatherWidget from "./widgets/WeatherWidget";
import StocksWidget from "./widgets/StocksWidget";
import CalendarWidget from "./widgets/CalendarWidget";
import NewsWidget from "./widgets/NewsWidget";
import styles from "./Dashboard.module.css";

export default function Dashboard() {
  return (
    <div className={styles.hero}>
      <div className={styles.leftPanel}>
        <ClockWidget />
        <WeatherWidget />
      </div>

      <div className={styles.rightPanel}>
        <StocksWidget />
        <CalendarWidget />
        <NewsWidget />
      </div>
    </div>
  );
}
