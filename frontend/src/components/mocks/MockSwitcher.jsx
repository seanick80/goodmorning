import { useState } from "react";
import Dashboard from "../Dashboard";
import MockLayoutGrid from "./MockLayoutGrid";
import MockLayoutHero from "./MockLayoutHero";
import MockLayoutBand from "./MockLayoutBand";
import MockLayoutFeatured from "./MockLayoutFeatured";
import styles from "./MockSwitcher.module.css";

const LAYOUTS = [
  { key: "grid", label: "Grid", component: MockLayoutGrid },
  { key: "hero", label: "Hero", component: MockLayoutHero },
  { key: "bands", label: "Bands", component: MockLayoutBand },
  { key: "featured", label: "Featured", component: MockLayoutFeatured },
  { key: "live", label: "Live", component: Dashboard },
];

export default function MockSwitcher() {
  const [active, setActive] = useState("grid");

  const current = LAYOUTS.find((l) => l.key === active);
  const LayoutComponent = current.component;

  return (
    <div className={styles.container}>
      <div className={styles.tabBar}>
        <div className={styles.tabBarInner}>
          {LAYOUTS.map((layout) => (
            <button
              key={layout.key}
              className={`${styles.tab} ${active === layout.key ? styles.tabActive : ""} ${layout.key === "live" ? styles.tabLive : ""}`}
              onClick={() => setActive(layout.key)}
            >
              {layout.label}
            </button>
          ))}
        </div>
      </div>
      <LayoutComponent />
    </div>
  );
}
