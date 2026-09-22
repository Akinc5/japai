"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchPending, PendingItem } from "@/lib/api";
import RiskBadge from "@/components/RiskBadge";
import LanguageBadge from "@/components/LanguageBadge";
import RejectionRateWidget from "@/components/RejectionRateWidget";

export default function ReviewListPage() {
  const [items, setItems] = useState<PendingItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPending()
      .then(setItems)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <main style={{ padding: "2.5rem 1.5rem 4rem", maxWidth: 900, margin: "0 auto" }}>
      <header style={{ marginBottom: "1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ margin: "0 0 4px", fontSize: "1.8rem", fontWeight: 800, color: "#002b49" }}>
            🛡️ Compliance Review Queue
          </h1>
          <p style={{ color: "#64748b", margin: 0, fontSize: "0.95rem" }}>
            Content pending human compliance review &amp; provenance audit, newest first.
          </p>
        </div>
        <Link href="/" style={{ color: "#0066cc", textDecoration: "none", fontSize: "0.9rem", fontWeight: 600 }}>
          ← Home
        </Link>
      </header>

      <RejectionRateWidget />

      {error && <div style={{ color: "#b91c1c", background: "#fef2f2", padding: "10px 14px", borderRadius: 6, border: "1px solid #fecaca", margin: "14px 0" }}>Error: {error}</div>}
      {!items && !error && <p style={{ color: "#64748b" }}>Loading queue…</p>}
      {items && items.length === 0 && (
        <div style={{ background: "#ffffff", padding: "2rem", textAlign: "center", borderRadius: 8, border: "1px solid #e2e8f0", color: "#64748b" }}>
          No content pending review right now.
        </div>
      )}

      {items && items.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {items.map((item) => (
            <Link
              key={item.content_version_id}
              href={`/review/${item.content_version_id}`}
              style={{
                display: "block",
                border: "1px solid #e2e8f0",
                borderRadius: 8,
                padding: "16px 18px",
                textDecoration: "none",
                color: "inherit",
                background: "#ffffff",
                boxShadow: "0 1px 3px rgba(0, 43, 73, 0.04)",
                transition: "border-color 0.15s ease",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8, flexWrap: "wrap", gap: 8 }}>
                <strong style={{ color: "#002b49", fontSize: "1rem" }}>
                  {item.brand_name || "Unknown brand"} · {item.platform || "—"}
                </strong>
                <span style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
                  <LanguageBadge language={item.language} isLocalized={item.is_localized} />
                  <RiskBadge riskLevel={item.risk_level} />
                </span>
              </div>
              <p
                lang={item.language ?? "en"}
                style={{
                  margin: 0,
                  color: "#334155",
                  lineHeight: 1.55,
                  fontSize: "0.9rem",
                  fontFamily:
                    '-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
                }}
              >
                {item.body_preview}…
              </p>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
