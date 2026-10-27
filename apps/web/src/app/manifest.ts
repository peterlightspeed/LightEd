import type { MetadataRoute } from "next";

/** Web App Manifest: makes LightEd installable (Add to Home Screen) on Android, iOS and desktop. */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "LightEd — AI Learning Platform",
    short_name: "LightEd",
    description: "Personalized learning with an AI tutor, quizzes and progress insights.",
    start_url: "/dashboard",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#ffffff",
    theme_color: "#1f55e6",
    categories: ["education"],
    icons: [
      { src: "/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
