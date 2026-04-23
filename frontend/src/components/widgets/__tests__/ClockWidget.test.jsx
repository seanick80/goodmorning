import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ClockWidget from "../ClockWidget";

vi.mock("../../../api/timers", () => ({
  fetchTimers: vi.fn(() => Promise.resolve([])),
  cancelTimer: vi.fn(),
  dismissTimers: vi.fn(),
}));

function renderWithQuery(ui) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

describe("ClockWidget", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 3, 3, 9, 30, 0));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders greeting, time, and date", () => {
    renderWithQuery(<ClockWidget settings={{}} />);
    expect(screen.getByText("Good Morning")).toBeInTheDocument();
  });

  it("shows Good Morning for hour 5-11", () => {
    vi.setSystemTime(new Date(2026, 3, 3, 5, 0, 0));
    renderWithQuery(<ClockWidget settings={{}} />);
    expect(screen.getByText("Good Morning")).toBeInTheDocument();
  });

  it("shows Good Afternoon for hour 12-16", () => {
    vi.setSystemTime(new Date(2026, 3, 3, 14, 0, 0));
    renderWithQuery(<ClockWidget settings={{}} />);
    expect(screen.getByText("Good Afternoon")).toBeInTheDocument();
  });

  it("shows Good Evening for hour 17+", () => {
    vi.setSystemTime(new Date(2026, 3, 3, 20, 0, 0));
    renderWithQuery(<ClockWidget settings={{}} />);
    expect(screen.getByText("Good Evening")).toBeInTheDocument();
  });

  it("shows Good Evening for hour 0-4", () => {
    vi.setSystemTime(new Date(2026, 3, 3, 3, 0, 0));
    renderWithQuery(<ClockWidget settings={{}} />);
    expect(screen.getByText("Good Evening")).toBeInTheDocument();
  });

  it("does not display seconds in time", () => {
    vi.setSystemTime(new Date(2026, 3, 3, 9, 30, 45));
    renderWithQuery(<ClockWidget settings={{}} />);
    const timeEl = document.querySelector("[class*='primaryTime']");
    expect(timeEl).toBeInTheDocument();
    expect(timeEl.textContent).not.toMatch(/:\d{2}:\d{2}/);
    expect(timeEl.textContent).toMatch(/9:30/);
  });

  it("renders 24h format when configured", () => {
    vi.setSystemTime(new Date(2026, 3, 3, 14, 30, 0));
    renderWithQuery(<ClockWidget settings={{ format: "24h" }} />);
    const timeEl = document.querySelector("[class*='primaryTime']");
    expect(timeEl.textContent).toMatch(/14:30/);
    expect(timeEl.textContent).not.toMatch(/AM|PM/);
  });

  it("renders aux clocks when configured", () => {
    renderWithQuery(
      <ClockWidget
        settings={{
          aux: [
            { timezone: "America/New_York", label: "New York" },
            { timezone: "Europe/London", label: "London" },
          ],
        }}
      />,
    );
    expect(screen.getByText("New York")).toBeInTheDocument();
    expect(screen.getByText("London")).toBeInTheDocument();
  });

  it("filters out invalid timezones from aux", () => {
    renderWithQuery(
      <ClockWidget
        settings={{
          aux: [
            { timezone: "Invalid/Zone", label: "Bad" },
            { timezone: "America/New_York", label: "New York" },
          ],
        }}
      />,
    );
    expect(screen.queryByText("Bad")).not.toBeInTheDocument();
    expect(screen.getByText("New York")).toBeInTheDocument();
  });

  it("renders date string", () => {
    renderWithQuery(<ClockWidget settings={{}} />);
    expect(screen.getByText(/April/)).toBeInTheDocument();
    expect(screen.getByText(/2026/)).toBeInTheDocument();
  });
});
