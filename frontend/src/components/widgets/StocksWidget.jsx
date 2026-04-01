import { useStocks } from "../../hooks/useStocks";
import StaleIndicator from "../StaleIndicator";
import WidgetCard from "../WidgetCard";
import styles from "./StocksWidget.module.css";

export default function StocksWidget({ kioskMode }) {
  const { data, isLoading, isError } = useStocks();

  if (isLoading) {
    return (
      <WidgetCard title="Stocks">
        <div className={styles.loading}>Loading stocks...</div>
      </WidgetCard>
    );
  }

  if (isError) {
    return (
      <WidgetCard title="Stocks">
        <div className={styles.error}>Unable to load stock data</div>
      </WidgetCard>
    );
  }

  const stocks = Array.isArray(data) ? data : [];

  return (
    <WidgetCard title="Stocks" titleExtra={<StaleIndicator fetchedAt={stocks[0]?.fetched_at} />}>
      {stocks.map((stock) => {
        const change = parseFloat(stock.change);
        const isUp = change >= 0;
        return (
          <a
            key={stock.symbol}
            className={styles.row}
            href={kioskMode ? undefined : `https://www.google.com/finance/quote/${stock.symbol}:NASDAQ`}
            target={kioskMode ? undefined : "_blank"}
            rel={kioskMode ? undefined : "noopener noreferrer"}
            onClick={kioskMode ? (e) => e.preventDefault() : undefined}
          >
            <span className={styles.symbol}>{stock.symbol}</span>
            <span className={styles.price}>
              ${parseFloat(stock.current_price).toFixed(2)}
            </span>
            <span
              className={`${styles.change} ${isUp ? styles.up : styles.down}`}
            >
              {isUp ? "\u25B2" : "\u25BC"}{" "}
              {Math.abs(parseFloat(stock.change_percent)).toFixed(2)}%
            </span>
          </a>
        );
      })}
    </WidgetCard>
  );
}
