import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import GlucoseWidget from "../GlucoseWidget";

vi.mock("../../../hooks/useGlucose", () => ({
  useGlucose: vi.fn(),
}));
vi.mock("../../StaleIndicator", () => ({
  default: () => null,
}));

import { useGlucose } from "../../../hooks/useGlucose";

describe("GlucoseWidget", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 3, 3, 10, 0, 0));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows loading state", () => {
    useGlucose.mockReturnValue({ data: null, isLoading: true, isError: false });
    render(<GlucoseWidget />);
    expect(screen.getByText("Loading glucose...")).toBeInTheDocument();
  });

  it("shows error state when no data", () => {
    useGlucose.mockReturnValue({ data: null, isLoading: false, isError: true });
    render(<GlucoseWidget />);
    expect(screen.getByText("No glucose data")).toBeInTheDocument();
  });

  it("shows error state when current is missing", () => {
    useGlucose.mockReturnValue({
      data: { current: null, history: [] },
      isLoading: false,
      isError: false,
    });
    render(<GlucoseWidget />);
    expect(screen.getByText("No glucose data")).toBeInTheDocument();
  });

  it("renders current glucose value and unit", () => {
    useGlucose.mockReturnValue({
      data: {
        current: {
          value: 120,
          trend_arrow: "→",
          recorded_at: new Date(2026, 3, 3, 9, 55, 0).toISOString(),
          fetched_at: new Date(2026, 3, 3, 9, 55, 0).toISOString(),
        },
        history: [],
      },
      isLoading: false,
      isError: false,
    });
    render(<GlucoseWidget />);
    expect(screen.getByText("120")).toBeInTheDocument();
    expect(screen.getByText("mg/dL")).toBeInTheDocument();
    expect(screen.getByText("→")).toBeInTheDocument();
  });

  it("applies inRange class for normal values (70-180)", () => {
    useGlucose.mockReturnValue({
      data: {
        current: {
          value: 120,
          trend_arrow: "→",
          recorded_at: new Date(2026, 3, 3, 9, 55, 0).toISOString(),
          fetched_at: new Date(2026, 3, 3, 9, 55, 0).toISOString(),
        },
        history: [],
      },
      isLoading: false,
      isError: false,
    });
    render(<GlucoseWidget />);
    const valueEl = screen.getByText("120");
    expect(valueEl.className).toContain("inRange");
  });

  it("applies highRange class for value > 180", () => {
    useGlucose.mockReturnValue({
      data: {
        current: {
          value: 200,
          trend_arrow: "↑",
          recorded_at: new Date(2026, 3, 3, 9, 55, 0).toISOString(),
          fetched_at: new Date(2026, 3, 3, 9, 55, 0).toISOString(),
        },
        history: [],
      },
      isLoading: false,
      isError: false,
    });
    render(<GlucoseWidget />);
    const valueEl = screen.getByText("200");
    expect(valueEl.className).toContain("highRange");
  });

  it("applies urgentRange class for value > 250", () => {
    useGlucose.mockReturnValue({
      data: {
        current: {
          value: 280,
          trend_arrow: "↑↑",
          recorded_at: new Date(2026, 3, 3, 9, 55, 0).toISOString(),
          fetched_at: new Date(2026, 3, 3, 9, 55, 0).toISOString(),
        },
        history: [],
      },
      isLoading: false,
      isError: false,
    });
    render(<GlucoseWidget />);
    const valueEl = screen.getByText("280");
    expect(valueEl.className).toContain("urgentRange");
  });

  it("applies highRange class for value < 70", () => {
    useGlucose.mockReturnValue({
      data: {
        current: {
          value: 65,
          trend_arrow: "↓",
          recorded_at: new Date(2026, 3, 3, 9, 55, 0).toISOString(),
          fetched_at: new Date(2026, 3, 3, 9, 55, 0).toISOString(),
        },
        history: [],
      },
      isLoading: false,
      isError: false,
    });
    render(<GlucoseWidget />);
    const valueEl = screen.getByText("65");
    expect(valueEl.className).toContain("highRange");
  });

  it("applies urgentRange class for value < 55", () => {
    useGlucose.mockReturnValue({
      data: {
        current: {
          value: 50,
          trend_arrow: "↓↓",
          recorded_at: new Date(2026, 3, 3, 9, 55, 0).toISOString(),
          fetched_at: new Date(2026, 3, 3, 9, 55, 0).toISOString(),
        },
        history: [],
      },
      isLoading: false,
      isError: false,
    });
    render(<GlucoseWidget />);
    const valueEl = screen.getByText("50");
    expect(valueEl.className).toContain("urgentRange");
  });

  it("shows stale indicator when reading is >15 min old", () => {
    useGlucose.mockReturnValue({
      data: {
        current: {
          value: 120,
          trend_arrow: "→",
          recorded_at: new Date(2026, 3, 3, 9, 30, 0).toISOString(), // 30 min ago
          fetched_at: new Date(2026, 3, 3, 9, 30, 0).toISOString(),
        },
        history: [],
      },
      isLoading: false,
      isError: false,
    });
    render(<GlucoseWidget />);
    expect(screen.getByText("30 min ago")).toBeInTheDocument();
  });

  it("does not show stale indicator when reading is fresh", () => {
    useGlucose.mockReturnValue({
      data: {
        current: {
          value: 120,
          trend_arrow: "→",
          recorded_at: new Date(2026, 3, 3, 9, 55, 0).toISOString(), // 5 min ago
          fetched_at: new Date(2026, 3, 3, 9, 55, 0).toISOString(),
        },
        history: [],
      },
      isLoading: false,
      isError: false,
    });
    render(<GlucoseWidget />);
    expect(screen.queryByText(/min ago/)).not.toBeInTheDocument();
  });
});
