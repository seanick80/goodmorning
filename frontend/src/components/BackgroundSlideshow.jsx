import { useState, useEffect, useRef } from "react";
import { useDashboard } from "../hooks/useDashboard";
import styles from "./BackgroundSlideshow.module.css";

const DEFAULT_INTERVAL = 60;
const FADE_DURATION = 2000;

function getPhotosConfig(dashboard) {
  if (!dashboard?.widget_layout) return { count: 0, interval: DEFAULT_INTERVAL };
  const widget = dashboard.widget_layout.find((w) => w.widget === "photos");
  if (!widget) return { count: 0, interval: DEFAULT_INTERVAL };
  const media = widget.settings?.cached_media ?? [];
  const interval = widget.settings?.interval_seconds ?? DEFAULT_INTERVAL;
  return { count: media.length, interval };
}

export default function BackgroundSlideshow({ onAdvance } = {}) {
  const { data: dashboard } = useDashboard();
  const { count, interval } = getPhotosConfig(dashboard);
  const [current, setCurrent] = useState(0);
  const [next, setNext] = useState(null);
  const [phase, setPhase] = useState("showing"); // "showing" | "preloading" | "fading"
  const timerRef = useRef(null);
  const preloadRef = useRef(null);
  const onAdvanceRef = useRef(onAdvance);
  const currentRef = useRef(current);

  useEffect(() => {
    onAdvanceRef.current = onAdvance;
  }, [onAdvance]);

  useEffect(() => {
    currentRef.current = current;
  }, [current]);

  useEffect(() => {
    if (count <= 1) return;

    function advance() {
      const nextIdx = (currentRef.current + 1) % count;
      setNext(nextIdx);
      setPhase("preloading");

      const img = new Image();
      preloadRef.current = img;
      img.onload = () => {
        setPhase("fading");
        setTimeout(() => {
          setCurrent(nextIdx);
          currentRef.current = nextIdx;
          setNext(null);
          setPhase("showing");
          if (onAdvanceRef.current) onAdvanceRef.current(nextIdx);
        }, FADE_DURATION);
      };
      img.onerror = () => {
        setCurrent(nextIdx);
        currentRef.current = nextIdx;
        setNext(null);
        setPhase("showing");
      };
      img.src = `/api/photos/${nextIdx}/?w=1920&h=1080`;
    }

    timerRef.current = setInterval(advance, interval * 1000);
    return () => clearInterval(timerRef.current);
  }, [count, interval]);

  if (count === 0) return null;

  return (
    <div className={styles.container}>
      <img
        src={`/api/photos/${current}/?w=1920&h=1080`}
        alt=""
        className={`${styles.image} ${phase === "fading" ? styles.fadeOut : styles.visible}`}
      />
      {next !== null && (
        <img
          src={`/api/photos/${next}/?w=1920&h=1080`}
          alt=""
          className={`${styles.image} ${styles.nextImage} ${phase === "fading" ? styles.visible : ""}`}
        />
      )}
      <div className={styles.overlay} />
    </div>
  );
}
