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
    <main style={{ padding: "2rem", maxWidth: 900, margin: "0 auto" }}>
      <h1 style={{ marginBottom: 4 }}>Review Queue</h1>
      <p style={{ color: "#666", marginTop: 0 }}>
        Content pending human review, newest first.
      </p>

      <RejectionRateWidget />

      {error && <p style={{ color: "#991b1b" }}>Error: {error}</p>}
      {!items && !error && <p>Loading…</p>}
      {items && items.length === 0 && <p>Nothing pending review right now.</p>}

      {items && items.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {items.map((item) => (
            <Link
              key={item.content_version_id}
              href={`/review/${item.content_version_id}`}
              style={{
                display: "block",
                border: "1px solid #ddd",
                borderRadius: 8,
                padding: "14px 16px",
                textDecoration: "none",
                color: "inherit",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                <strong>
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
                  color: "#444",
                  lineHeight: 1.6,
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
