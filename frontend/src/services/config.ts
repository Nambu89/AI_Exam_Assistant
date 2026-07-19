/** Runtime configuration derived from Vite env vars. */

/** Base URL of the backend. Defaults to the documented local FastAPI port. */
export const API_URL: string =
  import.meta.env.VITE_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

/**
 * Whether to use the in-app mock layer instead of a live backend.
 * Defaults to ON in dev (so the app runs offline) and OFF in prod builds,
 * unless the env var explicitly overrides it.
 */
export const USE_MOCKS: boolean = (() => {
  const raw = import.meta.env.VITE_USE_MOCKS;
  if (raw === undefined || raw === "") return import.meta.env.DEV;
  return raw === "true" || raw === "1";
})();

/** Full URL for a given API path (path should start with `/api`). */
export function apiUrl(path: string): string {
  return `${API_URL}${path}`;
}
