"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  fetchBrands,
  fetchMasterclassTemplates,
  generateRepurposedContent,
  saveRepurposedAssetToQueue,
  MasterclassTemplate,
  RepurposedNurtureKit,
  BrandSummary,
} from "@/lib/api";

export default function RepurposePage() {
  const [brands, setBrands] = useState<BrandSummary[]>([]);
  const [templates, setTemplates] = useState<MasterclassTemplate[]>([]);
  const [selectedBrand, setSelectedBrand] = useState("jade");
  const [sourceText, setSourceText] = useState("");
  const [docTitle, setDocTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"linkedin" | "carousel" | "x_thread" | "email">("linkedin");
  const [result, setResult] = useState<RepurposedNurtureKit | null>(null);
  const [copyStatus, setCopyStatus] = useState<string | null>(null);
  const [queueStatus, setQueueStatus] = useState<{ type: "success" | "error"; text: string; versionId?: string } | null>(null);
  const [savingToQueue, setSavingToQueue] = useState(false);

  useEffect(() => {
    fetchBrands()
      .then((bs) => {
        if (Array.isArray(bs) && bs.length > 0) {
          setBrands(bs);
        }
      })
      .catch((err) => console.warn("Failed to load brands:", err));

    fetchMasterclassTemplates()
      .then((data) => {
        if (Array.isArray(data)) {
          setTemplates(data);
          if (data.length > 0) {
            setSelectedBrand(data[0].brand_slug);
            setDocTitle(data[0].title);
            setSourceText(data[0].content);
          }
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
        text: `✅ ${res.message} (Compliance Verdict: ${res.compliance_outcome.replace(/_/g, ' ').toUpperCase()})`,
        versionId: res.version_id,
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
    <main style={{ padding: "2.5rem 1.5rem 4rem", maxWidth: 1100, margin: "0 auto" }}>
      <header style={{ marginBottom: "2rem", borderBottom: "1px solid #e2e8f0", paddingBottom: "1rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.25rem" }}>
              <h1 style={{ fontSize: "1.8rem", fontWeight: 800, margin: 0, color: "#002b49" }}>
                📚 Content Repurposing Engine
              </h1>
              <span
                style={{
                  background: "#eff6ff",
                  color: "#0066cc",
                  border: "1px solid #bfdbfe",
                  padding: "2px 8px",
                  borderRadius: "4px",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                }}
              >
                MULTI-CHANNEL
              </span>
            </div>
            <p style={{ color: "#64748b", marginTop: "0.25rem", fontSize: "0.95rem" }}>
              Transform complex insurance policy whitepapers, case studies, and masterclass guides into high-converting,
              compliance-gated multi-channel nurture kits.
            </p>
          </div>
          <Link href="/" style={{ color: "#0066cc", textDecoration: "none", fontSize: "0.9rem", fontWeight: 600 }}>
            ← Home
          </Link>
        </div>
      </header>

      {/* Quick Template Selector */}
      <section style={{ marginBottom: "1.5rem" }}>
        <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 700, color: "#002b49", marginBottom: "0.5rem" }}>
          ⚡ 1-Click Load Masterclass Whitepapers / Case Studies:
        </label>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          {templates.map((tpl) => (
            <button
              key={tpl.id}
              onClick={() => handleSelectTemplate(tpl)}
              style={{
                background: docTitle === tpl.title ? "#0066cc" : "#ffffff",
                border: docTitle === tpl.title ? "1px solid #0066cc" : "1px solid #cbd5e1",
                color: docTitle === tpl.title ? "#ffffff" : "#334155",
                padding: "8px 14px",
                borderRadius: "6px",
                fontSize: "0.85rem",
                cursor: "pointer",
                fontWeight: 600,
                transition: "all 0.15s ease",
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
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: "12px",
          padding: "1.75rem",
          marginBottom: "2rem",
          boxShadow: "0 1px 4px rgba(0, 43, 73, 0.04)",
        }}
      >
        <div style={{ display: "grid", gridTemplateColumns: "1fr 240px", gap: "1rem", marginBottom: "1rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 700, color: "#002b49", marginBottom: "0.25rem" }}>
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
                border: "1px solid #cbd5e1",
                background: "#f8fafc",
                color: "#0f172a",
                fontSize: "0.9rem",
              }}
            />
          </div>
          <div>
            <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 700, color: "#002b49", marginBottom: "0.25rem" }}>
              Target Brand:
            </label>
            <select
              value={selectedBrand}
              onChange={(e) => setSelectedBrand(e.target.value)}
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: "6px",
                border: "1px solid #cbd5e1",
                background: "#ffffff",
                color: "#0f172a",
                fontSize: "0.9rem",
              }}
            >
              {brands.length > 0 ? (
                brands.map((b) => (
                  <option key={b.brand_id} value={b.slug}>
                    {b.name}
                  </option>
                ))
              ) : (
                <>
                  <option value="jade">Jade (Jewellers Block)</option>
                  <option value="jaguar-transit">Jaguar Transit (Cargo)</option>
                  <option value="doctorshield">DoctorShield (Medical Indemnity)</option>
                </>
              )}
            </select>
          </div>
        </div>

        <div style={{ marginBottom: "1.25rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.25rem" }}>
            <label style={{ fontSize: "0.85rem", fontWeight: 700, color: "#002b49" }}>
              Source Material (Whitepaper / Case Study / Policy Clauses):
            </label>
            <span style={{ fontSize: "0.75rem", color: "#64748b" }}>{sourceText.length} characters</span>
          </div>
          <textarea
            rows={6}
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value)}
            placeholder="Paste raw insurance training material, policy wording, or masterclass transcript here..."
            style={{
              width: "100%",
              padding: "12px",
              borderRadius: "8px",
              border: "1px solid #cbd5e1",
              background: "#f8fafc",
              color: "#0f172a",
              fontSize: "0.88rem",
              lineHeight: 1.5,
              resize: "vertical",
            }}
          />
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
            🛡️ Automatically audited against MAS Advertising Rules before release.
          </span>
          <button
            onClick={handleRepurpose}
            disabled={loading || !sourceText.trim()}
            style={{
              background: loading ? "#94a3b8" : "#0066cc",
              color: "#fff",
              border: "none",
              padding: "11px 22px",
              borderRadius: "6px",
              fontWeight: 700,
              fontSize: "0.95rem",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "⚙️ Repurposing with Gemini..." : "✨ Repurpose into Multi-Channel Kit"}
          </button>
        </div>
      </div>

      {queueStatus && (
        <div
          style={{
            padding: "16px 18px",
            borderRadius: "8px",
            marginBottom: "1.5rem",
            background: queueStatus.type === "success" ? "#ecfdf5" : "#fef2f2",
            color: queueStatus.type === "success" ? "#047857" : "#b91c1c",
            border: `1px solid ${queueStatus.type === "success" ? "#a7f3d0" : "#fecaca"}`,
            fontSize: "0.95rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 10,
            boxShadow: "0 2px 5px rgba(0,0,0,0.03)",
          }}
        >
          <span>{queueStatus.text}</span>
          {queueStatus.type === "success" && (
            <Link
              href={queueStatus.versionId ? `/review/${queueStatus.versionId}` : "/review"}
              style={{
                color: "#ffffff",
                background: "#047857",
                padding: "6px 14px",
                borderRadius: "6px",
                textDecoration: "none",
                fontWeight: 700,
                fontSize: "0.85rem",
              }}
            >
              Open in Review Queue →
            </Link>
          )}
        </div>
      )}

      {/* Output Section */}
      {result && (
        <section
          style={{
            background: "#ffffff",
            border: "1px solid #e2e8f0",
            borderRadius: "12px",
            padding: "1.75rem",
            boxShadow: "0 1px 4px rgba(0, 43, 73, 0.04)",
          }}
        >
          {/* Executive Insights Bar */}
          <div
            style={{
              background: "#eff6ff",
              borderRadius: "8px",
              padding: "1.25rem",
              marginBottom: "1.25rem",
              borderLeft: "4px solid #0066cc",
            }}
          >
            <span style={{ fontSize: "0.75rem", fontWeight: 800, color: "#0066cc", textTransform: "uppercase" }}>
              Synthesized Executive Synopsis
            </span>
            <p style={{ margin: "0.25rem 0 0 0", color: "#002b49", fontSize: "0.95rem", lineHeight: 1.5, fontWeight: 500 }}>
              {result.executive_summary}
            </p>
          </div>

          {/* Real-Time Compliance Pre-Audit Status Strip */}
          {result.compliance_check && (
            <div
              style={{
                background: result.compliance_check.passed ? "#f0fdf4" : "#fffbeb",
                border: `1px solid ${result.compliance_check.passed ? "#bbf7d0" : "#fde68a"}`,
                borderRadius: "8px",
                padding: "12px 16px",
                marginBottom: "1.5rem",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: 8,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 16 }}>{result.compliance_check.passed ? "🛡️" : "⚠️"}</span>
                <div>
                  <strong style={{ color: result.compliance_check.passed ? "#166534" : "#92400e", fontSize: "0.9rem" }}>
                    Compliance Engine Audit: {result.compliance_check.passed ? "PASSED (Zero MAS Violations Detected)" : "FLAGGED FOR HUMAN REVIEW"}
                  </strong>
                  {result.compliance_check.issues_found && result.compliance_check.issues_found.length > 0 && (
                    <div style={{ fontSize: "0.8rem", color: "#b91c1c", marginTop: 2 }}>
                      Issues detected: {result.compliance_check.issues_found.map((i: any) => i.term).join(", ")}
                    </div>
                  )}
                </div>
              </div>
              <span
                style={{
                  background: result.compliance_check.passed ? "#dcfce7" : "#fef3c7",
                  color: result.compliance_check.passed ? "#15803d" : "#b45309",
                  fontWeight: 700,
                  fontSize: "0.75rem",
                  padding: "3px 8px",
                  borderRadius: 4,
                  textTransform: "uppercase",
                }}
              >
                MAS Advertising Check
              </span>
            </div>
          )}

          {/* Format Tabs */}
          <div
            style={{
              display: "flex",
              gap: "0.5rem",
              borderBottom: "1px solid #e2e8f0",
              marginBottom: "1.5rem",
              overflowX: "auto",
            }}
          >
            {[
              { id: "linkedin", label: "💼 LinkedIn Executive Post" },
              { id: "carousel", label: "📱 5-Slide Carousel Breakdown" },
              { id: "x_thread", label: "🧵 X (Twitter) Thread" },
              { id: "email", label: "✉️ B2B Outreach Pitch" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                style={{
                  background: activeTab === tab.id ? "#0066cc" : "transparent",
                  color: activeTab === tab.id ? "#ffffff" : "#64748b",
                  border: "none",
                  padding: "10px 18px",
                  borderRadius: "6px 6px 0 0",
                  fontWeight: 700,
                  fontSize: "0.9rem",
                  cursor: "pointer",
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* TAB 1: LinkedIn Brief */}
          {activeTab === "linkedin" && (
            <div>
              <div
                style={{
                  background: "#f8fafc",
                  borderRadius: "8px",
                  padding: "1.5rem",
                  border: "1px solid #e2e8f0",
                  marginBottom: "1rem",
                }}
              >
                <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#002b49", marginBottom: "1rem" }}>
                  {result.linkedin_brief?.headline}
                </div>
                <div style={{ whiteSpace: "pre-wrap", color: "#0f172a", fontSize: "0.95rem", lineHeight: 1.6 }}>
                  {result.linkedin_brief?.body}
                </div>
                <div style={{ marginTop: "1rem", color: "#0066cc", fontSize: "0.88rem", fontWeight: 600 }}>
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
                    background: "#f1f5f9",
                    color: "#0f172a",
                    border: "1px solid #cbd5e1",
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
                    background: "#0066cc",
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

          {/* TAB 2: Carousel */}
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
                      background: "#f8fafc",
                      border: "1px solid #e2e8f0",
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
                            background: "#eff6ff",
                            color: "#0066cc",
                            padding: "2px 8px",
                            borderRadius: "4px",
                            fontSize: "0.75rem",
                            fontWeight: 800,
                          }}
                        >
                          SLIDE {slide.slide_number}
                        </span>
                        <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600 }}>{slide.role}</span>
                      </div>
                      <h4 style={{ margin: "0 0 0.5rem 0", color: "#002b49", fontSize: "0.95rem", fontWeight: 700 }}>
                        {slide.headline}
                      </h4>
                      <p style={{ margin: 0, color: "#334155", fontSize: "0.85rem", lineHeight: 1.5 }}>
                        {slide.body}
                      </p>
                    </div>

                    <div
                      style={{
                        marginTop: "1rem",
                        padding: "8px 10px",
                        background: "#ffffff",
                        borderRadius: "6px",
                        border: "1px solid #e2e8f0",
                        fontSize: "0.8rem",
                        color: "#0066cc",
                      }}
                    >
                      🎨 <strong>Visual:</strong> {slide.visual_direction}
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
                        .join("\n\n") || "",
                      "carousel"
                    )
                  }
                  style={{
                    background: "#f1f5f9",
                    color: "#0f172a",
                    border: "1px solid #cbd5e1",
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
                    background: "#0066cc",
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
                      background: "#f8fafc",
                      border: "1px solid #e2e8f0",
                      borderRadius: "8px",
                      padding: "1rem",
                      display: "flex",
                      gap: "1rem",
                    }}
                  >
                    <div
                      style={{
                        background: "#e0f2fe",
                        color: "#0284c7",
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
                      <p style={{ margin: 0, color: "#0f172a", fontSize: "0.9rem", lineHeight: 1.5 }}>
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
                      result.x_thread?.map((t) => `${t.post_number}/${result.x_thread?.length || 0} ${t.tweet}`).join("\n\n") || "",
                      "x_thread"
                    )
                  }
                  style={{
                    background: "#f1f5f9",
                    color: "#0f172a",
                    border: "1px solid #cbd5e1",
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
                      result.x_thread?.map((t) => `${t.post_number}/${result.x_thread?.length || 0} ${t.tweet}`).join("\n\n") || ""
                    )
                  }
                  disabled={savingToQueue}
                  style={{
                    background: "#0066cc",
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
                  background: "#f8fafc",
                  border: "1px solid #e2e8f0",
                  borderRadius: "8px",
                  padding: "1.5rem",
                  marginBottom: "1.25rem",
                }}
              >
                <div style={{ marginBottom: "1rem", borderBottom: "1px solid #e2e8f0", paddingBottom: "0.75rem" }}>
                  <span style={{ fontSize: "0.8rem", color: "#64748b" }}>Subject: </span>
                  <strong style={{ color: "#002b49", fontSize: "0.95rem" }}>
                    {result.outreach_email?.subject}
                  </strong>
                </div>
                <div style={{ whiteSpace: "pre-wrap", color: "#0f172a", fontSize: "0.92rem", lineHeight: 1.6 }}>
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
                    background: "#f1f5f9",
                    color: "#0f172a",
                    border: "1px solid #cbd5e1",
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
                    background: "#0066cc",
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
