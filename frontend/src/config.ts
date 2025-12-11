// frontend/src/config.ts

// Base URL for the Python backend (FastAPI) – local fallback.
export const BACKEND_BASE_URL =
  import.meta.env.VITE_BACKEND_BASE_URL || "http://127.0.0.1:4000";

// Base URL used to build public verify URLs inside QR codes.
export const PUBLIC_VERIFY_BASE =
  import.meta.env.VITE_PUBLIC_VERIFY_BASE || "http://localhost:5173/verify";