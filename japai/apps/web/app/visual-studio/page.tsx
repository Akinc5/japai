"use client";

import { useState } from "react";
import Link from "next/link";
import { generateVisualCreative, VisualCreativeResponse } from "@/lib/api";

const BRANDS = [
  { slug: "jade", name: "Jade Jewellers Block", tag: "Luxury Jewelry & Timepieces" },
  { slug: "jaguar-transit", name: "Jaguar Transit", tag: "High-Value Cargo & Transit" },
  { slug: "doctorshield", name: "DoctorShield", tag: "Medical Indemnity & Liability" },
];

const SAMPLE_TOPICS = {
  jade: "Exhibition vault security warranties during private VIP viewing",
  "jaguar-transit": "Securing fine art and diamond air-freight across customs transitions",
  doctorshield: "Navigating SMC statutory disciplinary inquiries and surgical defense costs",
};

export default function VisualStudioPage() {
  const [selectedBrand, setSelectedBrand] = useState("jade");
  const [topic, setTopic] = useState(SAMPLE_TOPICS["jade"]);
  const [platform, setPlatform] = useState("instagram_carousel");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VisualCreativeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleBrandChange = (slug: string) => {
    setSelectedBrand(slug);
    setTopic(SAMPLE_TOPICS[slug as keyof typeof SAMPLE_TOPICS] || "");
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await generateVisualCreative(selectedBrand, topic, platform);
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to generate visual creative.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ padding: "2.5rem 1.5rem 4rem", maxWidth: 1000, margin: "0 auto" }}>
      <header style={{ marginBottom: "2rem", borderBottom: "1px solid #e2e8f0", paddingBottom: "1rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h1 style={{ fontSize: "1.8rem", fontWeight: 800, margin: 0, color: "#002b49" }}>
              🎨 Visual &amp; Carousel Creative Studio
            </h1>
            <p style={{ color: "#64748b", marginTop: "0.25rem", fontSize: "0.95rem" }}>
              Generate brand-aesthetic Midjourney/Flux visual prompts &amp; 5-slide structured educational carousels.
            </p>
          </div>
          <Link
            href="/"
            style={{ color: "#0066cc", textDecoration: "none", fontSize: "0.9rem", fontWeight: 600 }}
          >
            ← Home
          </Link>
        </div>
      </header>

      {/* Configuration Card */}
      <section
        style={{
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: "12px",
          padding: "1.75rem",
          marginBottom: "2rem",
          boxShadow: "0 1px 4px rgba(0, 43, 73, 0.04)",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* Brand Selection */}
          <div>
            <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 700, color: "#002b49", marginBottom: "0.5rem" }}>
              Select Insurance Brand Vertical:
            </label>
            <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
              {BRANDS.map((b) => (
                <button
                  key={b.slug}
                  onClick={() => handleBrandChange(b.slug)}
                  style={{
                    padding: "8px 16px",
                    borderRadius: "6px",
                    fontSize: "0.88rem",
                    fontWeight: 600,
                    cursor: "pointer",
                    background: selectedBrand === b.slug ? "#0066cc" : "#ffffff",
                    color: selectedBrand === b.slug ? "#ffffff" : "#334155",
                    border: selectedBrand === b.slug ? "1px solid #0066cc" : "1px solid #cbd5e1",
                    transition: "all 0.15s ease",
                  }}
                >
                  {b.name}
                </button>
              ))}
            </div>
          </div>

          {/* Topic Input */}
          <div>
            <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 700, color: "#002b49", marginBottom: "0.5rem" }}>
              Creative Theme / Campaign Subject:
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Enter subject or risk scenario..."
              style={{
                width: "100%",
                padding: "10px 14px",
                background: "#f8fafc",
                border: "1px solid #cbd5e1",
                borderRadius: "6px",
                color: "#0f172a",
                fontSize: "0.95rem",
                outline: "none",
              }}
            />
          </div>

          {/* Platform / Format Selection */}
          <div>
            <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 700, color: "#002b49", marginBottom: "0.5rem" }}>
              Target Visual Format:
            </label>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              style={{
                padding: "8px 12px",
                background: "#ffffff",
                border: "1px solid #cbd5e1",
                borderRadius: "6px",
                color: "#0f172a",
                fontSize: "0.9rem",
                outline: "none",
              }}
            >
              <option value="instagram_carousel">5-Slide Educational Carousel (Instagram / LinkedIn)</option>
              <option value="hero_banner">Editorial Hero Keyframe (16:9 Midjourney Prompt)</option>
              <option value="square_feed">Social Grid Post (1:1 Aspect Ratio)</option>
            </select>
          </div>

          {/* Action Trigger */}
          <button
            onClick={handleGenerate}
            disabled={loading || !topic.trim()}
            style={{
              padding: "11px 22px",
              background: loading ? "#94a3b8" : "#0066cc",
              color: "white",
              borderRadius: "6px",
              fontWeight: 700,
              fontSize: "0.95rem",
              border: "none",
              cursor: loading ? "not-allowed" : "pointer",
              alignSelf: "flex-start",
            }}
          >
            {loading ? "Generating Creative Package..." : "✨ Generate Creative Package"}
          </button>
        </div>
      </section>

      {error && (
        <div style={{ padding: "12px 16px", background: "#fef2f2", color: "#b91c1c", border: "1px solid #fecaca", borderRadius: 8, marginBottom: "1.5rem" }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Creative Result Presentation */}
      {result && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Hero Image Prompt Box */}
          <div style={{ background: "#ffffff", border: "1px solid #0066cc", borderRadius: 10, padding: "1.5rem", boxShadow: "0 1px 4px rgba(0, 43, 73, 0.04)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <h3 style={{ margin: 0, color: "#0066cc", fontSize: "1.1rem", fontWeight: 700 }}>
                🖼️ Midjourney / Flux Hero Image Blueprint
              </h3>
              <span style={{ fontSize: "0.8rem", background: "#e0f2fe", color: "#0369a1", padding: "4px 8px", borderRadius: 4, fontWeight: 700 }}>
                Ratio: {result.creative?.aspect_ratio || "16:9"}
              </span>
            </div>
            <div style={{ background: "#f8fafc", padding: "12px", borderRadius: 6, color: "#0f172a", fontSize: "0.95rem", lineHeight: 1.5, border: "1px solid #e2e8f0" }}>
              <code>{result.creative?.hero_image_prompt}</code>
            </div>
            <div style={{ marginTop: 8, fontSize: "0.85rem", color: "#64748b" }}>
              <strong style={{ color: "#0f172a" }}>Negative Filters:</strong> {result.creative?.negative_prompt}
            </div>
          </div>

          {/* 5-Slide Carousel Breakdown */}
          <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 10, padding: "1.5rem", boxShadow: "0 1px 4px rgba(0, 43, 73, 0.04)" }}>
            <h3 style={{ margin: "0 0 1rem 0", color: "#002b49", fontSize: "1.1rem", fontWeight: 700 }}>
              📱 5-Slide Structured Carousel Sequence
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "12px" }}>
              {(result.creative?.carousel_slides || []).map((slide) => (
                <div
                  key={slide.slide_number}
                  style={{
                    background: "#f8fafc",
                    padding: "14px",
                    borderRadius: "8px",
                    border: "1px solid #e2e8f0",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                      <span style={{ fontSize: "0.75rem", fontWeight: 800, color: "#0066cc", background: "#e0f2fe", padding: "2px 6px", borderRadius: 4 }}>
                        SLIDE {slide.slide_number}
                      </span>
                      <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600 }}>{slide.role}</span>
                    </div>
                    <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#002b49", marginBottom: "6px" }}>
                      {slide.headline}
                    </div>
                    <div style={{ fontSize: "0.85rem", color: "#475569", lineHeight: 1.45 }}>{slide.body}</div>
                  </div>
                  <div style={{ marginTop: "10px", fontSize: "0.78rem", color: "#0066cc", background: "#ffffff", padding: "6px 8px", borderRadius: 4, border: "1px solid #e2e8f0" }}>
                    🎨 <strong>Visual:</strong> {slide.visual_direction}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
