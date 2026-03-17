import { useState, useEffect } from "react";
import { useNews } from "../../hooks/useNews";
import WidgetCard from "../WidgetCard";
import styles from "./NewsWidget.module.css";

function relativeTime(dateStr) {
  if (!dateStr) return "";
  const now = new Date();
  const then = new Date(dateStr);
  const diffMs = now - then;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHrs = Math.floor(diffMin / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  const diffDays = Math.floor(diffHrs / 24);
  return `${diffDays}d ago`;
}

export default function NewsWidget() {
  const { data, isLoading, isError } = useNews();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [visible, setVisible] = useState(true);

  const headlines = Array.isArray(data) ? data : [];

  useEffect(() => {
    if (headlines.length <= 1) return;

    const id = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setCurrentIndex((prev) => (prev + 1) % headlines.length);
        setVisible(true);
      }, 400);
    }, 30000);

    return () => clearInterval(id);
  }, [headlines.length]);

  if (isLoading) {
    return (
      <WidgetCard title="News">
        <div className={styles.loading}>Loading news...</div>
      </WidgetCard>
    );
  }

  if (isError) {
    return (
      <WidgetCard title="News">
        <div className={styles.error}>Unable to load news</div>
      </WidgetCard>
    );
  }

  if (headlines.length === 0) {
    return (
      <WidgetCard title="News">
        <div className={styles.empty}>No headlines available</div>
      </WidgetCard>
    );
  }

  const idx = currentIndex % headlines.length;
  const headline = headlines[idx];

  const goTo = (next) => {
    setVisible(false);
    setTimeout(() => {
      setCurrentIndex(next);
      setVisible(true);
    }, 300);
  };

  const goPrev = (e) => {
    e.stopPropagation();
    goTo((idx - 1 + headlines.length) % headlines.length);
  };

  const goNext = (e) => {
    e.stopPropagation();
    goTo((idx + 1) % headlines.length);
  };

  return (
    <WidgetCard title="News">
      <div className={`${styles.headline} ${visible ? styles.visible : styles.hidden}`}>
        {headline.link ? (
          <a
            href={headline.link}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.titleLink}
          >
            {headline.title}
          </a>
        ) : (
          <div className={styles.title}>{headline.title}</div>
        )}
        <div className={styles.meta}>
          <span className={styles.source}>{headline.source_name}</span>
          {headline.published_at && (
            <>
              {" \u00B7 "}
              {relativeTime(headline.published_at)}
            </>
          )}
        </div>
      </div>
      {headlines.length > 1 && (
        <div className={styles.nav}>
          <button className={styles.navBtn} onClick={goPrev} aria-label="Previous headline">&lsaquo;</button>
          <span className={styles.counter}>{idx + 1} / {headlines.length}</span>
          <button className={styles.navBtn} onClick={goNext} aria-label="Next headline">&rsaquo;</button>
        </div>
      )}
    </WidgetCard>
  );
}
