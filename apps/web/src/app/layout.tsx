import type { Metadata, Viewport } from "next";

import { AuthProvider } from "@/lib/auth-context";
import { SITE_URL } from "@/lib/site";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "LightEd — Personalized learning, powered by AI",
  description:
    "LightEd is an AI-assisted learning platform for students and teachers: adaptive lessons, instant quizzes, and progress insights.",
  openGraph: {
    title: "LightEd — Personalized learning, powered by AI",
    description: "Adaptive lessons, instant quizzes and progress insights for students and teachers.",
    images: [{ url: "/og.png", width: 1200, height: 630, alt: "LightEd" }],
    type: "website",
  },
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
