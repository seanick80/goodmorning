import { describe, it, expect, vi, beforeEach } from "vitest";
import { fetchGlucose } from "../glucose";
import * as client from "../client";

vi.mock("../client");

describe("fetchGlucose", () => {
  beforeEach(() => vi.clearAllMocks());

  it("calls apiFetch with /glucose/", async () => {
    client.apiFetch.mockResolvedValue({ current: {}, history: [] });
    const result = await fetchGlucose();
    expect(client.apiFetch).toHaveBeenCalledWith("/glucose/");
    expect(result).toEqual({ current: {}, history: [] });
  });
});
