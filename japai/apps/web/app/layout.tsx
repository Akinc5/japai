import "./globals.css";
import Link from "next/link";

export const metadata = {
  title: "JA Assure™ AI Marketing OS",
  description: "Autonomous AI Marketing & Compliance Operating System for Jade, Jaguar Transit, and DoctorShield",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header
          style={{
            background: "rgba(7, 21, 39, 0.85)",
            backdropFilter: "blur(12px)",
            borderBottom: "1px solid rgba(26, 56, 96, 0.6)",
            position: "sticky",
            top: 0,
            zIndex: 1000,
            padding: "0.85rem 2rem",
          }}
        >
          <div
            style={{
              maxWidth: 1200,
              margin: "0 auto",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            {/* Brand Logo & Name */}
            <Link
              href="/"
              style={{
                textDecoration: "none",
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
              }}
            >
              <div
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: "8px",
                  background: "linear-gradient(135deg, #00d2ff 0%, #0070f3 100%)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 800,
                  color: "#040d1a",
                  fontSize: "1rem",
                  boxShadow: "0 0 16px rgba(0, 210, 255, 0.4)",
                }}
              >
                JA
              </div>
              <div>
                <div
                  style={{
                    color: "#f8fafc",
                    fontWeight: 800,
                    fontSize: "1.1rem",
                    letterSpacing: "-0.02em",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.4rem",
                  }}
                >
                  JA ASSURE<span style={{ color: "#00d2ff" }}>™</span>
                  <span
                    style={{
                      fontSize: "0.65rem",
                      fontWeight: 700,
                      background: "rgba(0, 210, 255, 0.15)",
                      color: "#00d2ff",
                      border: "1px solid rgba(0, 210, 255, 0.3)",
                      padding: "1px 6px",
                      borderRadius: "4px",
                      letterSpacing: "0.05em",
                    }}
                  >
                    AI OS
                  </span>
                </div>
                <div style={{ color: "#64748b", fontSize: "0.7rem", fontWeight: 500 }}>
                  Singapore • Malaysia • Hong Kong
                </div>
              </div>
            </Link>

            {/* Navigation links */}
            <nav style={{ display: "flex", alignItems: "center", gap: "1.25rem" }}>
              <Link
                href="/demo"
                style={{
                  color: "#e2e8f0",
                  textDecoration: "none",
                  fontSize: "0.88rem",
                  fontWeight: 600,
                  display: "flex",
                  alignItems: "center",
                  gap: "0.35rem",
                  transition: "color 0.15s ease",
                }}
              >
                <span style={{ color: "#00d2ff" }}>▶</span> Live Demo
              </Link>
              <Link
                href="/repurpose"
                style={{
                  color: "#94a3b8",
                  textDecoration: "none",
                  fontSize: "0.88rem",
                  fontWeight: 500,
                }}
              >
                Repurposer
              </Link>
              <Link
                href="/leads"
                style={{
                  color: "#94a3b8",
                  textDecoration: "none",
                  fontSize: "0.88rem",
                  fontWeight: 500,
                }}
              >
                OSM Leads
              </Link>
              <Link
                href="/visual-studio"
                style={{
                  color: "#94a3b8",
                  textDecoration: "none",
                  fontSize: "0.88rem",
                  fontWeight: 500,
                }}
              >
                Visual Studio
              </Link>
              <Link
                href="/events"
                style={{
                  color: "#94a3b8",
                  textDecoration: "none",
                  fontSize: "0.88rem",
                  fontWeight: 500,
                }}
              >
                Events
              </Link>
              <Link
                href="/review"
                style={{
                  color: "#94a3b8",
                  textDecoration: "none",
                  fontSize: "0.88rem",
                  fontWeight: 500,
                }}
              >
                Review
              </Link>
              <Link
                href="/observability"
                style={{
                  color: "#94a3b8",
                  textDecoration: "none",
                  fontSize: "0.88rem",
                  fontWeight: 500,
                }}
              >
                Observability
              </Link>
            </nav>

            {/* Brand Vertical Badges */}
            <div style={{ display: "flex", gap: "0.4rem" }}>
              <span
                style={{
                  fontSize: "0.7rem",
                  fontWeight: 700,
                  padding: "3px 8px",
                  borderRadius: "9999px",
                  background: "rgba(16, 185, 129, 0.15)",
                  color: "#34d399",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                }}
              >
                💎 Jade
              </span>
              <span
                style={{
                  fontSize: "0.7rem",
                  fontWeight: 700,
                  padding: "3px 8px",
                  borderRadius: "9999px",
                  background: "rgba(245, 158, 11, 0.15)",
                  color: "#fbbf24",
                  border: "1px solid rgba(245, 158, 11, 0.3)",
                }}
              >
                🚢 Jaguar
              </span>
              <span
                style={{
                  fontSize: "0.7rem",
                  fontWeight: 700,
                  padding: "3px 8px",
                  borderRadius: "9999px",
                  background: "rgba(56, 189, 248, 0.15)",
                  color: "#38bdf8",
                  border: "1px solid rgba(56, 189, 248, 0.3)",
                }}
              >
                🩺 DoctorShield
              </span>
            </div>
          </div>
        </header>

        {children}
      </body>
    </html>
  );
}
