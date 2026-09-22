import Link from "next/link";

export default function Home() {
  const cards = [
    {
      title: "Live Judge Compliance Sandbox",
      subtitle: "The 4-Step Safety Engine",
      description: "Interactive live sandbox: test any insurance claim live against our 4-step compliance gate with real-time MAS & underwriter policy citation.",
      href: "/demo",
      badge: "LIVE DEMO",
      color: "#00d2ff",
      icon: "▶",
      highlight: true,
    },
    {
      title: "Insurtech 101 Omnichannel Repurposer",
      subtitle: "High-Yield Content Engine",
      description: "Repurpose complex insurance masterclasses into multi-channel LinkedIn copy, 5-slide carousels, X threads & high-conversion B2B emails.",
      href: "/repurpose",
      badge: "STANDOUT",
      color: "#10b981",
      icon: "📚",
      highlight: true,
    },
    {
      title: "Singapore OSM Lead Prospecting",
      subtitle: "Real-Time Geo Intelligence",
      description: "Live Overpass API queries discovering active jewelry boutiques (Orchard), medical clinics (Novena), and freight hubs (Jurong).",
      href: "/leads",
      badge: "OSM LIVE",
      color: "#38bdf8",
      icon: "🎯",
    },
    {
      title: "Visual & Carousel Creative Studio",
      subtitle: "Midjourney & Carousel Blueprints",
      description: "Generate brand-tailored luxury visual prompts for Midjourney/Flux and structured 5-slide educational carousels.",
      href: "/visual-studio",
      badge: "CREATIVE",
      color: "#ec4899",
      icon: "🎨",
    },
    {
      title: "Industry Event Trigger Engine",
      subtitle: "Milestone Campaign Automation",
      description: "1-Click automated campaign generation with pre-configured regulatory angles for SIJE, SMA Convention, and Maritime Week.",
      href: "/events",
      badge: "AUTOMATION",
      color: "#f59e0b",
      icon: "🗓️",
    },
    {
      title: "Compliance Human-in-the-Loop Review",
      subtitle: "Provenance & Decision Queue",
      description: "Inspect flagged claims, cited MAS & brand policy rules, and multi-language variants with chunk-level knowledge provenance.",
      href: "/review",
      badge: "COMPLIANCE",
      color: "#6366f1",
      icon: "🛡️",
    },
    {
      title: "Market Opportunities & Intelligence",
      subtitle: "Deterministic Trend Scoring",
      description: "Research synthesis, competitor monitoring, and algorithmic opportunity scoring matrices without hallucinated scores.",
      href: "/opportunities",
      badge: "RESEARCH",
      color: "#8b5cf6",
      icon: "💡",
    },
    {
      title: "Continuous Optimization & Analytics",
      subtitle: "Evidence-Based Copy Loops",
      description: "Engagement analytics breakdown, A/B copy performance, and deterministic insight generation feeding back into prompts.",
      href: "/optimization",
      badge: "INSIGHTS",
      color: "#06b6d4",
      icon: "📈",
    },
    {
      title: "Enterprise Observability & Guardrails",
      subtitle: "Telemetry & Budget Controls",
      description: "Full audit log of every LLM run, token usage, latency metrics, and demo daily quota budget ceilings.",
      href: "/observability",
      badge: "SYSTEM",
      color: "#64748b",
      icon: "📡",
    },
  ];

  return (
    <main style={{ padding: "3.5rem 1.5rem 5rem", maxWidth: 1200, margin: "0 auto" }}>
      {/* Hero Section */}
      <section style={{ textAlign: "center", marginBottom: "3.5rem", position: "relative" }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.5rem",
            padding: "6px 16px",
            background: "rgba(0, 210, 255, 0.08)",
            color: "#00d2ff",
            borderRadius: "9999px",
            fontSize: "0.85rem",
            fontWeight: 700,
            marginBottom: "1.25rem",
            border: "1px solid rgba(0, 210, 255, 0.25)",
            boxShadow: "0 0 20px rgba(0, 210, 255, 0.15)",
          }}
        >
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#00d2ff", display: "inline-block", boxShadow: "0 0 8px #00d2ff" }} />
          JA ASSURE™ • MULTINATIONAL INSURTECH MARKETING & COMPLIANCE OS
        </div>

        <h1
          style={{
            fontSize: "clamp(2.2rem, 5vw, 3.4rem)",
            fontWeight: 800,
            margin: "0 0 1rem",
            letterSpacing: "-0.03em",
            lineHeight: 1.15,
            color: "#ffffff",
          }}
        >
          Autonomous AI Marketing &amp; Compliance for{" "}
          <span
            style={{
              background: "linear-gradient(135deg, #00d2ff 0%, #0070f3 50%, #38bdf8 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Specialized Insurance
          </span>
        </h1>

        <p
          style={{
            color: "#94a3b8",
            fontSize: "1.15rem",
            maxWidth: 780,
            margin: "0 auto 2rem",
            lineHeight: 1.6,
          }}
        >
          Engineered for JA Assure&apos;s flagship verticals: <strong>Jade (Jewellers Block)</strong>,{" "}
          <strong>Jaguar Transit (High-Value Cargo)</strong>, and <strong>DoctorShield (Medical Indemnity)</strong>.
          Guaranteed MAS regulatory compliance, live OSM prospecting, and cultural localization.
        </p>

        {/* Quick KPI stats bar */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "1rem",
            maxWidth: 950,
            margin: "0 auto",
            background: "rgba(11, 31, 58, 0.6)",
            border: "1px solid rgba(26, 56, 96, 0.8)",
            borderRadius: "12px",
            padding: "1.25rem",
            backdropFilter: "blur(10px)",
          }}
        >
          <div>
            <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#00d2ff" }}>4-Step</div>
            <div style={{ fontSize: "0.8rem", color: "#94a3b8", fontWeight: 600 }}>Compliance Gate</div>
          </div>
          <div>
            <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#10b981" }}>4 Languages</div>
            <div style={{ fontSize: "0.8rem", color: "#94a3b8", fontWeight: 600 }}>EN • 中文 • MS • ID</div>
          </div>
          <div>
            <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#f59e0b" }}>Live OSM</div>
            <div style={{ fontSize: "0.8rem", color: "#94a3b8", fontWeight: 600 }}>Singapore Prospecting</div>
          </div>
          <div>
            <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#38bdf8" }}>100%</div>
            <div style={{ fontSize: "0.8rem", color: "#94a3b8", fontWeight: 600 }}>MAS Advertising Aligned</div>
          </div>
        </div>
      </section>

      {/* Grid of OS Modules */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
          gap: "1.5rem",
        }}
      >
        {cards.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="ja-card"
            style={{
              textDecoration: "none",
              background: card.highlight 
                ? "linear-gradient(180deg, rgba(15, 39, 71, 0.9) 0%, rgba(11, 31, 58, 0.9) 100%)" 
                : "rgba(11, 31, 58, 0.6)",
              border: card.highlight ? "1px solid rgba(0, 210, 255, 0.4)" : "1px solid rgba(26, 56, 96, 0.7)",
              borderRadius: "14px",
              padding: "1.75rem",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              position: "relative",
              overflow: "hidden",
            }}
          >
            {card.highlight && (
              <div
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  right: 0,
                  height: 3,
                  background: "linear-gradient(90deg, #00d2ff, #0070f3, #10b981)",
                }}
              />
            )}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                  <span style={{ fontSize: "1.4rem" }}>{card.icon}</span>
                  <div>
                    <h2 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 700, color: "#ffffff" }}>
                      {card.title}
                    </h2>
                    <div style={{ fontSize: "0.75rem", color: "#00d2ff", fontWeight: 600, marginTop: "2px" }}>
                      {card.subtitle}
                    </div>
                  </div>
                </div>
                <span
                  style={{
                    fontSize: "0.65rem",
                    fontWeight: 800,
                    padding: "3px 8px",
                    borderRadius: "6px",
                    background: card.highlight ? "#00d2ff" : "rgba(255, 255, 255, 0.1)",
                    color: card.highlight ? "#040d1a" : "#f8fafc",
                    letterSpacing: "0.04em",
                  }}
                >
                  {card.badge}
                </span>
              </div>
              <p style={{ margin: 0, color: "#94a3b8", fontSize: "0.9rem", lineHeight: 1.55 }}>
                {card.description}
              </p>
            </div>
            <div
              style={{
                marginTop: "1.5rem",
                paddingTop: "1rem",
                borderTop: "1px solid rgba(26, 56, 96, 0.6)",
                fontSize: "0.85rem",
                fontWeight: 700,
                color: "#00d2ff",
                display: "flex",
                alignItems: "center",
                gap: "0.4rem",
              }}
            >
              Launch Module <span style={{ transition: "transform 0.2s ease" }}>→</span>
            </div>
          </Link>
        ))}
      </div>

      {/* Brand Footer */}
      <footer
        style={{
          marginTop: "4rem",
          paddingTop: "2rem",
          borderTop: "1px solid rgba(26, 56, 96, 0.6)",
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "space-between",
          alignItems: "center",
          color: "#64748b",
          fontSize: "0.85rem",
          gap: "1rem",
        }}
      >
        <div>
          <strong style={{ color: "#94a3b8" }}>JA Assure™ Insurtech Ecosystem:</strong> Singapore • Malaysia • Hong Kong • Indonesia • Thailand
        </div>
        <div>
          Protected under MAS Advertising Regulations &amp; Insurance Act Standards
        </div>
      </footer>
    </main>
  );
}
