"use client";

import { useEffect, useState } from "react";
import { fetchRejectionRates, BrandRejectionRate } from "@/lib/api";

function pct(rate: number | null): string {
  return rate === null ? "—" : `${Math.round(rate * 100)}%`;
}

function BrandRow({ brand }: { brand: BrandRejectionRate }) {
  const maxBar = 120;
  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{ marginBottom: 6 }}>
        <strong>{brand.brand_name}</strong>{" "}
        <span style={{ color: "#888", fontSize: 13 }}>
          overall {pct(brand.overall_rejection_rate)} rejected ({brand.total_rejected}/
          {brand.total_decided} decided)
        </span>
      </div>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 6, height: maxBar + 40 }}>
        {(brand.buckets || []).map((b) => {
          const height = b.rejection_rate === null ? 0 : b.rejection_rate * maxBar;
          return (
            <div
              key={b.bucket}
              title={`Batch ${b.bucket}: ${b.rejected} rejected / ${b.versions} decided`}
              style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}
            >
              <span style={{ fontSize: 11, color: "#888" }}>{pct(b.rejection_rate)}</span>
              <div
                style={{
                  width: 34,
                  height: Math.max(height, 2),
                  background: "#f87171",
                  borderRadius: "3px 3px 0 0",
                }}
              />
              <span style={{ fontSize: 11, color: "#888" }}>#{b.bucket}</span>
            </div>
          );
        })}
      </div>
      <div style={{ fontSize: 11, color: "#777", marginTop: 4 }}>
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

  if (error) return <p style={{ color: "#991b1b" }}>Metrics error: {error}</p>;
  if (!brands) return <p style={{ color: "#888" }}>Loading metrics…</p>;
  if (brands.length === 0) return <p style={{ color: "#888" }}>No decided content yet.</p>;

  return (
    <section
      style={{
        border: "1px solid #333",
        borderRadius: 8,
        padding: "14px 16px",
        marginBottom: 24,
      }}
    >
      <h2 style={{ margin: "0 0 4px", fontSize: 16 }}>Rejection rate over time</h2>
      <p style={{ margin: "0 0 14px", color: "#888", fontSize: 13 }}>
        Should trend down as reviewer feedback accumulates into lessons.
      </p>
      {brands.map((brand) => (
        <BrandRow key={brand.brand_id} brand={brand} />
      ))}
    </section>
  );
}
