"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  fetchMasterclassTemplates,
  generateRepurposedContent,
  saveRepurposedAssetToQueue,
  MasterclassTemplate,
  RepurposedNurtureKit,
} from "@/lib/api";

export default function RepurposePage() {
  const [templates, setTemplates] = useState<MasterclassTemplate[]>([]);
  const [selectedBrand, setSelectedBrand] = useState("jade");
  const [sourceText, setSourceText] = useState("");
  const [docTitle, setDocTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"linkedin" | "carousel" | "x_thread" | "email">("linkedin");
  const [result, setResult] = useState<RepurposedNurtureKit | null>(null);
  const [copyStatus, setCopyStatus] = useState<string | null>(null);
  const [queueStatus, setQueueStatus] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [savingToQueue, setSavingToQueue] = useState(false);

  useEffect(() => {
    fetchMasterclassTemplates()
      .then((data) => {
        setTemplates(data);
        if (data.length > 0) {
          setSelectedBrand(data[0].brand_slug);
          setDocTitle(data[0].title);
          setSourceText(data[0].content);
        }
      })
      .catch((err) => console.error("Failed to load templates:", err));
  }, []);

  const handleSelectTemplate = (template: MasterclassTemplate) => {
    setSelectedBrand(template.brand_slug);
    setDocTitle(template.title);
    setSourceText(template.content);
    setResult(null);
    setQueueStatus(null);
  };

  const handleRepurpose = async () => {
    if (!sourceText.trim()) return;
    setLoading(true);
    setQueueStatus(null);
    try {
      const data = await generateRepurposedContent(sourceText, selectedBrand, docTitle);
      setResult(data);
    } catch (err: any) {
      setQueueStatus({ type: "error", text: `Repurposing failed: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopyStatus(label);
    setTimeout(() => setCopyStatus(null), 2500);
  };

  const handleSendToQueue = async (platform: string, assetType: string, contentText: string) => {
    setSavingToQueue(true);
    setQueueStatus(null);
    try {
      const res = await saveRepurposedAssetToQueue(
        selectedBrand,
        platform,
        assetType,
        contentText,
        docTitle || "Repurposed Masterclass Content"
      );
      setQueueStatus({
        type: "success",
        text: `✅ ${res.message} (Outcome: ${res.compliance_outcome.toUpperCase()}) — Visible on /review dashboard`,
      });
    } catch (err: any) {
      setQueueStatus({
        type: "error",
        text: `Failed to save asset: ${err.message}`,
      });
    } finally {
      setSavingToQueue(false);
    }
  };

  return (
    <main style={{ padding: "2.5rem", maxWidth: 1100, margin: "0 auto", fontFamily: "system-ui, sans-serif" }}>
      <header style={{ marginBottom: "2rem", borderBottom: "1px solid #334155", paddingBottom: "1rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.25rem" }}>
              <h1 style={{ fontSize: "1.8rem", fontWeight: 800, margin: 0, color: "#f8fafc" }}>
                📚 Insurtech 101 Knowledge Repurposing Agent
              </h1>
              <span
                style={{
                  background: "#6366f122",
                  color: "#818cf8",
                  border: "1px solid #6366f144",
                  padding: "2px 8px",
                  borderRadius: "4px",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                }}
              >
                HACKATHON BONUS
              </span>
            </div>
            <p style={{ color: "#94a3b8", marginTop: "0.25rem", fontSize: "0.95rem" }}>
              Transform complex insurance policy whitepapers, case studies, and masterclass guides into high-converting,
              compliance-gated multi-channel nurture kits.
            </p>
          </div>
          <Link href="/" style={{ color: "#38bdf8", textDecoration: "none", fontSize: "0.9rem", fontWeight: 600 }}>
            ← Back to OS Hub
          </Link>
        </div>
      </header>

      {/* Quick Template Selector */}
      <section style={{ marginBottom: "1.5rem" }}>
        <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, color: "#cbd5e1", marginBottom: "0.5rem" }}>
          ⚡ 1-Click Load Masterclass Whitepapers / Case Studies:
        </label>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          {templates.map((tpl) => (
            <button
              key={tpl.id}
              onClick={() => handleSelectTemplate(tpl)}
              style={{
                background: docTitle === tpl.title ? "#1e293b" : "#0f172a",
                border: docTitle === tpl.title ? "1px solid #38bdf8" : "1px solid #334155",
                color: docTitle === tpl.title ? "#38bdf8" : "#94a3b8",
                padding: "8px 14px",
                borderRadius: "6px",
                fontSize: "0.85rem",
                cursor: "pointer",
                fontWeight: 600,
                transition: "all 0.2s ease",
              }}
            >
              📖 {tpl.title}
            </button>
          ))}
        </div>
      </section>

      {/* Input Form */}
      <div
        style={{
          background: "#0f172a",
          border: "1px solid #1e293b",
          borderRadius: "12px",
          padding: "1.5rem",
          marginBottom: "2rem",
        }}
      >
        <div style={{ display: "grid", gridTemplateColumns: "1fr 200px", gap: "1rem", marginBottom: "1rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, color: "#cbd5e1", marginBottom: "0.25rem" }}>
              Document / Masterclass Topic:
            </label>
            <input
              type="text"
              value={docTitle}
              onChange={(e) => setDocTitle(e.target.value)}
              placeholder="e.g. Jewellers Block vs Commercial Property 101"
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: "6px",
                border: "1px solid #334155",
                background: "#1e293b",
                color: "#f8fafc",
                fontSize: "0.9rem",
              }}
            />
          </div>
          <div>
            <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, color: "#cbd5e1", marginBottom: "0.25rem" }}>
              Target Brand:
            </label>
            <select
              value={selectedBrand}
              onChange={(e) => setSelectedBrand(e.target.value)}
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: "6px",
                border: "1px solid #334155",
                background: "#1e293b",
                color: "#f8fafc",
                fontSize: "0.9rem",
              }}
            >
              <option value="jade">Jade (Jewellers Block)</option>
              <option value="ja-assure">JA Assure / Jaguar Transit</option>
              <option value="doctor-shield">DoctorShield (Medical Indemnity)</option>
            </select>
          </div>
        </div>

        <div style={{ marginBottom: "1.25rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.25rem" }}>
            <label style={{ fontSize: "0.85rem", fontWeight: 600, color: "#cbd5e1" }}>
              Source Material (Whitepaper / Case Study / Complex Policy Clauses):
            </label>
            <span style={{ fontSize: "0.75rem", color: "#64748b" }}>{sourceText.length} characters</span>
          </div>
          <textarea
            rows={7}
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value)}
            placeholder="Paste raw insurance training material, policy wording, or masterclass transcript here..."
            style={{
              width: "100%",
              padding: "12px",
              borderRadius: "8px",
              border: "1px solid #334155",
              background: "#1e293b",
              color: "#f8fafc",
              fontSize: "0.88rem",
              lineHeight: 1.5,
              fontFamily: "monospace",
              resize: "vertical",
            }}
          />
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
            🛡️ Automatically checked against MAS Notice 124 & brand guidelines before emission.
          </span>
          <button
            onClick={handleRepurpose}
            disabled={loading || !sourceText.trim()}
            style={{
              background: loading ? "#475569" : "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
              color: "#fff",
              border: "none",
              padding: "12px 24px",
              borderRadius: "8px",
              fontWeight: 700,
              fontSize: "0.95rem",
              cursor: loading ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              boxShadow: "0 4px 14px rgba(99, 102, 241, 0.3)",
            }}
          >
            {loading ? "⚙️ Repurposing with Gemini..." : "✨ Repurpose into Multi-Channel Kit"}
          </button>
        </div>
      </div>

      {queueStatus && (
        <div
          style={{
            padding: "14px",
            borderRadius: "8px",
            marginBottom: "1.5rem",
            background: queueStatus.type === "success" ? "#064e3b" : "#7f1d1d",
            color: queueStatus.type === "success" ? "#a7f3d0" : "#fecaca",
            border: `1px solid ${queueStatus.type === "success" ? "#059669" : "#dc2626"}`,
            fontSize: "0.9rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span>{queueStatus.text}</span>
          {queueStatus.type === "success" && (
            <Link
              href="/review"
              style={{
                color: "#6ee7b7",
                textDecoration: "underline",
                fontWeight: 700,
                fontSize: "0.85rem",
              }}
            >
              Open Review Queue →
            </Link>
          )}
        </div>
      )}

      {/* Output Section */}
      {result && (
        <section
          style={{
            background: "#0f172a",
            border: "1px solid #1e293b",
            borderRadius: "12px",
            padding: "1.5rem",
          }}
        >
          {/* Executive Insights Bar */}
          <div
            style={{
              background: "#1e293b",
              borderRadius: "8px",
              padding: "1.25rem",
              marginBottom: "1.5rem",
              borderLeft: "4px solid #6366f1",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.5rem" }}>
              <div>
                <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#818cf8", textTransform: "uppercase" }}>
                  Synthesized Executive Synopsis
                </span>
                <p style={{ margin: "0.25rem 0 0 0", color: "#f8fafc", fontSize: "0.95rem", lineHeight: 1.5 }}>
                  {result.executive_summary}
                </p>
              </div>
              <div style={{ textAlign: "right", minWidth: 160 }}>
                <span
                  style={{
                    background: result.compliance_check.passed ? "#064e3b" : "#78350f",
                    color: result.compliance_check.passed ? "#a7f3d0" : "#fde68a",
                    padding: "4px 8px",
                    borderRadius: "4px",
                    fontSize: "0.75rem",
                    fontWeight: 700,
                  }}
                >
                  {result.compliance_check.passed ? "🛡️ MAS Passed" : "⚠️ Compliance Review"}
                </span>
              </div>
            </div>

            <div style={{ display: "flex", gap: "1.5rem", marginTop: "0.75rem", fontSize: "0.85rem", color: "#94a3b8" }}>
              <div>
                <strong style={{ color: "#cbd5e1" }}>Audience:</strong> {result.target_audience}
              </div>
              <div>
                <strong style={{ color: "#cbd5e1" }}>Key Focus:</strong> {result.key_takeaways?.join(" • ") || "Specialist Risk Management"}
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div style={{ display: "flex", borderBottom: "1px solid #334155", marginBottom: "1.5rem", gap: "0.5rem" }}>
            <button
              onClick={() => setActiveTab("linkedin")}
              style={{
                background: activeTab === "linkedin" ? "#1e293b" : "transparent",
                border: "none",
                borderBottom: activeTab === "linkedin" ? "2px solid #38bdf8" : "none",
                color: activeTab === "linkedin" ? "#38bdf8" : "#94a3b8",
                padding: "10px 16px",
                fontWeight: 700,
                fontSize: "0.9rem",
                cursor: "pointer",
                borderRadius: "6px 6px 0 0",
              }}
            >
              💼 LinkedIn Executive Post
            </button>
            <button
              onClick={() => setActiveTab("carousel")}
              style={{
                background: activeTab === "carousel" ? "#1e293b" : "transparent",
                border: "none",
                borderBottom: activeTab === "carousel" ? "2px solid #ec4899" : "none",
                color: activeTab === "carousel" ? "#ec4899" : "#94a3b8",
                padding: "10px 16px",
                fontWeight: 700,
                fontSize: "0.9rem",
                cursor: "pointer",
                borderRadius: "6px 6px 0 0",
              }}
            >
              🖼️ 5-Slide Infographic Carousel ({result.carousel_deck?.slides?.length || 5} Slides)
            </button>
            <button
              onClick={() => setActiveTab("x_thread")}
              style={{
                background: activeTab === "x_thread" ? "#1e293b" : "transparent",
                border: "none",
                borderBottom: activeTab === "x_thread" ? "2px solid #f59e0b" : "none",
                color: activeTab === "x_thread" ? "#f59e0b" : "#94a3b8",
                padding: "10px 16px",
                fontWeight: 700,
                fontSize: "0.9rem",
                cursor: "pointer",
                borderRadius: "6px 6px 0 0",
              }}
            >
              🐦 X (Twitter) Thread ({result.x_thread?.length || 4} Posts)
            </button>
            <button
              onClick={() => setActiveTab("email")}
              style={{
                background: activeTab === "email" ? "#1e293b" : "transparent",
                border: "none",
                borderBottom: activeTab === "email" ? "2px solid #10b981" : "none",
                color: activeTab === "email" ? "#10b981" : "#94a3b8",
                padding: "10px 16px",
                fontWeight: 700,
                fontSize: "0.9rem",
                cursor: "pointer",
                borderRadius: "6px 6px 0 0",
              }}
            >
              ✉️ High-Conversion B2B Email
            </button>
          </div>

          {/* TAB 1: LinkedIn Brief */}
          {activeTab === "linkedin" && (
            <div>
              <div
                style={{
                  background: "#1e293b",
                  borderRadius: "8px",
                  padding: "1.5rem",
                  border: "1px solid #334155",
                  marginBottom: "1rem",
                }}
              >
                <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#f8fafc", marginBottom: "1rem" }}>
                  {result.linkedin_brief?.headline}
                </div>
                <div style={{ whiteSpace: "pre-wrap", color: "#cbd5e1", fontSize: "0.92rem", lineHeight: 1.6 }}>
                  {result.linkedin_brief?.body}
                </div>
                <div style={{ marginTop: "1rem", color: "#38bdf8", fontSize: "0.85rem", fontWeight: 600 }}>
                  {result.linkedin_brief?.hashtags?.join(" ")}
                </div>
              </div>

              <div style={{ display: "flex", gap: "0.75rem" }}>
                <button
                  onClick={() =>
                    handleCopy(
                      `${result.linkedin_brief?.headline}\n\n${result.linkedin_brief?.body}\n\n${result.linkedin_brief?.hashtags?.join(" ")}`,
                      "linkedin"
                    )
                  }
                  style={{
                    background: "#334155",
                    color: "#f8fafc",
                    border: "none",
                    padding: "8px 16px",
                    borderRadius: "6px",
                    fontWeight: 600,
                    fontSize: "0.85rem",
                    cursor: "pointer",
                  }}
                >
                  {copyStatus === "linkedin" ? "✓ Copied!" : "📋 Copy LinkedIn Post"}
                </button>
                <button
                  onClick={() =>
                    handleSendToQueue("linkedin", "social_post", result.linkedin_brief?.body || "")
                  }
                  disabled={savingToQueue}
                  style={{
                    background: "#0284c7",
                    color: "#fff",
                    border: "none",
                    padding: "8px 16px",
                    borderRadius: "6px",
                    fontWeight: 600,
                    fontSize: "0.85rem",
                    cursor: savingToQueue ? "not-allowed" : "pointer",
                  }}
                >
                  🛡️ Push to Compliance Review Queue
                </button>
              </div>
            </div>
          )}

          {/* TAB 2: 5-Slide Carousel Deck */}
          {activeTab === "carousel" && (
            <div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                  gap: "1rem",
                  marginBottom: "1.25rem",
                }}
              >
                {result.carousel_deck?.slides?.map((slide) => (
                  <div
                    key={slide.slide_number}
                    style={{
                      background: "#1e293b",
                      border: "1px solid #334155",
                      borderRadius: "10px",
                      padding: "1.25rem",
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
                          marginBottom: "0.75rem",
                        }}
                      >
                        <span
                          style={{
                            background: "#ec489922",
                            color: "#f472b6",
                            padding: "2px 8px",
                            borderRadius: "4px",
                            fontSize: "0.75rem",
                            fontWeight: 800,
                          }}
                        >
                          SLIDE {slide.slide_number}
                        </span>
                        <span style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: 600 }}>{slide.role}</span>
                      </div>
                      <h4 style={{ margin: "0 0 0.5rem 0", color: "#f8fafc", fontSize: "0.95rem" }}>
                        {slide.headline}
                      </h4>
                      <p style={{ margin: 0, color: "#cbd5e1", fontSize: "0.85rem", lineHeight: 1.5 }}>
                        {slide.body}
                      </p>
                    </div>

                    <div
                      style={{
                        marginTop: "1rem",
                        padding: "8px",
                        background: "#0f172a",
                        borderRadius: "6px",
                        border: "1px solid #334155",
                        fontSize: "0.75rem",
                        color: "#a5b4fc",
                      }}
                    >
                      🎨 <strong>Visual Cue:</strong> {slide.visual_direction}
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ display: "flex", gap: "0.75rem" }}>
                <button
                  onClick={() =>
                    handleCopy(
                      result.carousel_deck?.slides
                        ?.map((s) => `[Slide ${s.slide_number} - ${s.role}]\n${s.headline}\n${s.body}\nVisual: ${s.visual_direction}`)
                        .join("\n\n"),
                      "carousel"
                    )
                  }
                  style={{
                    background: "#334155",
                    color: "#f8fafc",
                    border: "none",
                    padding: "8px 16px",
                    borderRadius: "6px",
                    fontWeight: 600,
                    fontSize: "0.85rem",
                    cursor: "pointer",
                  }}
                >
                  {copyStatus === "carousel" ? "✓ Copied!" : "📋 Copy All 5 Slides"}
                </button>
                <button
                  onClick={() =>
                    handleSendToQueue(
                      "instagram",
                      "social_post",
                      result.carousel_deck?.slides?.map((s) => `Slide ${s.slide_number}: ${s.headline}\n${s.body}`).join("\n\n") || ""
                    )
                  }
                  disabled={savingToQueue}
                  style={{
                    background: "#ec4899",
                    color: "#fff",
                    border: "none",
                    padding: "8px 16px",
                    borderRadius: "6px",
                    fontWeight: 600,
                    fontSize: "0.85rem",
                    cursor: savingToQueue ? "not-allowed" : "pointer",
                  }}
                >
                  🛡️ Push Carousel to Review Queue
                </button>
              </div>
            </div>
          )}

          {/* TAB 3: X (Twitter) Thread */}
          {activeTab === "x_thread" && (
            <div>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.25rem" }}>
                {result.x_thread?.map((item) => (
                  <div
                    key={item.post_number}
                    style={{
                      background: "#1e293b",
                      border: "1px solid #334155",
                      borderRadius: "8px",
                      padding: "1rem",
                      display: "flex",
                      gap: "1rem",
                    }}
                  >
                    <div
                      style={{
                        background: "#f59e0b22",
                        color: "#fbbf24",
                        width: 28,
                        height: 28,
                        borderRadius: "50%",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontWeight: 800,
                        fontSize: "0.8rem",
                        flexShrink: 0,
                      }}
                    >
                      {item.post_number}
                    </div>
                    <div style={{ flex: 1 }}>
                      <p style={{ margin: 0, color: "#f8fafc", fontSize: "0.9rem", lineHeight: 1.5 }}>
                        {item.tweet}
                      </p>
                      <span style={{ display: "block", marginTop: "0.5rem", fontSize: "0.75rem", color: "#64748b" }}>
                        {item.tweet.length} / 280 characters
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ display: "flex", gap: "0.75rem" }}>
                <button
                  onClick={() =>
                    handleCopy(
                      result.x_thread?.map((t) => `${t.post_number}/${result.x_thread.length} ${t.tweet}`).join("\n\n"),
                      "x_thread"
                    )
                  }
                  style={{
                    background: "#334155",
                    color: "#f8fafc",
                    border: "none",
                    padding: "8px 16px",
                    borderRadius: "6px",
                    fontWeight: 600,
                    fontSize: "0.85rem",
                    cursor: "pointer",
                  }}
                >
                  {copyStatus === "x_thread" ? "✓ Copied!" : "📋 Copy Full Thread"}
                </button>
                <button
                  onClick={() =>
                    handleSendToQueue(
                      "x",
                      "social_post",
                      result.x_thread?.map((t) => `${t.post_number}/${result.x_thread.length} ${t.tweet}`).join("\n\n") || ""
                    )
                  }
                  disabled={savingToQueue}
                  style={{
                    background: "#d97706",
                    color: "#fff",
                    border: "none",
                    padding: "8px 16px",
                    borderRadius: "6px",
                    fontWeight: 600,
                    fontSize: "0.85rem",
                    cursor: savingToQueue ? "not-allowed" : "pointer",
                  }}
                >
                  🛡️ Push Thread to Review Queue
                </button>
              </div>
            </div>
          )}

          {/* TAB 4: B2B Outreach Email */}
          {activeTab === "email" && (
            <div>
              <div
                style={{
                  background: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  padding: "1.5rem",
                  marginBottom: "1.25rem",
                }}
              >
                <div style={{ marginBottom: "1rem", borderBottom: "1px solid #334155", paddingBottom: "0.75rem" }}>
                  <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Subject: </span>
                  <strong style={{ color: "#f8fafc", fontSize: "0.95rem" }}>
                    {result.outreach_email?.subject}
                  </strong>
                </div>
                <div style={{ whiteSpace: "pre-wrap", color: "#cbd5e1", fontSize: "0.92rem", lineHeight: 1.6 }}>
                  {result.outreach_email?.body}
                </div>
              </div>

              <div style={{ display: "flex", gap: "0.75rem" }}>
                <button
                  onClick={() =>
                    handleCopy(
                      `Subject: ${result.outreach_email?.subject}\n\n${result.outreach_email?.body}`,
                      "email"
                    )
                  }
                  style={{
                    background: "#334155",
                    color: "#f8fafc",
                    border: "none",
                    padding: "8px 16px",
                    borderRadius: "6px",
                    fontWeight: 600,
                    fontSize: "0.85rem",
                    cursor: "pointer",
                  }}
                >
                  {copyStatus === "email" ? "✓ Copied!" : "📋 Copy Email Pitch"}
                </button>
                <button
                  onClick={() =>
                    handleSendToQueue("email", "email", result.outreach_email?.body || "")
                  }
                  disabled={savingToQueue}
                  style={{
                    background: "#059669",
                    color: "#fff",
                    border: "none",
                    padding: "8px 16px",
                    borderRadius: "6px",
                    fontWeight: 600,
                    fontSize: "0.85rem",
                    cursor: savingToQueue ? "not-allowed" : "pointer",
                  }}
                >
                  🛡️ Push Email to Review Queue
                </button>
              </div>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
