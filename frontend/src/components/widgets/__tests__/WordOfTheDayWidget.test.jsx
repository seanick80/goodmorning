import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import WordOfTheDayWidget from "../WordOfTheDayWidget";

vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(),
}));

import { useQuery } from "@tanstack/react-query";

describe("WordOfTheDayWidget", () => {
  it("shows loading state", () => {
    useQuery.mockReturnValue({ data: null, isLoading: true, isError: false });
    render(<WordOfTheDayWidget />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("shows error state", () => {
    useQuery.mockReturnValue({ data: null, isLoading: false, isError: true });
    render(<WordOfTheDayWidget />);
    expect(screen.getByText("Unable to load word")).toBeInTheDocument();
  });

  it("renders the word", () => {
    useQuery.mockReturnValue({
      data: {
        word: "cat",
        pattern: "at",
        pattern_position: "end",
        day_index: 0,
        is_weekend: false,
      },
      isLoading: false,
      isError: false,
    });
    render(<WordOfTheDayWidget />);
    const wordEl = document.querySelector(".word");
    expect(wordEl).toBeInTheDocument();
    expect(wordEl.textContent).toBe("cat");
  });

  it("highlights pattern at end of word", () => {
    useQuery.mockReturnValue({
      data: {
        word: "cat",
        pattern: "at",
        pattern_position: "end",
        day_index: 0,
        is_weekend: false,
      },
      isLoading: false,
      isError: false,
    });
    render(<WordOfTheDayWidget />);
    const highlight = document.querySelector(".highlight");
    expect(highlight).toBeInTheDocument();
    expect(highlight.textContent).toBe("at");
  });

  it("highlights pattern at start of word", () => {
    useQuery.mockReturnValue({
      data: {
        word: "shout",
        pattern: "sh",
        pattern_position: "start",
        day_index: 2,
        is_weekend: false,
      },
      isLoading: false,
      isError: false,
    });
    render(<WordOfTheDayWidget />);
    const highlight = document.querySelector(".highlight");
    expect(highlight).toBeInTheDocument();
    expect(highlight.textContent).toBe("sh");
  });

  it("highlights pattern in middle of word", () => {
    useQuery.mockReturnValue({
      data: {
        word: "book",
        pattern: "oo",
        pattern_position: "middle",
        day_index: 1,
        is_weekend: false,
      },
      isLoading: false,
      isError: false,
    });
    render(<WordOfTheDayWidget />);
    const highlight = document.querySelector(".highlight");
    expect(highlight).toBeInTheDocument();
    expect(highlight.textContent).toBe("oo");
  });

  it("shows pattern description", () => {
    useQuery.mockReturnValue({
      data: {
        word: "cat",
        pattern: "at",
        pattern_position: "end",
        day_index: 0,
        is_weekend: false,
      },
      isLoading: false,
      isError: false,
    });
    render(<WordOfTheDayWidget />);
    expect(screen.getByText(/-at/)).toBeInTheDocument();
  });

  it("renders weekday dots on weekdays", () => {
    useQuery.mockReturnValue({
      data: {
        word: "cat",
        pattern: "at",
        pattern_position: "end",
        day_index: 2,
        is_weekend: false,
      },
      isLoading: false,
      isError: false,
    });
    render(<WordOfTheDayWidget />);
    const dots = document.querySelectorAll(".dot, .dotActive, .dotCurrent");
    expect(dots.length).toBe(5);
  });

  it("does not render dots on weekends", () => {
    useQuery.mockReturnValue({
      data: {
        word: "cat",
        pattern: "at",
        pattern_position: "end",
        day_index: 4,
        is_weekend: true,
      },
      isLoading: false,
      isError: false,
    });
    render(<WordOfTheDayWidget />);
    const dotsContainer = document.querySelector(".dots");
    expect(dotsContainer).not.toBeInTheDocument();
  });

  it("marks active and current dots correctly", () => {
    useQuery.mockReturnValue({
      data: {
        word: "hat",
        pattern: "at",
        pattern_position: "end",
        day_index: 2,
        is_weekend: false,
      },
      isLoading: false,
      isError: false,
    });
    render(<WordOfTheDayWidget />);
    const activeDots = document.querySelectorAll("[class*='dotActive']");
    const currentDots = document.querySelectorAll("[class*='dotCurrent']");
    expect(activeDots.length).toBe(2); // days 0, 1
    expect(currentDots.length).toBe(1); // day 2
  });
});
