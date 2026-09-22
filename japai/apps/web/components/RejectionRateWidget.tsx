"use client";

import { useEffect, useState } from "react";
import { fetchRejectionRates, BrandRejectionRate } from "@/lib/api";

function pct(rate: number | null): string {
  return rate === null ? "—" : `${Math.round(rate * 100)}%`;
}

function BrandRow({ brand }: { brand: BrandRejectionRate }) {
  const maxBar = 100;
  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{ marginBottom: 8, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap" }}>
        <strong style={{ color: "#002b49", fontSize: 14 }}>{brand.brand_name}</strong>{" "}
        <span style={{ color: "#64748b", fontSize: 12 }}>
          Overall Rejection: <strong style={{ color: "#0066cc" }}>{pct(brand.overall_rejection_rate)}</strong> ({brand.total_rejected}/
          {brand.total_decided} decided)
        </span>
      </div>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 8, height: maxBar + 40, background: "#f8fafc", padding: "10px", borderRadius: 6, border: "1px solid #e2e8f0" }}>
        {(brand.buckets || []).map((b) => {
          const height = b.rejection_rate === null ? 0 : b.rejection_rate * maxBar;
          return (
            <div
              key={b.bucket}
              title={`Batch ${b.bucket}: ${b.rejected} rejected / ${b.versions} decided`}
              style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}
            >
              <span style={{ fontSize: 10, color: "#64748b", fontWeight: 600 }}>{pct(b.rejection_rate)}</span>
              <div
                style={{
                  width: 32,
                  height: Math.max(height, 4),
                  background: (b.rejection_rate ?? 0) > 0.3 ? "#ef4444" : "#0066cc",
                  borderRadius: "3px 3px 0 0",
                  transition: "height 0.3s ease",
                }}
              />
              <span style={{ fontSize: 10, color: "#94a3b8" }}>#{b.bucket}</span>
            </div>
          );
        })}
      </div>
      <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 4 }}>
        Sequential batches of {brand.bucket_size} decided versions, oldest → newest
      </div>
    </div>
  );
}

export default function RejectionRateWidget() {
  const [brands, setBrands] = useState<BrandRejectionRate[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRejectionRates()
      .then(setBrands)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return null;
  if (!brands || brands.length === 0) return null;

  return (
    <section
      style={{
        border: "1px solid #e2e8f0",
        background: "#ffffff",
        borderRadius: 10,
        padding: "16px 20px",
        marginBottom: 24,
        boxShadow: "0 1px 3px rgba(0, 43, 73, 0.04)",
      }}
    >
      <h2 style={{ margin: "0 0 4px", fontSize: 15, fontWeight: 800, color: "#002b49" }}>
        📉 Compliance Rejection Rate Trend
      </h2>
      <p style={{ margin: "0 0 14px", color: "#64748b", fontSize: 13 }}>
        Monitors how rejection rates decline over time as feedback reinforces few-shot guardrails.
      </p>
      {brands.map((brand) => (
        <BrandRow key={brand.brand_id} brand={brand} />
      ))}
    </section>
  );
}
