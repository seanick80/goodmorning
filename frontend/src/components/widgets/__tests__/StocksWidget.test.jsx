import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import StocksWidget from "../StocksWidget";

vi.mock("../../../hooks/useStocks", () => ({
  useStocks: vi.fn(),
}));
vi.mock("../../StaleIndicator", () => ({
  default: () => null,
}));

import { useStocks } from "../../../hooks/useStocks";

const mockStocks = [
  {
    symbol: "AAPL",
    current_price: "185.50",
    change: "2.30",
    change_percent: "1.25",
    fetched_at: new Date().toISOString(),
  },
  {
    symbol: "GOOGL",
    current_price: "142.80",
    change: "-1.10",
    change_percent: "-0.76",
    fetched_at: new Date().toISOString(),
  },
];

describe("StocksWidget", () => {
  it("shows loading state", () => {
    useStocks.mockReturnValue({ data: null, isLoading: true, isError: false });
    render(<StocksWidget />);
    expect(screen.getByText("Loading stocks...")).toBeInTheDocument();
  });

  it("shows error state", () => {
    useStocks.mockReturnValue({ data: null, isLoading: false, isError: true });
    render(<StocksWidget />);
    expect(screen.getByText("Unable to load stock data")).toBeInTheDocument();
  });

  it("renders stock symbols and prices", () => {
    useStocks.mockReturnValue({
      data: mockStocks,
      isLoading: false,
      isError: false,
    });
    render(<StocksWidget />);
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("$185.50")).toBeInTheDocument();
    expect(screen.getByText("GOOGL")).toBeInTheDocument();
    expect(screen.getByText("$142.80")).toBeInTheDocument();
  });

  it("shows up arrow and green class for positive change", () => {
    useStocks.mockReturnValue({
      data: mockStocks,
      isLoading: false,
      isError: false,
    });
    render(<StocksWidget />);
    const upChange = screen.getByText(/1\.25%/);
    expect(upChange.className).toContain("up");
    expect(upChange.textContent).toContain("▲");
  });

  it("shows down arrow and red class for negative change", () => {
    useStocks.mockReturnValue({
      data: mockStocks,
      isLoading: false,
      isError: false,
    });
    render(<StocksWidget />);
    const downChange = screen.getByText(/0\.76%/);
    expect(downChange.className).toContain("down");
    expect(downChange.textContent).toContain("▼");
  });

  it("renders links in normal mode", () => {
    useStocks.mockReturnValue({
      data: mockStocks,
      isLoading: false,
      isError: false,
    });
    render(<StocksWidget kioskMode={false} />);
    const links = document.querySelectorAll("a[href]");
    expect(links.length).toBe(2);
    expect(links[0].getAttribute("href")).toContain("AAPL");
  });

  it("disables links in kiosk mode", () => {
    useStocks.mockReturnValue({
      data: mockStocks,
      isLoading: false,
      isError: false,
    });
    render(<StocksWidget kioskMode={true} />);
    const links = document.querySelectorAll("a[href]");
    expect(links.length).toBe(0);
  });
});
