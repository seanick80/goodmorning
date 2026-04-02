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

export default function WordOfTheDayWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["wordoftheday"],
    queryFn: fetchWordOfTheDay,
    refetchInterval: 3600000,
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

  const { word, pattern, pattern_position, day_index, is_weekend } = data;
  const weekdays = [0, 1, 2, 3, 4];

  return (
    <WidgetCard title="WORD OF THE DAY">
      <div className={styles.word}>
        {highlightPattern(word, pattern, pattern_position)}
      </div>
      <div className={styles.pattern}>
        This week&apos;s pattern: <strong>-{pattern}</strong>
      </div>
      {!is_weekend && (
        <div className={styles.dots}>
          {weekdays.map((d) => {
            let dotClass = styles.dot;
            if (d < day_index) dotClass += ` ${styles.dotActive}`;
            if (d === day_index) dotClass += ` ${styles.dotCurrent}`;
            return <span key={d} className={dotClass} />;
          })}
        </div>
      )}
    </WidgetCard>
  );
}
