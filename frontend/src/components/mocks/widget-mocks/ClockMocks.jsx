import WidgetCard from "../../WidgetCard";
import { mockClocks } from "../mockData";
import styles from "./ClockMocks.module.css";

function VariantStacked() {
  const { primary, aux } = mockClocks;

  return (
    <WidgetCard className={styles.variantStacked}>
      <div className={styles.stackedGreeting}>Good Morning</div>
      <div className={styles.stackedPrimaryTime}>{primary.time}</div>
      <div className={styles.stackedPrimaryLabel}>{primary.label}</div>
      <div className={styles.stackedDate}>{primary.date}</div>
      <div className={styles.stackedDivider} />
      <div className={styles.stackedAuxRow}>
        {aux.map((clock) => (
          <div key={clock.timezone} className={styles.stackedAuxClock}>
            <div className={styles.stackedAuxLabel}>{clock.label}</div>
            <div className={styles.stackedAuxTime}>{clock.time}</div>
          </div>
        ))}
      </div>
    </WidgetCard>
  );
}

function VariantStrip() {
  const { primary, aux } = mockClocks;

  return (
    <WidgetCard className={styles.variantStrip}>
      <div className={styles.stripGreeting}>Good Morning</div>
      <div className={styles.stripRow}>
        <div className={styles.stripClock}>
          <div className={styles.stripAuxLabel}>{aux[0].label}</div>
          <div className={styles.stripAuxTime}>{aux[0].time}</div>
        </div>
        <div className={styles.stripDivider} />
        <div className={styles.stripClockPrimary}>
          <div className={styles.stripPrimaryLabel}>{primary.label}</div>
          <div className={styles.stripPrimaryTime}>{primary.time}</div>
          <div className={styles.stripPrimaryAccent} />
          <div className={styles.stripPrimaryDate}>{primary.date}</div>
        </div>
        <div className={styles.stripDivider} />
        <div className={styles.stripClock}>
          <div className={styles.stripAuxLabel}>{aux[1].label}</div>
          <div className={styles.stripAuxTime}>{aux[1].time}</div>
        </div>
      </div>
    </WidgetCard>
  );
}

export default function ClockMocks() {
  return (
    <div className={styles.grid}>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant A: Stacked</div>
        <VariantStacked />
      </div>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant B: World Clock Strip</div>
        <VariantStrip />
      </div>
    </div>
  );
}
