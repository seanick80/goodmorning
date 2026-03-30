import { useState, useEffect, useRef } from "react";
import { useDashboard } from "../hooks/useDashboard";
import styles from "./BackgroundSlideshow.module.css";

function getPhotoCount(dashboard) {
  if (!dashboard?.widget_layout) return 0;
  const widget = dashboard.widget_layout.find((w) => w.widget === "photos");
  return widget?.settings?.cached_media?.length ?? 0;
}

export default function BackgroundSlideshow() {
  const { data: dashboard } = useDashboard();
  const count = getPhotoCount(dashboard);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    if (count <= 1) return;
    timerRef.current = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % count);
      setLoaded(false);
    }, 30000);
    return () => clearInterval(timerRef.current);
  }, [count]);

  if (count === 0) return null;

  const index = currentIndex % count;
  const url = `/api/photos/${index}/?w=1920&h=1080`;

  return (
    <div className={styles.container}>
      <img
        key={index}
        src={url}
        alt=""
        className={`${styles.image} ${loaded ? styles.loaded : ""}`}
        onLoad={() => setLoaded(true)}
      />
      <div className={styles.overlay} />
    </div>
  );
}
