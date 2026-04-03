import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import NewsWidget from "../NewsWidget";

vi.mock("../../../hooks/useNews", () => ({
  useNews: vi.fn(),
}));
vi.mock("../../StaleIndicator", () => ({
  default: () => null,
}));

import { useNews } from "../../../hooks/useNews";

const mockHeadlines = [
  {
    title: "Test Headline One",
    link: "https://example.com/1",
    source_name: "Test Source",
    published_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    fetched_at: new Date().toISOString(),
  },
  {
    title: "Test Headline Two",
    link: "https://example.com/2",
    source_name: "Other Source",
    published_at: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
    fetched_at: new Date().toISOString(),
  },
];

describe("NewsWidget", () => {
  it("shows loading state", () => {
    useNews.mockReturnValue({ data: null, isLoading: true, isError: false });
    render(<NewsWidget settings={{}} />);
    expect(screen.getByText("Loading news...")).toBeInTheDocument();
  });

  it("shows error state", () => {
    useNews.mockReturnValue({ data: null, isLoading: false, isError: true });
    render(<NewsWidget settings={{}} />);
    expect(screen.getByText("Unable to load news")).toBeInTheDocument();
  });

  it("shows empty state", () => {
    useNews.mockReturnValue({ data: [], isLoading: false, isError: false });
    render(<NewsWidget settings={{}} />);
    expect(screen.getByText("No headlines available")).toBeInTheDocument();
  });

  it("renders headline title", () => {
    useNews.mockReturnValue({
      data: mockHeadlines,
      isLoading: false,
      isError: false,
    });
    render(<NewsWidget settings={{}} />);
    expect(screen.getByText("Test Headline One")).toBeInTheDocument();
  });

  it("renders source name", () => {
    useNews.mockReturnValue({
      data: mockHeadlines,
      isLoading: false,
      isError: false,
    });
    render(<NewsWidget settings={{}} />);
    expect(screen.getByText("Test Source")).toBeInTheDocument();
  });

  it("renders relative time", () => {
    useNews.mockReturnValue({
      data: mockHeadlines,
      isLoading: false,
      isError: false,
    });
    render(<NewsWidget settings={{}} />);
    const meta = document.querySelector(".meta");
    expect(meta.textContent).toContain("1h ago");
  });

  it("renders navigation when multiple headlines", () => {
    useNews.mockReturnValue({
      data: mockHeadlines,
      isLoading: false,
      isError: false,
    });
    render(<NewsWidget settings={{}} />);
    expect(screen.getByText("1 / 2")).toBeInTheDocument();
    expect(screen.getByLabelText("Previous headline")).toBeInTheDocument();
    expect(screen.getByLabelText("Next headline")).toBeInTheDocument();
  });

  it("does not render navigation for single headline", () => {
    useNews.mockReturnValue({
      data: [mockHeadlines[0]],
      isLoading: false,
      isError: false,
    });
    render(<NewsWidget settings={{}} />);
    expect(screen.queryByLabelText("Previous headline")).not.toBeInTheDocument();
  });

  it("renders links in normal mode", () => {
    useNews.mockReturnValue({
      data: [mockHeadlines[0]],
      isLoading: false,
      isError: false,
    });
    render(<NewsWidget settings={{}} kioskMode={false} />);
    const link = document.querySelector("a[href]");
    expect(link).toBeInTheDocument();
    expect(link.getAttribute("href")).toBe("https://example.com/1");
  });

  it("disables links in kiosk mode", () => {
    useNews.mockReturnValue({
      data: [mockHeadlines[0]],
      isLoading: false,
      isError: false,
    });
    render(<NewsWidget settings={{}} kioskMode={true} />);
    const links = document.querySelectorAll("a[href]");
    expect(links.length).toBe(0);
  });
});
