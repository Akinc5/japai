const COLORS: Record<string, { bg: string; fg: string }> = {
  pass: { bg: "#dcfce7", fg: "#166534" },
  review: { bg: "#fef9c3", fg: "#854d0e" },
  block: { bg: "#fee2e2", fg: "#991b1b" },
};

export default function RiskBadge({ riskLevel }: { riskLevel: string | null }) {
  const key = riskLevel || "review";
  const colors = COLORS[key] || COLORS.review;
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: 999,
        fontSize: 12,
        fontWeight: 600,
        textTransform: "uppercase",
        letterSpacing: 0.4,
        background: colors.bg,
        color: colors.fg,
      }}
    >
      {key}
    </span>
  );
}
