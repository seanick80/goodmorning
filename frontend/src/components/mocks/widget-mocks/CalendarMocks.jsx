import WidgetCard from "../../WidgetCard";
import { mockCalendar } from "../mockData";
import styles from "./CalendarMocks.module.css";

const accentColors = [
  "rgba(139, 92, 246, 0.25)",
  "rgba(59, 130, 246, 0.25)",
  "rgba(16, 185, 129, 0.25)",
  "rgba(245, 158, 11, 0.25)",
];

const accentBorders = [
  "rgba(139, 92, 246, 0.6)",
  "rgba(59, 130, 246, 0.6)",
  "rgba(16, 185, 129, 0.6)",
  "rgba(245, 158, 11, 0.6)",
];

function VariantSimple() {
  return (
    <WidgetCard title="Today's Schedule">
      {mockCalendar.map((ev, i) => (
        <div key={i} className={styles.simpleEvent}>
          <span className={styles.simpleTime}>{ev.start} - {ev.end}</span>
          <span className={styles.simpleTitle}>{ev.title}</span>
          {ev.location && <span className={styles.simpleLocation}>{ev.location}</span>}
        </div>
      ))}
    </WidgetCard>
  );
}

function VariantTimeline() {
  return (
    <WidgetCard title="Today's Schedule">
      <div className={styles.timeline}>
        {mockCalendar.map((ev, i) => (
          <div key={i} className={styles.tlEvent}>
            <div className={styles.tlLine}>
              <div className={styles.tlDot} />
              {i < mockCalendar.length - 1 && <div className={styles.tlConnector} />}
            </div>
            <div className={styles.tlContent}>
              <div className={styles.tlTime}>{ev.start}</div>
              <div className={styles.tlCard}>
                <div className={styles.tlTitle}>{ev.title}</div>
                {ev.location && <div className={styles.tlLocation}>{ev.location}</div>}
              </div>
            </div>
          </div>
        ))}
      </div>
    </WidgetCard>
  );
}

function VariantColorBlocks() {
  return (
    <WidgetCard title="Today's Schedule">
      <div className={styles.colorBlocks}>
        {mockCalendar.map((ev, i) => (
          <div
            key={i}
            className={styles.colorBlock}
            style={{
              background: accentColors[i % accentColors.length],
              borderLeft: `3px solid ${accentBorders[i % accentBorders.length]}`,
            }}
          >
            <div className={styles.cbTimeRange}>{ev.start} - {ev.end}</div>
            <div className={styles.cbRight}>
              <div className={styles.cbTitle}>{ev.title}</div>
              {ev.location && <div className={styles.cbLocation}>{ev.location}</div>}
            </div>
          </div>
        ))}
      </div>
    </WidgetCard>
  );
}

function VariantNextUp() {
  const next = mockCalendar[0];
  const rest = mockCalendar.slice(1);

  return (
    <WidgetCard title="Today's Schedule">
      <div className={styles.nextUpLabel}>Next Up</div>
      <div className={styles.nextUpMain}>
        <div className={styles.nextUpTitle}>{next.title}</div>
        <div className={styles.nextUpTime}>{next.start} - {next.end}</div>
        {next.location && <div className={styles.nextUpLocation}>{next.location}</div>}
        <div className={styles.nextUpCountdown}>In 2 hours</div>
      </div>
      {rest.length > 0 && (
        <div className={styles.nextUpRest}>
          <div className={styles.nextUpRestLabel}>Later</div>
          {rest.map((ev, i) => (
            <div key={i} className={styles.nextUpRestItem}>
              <span className={styles.nextUpRestTime}>{ev.start}</span>
              <span className={styles.nextUpRestTitle}>{ev.title}</span>
            </div>
          ))}
        </div>
      )}
    </WidgetCard>
  );
}

export default function CalendarMocks() {
  return (
    <div className={styles.grid}>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant A: Simple List</div>
        <VariantSimple />
      </div>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant B: Timeline</div>
        <VariantTimeline />
      </div>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant C: Color Blocks</div>
        <VariantColorBlocks />
      </div>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant D: Next Up</div>
        <VariantNextUp />
      </div>
    </div>
  );
}
