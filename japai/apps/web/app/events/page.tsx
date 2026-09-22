"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchIndustryEvents, triggerEventCampaign, IndustryEvent } from "@/lib/api";

export default function EventsPage() {
  const [events, setEvents] = useState<IndustryEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggeringId, setTriggeringId] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    fetchIndustryEvents()
      .then((data) => {
        setEvents(data);
        setLoading(false);
      })
      .catch((err) => {
        setStatusMessage({ type: "error", text: "Failed to load events: " + err.message });
        setLoading(false);
      });
  }, []);

  const handleTrigger = async (eventId: string, title: string) => {
    setTriggeringId(eventId);
    setStatusMessage(null);
    try {
      const res = await triggerEventCampaign(eventId);
      setStatusMessage({
        type: "success",
        text: `🚀 Campaign successfully launched for "${title}"! Campaign ID: ${res.campaign_id}`,
      });
    } catch (err: any) {
      setStatusMessage({
        type: "error",
        text: `Campaign launch failed: ${err.message}`,
      });
    } finally {
      setTriggeringId(null);
    }
  };

  return (
    <main style={{ padding: "2.5rem", maxWidth: 1000, margin: "0 auto", fontFamily: "system-ui, sans-serif" }}>
      <header style={{ marginBottom: "2rem", borderBottom: "1px solid #334155", paddingBottom: "1rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h1 style={{ fontSize: "1.8rem", fontWeight: 800, margin: 0, color: "#f8fafc" }}>
              🗓️ Industry Event Calendar & Seasonal Triggers
            </h1>
            <p style={{ color: "#94a3b8", marginTop: "0.25rem" }}>
              Automated trigger engine to launch compliance-screened campaigns for major Singapore expos & conventions.
            </p>
          </div>
          <Link href="/" style={{ color: "#38bdf8", textDecoration: "none", fontSize: "0.9rem", fontWeight: 600 }}>
            ← Back to OS Hub
          </Link>
        </div>
      </header>

      {statusMessage && (
        <div
          style={{
            padding: "14px",
            borderRadius: "8px",
            marginBottom: "1.5rem",
            background: statusMessage.type === "success" ? "#064e3b" : "#7f1d1d",
            color: statusMessage.type === "success" ? "#a7f3d0" : "#fecaca",
            border: `1px solid ${statusMessage.type === "success" ? "#059669" : "#dc2626"}`,
            fontSize: "0.95rem",
            fontWeight: 600,
          }}
        >
          {statusMessage.text}
        </div>
      )}

      {loading ? (
        <div style={{ color: "#94a3b8", padding: "2rem", textAlign: "center" }}>Loading industry events...</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {Array.isArray(events) && events.map((evt) => (
            <div
              key={evt.id}
              style={{
                background: "#1e293b",
                border: "1px solid #334155",
                borderRadius: "10px",
                padding: "1.5rem",
                display: "flex",
                flexDirection: "column",
                gap: "1rem",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
                    <span
                      style={{
                        fontSize: "0.75rem",
                        fontWeight: 800,
                        textTransform: "uppercase",
                        padding: "3px 8px",
                        borderRadius: "4px",
                        background:
                          evt.urgency === "Immediate" || evt.urgency === "Critical" ? "#b91c1c" : "#d97706",
                        color: "#ffffff",
                      }}
                    >
                      {evt.urgency} ({evt.days_remaining}d)
                    </span>
                    <span style={{ fontSize: "0.85rem", color: "#38bdf8", fontWeight: 700 }}>
                      {evt.brand_name}
                    </span>
                  </div>
                  <h2 style={{ margin: "0.25rem 0", fontSize: "1.25rem", color: "#f8fafc" }}>{evt.title}</h2>
                  <div style={{ fontSize: "0.85rem", color: "#94a3b8" }}>
                    📍 {evt.location} &nbsp;|&nbsp; 📅 {evt.date_window}
                  </div>
                </div>

                <button
                  onClick={() => handleTrigger(evt.id, evt.title)}
                  disabled={triggeringId === evt.id}
                  style={{
                    padding: "10px 18px",
                    borderRadius: "6px",
                    background: triggeringId === evt.id ? "#64748b" : "#4f46e5",
                    color: "white",
                    fontWeight: 700,
                    fontSize: "0.9rem",
                    border: "none",
                    cursor: triggeringId === evt.id ? "not-allowed" : "pointer",
                    whiteSpace: "nowrap",
                  }}
                >
                  {triggeringId === evt.id ? "Launching..." : "⚡ 1-Click Launch Campaign"}
                </button>
              </div>

              {/* Angles & CTA */}
              <div style={{ background: "#0f172a", padding: "12px", borderRadius: "8px" }}>
                <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#cbd5e1", marginBottom: 6 }}>
                  SUGGESTED REGULATORY & VALUE ANGLES:
                </div>
                <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.85rem", color: "#94a3b8" }}>
                  {evt.suggested_angles.map((angle, idx) => (
                    <li key={idx} style={{ marginBottom: "4px" }}>
                      {angle}
                    </li>
                  ))}
                </ul>
                <div style={{ marginTop: "8px", fontSize: "0.8rem", color: "#34d399", fontWeight: 600 }}>
                  🎯 Preconfigured CTA: &quot;{evt.default_cta}&quot;
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
