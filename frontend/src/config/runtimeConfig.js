const isProduction = process.env.NODE_ENV === "production";

export const API_PREFIX = process.env.REACT_APP_API_PREFIX || "/api/v1";

export const API_BASE =
  process.env.REACT_APP_API_URL ||
  (isProduction ? "https://raaga-therapy.onrender.com" : "http://localhost:8000");

export const WS_URL =
  process.env.REACT_APP_WS_URL ||
  `${API_BASE.replace(/^http/, "ws")}${API_PREFIX}/ws/live`;

