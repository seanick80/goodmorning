import WidgetCard from "../WidgetCard";
import { mockWeather, mockStocks, mockCalendar, mockNews } from "./mockData";
import styles from "./MockLayoutFeatured.module.css";

export default function MockLayoutFeatured() {
  return (
    <div className={styles.featured}>
      {/* Clock - small overlay in top-right */}
      <WidgetCard className={styles.clockOverlay}>
        <div className={styles.greeting}>Good Morning</div>
        <div className={styles.time}>10:30 AM</div>
        <div className={styles.date}>Monday, March 17, 2026</div>
      </WidgetCard>

      {/* Featured Weather - large central card */}
      <WidgetCard className={styles.weatherFeatured}>
        <div className={styles.weatherTop}>
          <span className={styles.weatherEmoji}>{"\u26C5"}</span>
          <div className={styles.weatherTempBlock}>
            <div className={styles.weatherTemp}>
              {Math.round(mockWeather.temperature)}
              <span className={styles.weatherUnit}>{"\u00B0F"}</span>
            </div>
          </div>
        </div>
        <div className={styles.weatherDesc}>{mockWeather.weather_description}</div>
        <div className={styles.weatherDetails}>
          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>Feels like</span>
            <span className={styles.detailValue}>{Math.round(mockWeather.feels_like)}{"\u00B0F"}</span>
          </div>
          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>High / Low</span>
            <span className={styles.detailValue}>{Math.round(mockWeather.daily_high)}{"\u00B0F"} / {Math.round(mockWeather.daily_low)}{"\u00B0F"}</span>
          </div>
          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>Humidity</span>
            <span className={styles.detailValue}>{mockWeather.humidity}%</span>
          </div>
          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>Sunrise / Sunset</span>
            <span className={styles.detailValue}>{mockWeather.sunrise} / {mockWeather.sunset}</span>
          </div>
        </div>
      </WidgetCard>

      {/* Bottom row: Stocks, Calendar, News */}
      <div className={styles.bottomRow}>
        <WidgetCard title="Stocks">
          {mockStocks.map((stock) => {
            const isUp = parseFloat(stock.change) >= 0;
            return (
              <div key={stock.symbol} className={styles.stockRow}>
                <span className={styles.stockSymbol}>{stock.symbol}</span>
                <span className={styles.stockPrice}>${stock.current_price}</span>
                <span className={`${styles.stockChange} ${isUp ? styles.stockUp : styles.stockDown}`}>
                  {isUp ? "\u25B2" : "\u25BC"} {Math.abs(parseFloat(stock.change_percent)).toFixed(2)}%
                </span>
              </div>
            );
          })}
        </WidgetCard>

        <WidgetCard title="Calendar">
          {mockCalendar.map((event, i) => (
            <div key={i} className={styles.calendarEvent}>
              <span className={styles.calendarTime}>{event.start} - {event.end}</span>
              <span className={styles.calendarTitle}>{event.title}</span>
              <span className={styles.calendarLocation}>{event.location}</span>
            </div>
          ))}
        </WidgetCard>

        <WidgetCard title="News">
          {mockNews.map((item, i) => (
            <div key={i} className={styles.newsItem}>
              <div className={styles.newsTitle}>{item.title}</div>
              <div className={styles.newsMeta}>
                <span className={styles.newsSource}>{item.source_name}</span> &middot; {item.published_at}
              </div>
            </div>
          ))}
        </WidgetCard>
      </div>
    </div>
  );
}
