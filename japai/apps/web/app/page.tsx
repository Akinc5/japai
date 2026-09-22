import Link from "next/link";

export default function Home() {
  const cards = [
    {
      title: "Compliance Sandbox",
      badge: "LIVE DEMO",
      desc: "Test any insurance claim live against our 4-step MAS compliance gate.",
      href: "/demo",
      highlight: true,
    },
    {
      title: "Content Repurposer",
      badge: "REPURPOSE",
      desc: "Transform whitepapers into LinkedIn posts, carousels, threads & B2B emails.",
      href: "/repurpose",
      highlight: true,
    },
    {
      title: "Lead Discovery (OSM)",
      badge: "LIVE MAP",
      desc: "Real-time Singapore OpenStreetMap discovery for jewelers, clinics & freight hubs.",
      href: "/leads",
    },
    {
      title: "Visual Studio",
      badge: "CREATIVE",
      desc: "Midjourney luxury visual blueprints and 5-slide educational carousels.",
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
      desc: "Human-in-the-loop review queue with full knowledge chunk provenance.",
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
      desc: "Audit logs of model latency, token consumption, and daily rate limit guardrails.",
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
            color: "#0066cc",
            marginBottom: "0.75rem",
          }}
        >
          Insure • Innovate • Integrate
        </div>

        <h1
          style={{
            fontSize: "clamp(2rem, 4vw, 2.75rem)",
            fontWeight: 800,
            letterSpacing: "-0.03em",
            lineHeight: 1.15,
            color: "#002b49",
            margin: "0 0 0.75rem",
          }}
        >
          JA Assure<span style={{ color: "#0066cc" }}>™</span> Marketing OS
        </h1>

        <p
          style={{
            color: "#475569",
            fontSize: "1.05rem",
            maxWidth: 620,
            margin: "0 auto 1.75rem",
            lineHeight: 1.5,
          }}
        >
          Autonomous multi-agent insurance marketing, regulatory compliance &amp; lead intelligence for{" "}
          <strong style={{ color: "#002b49" }}>Jade</strong>,{" "}
          <strong style={{ color: "#002b49" }}>Jaguar Transit</strong> &amp;{" "}
          <strong style={{ color: "#002b49" }}>DoctorShield</strong>.
        </p>

        {/* 3 Verticals Pills */}
        <div style={{ display: "flex", justifyContent: "center", gap: "0.5rem", flexWrap: "wrap" }}>
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: 600,
              padding: "4px 12px",
              borderRadius: "9999px",
              background: "#ecfdf5",
              color: "#047857",
              border: "1px solid #a7f3d0",
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
              background: "#fffbeb",
              color: "#b45309",
              border: "1px solid #fde68a",
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
              background: "#eff6ff",
              color: "#1d4ed8",
              border: "1px solid #bfdbfe",
            }}
          >
            🩺 DoctorShield (Medical Indemnity)
          </span>
        </div>
      </section>

      {/* Clean Blue & White Cards Grid */}
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
              background: "#ffffff",
              border: card.highlight ? "1.5px solid #0066cc" : "1px solid #e2e8f0",
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
                    color: "#002b49",
                  }}
                >
                  {card.title}
                </h2>
                <span
                  style={{
                    fontSize: "0.65rem",
                    fontWeight: 700,
                    padding: "3px 8px",
                    borderRadius: "4px",
                    background: card.highlight ? "#e0f2fe" : "#f1f5f9",
                    color: card.highlight ? "#0284c7" : "#64748b",
                  }}
                >
                  {card.badge}
                </span>
              </div>
              <p
                style={{
                  margin: 0,
                  color: "#64748b",
                  fontSize: "0.88rem",
                  lineHeight: 1.5,
                }}
              >
                {card.desc}
              </p>
            </div>
            <div
              style={{
                marginTop: "1.25rem",
                fontSize: "0.85rem",
                fontWeight: 600,
                color: "#0066cc",
              }}
            >
              Open Module →
            </div>
          </Link>
        ))}
      </div>

      {/* Clean Footer */}
      <footer
        style={{
          marginTop: "3.5rem",
          paddingTop: "1.5rem",
          borderTop: "1px solid #e2e8f0",
          display: "flex",
          justifyContent: "space-between",
          color: "#94a3b8",
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
