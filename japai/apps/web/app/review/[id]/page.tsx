"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
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

  if (error && !detail) return <main style={{ padding: "2rem" }}>Error: {error}</main>;
  if (!detail) return <main style={{ padding: "2rem" }}>Loading…</main>;

  const issues = detail.compliance?.detected_issues || [];

  return (
    <main style={{ padding: "2rem", maxWidth: 900, margin: "0 auto" }}>
      <a href="/review" style={{ color: "#555", fontSize: 14 }}>
        ← Back to queue
      </a>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
        <h1 style={{ margin: 0 }}>
          {detail.brand_name || "Unknown brand"} · {detail.platform || "—"}
        </h1>
        <span style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
          <LanguageBadge language={detail.language} isLocalized={detail.is_localized} />
          <RiskBadge riskLevel={detail.compliance?.risk_level ?? null} />
        </span>
      </div>
      <p style={{ color: "#666" }}>
        Status: <strong>{detail.status}</strong>
        {detail.topic && <> · Topic: {detail.topic}</>}
      </p>

      {error && <p style={{ color: "#991b1b" }}>{error}</p>}
      {resultMessage && <p style={{ color: "#166534" }}>{resultMessage}</p>}

      <section style={{ marginTop: 24 }}>
        <h3>Body</h3>
        {mode === "edit" ? (
          <textarea
            value={editedBody}
            onChange={(e) => setEditedBody(e.target.value)}
            rows={10}
            style={{ width: "100%", padding: 10, fontFamily: "inherit", fontSize: 14 }}
          />
        ) : (
          <div
            lang={detail.language ?? "en"}
            style={{
              whiteSpace: "pre-wrap",
              border: "1px solid #eee",
              borderRadius: 8,
              padding: 16,
              background: "#fafafa",
              color: "#111",
              // CJK needs a font stack that actually carries the glyphs, and a
              // looser line-height than the Latin default to stay readable.
              lineHeight: 1.75,
              fontFamily:
                '-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
            }}
          >
            {detail.body}
          </div>
        )}
      </section>

      {detail.suggested_revision && (
        <section style={{ marginTop: 20 }}>
          <h3>Suggested revision (from compliance review)</h3>
          <div
            style={{
              whiteSpace: "pre-wrap",
              border: "1px solid #fef08a",
              borderRadius: 8,
              padding: 16,
              background: "#fefce8",
              color: "#111",
            }}
          >
            {detail.suggested_revision}
          </div>
        </section>
      )}

      <section style={{ marginTop: 20 }}>
        <h3>Compliance findings</h3>
        {detail.compliance ? (
          <>
            <p style={{ color: "#666" }}>
              Outcome: <strong>{detail.compliance.outcome}</strong> · Reviewer:{" "}
              {detail.compliance.reviewer_type} · {detail.compliance.notes}
            </p>
            {issues.length === 0 ? (
              <p>No issues detected.</p>
            ) : (
              <ul style={{ paddingLeft: 20 }}>
                {issues.map((issue, i) => (
                  <li key={i} style={{ marginBottom: 8 }}>
                    <strong>{issue.term}</strong> — {issue.reason}
                    {issue.policy_ref && (
                      <span style={{ color: "#888" }}> (policy: {issue.policy_ref})</span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </>
        ) : (
          <p>No compliance review on file.</p>
        )}
      </section>

      <section style={{ marginTop: 20 }}>
        <h3>Why was this generated? (provenance)</h3>
        {detail.sources.length === 0 ? (
          <p>No source chunks recorded.</p>
        ) : (
          <ul style={{ paddingLeft: 20 }}>
            {detail.sources.map((s, i) => (
              <li key={i} style={{ marginBottom: 8 }}>
                <em>[{s.category}]</em> {s.title && <strong>{s.title}: </strong>}
                {s.content || "(chunk content unavailable)"}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section style={{ marginTop: 28, borderTop: "1px solid #eee", paddingTop: 20 }}>
        <h3>Decision</h3>

        {mode === "reject" && (
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: "block", marginBottom: 4 }}>Reason</label>
            <select value={reasonTag} onChange={(e) => setReasonTag(e.target.value)} style={{ marginBottom: 8 }}>
              {REASON_TAGS.map((tag) => (
                <option key={tag} value={tag}>
                  {tag}
                </option>
              ))}
            </select>
            <label style={{ display: "block", marginBottom: 4 }}>Note (required)</label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              style={{ width: "100%", padding: 8 }}
            />
          </div>
        )}

        {mode === "edit" && (
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: "block", marginBottom: 4 }}>Reason (optional)</label>
            <select value={reasonTag} onChange={(e) => setReasonTag(e.target.value)} style={{ marginBottom: 8 }}>
              {REASON_TAGS.map((tag) => (
                <option key={tag} value={tag}>
                  {tag}
                </option>
              ))}
            </select>
            <label style={{ display: "block", marginBottom: 4 }}>Note (optional)</label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              style={{ width: "100%", padding: 8 }}
            />
          </div>
        )}

        <div style={{ display: "flex", gap: 10 }}>
          {mode === "view" && (
            <>
              <button disabled={submitting} onClick={handleApprove}>
                Approve
              </button>
              <button disabled={submitting} onClick={() => setMode("edit")}>
                Edit
              </button>
              <button disabled={submitting} onClick={() => setMode("reject")}>
                Reject
              </button>
            </>
          )}
          {mode === "edit" && (
            <>
              <button disabled={submitting} onClick={handleSaveEdit}>
                Save Edit &amp; Approve
              </button>
              <button disabled={submitting} onClick={() => setMode("view")}>
                Cancel
              </button>
            </>
          )}
          {mode === "reject" && (
            <>
              <button disabled={submitting} onClick={handleReject}>
                Confirm Reject
              </button>
              <button disabled={submitting} onClick={() => setMode("view")}>
                Cancel
              </button>
            </>
          )}
        </div>
      </section>
    </main>
  );
}
