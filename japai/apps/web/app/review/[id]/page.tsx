"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { fetchReviewDetail, submitDecision, ReviewDetail } from "@/lib/api";
import RiskBadge from "@/components/RiskBadge";
import LanguageBadge from "@/components/LanguageBadge";

const REASON_TAGS = [
  "too_salesy",
  "unsupported_claim",
  "wrong_tone",
  "generic",
  "wrong_cta",
  "other",
] as const;

type Mode = "view" | "edit" | "reject";

export default function ReviewDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();

  const [detail, setDetail] = useState<ReviewDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>("view");
  const [editedBody, setEditedBody] = useState("");
  const [reasonTag, setReasonTag] = useState<string>(REASON_TAGS[0]);
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [resultMessage, setResultMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchReviewDetail(params.id)
      .then((d) => {
        setDetail(d);
        setEditedBody(d.body);
      })
      .catch((e) => setError(e.message));
  }, [params.id]);

  async function handleApprove() {
    setSubmitting(true);
    setError(null);
    try {
      await submitDecision(params.id, { action: "approve", note: note || undefined });
      setResultMessage("Approved.");
      router.push("/review");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleReject() {
    if (!reasonTag || !note.trim()) {
      setError("Reject requires a reason and a note.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await submitDecision(params.id, { action: "reject", reason_tag: reasonTag, note });
      setResultMessage("Rejected.");
      router.push("/review");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSaveEdit() {
    if (!editedBody.trim()) {
      setError("Edited body cannot be empty.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await submitDecision(params.id, {
        action: "edit",
        edited_body: editedBody,
        reason_tag: reasonTag || undefined,
        note: note || undefined,
      });
      setResultMessage("Edited and approved.");
      router.push("/review");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (error && !detail) {
    return (
      <main style={{ padding: "2.5rem 1.5rem", maxWidth: 900, margin: "0 auto" }}>
        <div style={{ color: "#b91c1c", background: "#fef2f2", padding: "14px", borderRadius: 8, border: "1px solid #fecaca" }}>
          Error: {error}
        </div>
      </main>
    );
  }

  if (!detail) {
    return (
      <main style={{ padding: "2.5rem 1.5rem", maxWidth: 900, margin: "0 auto", color: "#64748b" }}>
        Loading review detail…
      </main>
    );
  }

  const issues = detail.compliance?.detected_issues || [];

  return (
    <main style={{ padding: "2.5rem 1.5rem 4rem", maxWidth: 900, margin: "0 auto" }}>
      <header style={{ marginBottom: "1.5rem" }}>
        <Link href="/review" style={{ color: "#0066cc", fontSize: 13, textDecoration: "none", fontWeight: 600 }}>
          ← Back to review queue
        </Link>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8, flexWrap: "wrap", gap: 8 }}>
          <h1 style={{ margin: 0, fontSize: "1.6rem", fontWeight: 800, color: "#002b49" }}>
            {detail.brand_name || "Unknown brand"} · {detail.platform || "—"}
          </h1>
          <span style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
            <LanguageBadge language={detail.language} isLocalized={detail.is_localized} />
            <RiskBadge riskLevel={detail.compliance?.risk_level ?? null} />
          </span>
        </div>
        <p style={{ color: "#64748b", margin: "4px 0 0", fontSize: 13 }}>
          Status: <strong style={{ color: "#002b49" }}>{detail.status}</strong>
          {detail.topic && <> · Topic: {detail.topic}</>}
        </p>
      </header>

      {error && (
        <div style={{ color: "#b91c1c", background: "#fef2f2", padding: "10px 14px", borderRadius: 6, border: "1px solid #fecaca", marginBottom: 14 }}>
          {error}
        </div>
      )}
      {resultMessage && (
        <div style={{ color: "#047857", background: "#ecfdf5", padding: "10px 14px", borderRadius: 6, border: "1px solid #a7f3d0", marginBottom: 14 }}>
          {resultMessage}
        </div>
      )}

      {/* Body card */}
      <section style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 10, padding: "18px 20px", marginBottom: 20, boxShadow: "0 1px 3px rgba(0, 43, 73, 0.04)" }}>
        <h3 style={{ margin: "0 0 10px", fontSize: "1rem", fontWeight: 700, color: "#002b49" }}>Content Body</h3>
        {mode === "edit" ? (
          <textarea
            value={editedBody}
            onChange={(e) => setEditedBody(e.target.value)}
            rows={10}
            style={{
              width: "100%",
              padding: 12,
              fontFamily: "inherit",
              fontSize: 14,
              border: "1px solid #cbd5e1",
              borderRadius: 6,
              background: "#f8fafc",
              color: "#0f172a",
              outline: "none",
            }}
          />
        ) : (
          <div
            lang={detail.language ?? "en"}
            style={{
              whiteSpace: "pre-wrap",
              border: "1px solid #e2e8f0",
              borderRadius: 8,
              padding: 16,
              background: "#f8fafc",
              color: "#0f172a",
              lineHeight: 1.7,
              fontSize: 14,
              fontFamily:
                '-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
            }}
          >
            {detail.body}
          </div>
        )}
      </section>

      {/* Suggested revision */}
      {detail.suggested_revision && (
        <section style={{ background: "#ffffff", border: "1px solid #fde68a", borderRadius: 10, padding: "18px 20px", marginBottom: 20, boxShadow: "0 1px 3px rgba(0, 43, 73, 0.04)" }}>
          <h3 style={{ margin: "0 0 10px", fontSize: "1rem", fontWeight: 700, color: "#b45309" }}>Suggested Compliant Revision</h3>
          <div
            style={{
              whiteSpace: "pre-wrap",
              border: "1px solid #fef08a",
              borderRadius: 8,
              padding: 16,
              background: "#fefce8",
              color: "#854d0e",
              fontSize: 14,
              lineHeight: 1.6,
            }}
          >
            {detail.suggested_revision}
          </div>
        </section>
      )}

      {/* Compliance findings */}
      <section style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 10, padding: "18px 20px", marginBottom: 20, boxShadow: "0 1px 3px rgba(0, 43, 73, 0.04)" }}>
        <h3 style={{ margin: "0 0 10px", fontSize: "1rem", fontWeight: 700, color: "#002b49" }}>Compliance Findings</h3>
        {detail.compliance ? (
          <>
            <p style={{ color: "#64748b", fontSize: 13, marginBottom: 10 }}>
              Outcome: <strong style={{ color: "#002b49" }}>{detail.compliance.outcome}</strong> · Reviewer:{" "}
              {detail.compliance.reviewer_type} · {detail.compliance.notes}
            </p>
            {issues.length === 0 ? (
              <p style={{ color: "#047857", fontSize: 13, margin: 0 }}>✓ No compliance issues detected.</p>
            ) : (
              <ul style={{ paddingLeft: 20, margin: 0, color: "#334155", fontSize: 13 }}>
                {issues.map((issue, i) => (
                  <li key={i} style={{ marginBottom: 6 }}>
                    <strong style={{ color: "#b91c1c" }}>{issue.term}</strong> — {issue.reason}
                    {issue.policy_ref && (
                      <span style={{ color: "#64748b" }}> (rule: {issue.policy_ref})</span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </>
        ) : (
          <p style={{ color: "#64748b", margin: 0, fontSize: 13 }}>No compliance review on file.</p>
        )}
      </section>

      {/* Provenance */}
      <section style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 10, padding: "18px 20px", marginBottom: 20, boxShadow: "0 1px 3px rgba(0, 43, 73, 0.04)" }}>
        <h3 style={{ margin: "0 0 10px", fontSize: "1rem", fontWeight: 700, color: "#002b49" }}>Provenance &amp; Grounding Chunks</h3>
        {(!detail.sources || detail.sources.length === 0) ? (
          <p style={{ color: "#64748b", margin: 0, fontSize: 13 }}>No source chunks recorded.</p>
        ) : (
          <ul style={{ paddingLeft: 20, margin: 0, color: "#334155", fontSize: 13 }}>
            {detail.sources.map((s, i) => (
              <li key={i} style={{ marginBottom: 6 }}>
                <em style={{ color: "#0066cc" }}>[{s.category}]</em> {s.title && <strong>{s.title}: </strong>}
                {s.content || "(chunk content unavailable)"}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Decision actions */}
      <section style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 10, padding: "18px 20px", boxShadow: "0 1px 3px rgba(0, 43, 73, 0.04)" }}>
        <h3 style={{ margin: "0 0 12px", fontSize: "1rem", fontWeight: 700, color: "#002b49" }}>Review Decision</h3>

        {mode === "reject" && (
          <div style={{ marginBottom: 14 }}>
            <label style={{ display: "block", marginBottom: 4, fontSize: 13, fontWeight: 700, color: "#002b49" }}>Reason</label>
            <select
              value={reasonTag}
              onChange={(e) => setReasonTag(e.target.value)}
              style={{ marginBottom: 10, padding: "6px 10px", borderRadius: 6, border: "1px solid #cbd5e1", background: "#ffffff" }}
            >
              {REASON_TAGS.map((tag) => (
                <option key={tag} value={tag}>
                  {tag}
                </option>
              ))}
            </select>
            <label style={{ display: "block", marginBottom: 4, fontSize: 13, fontWeight: 700, color: "#002b49" }}>Note (required)</label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              style={{ width: "100%", padding: 10, borderRadius: 6, border: "1px solid #cbd5e1", background: "#f8fafc" }}
            />
          </div>
        )}

        {mode === "edit" && (
          <div style={{ marginBottom: 14 }}>
            <label style={{ display: "block", marginBottom: 4, fontSize: 13, fontWeight: 700, color: "#002b49" }}>Reason (optional)</label>
            <select
              value={reasonTag}
              onChange={(e) => setReasonTag(e.target.value)}
              style={{ marginBottom: 10, padding: "6px 10px", borderRadius: 6, border: "1px solid #cbd5e1", background: "#ffffff" }}
            >
              {REASON_TAGS.map((tag) => (
                <option key={tag} value={tag}>
                  {tag}
                </option>
              ))}
            </select>
            <label style={{ display: "block", marginBottom: 4, fontSize: 13, fontWeight: 700, color: "#002b49" }}>Note (optional)</label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              style={{ width: "100%", padding: 10, borderRadius: 6, border: "1px solid #cbd5e1", background: "#f8fafc" }}
            />
          </div>
        )}

        <div style={{ display: "flex", gap: 10 }}>
          {mode === "view" && (
            <>
              <button
                disabled={submitting}
                onClick={handleApprove}
                style={{
                  padding: "8px 18px",
                  borderRadius: 6,
                  background: "#16a34a",
                  color: "white",
                  border: "none",
                  fontWeight: 700,
                  fontSize: 13,
                  cursor: submitting ? "not-allowed" : "pointer",
                }}
              >
                ✓ Approve &amp; Release
              </button>
              <button
                disabled={submitting}
                onClick={() => setMode("edit")}
                style={{
                  padding: "8px 18px",
                  borderRadius: 6,
                  background: "#0066cc",
                  color: "white",
                  border: "none",
                  fontWeight: 700,
                  fontSize: 13,
                  cursor: submitting ? "not-allowed" : "pointer",
                }}
              >
                ✏️ Edit &amp; Approve
              </button>
              <button
                disabled={submitting}
                onClick={() => setMode("reject")}
                style={{
                  padding: "8px 18px",
                  borderRadius: 6,
                  background: "#dc2626",
                  color: "white",
                  border: "none",
                  fontWeight: 700,
                  fontSize: 13,
                  cursor: submitting ? "not-allowed" : "pointer",
                }}
              >
                ✗ Reject
              </button>
            </>
          )}
          {mode === "edit" && (
            <>
              <button
                disabled={submitting}
                onClick={handleSaveEdit}
                style={{
                  padding: "8px 18px",
                  borderRadius: 6,
                  background: "#0066cc",
                  color: "white",
                  border: "none",
                  fontWeight: 700,
                  fontSize: 13,
                  cursor: submitting ? "not-allowed" : "pointer",
                }}
              >
                Save Edit &amp; Approve
              </button>
              <button
                disabled={submitting}
                onClick={() => setMode("view")}
                style={{
                  padding: "8px 16px",
                  borderRadius: 6,
                  background: "#f1f5f9",
                  color: "#334155",
                  border: "1px solid #cbd5e1",
                  fontWeight: 600,
                  fontSize: 13,
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
            </>
          )}
          {mode === "reject" && (
            <>
              <button
                disabled={submitting}
                onClick={handleReject}
                style={{
                  padding: "8px 18px",
                  borderRadius: 6,
                  background: "#dc2626",
                  color: "white",
                  border: "none",
                  fontWeight: 700,
                  fontSize: 13,
                  cursor: submitting ? "not-allowed" : "pointer",
                }}
              >
                Confirm Reject
              </button>
              <button
                disabled={submitting}
                onClick={() => setMode("view")}
                style={{
                  padding: "8px 16px",
                  borderRadius: 6,
                  background: "#f1f5f9",
                  color: "#334155",
                  border: "1px solid #cbd5e1",
                  fontWeight: 600,
                  fontSize: 13,
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
            </>
          )}
        </div>
      </section>
    </main>
  );
}
