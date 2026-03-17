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
  { source_name: "AP News", title: "Space agency announces new Mars mission timeline", published_at: "6h ago" },
  { source_name: "Bloomberg", title: "Global supply chain disruptions ease as shipping normalizes", published_at: "7h ago" },
];

export const mockHourlyForecast = [
  { time: "Now", temp: 72, code: 1 },
  { time: "10 AM", temp: 74, code: 1 },
  { time: "11 AM", temp: 76, code: 2 },
  { time: "12 PM", temp: 78, code: 2 },
  { time: "1 PM", temp: 77, code: 3 },
  { time: "2 PM", temp: 75, code: 3 },
];

export const mockClocks = {
  primary: { timezone: "America/New_York", label: "New York", time: "10:30 AM", date: "Monday, March 17, 2026" },
  aux: [
    { timezone: "Europe/London", label: "London", time: "3:30 PM" },
    { timezone: "Asia/Tokyo", label: "Tokyo", time: "12:30 AM" },
  ],
};

export const mockStocksDetailed = [
  { symbol: "AAPL", name: "Apple Inc.", current_price: "178.23", change: "1.15", change_percent: "0.65", high: "179.50", low: "176.80", open: "177.10" },
  { symbol: "GOOGL", name: "Alphabet Inc.", current_price: "141.80", change: "-0.45", change_percent: "-0.32", high: "143.00", low: "140.90", open: "142.25" },
  { symbol: "MSFT", name: "Microsoft Corp.", current_price: "415.60", change: "3.20", change_percent: "0.78", high: "417.00", low: "412.30", open: "413.00" },
  { symbol: "AMZN", name: "Amazon.com Inc.", current_price: "186.40", change: "-1.10", change_percent: "-0.59", high: "188.00", low: "185.50", open: "187.50" },
];
