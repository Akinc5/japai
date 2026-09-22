import "./globals.css";
import Link from "next/link";

export const metadata = {
  title: "JA Assure™ — AI Marketing & Compliance OS",
  description: "Autonomous InsurTech Marketing Platform for Jade, Jaguar Transit, and DoctorShield",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ background: "#f8fafc", color: "#0a192f" }}>
        <header
          style={{
            background: "#ffffff",
            borderBottom: "1px solid #e2e8f0",
            position: "sticky",
            top: 0,
            zIndex: 1000,
            padding: "0.85rem 2rem",
            boxShadow: "0 1px 3px rgba(0, 0, 0, 0.03)",
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
                gap: "0.65rem",
              }}
            >
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: "6px",
                  background: "#0066cc",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 800,
                  color: "#ffffff",
                  fontSize: "0.9rem",
                }}
              >
                JA
              </div>
              <div>
                <div
                  style={{
                    color: "#002b49",
                    fontWeight: 800,
                    fontSize: "1.1rem",
                    letterSpacing: "-0.02em",
                  }}
                >
                  JA ASSURE<span style={{ color: "#0066cc" }}>™</span>
                </div>
              </div>
            </Link>

            {/* Navigation links */}
            <nav style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
              <Link
                href="/demo"
                style={{
                  color: "#0066cc",
                  textDecoration: "none",
                  fontSize: "0.9rem",
                  fontWeight: 600,
                }}
              >
                Live Demo
              </Link>
              <Link
                href="/repurpose"
                style={{
                  color: "#475569",
                  textDecoration: "none",
                  fontSize: "0.9rem",
                  fontWeight: 500,
                }}
              >
                Repurposer
              </Link>
              <Link
                href="/leads"
                style={{
                  color: "#475569",
                  textDecoration: "none",
                  fontSize: "0.9rem",
                  fontWeight: 500,
                }}
              >
                Leads
              </Link>
              <Link
                href="/visual-studio"
                style={{
                  color: "#475569",
                  textDecoration: "none",
                  fontSize: "0.9rem",
                  fontWeight: 500,
                }}
              >
                Visuals
              </Link>
              <Link
                href="/events"
                style={{
                  color: "#475569",
                  textDecoration: "none",
                  fontSize: "0.9rem",
                  fontWeight: 500,
                }}
              >
                Events
              </Link>
              <Link
                href="/review"
                style={{
                  color: "#475569",
                  textDecoration: "none",
                  fontSize: "0.9rem",
                  fontWeight: 500,
                }}
              >
                Review
              </Link>
              <Link
                href="/observability"
                style={{
                  color: "#475569",
                  textDecoration: "none",
                  fontSize: "0.9rem",
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
