/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the page and the API are on different ports; the proxy keeps
// them on one origin, so no CORS setup is needed to try it.
const API = process.env.VITE_API_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  // The recorded demo is a static site that may be served from a sub-path.
  base: mode === "demo" ? "./" : "/",
  server: {
    proxy: { "/api": API, "/ready": API, "/health": API },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
  },
}));
