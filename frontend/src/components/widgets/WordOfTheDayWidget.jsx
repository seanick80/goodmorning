import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchWordOfTheDay } from "../../api/wordoftheday";
import WidgetCard from "../WidgetCard";
import styles from "./WordOfTheDayWidget.module.css";

function highlightPattern(word, pattern, patternPosition) {
  if (!word || !pattern) return word;

  let index = -1;
  if (patternPosition === "start") {
    if (word.toLowerCase().startsWith(pattern.toLowerCase())) {
      index = 0;
    }
  } else if (patternPosition === "end") {
    const lowered = word.toLowerCase();
    const loweredPattern = pattern.toLowerCase();
    const pos = lowered.lastIndexOf(loweredPattern);
    if (pos >= 0 && pos + loweredPattern.length === lowered.length) {
      index = pos;
    }
  } else {
    index = word.toLowerCase().indexOf(pattern.toLowerCase());
  }

  if (index < 0) return word;

  const before = word.slice(0, index);
  const match = word.slice(index, index + pattern.length);
  const after = word.slice(index + pattern.length);

  return (
    <>
      {before}
      <span className={styles.highlight}>{match}</span>
      {after}
    </>
  );
}

function useToday() {
  const [today, setToday] = useState(
    () => new Date().toLocaleDateString("en-CA"),
  );
  useEffect(() => {
    const id = setInterval(() => {
      const now = new Date().toLocaleDateString("en-CA");
      setToday((prev) => (prev !== now ? now : prev));
    }, 60_000);
    return () => clearInterval(id);
  }, []);
  return today;
}

export default function WordOfTheDayWidget() {
  const today = useToday();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["wordoftheday", today],
    queryFn: () => fetchWordOfTheDay(today),
    staleTime: 15 * 60_000,
    refetchInterval: 15 * 60_000,
  });

  if (isLoading) {
    return (
      <WidgetCard title="WORD OF THE DAY">
        <div className={styles.loading}>Loading...</div>
      </WidgetCard>
    );
  }

  if (isError || !data) {
    return (
      <WidgetCard title="WORD OF THE DAY">
        <div className={styles.error}>Unable to load word</div>
      </WidgetCard>
    );
  }

  const { word, pattern, pattern_position, day_index } = data;
  const days = [0, 1, 2, 3, 4, 5, 6];

  return (
    <WidgetCard title="WORD OF THE DAY">
      <div className={styles.word}>
        {highlightPattern(word, pattern, pattern_position)}
      </div>
      <div className={styles.pattern}>
        This week&apos;s pattern: <strong>-{pattern}</strong>
      </div>
      <div className={styles.dots}>
        {days.map((d) => {
          let dotClass = styles.dot;
          if (d < day_index) dotClass += ` ${styles.dotActive}`;
          if (d === day_index) dotClass += ` ${styles.dotCurrent}`;
          return <span key={d} className={dotClass} />;
        })}
      </div>
    </WidgetCard>
  );
}
