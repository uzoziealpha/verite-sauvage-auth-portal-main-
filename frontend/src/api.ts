// frontend/src/api.ts

import { BACKEND_BASE_URL } from "./config";

// Base URL that the whole frontend uses for the backend
export const BACKEND = BACKEND_BASE_URL;

export async function fetchJSON(url: string, init?: RequestInit) {
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    ...init,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP_${res.status}: ${text}`);
  }

  return res.json();
}

/**
 * Fetch the contract artifact (ABI + networks) from the backend.
 * Backend exposes this at GET /artifact.
 */
export async function getArtifact() {
  return fetchJSON(`${BACKEND}/artifact`);
}
