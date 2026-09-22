"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  API_BASE_URL,
  fetchBrands,
  DemoRunResponse,
  DemoStep,
  DemoSuggestion,
  QuotaStatus,
  fetchDemoSuggestions,
  fetchFallbackExamples,
  fetchQuotaStatus,
  runDemo,
} from "@/lib/api";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "zh-Hans", label: "简体中文" },
  { code: "ms", label: "Bahasa Melayu" },
  { code: "id", label: "Bahasa Indonesia" },
];

const CJK_STACK =
  '-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif';

const STATUS_STYLE: Record<string, { dot: string; fg: string; bg: string }> = {
  pass: { dot: "#16a34a", fg: "#15803d", bg: "#f0fdf4" },
  warn: { dot: "#d97706", fg: "#b45309", bg: "#fffbeb" },
  fail: { dot: "#dc2626", fg: "#b91c1c", bg: "#fef2f2" },
  skipped: { dot: "#94a3b8", fg: "#64748b", bg: "#f8fafc" },
  error: { dot: "#dc2626", fg: "#b91c1c", bg: "#fef2f2" },
  pending: { dot: "#cbd5e1", fg: "#94a3b8", bg: "#f8fafc" },
};

const VERDICT: Record<string, { bg: string; fg: string; border: string; label: string }> = {
  pass: { bg: "#ecfdf5", fg: "#047857", border: "#a7f3d0", label: "PASS — COMPLIANT" },
  review: { bg: "#fffbeb", fg: "#b45309", border: "#fde68a", label: "NEEDS HUMAN REVIEW" },
  block: { bg: "#fef2f2", fg: "#b91c1c", border: "#fecaca", label: "BLOCKED — NON-COMPLIANT" },
};

