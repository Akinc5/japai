import Link from "next/link";

export default function Home() {
  const cards = [
    {
      title: "Compliance Sandbox",
      badge: "LIVE DEMO",
      desc: "Interactive live testing against the 4-step MAS compliance & underwriter safety gate.",
      href: "/demo",
      highlight: true,
    },
    {
      title: "Content Repurposer",
      badge: "REPURPOSE",
      desc: "Transform insurance whitepapers into LinkedIn posts, carousels, threads & B2B emails.",
      href: "/repurpose",
      highlight: true,
    },
    {
      title: "Lead Discovery (OSM)",
      badge: "LIVE MAP",
      desc: "Real-time Singapore OpenStreetMap discovery of jewelry shops, clinics & freight hubs.",
      href: "/leads",
    },
    {
      title: "Visual Studio",
      badge: "CREATIVE",
      desc: "Midjourney luxury image blueprints and 5-slide educational carousel structures.",
      href: "/visual-studio",
    },
    {
      title: "Event Triggers",
      badge: "AUTOMATION",
      desc: "1-Click automated campaigns for SIJE, SMA Convention, and Maritime Week.",
      href: "/events",
    },
    {
      title: "Review Queue",
      badge: "AUDIT",
      desc: "Human-in-the-loop review interface with chunk-level knowledge provenance.",
      href: "/review",
    },
    {
      title: "Market Opportunities",
      badge: "RESEARCH",
      desc: "Deterministic trend scoring and competitive intelligence without hallucinations.",
      href: "/opportunities",
    },
    {
      title: "Campaign Insights",
      badge: "ANALYTICS",
      desc: "Evidence-based A/B hook performance analytics feeding directly into prompts.",
      href: "/optimization",
    },
    {
      title: "System Logs",
      badge: "TELEMETRY",
      desc: "Full audit logs of model latency, token consumption, and daily rate limit guardrails.",
      href: "/observability",
    },
  ];

  return (
    <main style={{ maxWidth: 1100, margin: "0 auto", padding: "3.5rem 1.5rem 4rem" }}>
      {/* Hero Header */}
      <section style={{ textAlign: "center", marginBottom: "3rem" }}>
        <div
          style={{
            fontSize: "0.8rem",
            fontWeight: 700,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "#00d2ff",
            marginBottom: "0.75rem",
          }}
        >
          Insure • Innovate • Integrate
        </div>

        <h1
          style={{
            fontSize: "clamp(2rem, 4vw, 3rem)",
            fontWeight: 800,
            letterSpacing: "-0.03em",
            lineHeight: 1.15,
            color: "#ffffff",
            margin: "0 0 0.75rem",
          }}
        >
          JA Assure<span style={{ color: "#00d2ff" }}>™</span> Marketing OS
        </h1>

        <p
          style={{
            color: "#94a3b8",
            fontSize: "1.05rem",
            maxWidth: 620,
            margin: "0 auto 1.75rem",
            lineHeight: 1.5,
          }}
        >
          Autonomous multi-agent insurance marketing, regulatory compliance &amp; lead intelligence for{" "}
          <strong style={{ color: "#ffffff" }}>Jade</strong>,{" "}
          <strong style={{ color: "#ffffff" }}>Jaguar Transit</strong> &amp;{" "}
          <strong style={{ color: "#ffffff" }}>DoctorShield</strong>.
        </p>

        {/* 3 Verticals Pills */}
        <div style={{ display: "flex", justifyContent: "center", gap: "0.5rem", flexWrap: "wrap" }}>
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: 600,
              padding: "4px 12px",
              borderRadius: "9999px",
              background: "rgba(16, 185, 129, 0.12)",
              color: "#34d399",
              border: "1px solid rgba(16, 185, 129, 0.25)",
            }}
          >
            💎 Jade (Jewellers Block)
          </span>
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: 600,
              padding: "4px 12px",
              borderRadius: "9999px",
              background: "rgba(245, 158, 11, 0.12)",
              color: "#fbbf24",
              border: "1px solid rgba(245, 158, 11, 0.25)",
            }}
          >
            🚢 Jaguar (High-Value Cargo)
          </span>
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: 600,
              padding: "4px 12px",
              borderRadius: "9999px",
              background: "rgba(56, 189, 248, 0.12)",
              color: "#38bdf8",
              border: "1px solid rgba(56, 189, 248, 0.25)",
            }}
          >
            🩺 DoctorShield (Medical Indemnity)
          </span>
        </div>
      </section>

      {/* Clean Cards Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(310px, 1fr))",
          gap: "1.25rem",
        }}
      >
        {cards.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="ja-card"
            style={{
              textDecoration: "none",
              background: "#0c1c33",
              border: card.highlight ? "1px solid #00d2ff" : "1px solid #162f52",
              borderRadius: "10px",
              padding: "1.4rem",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "0.6rem",
                }}
              >
                <h2
                  style={{
                    margin: 0,
                    fontSize: "1.05rem",
                    fontWeight: 700,
                    color: "#ffffff",
                  }}
                >
                  {card.title}
                </h2>
                <span
                  style={{
                    fontSize: "0.65rem",
                    fontWeight: 700,
                    padding: "2px 7px",
                    borderRadius: "4px",
                    background: card.highlight ? "rgba(0, 210, 255, 0.15)" : "rgba(255, 255, 255, 0.06)",
                    color: card.highlight ? "#00d2ff" : "#94a3b8",
                  }}
                >
                  {card.badge}
                </span>
              </div>
              <p
                style={{
                  margin: 0,
                  color: "#94a3b8",
                  fontSize: "0.85rem",
                  lineHeight: 1.5,
                }}
              >
                {card.desc}
              </p>
            </div>
            <div
              style={{
                marginTop: "1.25rem",
                fontSize: "0.8rem",
                fontWeight: 600,
                color: "#00d2ff",
              }}
            >
              Open →
            </div>
          </Link>
        ))}
      </div>

      {/* Clean Footer */}
      <footer
        style={{
          marginTop: "3.5rem",
          paddingTop: "1.5rem",
          borderTop: "1px solid #162f52",
          display: "flex",
          justifyContent: "space-between",
          color: "#64748b",
          fontSize: "0.8rem",
          flexWrap: "wrap",
          gap: "0.75rem",
        }}
      >
        <div>JA Assure™ Insurtech Operating System</div>
        <div>Singapore • Malaysia • Hong Kong</div>
      </footer>
    </main>
  );
}
