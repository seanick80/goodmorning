const BASE_URL = "/api";

export async function apiFetch(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = new Error(
      `API error: ${response.status} ${response.statusText}`
    );
    error.status = response.status;
    throw error;
  }

  return response.json();
}
