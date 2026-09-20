import Link from "next/link";

export default function Home() {
  const cards = [
    {
      title: "▶ Live Judge Demo",
      description: "Interactive live sandbox: run any insurance claim against our 4-step compliance gate.",
      href: "/demo",
      badge: "LIVE",
      color: "#6366f1",
      highlight: true,
    },
    {
      title: "🛡️ Compliance Review Queue",
      description: "Inspect flagged claims, cited MAS & brand policy rules, and multi-language variants.",
      href: "/review",
      badge: "13 Pending",
      color: "#0284c7",
    },
    {
      title: "🎨 Visual & Carousel Studio",
      description: "Generate brand-tailored Midjourney/Flux image prompts & 5-slide carousel breakdowns.",
      href: "/visual-studio",
      badge: "NEW",
      color: "#ec4899",
    },
    {
      title: "🗓️ Industry Event Triggers",
      description: "1-Click automated campaign generation for SIJE, SMA Convention, and Maritime Week.",
      href: "/events",
      badge: "NEW",
      color: "#f59e0b",
    },
    {
      title: "🎯 Lead Discovery & Scoring",
      description: "Live Singapore OpenStreetMap prospecting + deterministic arithmetic fit scoring.",
      href: "/leads",
      badge: "OSM Live",
      color: "#10b981",
    },
    {
      title: "💡 Market Opportunities",
      description: "Research synthesis, competitor analysis, and opportunity scoring matrices.",
      href: "/opportunities",
      badge: "9 Active",
      color: "#8b5cf6",
    },
    {
      title: "📈 Performance Insights",
      description: "Engagement analytics breakdown, A/B copy performance, and optimization agent notes.",
      href: "/optimization",
      badge: "Analytics",
      color: "#06b6d4",
    },
    {
      title: "📡 System Observability",
      description: "Full audit log of every LLM run, token usage, latency metrics, and daily quota guardrails.",
      href: "/observability",
      badge: "400+ Runs",
      color: "#64748b",
    },
  ];

  return (
    <main style={{ padding: "3rem 2rem", maxWidth: 1050, margin: "0 auto", fontFamily: "system-ui, sans-serif" }}>
      <header style={{ marginBottom: "2.5rem", textAlign: "center" }}>
        <div
          style={{
            display: "inline-block",
            padding: "4px 12px",
            background: "#1e1b4b",
            color: "#a5b4fc",
            borderRadius: "20px",
            fontSize: "0.85rem",
            fontWeight: 700,
            marginBottom: "0.75rem",
            border: "1px solid #4338ca",
          }}
        >
          JA ASSURE HACKATHON • UNIFIED AI MARKETING OS
        </div>
        <h1 style={{ fontSize: "2.5rem", fontWeight: 800, margin: "0 0 0.5rem", color: "#f8fafc" }}>
          JAPAI Marketing Operating System
        </h1>
        <p style={{ color: "#94a3b8", fontSize: "1.1rem", maxWidth: 700, margin: "0 auto" }}>
          Autonomous multi-agent insurance marketing: Live research, 4-language generation, 
          4-step regulatory guardrails, live OSM prospecting, and automated publishing.
        </p>
      </header>

      {/* Grid of OS Modules */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "1.25rem",
        }}
      >
        {cards.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            style={{
              textDecoration: "none",
              background: "#1e293b",
              border: card.highlight ? "2px solid #6366f1" : "1px solid #334155",
              borderRadius: "12px",
              padding: "1.5rem",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              transition: "transform 0.15s ease, border-color 0.15s ease",
            }}
          >
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                <h2 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 700, color: "#f8fafc" }}>
                  {card.title}
                </h2>
                <span
                  style={{
                    fontSize: "0.7rem",
                    fontWeight: 800,
                    padding: "3px 8px",
                    borderRadius: "4px",
                    background: card.color,
                    color: "white",
                  }}
                >
                  {card.badge}
                </span>
              </div>
              <p style={{ margin: 0, color: "#94a3b8", fontSize: "0.9rem", lineHeight: 1.5 }}>
                {card.description}
              </p>
            </div>
            <div style={{ marginTop: "1.25rem", fontSize: "0.85rem", fontWeight: 700, color: "#38bdf8" }}>
              Launch Module →
            </div>
          </Link>
        ))}
      </div>

      <footer
        style={{
          marginTop: "3rem",
          paddingTop: "1.5rem",
          borderTop: "1px solid #334155",
          display: "flex",
          justifyContent: "space-between",
          color: "#64748b",
          fontSize: "0.85rem",
        }}
      >
        <div>Covering <strong>Jade</strong>, <strong>Jaguar Transit</strong>, & <strong>DoctorShield</strong></div>
        <div>Compliant with MAS Guidelines & Insurance Act Standards</div>
      </footer>
    </main>
  );
}
