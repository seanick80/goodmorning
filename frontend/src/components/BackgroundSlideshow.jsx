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

export default function BackgroundSlideshow({ onAdvance, paused } = {}) {
  const { data: dashboard } = useDashboard();
  const { count, interval } = getPhotosConfig(dashboard);
  const [current, setCurrent] = useState(0);
  const [next, setNext] = useState(null);
  const [fading, setFading] = useState(false);
  const timerRef = useRef(null);
  const onAdvanceRef = useRef(onAdvance);
  const currentRef = useRef(0);
  const pausedRef = useRef(paused);

  useEffect(() => {
    onAdvanceRef.current = onAdvance;
  }, [onAdvance]);

  useEffect(() => {
    currentRef.current = current;
  }, [current]);

  useEffect(() => {
    pausedRef.current = paused;
  }, [paused]);

  useEffect(() => {
    if (count <= 1) return;

    function advance() {
      if (pausedRef.current) return;
      const nextIdx = (currentRef.current + 1) % count;
      setNext(nextIdx);
      setFading(false);

      const img = new Image();
      img.onload = () => {
        setFading(true);
        setTimeout(() => {
          setCurrent(nextIdx);
          currentRef.current = nextIdx;
          setNext(null);
          setFading(false);
          if (onAdvanceRef.current) onAdvanceRef.current(nextIdx);
        }, FADE_DURATION);
      };
      img.onerror = () => {
        setCurrent(nextIdx);
        currentRef.current = nextIdx;
        setNext(null);
        setFading(false);
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
        className={`${styles.image} ${styles.current}`}
      />
      {next !== null && (
        <img
          src={`/api/photos/${next}/?w=1920&h=1080`}
          alt=""
          className={`${styles.image} ${styles.next} ${fading ? styles.fadeIn : ""}`}
        />
      )}
      <div className={styles.overlay} />
    </div>
  );
}
