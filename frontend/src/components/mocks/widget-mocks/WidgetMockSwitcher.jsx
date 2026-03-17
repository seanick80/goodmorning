import { useState } from "react";
import ClockMocks from "./ClockMocks";
import WeatherMocks from "./WeatherMocks";
import StocksMocks from "./StocksMocks";
import CalendarMocks from "./CalendarMocks";
import NewsMocks from "./NewsMocks";
import styles from "./WidgetMockSwitcher.module.css";

const WIDGETS = [
  { key: "clock", label: "Clock", Component: ClockMocks },
  { key: "weather", label: "Weather", Component: WeatherMocks },
  { key: "stocks", label: "Stocks", Component: StocksMocks },
  { key: "calendar", label: "Calendar", Component: CalendarMocks },
  { key: "news", label: "News", Component: NewsMocks },
];

export default function WidgetMockSwitcher({ onBack }) {
  const [active, setActive] = useState("clock");
  const ActiveComponent = WIDGETS.find((w) => w.key === active).Component;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Widget Design Variants</h1>
        <button className={styles.backBtn} onClick={onBack}>
          Back to Dashboard
        </button>
      </div>

      <nav className={styles.tabBar}>
        {WIDGETS.map((w) => (
          <button
            key={w.key}
            className={`${styles.tab} ${active === w.key ? styles.tabActive : ""}`}
            onClick={() => setActive(w.key)}
          >
            {w.label}
          </button>
        ))}
      </nav>

      <div className={styles.content}>
        <ActiveComponent />
      </div>
    </div>
  );
}
