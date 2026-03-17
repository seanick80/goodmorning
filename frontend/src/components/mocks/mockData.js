export const mockWeather = {
  temperature: 72.5,
  temperature_unit: "fahrenheit",
  feels_like: 70.0,
  humidity: 55,
  weather_code: 1,
  weather_description: "Mainly Clear",
  daily_high: 78.0,
  daily_low: 62.0,
  sunrise: "06:45",
  sunset: "19:12",
};

export const mockStocks = [
  { symbol: "AAPL", current_price: "178.23", change: "1.15", change_percent: "0.65" },
  { symbol: "GOOGL", current_price: "141.80", change: "-0.45", change_percent: "-0.32" },
  { symbol: "MSFT", current_price: "415.60", change: "3.20", change_percent: "0.78" },
  { symbol: "AMZN", current_price: "186.40", change: "-1.10", change_percent: "-0.59" },
];

export const mockCalendar = [
  { title: "Team standup", start: "09:00", end: "09:15", location: "Zoom" },
  { title: "Product review", start: "14:00", end: "15:00", location: "Conf Room B" },
  { title: "1:1 with manager", start: "16:00", end: "16:30", location: "Office" },
];

export const mockNews = [
  { source_name: "BBC News", title: "Major climate agreement reached at UN summit", published_at: "2h ago" },
  { source_name: "NPR", title: "Federal Reserve holds interest rates steady", published_at: "4h ago" },
  { source_name: "Reuters", title: "Tech stocks rally on strong earnings reports", published_at: "5h ago" },
];
