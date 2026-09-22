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
            background: "rgba(6, 16, 30, 0.9)",
            backdropFilter: "blur(12px)",
            borderBottom: "1px solid #162f52",
            position: "sticky",
            top: 0,
            zIndex: 1000,
            padding: "0.85rem 2rem",
          }}
        >
          <div
            style={{
              maxWidth: 1140,
              margin: "0 auto",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            {/* Brand Logo */}
            <Link
              href="/"
              style={{
                textDecoration: "none",
                display: "flex",
                alignItems: "center",
                gap: "0.6rem",
              }}
            >
              <div
                style={{
                  width: 30,
                  height: 30,
                  borderRadius: "6px",
                  background: "#00d2ff",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 800,
                  color: "#06101e",
                  fontSize: "0.85rem",
                }}
              >
                JA
              </div>
              <div
                style={{
                  color: "#ffffff",
                  fontWeight: 800,
                  fontSize: "1.05rem",
                  letterSpacing: "-0.02em",
                }}
              >
                JA ASSURE<span style={{ color: "#00d2ff" }}>™</span>
              </div>
            </Link>

            {/* Navigation links */}
            <nav style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
              <Link
                href="/demo"
                style={{
                  color: "#00d2ff",
                  textDecoration: "none",
                  fontSize: "0.88rem",
                  fontWeight: 600,
                }}
              >
                Live Demo
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
                Leads
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
                Visuals
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
                Logs
              </Link>
            </nav>
          </div>
        </header>

        {children}
      </body>
    </html>
  );
}
