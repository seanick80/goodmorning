import { useState, useEffect } from "react";
import WidgetCard from "../../WidgetCard";
import { mockNews } from "../mockData";
import styles from "./NewsMocks.module.css";

const sourceColors = {
  "BBC News": "#bb1919",
  "NPR": "#2255aa",
  "Reuters": "#ff6600",
  "AP News": "#cc3333",
  "Bloomberg": "#5500aa",
};

function VariantSingleHeadline() {
  const [idx, setIdx] = useState(0);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const id = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setIdx((prev) => (prev + 1) % mockNews.length);
        setVisible(true);
      }, 400);
    }, 5000);
    return () => clearInterval(id);
  }, []);

  const h = mockNews[idx];
  return (
    <WidgetCard title="News">
      <div className={`${styles.singleHeadline} ${visible ? styles.visible : styles.hidden}`}>
        <div className={styles.singleTitle}>{h.title}</div>
        <div className={styles.singleMeta}>
          <span className={styles.singleSource}>{h.source_name}</span>
          <span className={styles.singleTime}> &middot; {h.published_at}</span>
        </div>
      </div>
      <div className={styles.dots}>
        {mockNews.map((_, i) => (
          <span key={i} className={`${styles.dot} ${i === idx ? styles.dotActive : ""}`} />
        ))}
      </div>
    </WidgetCard>
  );
}

function VariantStack() {
  const visible = mockNews.slice(0, 3);
  return (
    <WidgetCard title="News">
      <div className={styles.stack}>
        {visible.map((h, i) => (
          <div key={i} className={styles.stackItem}>
            <span
              className={styles.stackBadge}
              style={{ background: sourceColors[h.source_name] || "#555" }}
            >
              {h.source_name}
            </span>
            <div className={styles.stackTitle}>{h.title}</div>
          </div>
        ))}
      </div>
    </WidgetCard>
  );
}

function VariantFeatured() {
  const [featIdx, setFeatIdx] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setFeatIdx((prev) => (prev + 1) % mockNews.length);
    }, 8000);
    return () => clearInterval(id);
  }, []);

  const featured = mockNews[featIdx];
  const others = mockNews.filter((_, i) => i !== featIdx).slice(0, 2);

  return (
    <WidgetCard title="News">
      <div className={styles.featuredMain}>
        <div className={styles.featuredTitle}>{featured.title}</div>
        <div className={styles.featuredMeta}>
          <span className={styles.featuredSource}>{featured.source_name}</span>
          <span> &middot; {featured.published_at}</span>
        </div>
      </div>
      <div className={styles.featuredList}>
        {others.map((h, i) => (
          <div key={i} className={styles.featuredListItem}>
            <span className={styles.featuredListSource}>{h.source_name}</span>
            <span className={styles.featuredListTitle}>{h.title}</span>
          </div>
        ))}
      </div>
    </WidgetCard>
  );
}

function VariantTicker() {
  const items = [...mockNews, ...mockNews];
  return (
    <WidgetCard title="News">
      <div className={styles.tickerTrack}>
        <div className={styles.tickerScroll}>
          {items.map((h, i) => (
            <span key={i} className={styles.tickerItem}>
              <span className={styles.tickerSource}>{h.source_name}:</span>
              <span className={styles.tickerTitle}>{h.title}</span>
              <span className={styles.tickerSep}>|</span>
            </span>
          ))}
          {items.map((h, i) => (
            <span key={`dup-${i}`} className={styles.tickerItem}>
              <span className={styles.tickerSource}>{h.source_name}:</span>
              <span className={styles.tickerTitle}>{h.title}</span>
              <span className={styles.tickerSep}>|</span>
            </span>
          ))}
        </div>
      </div>
    </WidgetCard>
  );
}

export default function NewsMocks() {
  return (
    <div className={styles.grid}>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant A: Single Headline</div>
        <VariantSingleHeadline />
      </div>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant B: Stack</div>
        <VariantStack />
      </div>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant C: Featured + List</div>
        <VariantFeatured />
      </div>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant D: News Ticker</div>
        <VariantTicker />
      </div>
    </div>
  );
}
