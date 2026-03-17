import WidgetCard from "../../WidgetCard";
import { mockStocks, mockStocksDetailed } from "../mockData";
import styles from "./StocksMocks.module.css";

function ChangeIndicator({ change, percent }) {
  const val = parseFloat(change);
  const isUp = val >= 0;
  const arrow = isUp ? "\u25B2" : "\u25BC";
  const cls = isUp ? styles.up : styles.down;
  return (
    <span className={cls}>
      {arrow} {Math.abs(parseFloat(percent)).toFixed(2)}%
    </span>
  );
}

function VariantTable() {
  return (
    <WidgetCard title="Stocks">
      {mockStocks.map((s) => (
        <div key={s.symbol} className={styles.tableRow}>
          <span className={styles.tableSymbol}>{s.symbol}</span>
          <span className={styles.tablePrice}>${s.current_price}</span>
          <span className={styles.tableChange}>
            <ChangeIndicator change={s.change} percent={s.change_percent} />
          </span>
        </div>
      ))}
    </WidgetCard>
  );
}

function VariantCards() {
  return (
    <WidgetCard title="Stocks">
      <div className={styles.cardsGrid}>
        {mockStocks.map((s) => {
          const val = parseFloat(s.change);
          const isUp = val >= 0;
          return (
            <div key={s.symbol} className={styles.card}>
              <div className={styles.cardSymbol}>{s.symbol}</div>
              <div className={styles.cardPrice}>${s.current_price}</div>
              <div className={`${styles.cardBadge} ${isUp ? styles.badgeUp : styles.badgeDown}`}>
                {isUp ? "\u25B2" : "\u25BC"} {Math.abs(parseFloat(s.change_percent)).toFixed(2)}%
              </div>
            </div>
          );
        })}
      </div>
    </WidgetCard>
  );
}

function VariantTicker() {
  const items = [...mockStocks, ...mockStocks];
  const tickerContent = items.map((s, i) => {
    const val = parseFloat(s.change);
    const isUp = val >= 0;
    return (
      <span key={i} className={styles.tickerItem}>
        <span className={styles.tickerSymbol}>{s.symbol}</span>
        <span className={styles.tickerPrice}>${s.current_price}</span>
        <span className={isUp ? styles.up : styles.down}>
          {isUp ? "\u25B2" : "\u25BC"}{Math.abs(val).toFixed(2)}
        </span>
      </span>
    );
  });

  return (
    <WidgetCard title="Stocks">
      <div className={styles.tickerTrack}>
        <div className={styles.tickerScroll}>
          {tickerContent}
          {tickerContent}
        </div>
      </div>
    </WidgetCard>
  );
}

function VariantDetailed() {
  return (
    <WidgetCard title="Stocks">
      {mockStocksDetailed.map((s, i) => {
        const val = parseFloat(s.change);
        const isUp = val >= 0;
        return (
          <div
            key={s.symbol}
            className={`${styles.detailedRow} ${i % 2 === 0 ? styles.detailedRowAlt : ""}`}
          >
            <div className={styles.detailedLeft}>
              <span className={styles.detailedSymbol}>{s.symbol}</span>
              <span className={styles.detailedName}>{s.name}</span>
            </div>
            <div className={styles.detailedRight}>
              <span className={styles.detailedPrice}>${s.current_price}</span>
              <span className={isUp ? styles.up : styles.down}>
                {isUp ? "+" : ""}{s.change} ({Math.abs(parseFloat(s.change_percent)).toFixed(2)}%)
              </span>
            </div>
            <div className={styles.detailedMeta}>
              <span>O: ${s.open}</span>
              <span>H: ${s.high}</span>
              <span>L: ${s.low}</span>
            </div>
          </div>
        );
      })}
    </WidgetCard>
  );
}

export default function StocksMocks() {
  return (
    <div className={styles.grid}>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant A: Table</div>
        <VariantTable />
      </div>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant B: Cards</div>
        <VariantCards />
      </div>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant C: Ticker Strip</div>
        <VariantTicker />
      </div>
      <div className={styles.variantWrapper}>
        <div className={styles.variantLabel}>Variant D: Detailed List</div>
        <VariantDetailed />
      </div>
    </div>
  );
}
