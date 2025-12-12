// src/api.ts
import { BACKEND_BASE_URL } from "./config";

export const BACKEND = BACKEND_BASE_URL;

const ADMIN_TOKEN = import.meta.env.VITE_ADMIN_TOKEN || "";

/**
 * JSON fetch helper with:
 *  - default headers
 *  - optional X-Admin-Token for admin endpoints
 *  - throws on non-2xx
 */
export async function fetchJSON(
  url: string,
  options: RequestInit = {}
): Promise<any> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  // Automatically attach admin token to protected routes
  if (
    (url.includes("/verify/") ||
      url.includes("/codes") ||
      url.includes("/debug")) &&
    ADMIN_TOKEN
  ) {
    (headers as any)["X-Admin-Token"] = ADMIN_TOKEN;
  }

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP_${res.status}: ${text}`);
  }

  return res.json();
}

/**
 * Fetch the compiled contract artifact (ABI + networks + address)
 * from the backend.
 *
 * Backend route: GET /artifact
 */
export async function getArtifact(): Promise<any> {
  return fetchJSON(`${BACKEND}/artifact`);
}
