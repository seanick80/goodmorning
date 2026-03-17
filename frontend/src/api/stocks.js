import { apiFetch } from "./client";

export function fetchStocks() {
  return apiFetch("/stocks/");
}
