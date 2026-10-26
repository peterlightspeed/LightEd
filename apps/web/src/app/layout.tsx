import type { Metadata, Viewport } from "next";

import { AuthProvider } from "@/lib/auth-context";
import "./globals.css";

export const metadata: Metadata = {
  title: "LightEd — Personalized learning, powered by AI",
  description:
    "LightEd is an AI-assisted learning platform for students and teachers: adaptive lessons, instant quizzes, and progress insights.",
  keywords: ["LightEd", "AI tutor", "personalized learning", "education", "students", "teachers"],
};

export const viewport: Viewport = {
  themeColor: "#1D4076",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-mist font-sans text-ink antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
