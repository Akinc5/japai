const LANGUAGE_LABELS: Record<string, { label: string; endonym: string }> = {
  en: { label: "EN", endonym: "English" },
  "zh-Hans": { label: "中文", endonym: "简体中文" },
  ms: { label: "MS", endonym: "Bahasa Melayu" },
  id: { label: "ID", endonym: "Bahasa Indonesia" },
};

export default function LanguageBadge({
  language,
  isLocalized,
}: {
  language: string | null;
  isLocalized?: boolean;
}) {
  const code = language ?? "en";
  const spec = LANGUAGE_LABELS[code] ?? { label: code.toUpperCase(), endonym: code };

  // English originals are the baseline; only localized variants get the accent
  // colour, so a reviewer can pick non-English items out of the queue at a glance.
  const isEnglish = code === "en";

  return (
    <span
      title={spec.endonym}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        background: isEnglish ? "#f1f5f9" : "#eff6ff",
        color: isEnglish ? "#334155" : "#0066cc",
        border: isEnglish ? "1px solid #cbd5e1" : "1px solid #bfdbfe",
        borderRadius: 4,
        padding: "1px 7px",
        fontSize: 12,
        fontWeight: 600,
        whiteSpace: "nowrap",
      }}
    >
      {spec.label}
      {isLocalized && <span style={{ opacity: 0.85, fontWeight: 400 }}>localized</span>}
    </span>
  );
}