function StepRow({ step, revealed }: { step: DemoStep; revealed: boolean }) {
  const s = STATUS_STYLE[revealed ? step.status : "pending"] ?? STATUS_STYLE.pending;
  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        padding: "12px 0",
        borderTop: "1px solid #e2e8f0",
        opacity: revealed ? 1 : 0.4,
        transition: "opacity 220ms ease",
      }}
    >
      <span
        style={{
          width: 12,
          height: 12,
          borderRadius: 999,
          background: s.dot,
          marginTop: 4,
          flexShrink: 0,
        }}
      />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: revealed ? "#0f172a" : "#64748b" }}>
          {step.label}
        </div>
        {revealed && (
          <>
            <div style={{ color: "#475569", fontSize: 13, marginTop: 2 }}>{step.detail}</div>
            {step.terms && step.terms.length > 0 && (
              <div style={{ marginTop: 6, display: "flex", gap: 6, flexWrap: "wrap" }}>
                {step.terms.map((t) => (
                  <code
                    key={t}
                    style={{
                      background: "#fef2f2",
                      color: "#b91c1c",
                      padding: "2px 8px",
                      borderRadius: 4,
                      fontSize: 12,
                      border: "1px solid #fecaca",
                    }}
                  >
                    {t}
                  </code>
                ))}
              </div>
            )}
            {step.issues && step.issues.length > 0 && (
              <ul style={{ margin: "6px 0 0", paddingLeft: 18, color: "#334155", fontSize: 13 }}>
                {step.issues.slice(0, 4).map((iss, i) => (
                  <li key={i} style={{ marginBottom: 4 }}>
                    <strong style={{ color: "#0f172a" }}>“{iss.term.slice(0, 110)}”</strong>
                    <br />
                    <span style={{ color: "#64748b" }}>
                      {iss.reason}
                      {iss.policy_ref && (
                        <code style={{ color: "#b91c1c", background: "#fee2e2", padding: "1px 5px", marginLeft: 4, borderRadius: 3 }}>
                          [{iss.policy_ref}]
                        </code>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function DemoPage() {
  const [brands, setBrands] = useState<any[]>([]);
  const [brandId, setBrandId] = useState<string>("");
  const [language, setLanguage] = useState("en");
  const [mode, setMode] = useState<"generate" | "check_only">("generate");
  const [text, setText] = useState("");
  const [suggestions, setSuggestions] = useState<DemoSuggestion[]>([]);
  const [quota, setQuota] = useState<QuotaStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [res, setRes] = useState<DemoRunResponse | null>(null);
  const [revealed, setRevealed] = useState(0);
  const [recorded, setRecorded] = useState<any[] | null>(null);
  const [showRecorded, setShowRecorded] = useState<any | null>(null);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => {
    fetchBrands()
      .then((bs) => {
        setBrands(bs);
        const jade = bs.find((b: any) => b.slug === "jade") ?? bs[0];
        if (jade) setBrandId(jade.brand_id);
      })
      .catch((e) => {
        console.warn("fetchBrands error:", e);
      });
    fetchDemoSuggestions().then((d) => setSuggestions(d.suggestions)).catch(() => {});
    fetchQuotaStatus().then(setQuota).catch(() => {});
    fetchFallbackExamples().then((d) => setRecorded(d.examples)).catch(() => {});
    return () => timers.current.forEach(clearTimeout);
  }, []);

  function revealSteps(count: number) {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setRevealed(0);
    for (let i = 1; i <= count; i++) {
      timers.current.push(setTimeout(() => setRevealed(i), i * 420));
    }
  }

  async function submit(overrideText?: string) {
    const claim = (overrideText ?? text).trim();
    if (!brandId) return;
    setBusy(true);
    setError(null);
    setRes(null);
    setShowRecorded(null);

    try {
      const out = await runDemo({
        brand_id: brandId,
        language,
        mode,
        text: claim || undefined,
      });
      setRes(out);
      if (out.steps && out.steps.length > 0) {
        revealSteps(out.steps.length);
      }
    } catch (e: any) {
      setError(e.message || "Failed to run compliance demo");
    } finally {
      setBusy(false);
    }
  }

  const verdict = res?.result?.risk_level ? VERDICT[res.result.risk_level] : null;
  const isNonLatin = (res?.language ?? language) === "zh-Hans";

  return (
    <main style={{ padding: "2.5rem 1.5rem 4rem", maxWidth: 900, margin: "0 auto" }}>
      {/* Header */}
      <div
        style={{
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: 12,
          padding: "20px 24px",
          marginBottom: 20,
          boxShadow: "0 1px 4px rgba(0, 43, 73, 0.04)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, flexWrap: "wrap" }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 24, fontWeight: 800, color: "#002b49", letterSpacing: -0.5 }}>
              4-Step Compliance Sandbox
            </h1>
            <p style={{ margin: "6px 0 0", color: "#64748b", fontSize: 14, maxWidth: 580 }}>
              Test any insurance claim live against MAS advertising rules, brand policy constraints, and cultural translations.
            </p>
          </div>
          {quota && (
            <div
              style={{
                textAlign: "right",
                fontSize: 12,
                color: quota.live_available ? "#047857" : "#b91c1c",
                background: quota.live_available ? "#ecfdf5" : "#fef2f2",
                padding: "6px 12px",
                borderRadius: 6,
                border: `1px solid ${quota.live_available ? "#a7f3d0" : "#fecaca"}`,
              }}
            >
              <div style={{ fontWeight: 700 }}>
                {quota.live_available ? "● LIVE ACTIVE" : "● DEMO PAUSED"}
              </div>
              <div style={{ color: "#475569", marginTop: 2 }}>~{quota.estimated_runs_remaining} runs left today</div>
            </div>
          )}
        </div>
      </div>

      {/* Controls */}
      <div
        style={{
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: 12,
          padding: 20,
          boxShadow: "0 1px 4px rgba(0, 43, 73, 0.04)",
          marginBottom: 20,
        }}
      >
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 14 }}>
          <select
            value={brandId}
            onChange={(e) => setBrandId(e.target.value)}
            style={{ padding: "8px 12px", borderRadius: 6, background: "#ffffff", color: "#0f172a", border: "1px solid #cbd5e1", fontWeight: 600, fontSize: 14 }}
          >
            {brands.map((b) => (
              <option key={b.brand_id} value={b.brand_id}>
                {b.name}
              </option>
            ))}
          </select>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            style={{ padding: "8px 12px", borderRadius: 6, background: "#ffffff", color: "#0f172a", border: "1px solid #cbd5e1", fontFamily: CJK_STACK, fontSize: 14 }}
          >
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value as any)}
            style={{ padding: "8px 12px", borderRadius: 6, background: "#ffffff", color: "#0f172a", border: "1px solid #cbd5e1", fontSize: 14 }}
          >
            <option value="generate">Generate copy, then check it</option>
            <option value="check_only">Check my text exactly as written</option>
          </select>
        </div>

        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={
            mode === "check_only"
              ? "Paste insurance marketing copy to check compliance..."
              : "e.g. Jade covers bespoke jewellery stock while in exhibition transit"
          }
          rows={3}
          maxLength={300}
          style={{
            width: "100%",
            padding: 12,
            borderRadius: 8,
            background: "#f8fafc",
            color: "#0f172a",
            border: "1px solid #cbd5e1",
            fontSize: 14,
            fontFamily: "inherit",
            resize: "vertical",
            outline: "none",
          }}
        />
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 10 }}>
          <button
            onClick={() => submit()}
            disabled={busy || !brandId}
            style={{
              padding: "9px 20px",
              borderRadius: 6,
              border: "none",
              background: busy ? "#94a3b8" : "#0066cc",
              color: "white",
              fontWeight: 700,
              fontSize: 14,
              cursor: busy ? "wait" : "pointer",
            }}
          >
            {busy ? "Running 4-Step Safety Gate..." : "▶ Run Compliance Check"}
          </button>
          <span style={{ color: "#94a3b8", fontSize: 12 }}>{text.length}/300</span>
        </div>

        {/* Suggestion chips */}
        <div style={{ marginTop: 16, paddingTop: 14, borderTop: "1px solid #f1f5f9" }}>
          <div style={{ color: "#64748b", fontSize: 12, fontWeight: 600, marginBottom: 8 }}>
            Quick Test Examples:
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {suggestions.map((s) => (
              <button
                key={s.label}
                title={s.expectation}
                onClick={() => {
                  setText(s.text);
                  submit(s.text);
                }}
                disabled={busy}
                style={{
                  padding: "5px 12px",
                  borderRadius: 999,
                  border: "1px solid #cbd5e1",
                  background: "#ffffff",
                  color: "#334155",
                  fontSize: 13,
                  cursor: busy ? "wait" : "pointer",
                  fontWeight: 500,
                }}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div style={{ background: "#fef2f2", color: "#b91c1c", border: "1px solid #fecaca", padding: 14, borderRadius: 8, marginBottom: 20 }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Live result */}
      {res && res.mode === "live" && res.steps && (
        <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 12, padding: 22, boxShadow: "0 1px 4px rgba(0, 43, 73, 0.04)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
            <h2 style={{ fontSize: 17, margin: 0, fontWeight: 700, color: "#002b49" }}>Verification Steps</h2>
            <span style={{ fontSize: 12, color: "#16a34a", background: "#f0fdf4", border: "1px solid #bbf7d0", padding: "2px 8px", borderRadius: 4, fontWeight: 700 }}>
              ● LIVE RUN
            </span>
          </div>

          <div>
            {res.steps.map((s, i) => (
              <StepRow key={s.key + i} step={s} revealed={i < revealed} />
            ))}
          </div>

          {revealed >= (res.steps?.length ?? 0) && res.result && (
            <div style={{ marginTop: 20, paddingTop: 18, borderTop: "1px solid #e2e8f0" }}>
              {verdict && (
                <div
                  style={{
                    border: `1px solid ${verdict.border}`,
                    background: verdict.bg,
                    color: verdict.fg,
                    borderRadius: 8,
                    padding: "12px 16px",
                    fontWeight: 700,
                    fontSize: 14,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: 12,
                    flexWrap: "wrap",
                    marginBottom: 16,
                  }}
                >
                  <span>{verdict.label}</span>
                  {res.result.policy_refs.length > 0 && (
                    <span style={{ fontWeight: 600, fontSize: 12 }}>
                      Cited Rules: {res.result.policy_refs.join(", ")}
                    </span>
                  )}
                </div>
              )}

              <h3 style={{ fontSize: 14, fontWeight: 700, color: "#002b49", margin: "16px 0 6px" }}>
                Generated Output:
              </h3>
              <div
                lang={res.language ?? "en"}
                style={{
                  whiteSpace: "pre-wrap",
                  background: "#f8fafc",
                  border: "1px solid #e2e8f0",
                  borderRadius: 8,
                  padding: 14,
                  fontSize: 14,
                  color: "#0f172a",
                  lineHeight: isNonLatin ? 1.85 : 1.6,
                  fontFamily: CJK_STACK,
                }}
              >
                {res.result.body}
              </div>

              {res.result.suggested_revision && (
                <div style={{ marginTop: 14 }}>
                  <h4 style={{ fontSize: 13, fontWeight: 700, color: "#b45309", margin: "0 0 4px" }}>
                    Suggested Compliant Revision:
                  </h4>
                  <div
                    lang={res.language ?? "en"}
                    style={{
                      whiteSpace: "pre-wrap",
                      background: "#fffbeb",
                      border: "1px solid #fde68a",
                      borderRadius: 8,
                      padding: 12,
                      color: "#92400e",
                      fontSize: 13,
                      lineHeight: isNonLatin ? 1.85 : 1.5,
                      fontFamily: CJK_STACK,
                    }}
                  >
                    {res.result.suggested_revision}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </main>
  );
}
