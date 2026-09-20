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
    <main style={{ padding: "2.5rem", maxWidth: 1000, margin: "0 auto", fontFamily: "system-ui, sans-serif" }}>
      <header style={{ marginBottom: "2rem", borderBottom: "1px solid #334155", paddingBottom: "1rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h1 style={{ fontSize: "1.8rem", fontWeight: 800, margin: 0, color: "#f8fafc" }}>
              🎨 Visual & Carousel Creative Studio
            </h1>
            <p style={{ color: "#94a3b8", marginTop: "0.25rem" }}>
              Generate brand-aesthetic Midjourney/DALL-E prompts & 5-slide carousel breakdowns.
            </p>
          </div>
          <Link
            href="/"
            style={{ color: "#38bdf8", textDecoration: "none", fontSize: "0.9rem", fontWeight: 600 }}
          >
            ← Back to OS Hub
          </Link>
        </div>
      </header>

      {/* Brand Selector */}
      <section style={{ marginBottom: "1.5rem" }}>
        <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 700, color: "#cbd5e1", marginBottom: 8 }}>
          SELECT BRAND VERTICAL:
        </label>
        <div style={{ display: "flex", gap: "10px" }}>
          {BRANDS.map((b) => (
            <button
              key={b.slug}
              onClick={() => handleBrandChange(b.slug)}
              style={{
                flex: 1,
                padding: "12px",
                borderRadius: "8px",
                border: selectedBrand === b.slug ? "2px solid #38bdf8" : "1px solid #334155",
                background: selectedBrand === b.slug ? "#0f172a" : "#1e293b",
                color: "#f8fafc",
                cursor: "pointer",
                textAlign: "left",
              }}
            >
              <div style={{ fontWeight: 700, fontSize: "0.95rem" }}>{b.name}</div>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>{b.tag}</div>
            </button>
          ))}
        </div>
      </section>

      {/* Form Controls */}
      <section style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", marginBottom: "2rem" }}>
        <div style={{ marginBottom: "1rem" }}>
          <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 700, color: "#cbd5e1", marginBottom: 6 }}>
            MARKETING TOPIC / SCENARIO:
          </label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            style={{
              width: "100%",
              padding: "10px",
              borderRadius: "6px",
              border: "1px solid #475569",
              background: "#0f172a",
              color: "#f8fafc",
              fontSize: "0.95rem",
              boxSizing: "border-box",
            }}
          />
        </div>

        <div style={{ display: "flex", gap: "15px", alignItems: "center" }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 700, color: "#cbd5e1", marginBottom: 6 }}>
              OUTPUT PLATFORM FORMAT:
            </label>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              style={{
                width: "100%",
                padding: "10px",
                borderRadius: "6px",
                border: "1px solid #475569",
                background: "#0f172a",
                color: "#f8fafc",
                fontSize: "0.95rem",
              }}
            >
              <option value="instagram_carousel">Instagram Carousel (4:5 / 1:1)</option>
              <option value="linkedin_post">LinkedIn Hero Image (16:9)</option>
              <option value="reel_script">Reel Cover / Video Prompt (9:16)</option>
            </select>
          </div>

          <button
            onClick={handleGenerate}
            disabled={loading}
            style={{
              marginTop: "22px",
              padding: "12px 24px",
              borderRadius: "6px",
              background: loading ? "#64748b" : "#0284c7",
              color: "#ffffff",
              fontWeight: 700,
              fontSize: "0.95rem",
              border: "none",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Generating Creative..." : "✨ Generate Creative Package"}
          </button>
        </div>
      </section>

      {error && (
        <div style={{ padding: "12px", background: "#7f1d1d", color: "#fecaca", borderRadius: 8, marginBottom: "1.5rem" }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Creative Result Presentation */}
      {result && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Hero Image Prompt Box */}
          <div style={{ background: "#0f172a", border: "1px solid #0284c7", borderRadius: 10, padding: "1.5rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <h3 style={{ margin: 0, color: "#38bdf8", fontSize: "1.1rem" }}>
                🖼️ Midjourney / Flux Hero Image Prompt
              </h3>
              <span style={{ fontSize: "0.8rem", background: "#0369a1", color: "white", padding: "4px 8px", borderRadius: 4 }}>
                Ratio: {result.creative.aspect_ratio}
              </span>
            </div>
            <div style={{ background: "#1e293b", padding: "12px", borderRadius: 6, color: "#e2e8f0", fontSize: "0.95rem", lineHeight: 1.5 }}>
              <code>{result.creative.hero_image_prompt}</code>
            </div>
            <div style={{ marginTop: 8, fontSize: "0.8rem", color: "#94a3b8" }}>
              <strong>Negative Filters:</strong> {result.creative.negative_prompt}
            </div>
          </div>

          {/* 5-Slide Carousel Breakdown */}
          <div style={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 10, padding: "1.5rem" }}>
            <h3 style={{ margin: "0 0 1rem 0", color: "#f8fafc", fontSize: "1.1rem" }}>
              📱 5-Slide Structured Carousel Sequence
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px" }}>
              {result.creative.carousel_slides.map((slide) => (
                <div
                  key={slide.slide_number}
                  style={{
                    background: "#1e293b",
                    padding: "14px",
                    borderRadius: "8px",
                    borderTop: `4px solid ${slide.slide_number === 5 ? "#10b981" : "#38bdf8"}`,
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                    <span style={{ fontSize: "0.75rem", fontWeight: 800, color: "#94a3b8" }}>
                      SLIDE {slide.slide_number}
                    </span>
                    {slide.slide_number === 5 && (
                      <span style={{ fontSize: "0.7rem", color: "#10b981", fontWeight: 700 }}>CTA</span>
                    )}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#38bdf8", marginBottom: 6, fontStyle: "italic" }}>
                    👁️ {slide.visual_cue}
                  </div>
                  <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#f8fafc", marginBottom: 6 }}>
                    {slide.headline}
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "#cbd5e1", lineHeight: 1.4 }}>
                    {slide.body_copy}
                  </div>
                  {slide.cta && (
                    <div style={{ marginTop: 8, fontSize: "0.75rem", color: "#34d399", fontWeight: 600 }}>
                      👉 {slide.cta}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
