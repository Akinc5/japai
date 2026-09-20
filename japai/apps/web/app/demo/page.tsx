"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  API_BASE_URL,
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

const STATUS_STYLE: Record<string, { dot: string; fg: string }> = {
  pass: { dot: "#22c55e", fg: "#bbf7d0" },
  warn: { dot: "#f59e0b", fg: "#fde68a" },
  fail: { dot: "#ef4444", fg: "#fecaca" },
  skipped: { dot: "#52525b", fg: "#a1a1aa" },
  error: { dot: "#ef4444", fg: "#fecaca" },
  pending: { dot: "#3f3f46", fg: "#71717a" },
};

const VERDICT: Record<string, { bg: string; fg: string; border: string; label: string }> = {
  pass: { bg: "#052e16", fg: "#bbf7d0", border: "#166534", label: "PASS" },
  review: { bg: "#2d1b06", fg: "#fde68a", border: "#a16207", label: "NEEDS HUMAN REVIEW" },
  block: { bg: "#2a0a0a", fg: "#fecaca", border: "#b91c1c", label: "BLOCKED" },
};

function StepRow({ step, revealed }: { step: DemoStep; revealed: boolean }) {
  const s = STATUS_STYLE[revealed ? step.status : "pending"] ?? STATUS_STYLE.pending;
  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        padding: "10px 0",
        borderTop: "1px solid #27272a",
        opacity: revealed ? 1 : 0.35,
        transition: "opacity 220ms ease",
      }}
    >
      <span
        style={{
          width: 10,
          height: 10,
          borderRadius: 999,
          background: s.dot,
          marginTop: 6,
          flexShrink: 0,
          boxShadow: revealed && step.status === "fail" ? `0 0 0 4px ${s.dot}22` : undefined,
        }}
      />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 600, color: revealed ? "#e4e4e7" : "#71717a" }}>
          {step.label}
        </div>
        {revealed && (
          <>
            <div style={{ color: "#a1a1aa", fontSize: 13, marginTop: 2 }}>{step.detail}</div>
            {step.terms && step.terms.length > 0 && (
              <div style={{ marginTop: 6, display: "flex", gap: 6, flexWrap: "wrap" }}>
                {step.terms.map((t) => (
                  <code
                    key={t}
                    style={{
                      background: "#450a0a",
                      color: "#fecaca",
                      padding: "1px 7px",
                      borderRadius: 4,
                      fontSize: 12,
                    }}
                  >
                    {t}
                  </code>
                ))}
              </div>
            )}
            {step.issues && step.issues.length > 0 && (
              <ul style={{ margin: "6px 0 0", paddingLeft: 18, color: "#d4d4d8", fontSize: 13 }}>
                {step.issues.slice(0, 4).map((iss, i) => (
                  <li key={i} style={{ marginBottom: 3 }}>
                    <span style={{ color: "#e4e4e7" }}>“{iss.term.slice(0, 110)}”</span>
                    <br />
                    <span style={{ color: "#a1a1aa" }}>
                      {iss.reason}
                      {iss.policy_ref && (
                        <>
                          {" "}
                          <code style={{ color: "#fca5a5" }}>[{iss.policy_ref}]</code>
                        </>
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
    fetch(`${API_BASE_URL}/brands`)
      .then((r) => r.json())
      .then((bs) => {
        setBrands(bs);
        const jade = bs.find((b: any) => b.slug === "jade") ?? bs[0];
        if (jade) setBrandId(jade.brand_id);
      })
      .catch((e) => setError(e.message));
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
    setRevealed(0);
    try {
      const out = await runDemo({
        brand_id: brandId,
        language,
        claim_or_topic: claim,
        mode,
      });
      setRes(out);
      if (out.steps) revealSteps(out.steps.length);
      if (out.quota) setQuota(out.quota);
      else fetchQuotaStatus().then(setQuota).catch(() => {});
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const verdict = res?.result?.risk_level ? VERDICT[res.result.risk_level] : null;
  const isNonLatin = (res?.language ?? language) === "zh-Hans";

  return (
    <main style={{ padding: "2rem 1.5rem 4rem", maxWidth: 880, margin: "0 auto" }}>
      {/* Header */}
      <div
        style={{
          background: "linear-gradient(135deg, #1e1b4b 0%, #0c1844 50%, #041f3d 100%)",
          border: "1px solid #312e81",
          borderRadius: 14,
          padding: "22px 26px",
          marginBottom: 22,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, flexWrap: "wrap" }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 28, letterSpacing: -0.5 }}>Try it yourself</h1>
            <p style={{ margin: "6px 0 0", color: "#a5b4fc", maxWidth: 560 }}>
              Type a marketing claim. Watch it go through real generation and the real
              4-step compliance pipeline — the same code path as the internal{" "}
              <Link href="/review" style={{ color: "#c7d2fe" }}>
                review queue
              </Link>
              . Nothing here is scripted.
            </p>
          </div>
          {quota && (
            <div
              style={{
                textAlign: "right",
                fontSize: 12,
                color: quota.live_available ? "#a5b4fc" : "#fca5a5",
                whiteSpace: "nowrap",
              }}
            >
              <div style={{ fontWeight: 700, fontSize: 13 }}>
                {quota.live_available ? "● LIVE" : "● LIVE PAUSED"}
              </div>
              <div>~{quota.estimated_runs_remaining} runs left today</div>
              <div style={{ opacity: 0.7 }}>
                {quota.calls_used_today}/{quota.threshold} calls
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 14 }}>
        <select
          value={brandId}
          onChange={(e) => setBrandId(e.target.value)}
          style={{ padding: "8px 10px", borderRadius: 8, background: "#18181b", color: "#e4e4e7", border: "1px solid #3f3f46" }}
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
          style={{ padding: "8px 10px", borderRadius: 8, background: "#18181b", color: "#e4e4e7", border: "1px solid #3f3f46", fontFamily: CJK_STACK }}
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
          style={{ padding: "8px 10px", borderRadius: 8, background: "#18181b", color: "#e4e4e7", border: "1px solid #3f3f46" }}
          title="Generate new copy about your topic, or compliance-check your words exactly as written"
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
            ? "Paste marketing copy to be compliance-checked as-is…"
            : "e.g. our policy covers jewellery stock while it is in transit"
        }
        rows={3}
        maxLength={300}
        style={{
          width: "100%",
          padding: 12,
          borderRadius: 10,
          background: "#09090b",
          color: "#e4e4e7",
          border: "1px solid #3f3f46",
          fontSize: 15,
          fontFamily: "inherit",
          resize: "vertical",
        }}
      />
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8, gap: 12, flexWrap: "wrap" }}>
        <button
          onClick={() => submit()}
          disabled={busy || !brandId}
          style={{
            padding: "10px 20px",
            borderRadius: 10,
            border: "none",
            background: busy ? "#3730a3" : "#4f46e5",
            color: "white",
            fontWeight: 700,
            fontSize: 15,
            cursor: busy ? "wait" : "pointer",
          }}
        >
          {busy ? "Running the real pipeline…" : "Run it"}
        </button>
        <span style={{ color: "#71717a", fontSize: 12 }}>{text.length}/300</span>
      </div>

      {/* Suggestion chips */}
      <div style={{ marginTop: 16 }}>
        <div style={{ color: "#71717a", fontSize: 12, marginBottom: 6 }}>
          Or try one of these — two should sail through, two should get caught:
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
                padding: "6px 12px",
                borderRadius: 999,
                border: "1px solid #3f3f46",
                background: "#18181b",
                color: "#d4d4d8",
                fontSize: 13,
                cursor: busy ? "wait" : "pointer",
              }}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {error && <p style={{ color: "#fca5a5", marginTop: 18 }}>Error: {error}</p>}

      {/* Guard / rate-limit responses */}
      {res && (res.mode === "rejected" || res.mode === "rate_limited") && (
        <div
          style={{
            marginTop: 20,
            border: "1px solid #a16207",
            background: "#1c1301",
            borderRadius: 10,
            padding: "14px 18px",
            color: "#fde68a",
          }}
        >
          {res.message}
        </div>
      )}

      {/* Quota fallback */}
      {res && res.mode === "recorded" && (
        <div style={{ marginTop: 20 }}>
          <div
            style={{
              border: "1px solid #a16207",
              background: "#1c1301",
              borderRadius: 10,
              padding: "14px 18px",
              color: "#fde68a",
              marginBottom: 14,
            }}
          >
            <strong>Live demo temporarily paused</strong> — the daily model budget is nearly
            spent, so this is a <strong>real recorded run</strong> from earlier, replayed
            verbatim. It is not a live result and not a mock.
          </div>
          {res.example && <RecordedExample example={res.example} />}
        </div>
      )}

      {/* Live result */}
      {res && res.mode === "live" && res.steps && (
        <div style={{ marginTop: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
            <h2 style={{ fontSize: 17, margin: 0 }}>Pipeline</h2>
            <span style={{ fontSize: 12, color: "#22c55e", fontWeight: 700 }}>● LIVE RESULT</span>
          </div>
          <div style={{ color: "#71717a", fontSize: 12, marginBottom: 4 }}>
            Compliance ran on {res.compliance_ran_on}.
          </div>
          <div>
            {res.steps.map((s, i) => (
              <StepRow key={s.key + i} step={s} revealed={i < revealed} />
            ))}
          </div>

          {revealed >= (res.steps?.length ?? 0) && res.result && (
            <>
              {verdict && (
                <div
                  style={{
                    marginTop: 20,
                    border: `1px solid ${verdict.border}`,
                    background: verdict.bg,
                    color: verdict.fg,
                    borderRadius: 12,
                    padding: "14px 18px",
                    fontWeight: 700,
                    letterSpacing: 0.5,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: 12,
                    flexWrap: "wrap",
                  }}
                >
                  <span>{verdict.label}</span>
                  {res.result.policy_refs.length > 0 && (
                    <span style={{ fontWeight: 500, fontSize: 13 }}>
                      cited: {res.result.policy_refs.join(", ")}
                    </span>
                  )}
                </div>
              )}

              {res.english_source && (
                <details style={{ marginTop: 14 }}>
                  <summary style={{ cursor: "pointer", color: "#a1a1aa", fontSize: 13 }}>
                    Show the English source it was adapted from
                  </summary>
                  <div
                    style={{
                      whiteSpace: "pre-wrap",
                      background: "#09090b",
                      border: "1px solid #27272a",
                      borderRadius: 10,
                      padding: 14,
                      marginTop: 8,
                      color: "#a1a1aa",
                      fontSize: 14,
                    }}
                  >
                    {res.english_source}
                  </div>
                </details>
              )}

              <h3 style={{ fontSize: 15, marginTop: 20, marginBottom: 6 }}>
                Generated copy{res.language_name ? ` · ${res.language_name}` : ""}
              </h3>
              <div
                lang={res.language ?? "en"}
                style={{
                  whiteSpace: "pre-wrap",
                  background: "#09090b",
                  border: "1px solid #27272a",
                  borderRadius: 10,
                  padding: 16,
                  lineHeight: isNonLatin ? 1.85 : 1.65,
                  fontFamily: CJK_STACK,
                }}
              >
                {res.result.body}
              </div>

              {res.result.suggested_revision && (
                <>
                  <h3 style={{ fontSize: 15, marginTop: 18, marginBottom: 6 }}>
                    Suggested revision
                  </h3>
                  <div
                    lang={res.language ?? "en"}
                    style={{
                      whiteSpace: "pre-wrap",
                      background: "#1c1301",
                      border: "1px solid #a16207",
                      borderRadius: 10,
                      padding: 16,
                      color: "#fde68a",
                      lineHeight: isNonLatin ? 1.85 : 1.65,
                      fontFamily: CJK_STACK,
                    }}
                  >
                    {res.result.suggested_revision}
                  </div>
                </>
              )}

              <button
                onClick={() => {
                  setText("");
                  setRes(null);
                }}
                style={{
                  marginTop: 20,
                  padding: "8px 16px",
                  borderRadius: 8,
                  border: "1px solid #3f3f46",
                  background: "#18181b",
                  color: "#d4d4d8",
                  cursor: "pointer",
                }}
              >
                Try another one →
              </button>
            </>
          )}
        </div>
      )}

      {/* Recorded example browser */}
      {recorded && recorded.length > 0 && (
        <div style={{ marginTop: 40, borderTop: "1px solid #27272a", paddingTop: 20 }}>
          <h2 style={{ fontSize: 16, marginBottom: 4 }}>Recorded examples</h2>
          <p style={{ color: "#71717a", fontSize: 13, marginTop: 0 }}>
            Real runs captured earlier and saved verbatim — useful if you'd rather not wait
            for a live generation. Clearly labelled as replays, not live results.
          </p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {recorded.map((e) => (
              <button
                key={e.id}
                onClick={() => {
                  setShowRecorded(e);
                  setRes(null);
                }}
                style={{
                  padding: "6px 12px",
                  borderRadius: 999,
                  border: "1px solid #3f3f46",
                  background: showRecorded?.id === e.id ? "#27272a" : "#18181b",
                  color: "#d4d4d8",
                  fontSize: 13,
                  cursor: "pointer",
                }}
              >
                {e.title}
              </button>
            ))}
          </div>
          {showRecorded && (
            <div style={{ marginTop: 16 }}>
              <RecordedExample example={showRecorded} />
            </div>
          )}
        </div>
      )}
    </main>
  );
}

function RecordedExample({ example }: { example: any }) {
  const verdict = example?.result?.risk_level ? VERDICT[example.result.risk_level] : null;
  const isNonLatin = example?.language === "zh-Hans";

  return (
    <div style={{ border: "1px solid #3f3f46", borderRadius: 12, padding: 18, background: "#101012" }}>
      <div
        style={{
          display: "inline-block",
          background: "#3f3f46",
          color: "#e4e4e7",
          borderRadius: 4,
          padding: "2px 9px",
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: 0.6,
          marginBottom: 10,
        }}
      >
        ▶ RECORDED — NOT LIVE
      </div>
      <h3 style={{ margin: "0 0 4px", fontSize: 16 }}>{example.title}</h3>
      <p style={{ color: "#a1a1aa", fontSize: 13, marginTop: 0 }}>{example.description}</p>
      {example.recorded_at && (
        <div style={{ color: "#52525b", fontSize: 11, marginBottom: 10 }}>
          captured {new Date(example.recorded_at).toLocaleString()} · {example.recorded_by}
        </div>
      )}

      {example.kind === "opportunity" && example.opportunity && (
        <div>
          <strong>{example.opportunity.title}</strong>
          <div style={{ color: "#a1a1aa", fontSize: 13, margin: "6px 0" }}>
            {example.opportunity.rationale}
          </div>
          <div style={{ fontSize: 22, fontWeight: 700 }}>{example.opportunity.score}</div>
          {example.opportunity.score_breakdown?.formula && (
            <code style={{ color: "#71717a", fontSize: 12 }}>
              {example.opportunity.score_breakdown.formula}
            </code>
          )}
        </div>
      )}

      {example.kind === "demo_run" && (
        <>
          {example.claim_or_topic && (
            <div style={{ color: "#a1a1aa", fontSize: 13, marginBottom: 10 }}>
              Input: “{example.claim_or_topic}”
            </div>
          )}
          {(example.steps ?? []).map((s: DemoStep, i: number) => (
            <StepRow key={s.key + i} step={s} revealed />
          ))}
          {verdict && (
            <div
              style={{
                marginTop: 14,
                border: `1px solid ${verdict.border}`,
                background: verdict.bg,
                color: verdict.fg,
                borderRadius: 10,
                padding: "10px 14px",
                fontWeight: 700,
              }}
            >
              {verdict.label}
              {example.result.policy_refs?.length > 0 && (
                <span style={{ fontWeight: 500, fontSize: 13 }}>
                  {" "}
                  · cited: {example.result.policy_refs.join(", ")}
                </span>
              )}
            </div>
          )}
          {example.result?.body && (
            <div
              lang={example.language ?? "en"}
              style={{
                whiteSpace: "pre-wrap",
                background: "#09090b",
                border: "1px solid #27272a",
                borderRadius: 10,
                padding: 14,
                marginTop: 12,
                lineHeight: isNonLatin ? 1.85 : 1.65,
                fontFamily: CJK_STACK,
                fontSize: 14,
              }}
            >
              {example.result.body}
            </div>
          )}
        </>
      )}
    </div>
  );
}
