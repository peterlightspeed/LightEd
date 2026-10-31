"use client";

/** Last-resort boundary (errors in the root layout). Uses inline styles: the app CSS may not be available here. */
export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif", background: "#f4f6fc", color: "#0f1b33" }}>
        <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: 24, textAlign: "center" }}>
          <div style={{ maxWidth: 360 }}>
            <h1 style={{ fontSize: 22, margin: "0 0 8px" }}>Something went wrong</h1>
            <p style={{ margin: "0 0 20px", color: "#6b7a99", lineHeight: 1.5 }}>
              LightEd hit an unexpected problem. Your progress is saved. Please try again.
            </p>
            <button
              onClick={reset}
              style={{ background: "#1f55e6", color: "#fff", border: 0, borderRadius: 14, padding: "14px 22px", fontSize: 16, fontWeight: 600 }}
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
