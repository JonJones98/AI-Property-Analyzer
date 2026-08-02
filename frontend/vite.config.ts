import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Reads .env from the repo root so backend and frontend share one file.
export default defineConfig({
  envDir: "../",
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
  },
});
