import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import CalendarWidget from "../CalendarWidget";

vi.mock("../../../hooks/useCalendar", () => ({
  useCalendar: vi.fn(),
}));
vi.mock("../../../hooks/useAuth", () => ({
  useAuth: vi.fn(() => ({ data: null })),
}));
vi.mock("../../../hooks/useDashboard", () => ({
  useDashboard: vi.fn(() => ({ data: null })),
}));
vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(() => ({ data: null, isLoading: false, isError: false })),
  useQueryClient: vi.fn(() => ({ invalidateQueries: vi.fn() })),
}));
vi.mock("../../../api/auth", () => ({
  fetchGoogleCalendars: vi.fn(),
  patchDashboard: vi.fn(),
}));
vi.mock("../../StaleIndicator", () => ({
  default: () => null,
}));

import { useCalendar } from "../../../hooks/useCalendar";

describe("CalendarWidget", () => {
  it("shows loading state", () => {
    useCalendar.mockReturnValue({ data: null, isLoading: true, isError: false });
    render(<CalendarWidget />);
    expect(screen.getByText("Loading calendar...")).toBeInTheDocument();
  });

  it("shows error state", () => {
    useCalendar.mockReturnValue({ data: null, isLoading: false, isError: true });
    render(<CalendarWidget />);
    expect(screen.getByText("Unable to load calendar")).toBeInTheDocument();
  });

  it("shows empty state", () => {
    useCalendar.mockReturnValue({ data: [], isLoading: false, isError: false });
    render(<CalendarWidget />);
    expect(screen.getByText("No events today")).toBeInTheDocument();
  });

  it("renders event title and time", () => {
    const now = new Date();
    const eventStart = new Date(now);
    eventStart.setHours(14, 0, 0, 0);
    const eventEnd = new Date(now);
    eventEnd.setHours(15, 0, 0, 0);

    useCalendar.mockReturnValue({
      data: [
        {
          title: "Team Standup",
          start: eventStart.toISOString(),
          end: eventEnd.toISOString(),
          all_day: false,
          location: null,
          fetched_at: new Date().toISOString(),
        },
      ],
      isLoading: false,
      isError: false,
    });
    render(<CalendarWidget />);
    expect(screen.getByText("Team Standup")).toBeInTheDocument();
  });

  it("shows All day for all-day events", () => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    useCalendar.mockReturnValue({
      data: [
        {
          title: "Holiday",
          start: today.toISOString(),
          end: today.toISOString(),
          all_day: true,
          location: null,
          fetched_at: new Date().toISOString(),
        },
      ],
      isLoading: false,
      isError: false,
    });
    render(<CalendarWidget />);
    expect(screen.getByText("All day")).toBeInTheDocument();
    expect(screen.getByText("Holiday")).toBeInTheDocument();
  });

  it("renders event location when present", () => {
    const today = new Date();
    today.setHours(10, 0, 0, 0);

    useCalendar.mockReturnValue({
      data: [
        {
          title: "Lunch",
          start: today.toISOString(),
          end: today.toISOString(),
          all_day: false,
          location: "Conference Room B",
          fetched_at: new Date().toISOString(),
        },
      ],
      isLoading: false,
      isError: false,
    });
    render(<CalendarWidget />);
    expect(screen.getByText("Conference Room B")).toBeInTheDocument();
  });

  it("has a configure button", () => {
    useCalendar.mockReturnValue({ data: [], isLoading: false, isError: false });
    render(<CalendarWidget />);
    expect(screen.getAllByLabelText("Configure calendar").length).toBeGreaterThan(0);
  });
});
