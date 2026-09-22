export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" && window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : "https://japai.onrender.com");

export interface BrandSummary {
  brand_id: string;
  slug: string;
  name: string;
}

export const FALLBACK_BRANDS: BrandSummary[] = [
  { brand_id: "jade-default", slug: "jade", name: "Jade (Jewellers Block)" },
  { brand_id: "jaguar-default", slug: "jaguar-transit", name: "Jaguar Transit" },
  { brand_id: "doctorshield-default", slug: "doctorshield", name: "DoctorShield" },
];

export async function fetchBrands(): Promise<BrandSummary[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/brands`, { cache: "no-store" });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        return data;
      }
    }
  } catch (err) {
    console.warn("Backend warming up, using fallback brands:", err);
  }
  return FALLBACK_BRANDS;
}

export type ComplianceIssue = {
  term: string;
  reason: string;
  policy_ref: string | null;
};

export type ComplianceSummary = {
  id: string;
  outcome: string;
  risk_level: "pass" | "review" | "block" | null;
  reviewer_type: string;
  detected_issues: ComplianceIssue[];
  notes: string | null;
  reviewed_at: string;
};

export type PendingItem = {
  content_version_id: string;
  content_asset_id: string;
  brand_id: string;
  brand_name: string | null;
  platform: string | null;
  language: string | null;
  is_localized: boolean;
  body_preview: string;
  risk_level: "pass" | "review" | "block" | null;
  created_at: string;
};

export type SourceRef = {
  chunk_id: string;
  category: string | null;
  title: string | null;
  content: string | null;
};

export type ReviewDetail = {
  content_version_id: string;
  content_asset_id: string;
  brand_id: string;
  brand_name: string | null;
  platform: string | null;
  language: string | null;
  is_localized: boolean;
  status: string;
  body: string;
  topic: string | null;
  suggested_revision: string | null;
  sources: SourceRef[];
  compliance: ComplianceSummary | null;
};

export async function fetchPending(): Promise<PendingItem[]> {
  const res = await fetch(`${API_BASE_URL}/review/pending`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load pending review items (${res.status})`);
  return res.json();
}

export async function fetchReviewDetail(id: string): Promise<ReviewDetail> {
  const res = await fetch(`${API_BASE_URL}/review/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load review detail (${res.status})`);
  return res.json();
}

export type RejectionBucket = {
  bucket: number;
  versions: number;
  approved: number;
  rejected: number;
  rejection_rate: number | null;
  first_created_at: string;
  last_created_at: string;
};

export type BrandRejectionRate = {
  brand_id: string;
  brand_name: string;
  bucket_size: number;
  total_decided: number;
  total_approved: number;
  total_rejected: number;
  overall_rejection_rate: number | null;
  buckets: RejectionBucket[];
};

export async function fetchRejectionRates(): Promise<BrandRejectionRate[]> {
  const res = await fetch(`${API_BASE_URL}/metrics/rejection-rate`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load rejection rates (${res.status})`);
  const data = await res.json();
  return data.brands ?? [];
}

export type ScoreBreakdown = {
  competitor_mentions: number;
  competitor_mentions_points: number;
  recency_weight: number;
  recency_points: number;
  coverage_match: number;
  coverage_points: number;
  raw_total: number;
  capped_at: number;
  score: number;
  formula: string;
  matched_keywords: string[];
};

export type Opportunity = {
  opportunity_id: string;
  brand_id: string;
  title: string;
  rationale: string | null;
  opportunity_type: string | null;
  score: number | null;
  score_breakdown: ScoreBreakdown | null;
  suggested_angle: string | null;
  suggested_formats: string[];
  source_chunk_ids: string[];
  status: string;
};

export type CampaignResult = {
  campaign_id: string;
  campaign_name: string;
  brief: Record<string, string | null>;
  brief_compliance_warnings?: { field: string; term: string; reason: string }[];
  assets: {
    content_version_id: string;
    content_format: string;
    platform: string;
    status: string;
    compliance_outcome: string;
    risk_level: string;
    detected_issue_count: number;
  }[];
};

export async function fetchOpportunities(brandId: string): Promise<Opportunity[]> {
  const res = await fetch(`${API_BASE_URL}/opportunities?brand_id=${brandId}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to load opportunities (${res.status})`);
  return res.json();
}

export async function generateCampaign(opportunityId: string): Promise<CampaignResult> {
  const res = await fetch(`${API_BASE_URL}/campaigns/from-opportunity`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ opportunity_id: opportunityId }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Campaign generation failed (${res.status})`);
  }
  return res.json();
}

export type DecisionPayload = {
  action: "approve" | "edit" | "reject";
  edited_body?: string;
  reason_tag?: string;
  note?: string;
};

export async function submitDecision(id: string, payload: DecisionPayload) {
  const res = await fetch(`${API_BASE_URL}/review/${id}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Decision failed (${res.status})`);
  }
  return res.json();
}

export type LeadScoreComponent = {
  value: number;
  weight: number;
  points: number;
  detail: Record<string, any>;
};

export type LeadScoreBreakdown = {
  formula: string;
  components: Record<string, LeadScoreComponent>;
  raw_total: number;
  capped_at: number;
  score: number;
};

export type LeadOutreach = {
  content_version_id: string;
  status: string;
  is_current: boolean;
  body_preview: string | null;
  risk_level: string | null;
  compliance_outcome: string | null;
};

export type Lead = {
  lead_id: string;
  brand_id: string;
  company_name: string;
  contact_name: string | null;
  email: string | null;
  category: string | null;
  location: string | null;
  employee_count: number | null;
  source: string | null;
  status: string;
  fit_score: number | null;
  score_breakdown: LeadScoreBreakdown | null;
  outreach: LeadOutreach | null;
};

export type LeadsResponse = {
  brand_id: string;
  formula: string;
  count: number;
  leads: Lead[];
};

export async function fetchLeads(brandId: string): Promise<LeadsResponse> {
  const res = await fetch(`${API_BASE_URL}/leads?brand_id=${brandId}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load leads (${res.status})`);
  return res.json();
}

export async function generateLeads(brandId: string, maxOutreach = 3) {
  const res = await fetch(
    `${API_BASE_URL}/leads/generate?brand_id=${brandId}&max_outreach=${maxOutreach}`,
    { method: "POST" }
  );
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Lead generation failed (${res.status})`);
  }
  return res.json();
}

export type PerformanceInsight = {
  insight_id: string;
  insight_text: string;
  insight_type: string | null;
  supporting_metric: string | null;
  recommendation: string | null;
  derived_from: {
    primary_metric?: string;
    groups?: Record<string, { bucket: string; posts: number; avg_engagement_rate: number }[]>;
    analytics_are_simulated?: boolean;
  } | null;
  created_at: string;
};

export type InsightsResponse = {
  brand_id: string;
  count: number;
  data_is_simulated: boolean;
  simulated_note: string;
  insights: PerformanceInsight[];
};

export async function fetchInsights(brandId: string): Promise<InsightsResponse> {
  const res = await fetch(`${API_BASE_URL}/optimization/insights?brand_id=${brandId}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to load insights (${res.status})`);
  return res.json();
}

export async function runAnalysis(brandId: string) {
  const res = await fetch(`${API_BASE_URL}/optimization/analyze?brand_id=${brandId}`, {
    method: "POST",
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Analysis failed (${res.status})`);
  }
  return res.json();
}

export type AiRunRow = {
  id: string;
  agent_name: string;
  status: string;
  model: string | null;
  prompt_version: string | null;
  latency_ms: number | null;
  related_entity_type: string | null;
  error_message: string | null;
  input_summary: string | null;
  created_at: string;
};

export type ObservabilitySummary = {
  window_hours: number;
  total_calls: number;
  total_failed: number;
  success_rate: number | null;
  by_agent: {
    agent_name: string;
    calls: number;
    failed: number;
    success_rate: number | null;
    avg_latency_ms: number | null;
    max_latency_ms: number | null;
  }[];
  by_model: { model: string | null; calls: number }[];
  all_time_first_run: string | null;
  all_time_last_run: string | null;
  not_logged: string[];
  note: string;
};

export async function fetchObservabilitySummary(hours = 720): Promise<ObservabilitySummary> {
  const res = await fetch(`${API_BASE_URL}/observability/summary?hours=${hours}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to load summary (${res.status})`);
  return res.json();
}

export async function fetchAiRuns(limit = 50): Promise<{ runs: AiRunRow[]; count: number }> {
  const res = await fetch(`${API_BASE_URL}/observability/runs?limit=${limit}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to load runs (${res.status})`);
  return res.json();
}

// --- Live judge demo (Phase 10) ---
export type DemoStep = {
  key: string;
  label: string;
  status: "pass" | "warn" | "fail" | "skipped" | "error";
  detail: string;
  terms?: string[];
  issues?: { term: string; reason: string; policy_ref: string | null }[];
  policy_refs?: string[];
};

export type DemoResult = {
  content_version_id: string;
  body: string;
  status: string;
  outcome: string | null;
  risk_level: "pass" | "review" | "block" | null;
  detected_issues: { term: string; reason: string; policy_ref: string | null }[];
  policy_refs: string[];
  suggested_revision: string | null;
  reviewer_type: string | null;
};

export type QuotaStatus = {
  live_available: boolean;
  calls_used_today: number;
  ceiling: number;
  threshold: number;
  calls_remaining: number;
  estimated_runs_remaining: number;
  fallback_examples_available?: number;
  note: string;
};

export type DemoRunResponse = {
  mode: "live" | "recorded" | "rejected" | "rate_limited";
  demo_mode?: string;
  recorded?: boolean;
  live_available?: boolean;
  message?: string;
  retry_after_seconds?: number;
  brand?: { id: string; name: string; slug: string };
  language?: string;
  language_name?: string;
  claim_or_topic?: string;
  english_source?: string | null;
  compliance_ran_on?: string;
  steps?: DemoStep[];
  result?: DemoResult;
  quota?: QuotaStatus;
  example?: any;
};

export type DemoSuggestion = { label: string; text: string; expectation: string };

export async function fetchQuotaStatus(): Promise<QuotaStatus> {
  const res = await fetch(`${API_BASE_URL}/demo/quota-status`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load quota status (${res.status})`);
  return res.json();
}

export async function fetchDemoSuggestions(): Promise<{ suggestions: DemoSuggestion[] }> {
  const res = await fetch(`${API_BASE_URL}/demo/suggestions`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load suggestions (${res.status})`);
  return res.json();
}

export async function fetchFallbackExamples(): Promise<{ count: number; examples: any[]; note: string }> {
  const res = await fetch(`${API_BASE_URL}/demo/fallback-examples`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load recorded examples (${res.status})`);
  return res.json();
}

export async function runDemo(body: {
  brand_id: string;
  language: string;
  claim_or_topic: string;
  mode?: string;
}): Promise<DemoRunResponse> {
  let session = "anon";
  try {
    session = localStorage.getItem("ja-demo-session") ?? "";
    if (!session) {
      session = Math.random().toString(36).slice(2);
      localStorage.setItem("ja-demo-session", session);
    }
  } catch {
    session = "anon";
  }
  const res = await fetch(`${API_BASE_URL}/demo/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-demo-session": session },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Demo run failed (${res.status})`);
  }
  return res.json();
}

// --- Visual Studio & Carousel Studio ---
export type VisualCreativeResponse = {
  brand_slug: string;
  brand_name: string;
  topic: string;
  platform: string;
  creative: {
    hero_image_prompt: string;
    negative_prompt: string;
    aspect_ratio: string;
    carousel_slides: {
      slide_number: number;
      visual_cue: string;
      headline: string;
      body_copy: string;
      cta?: string;
    }[];
  };
};

export async function generateVisualCreative(
  brand_slug: string,
  topic: string,
  platform = "instagram_carousel"
): Promise<VisualCreativeResponse> {
  const res = await fetch(`${API_BASE_URL}/visual/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brand_slug, topic, platform }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Visual generation failed (${res.status})`);
  }
  return res.json();
}

// --- Industry Events & 1-Click Campaigns ---
export type IndustryEvent = {
  id: string;
  title: string;
  brand_slug: string;
  brand_name: string;
  target_audience: string;
  location: string;
  date_window: string;
  days_remaining: number;
  urgency: string;
  suggested_angles: string[];
  default_cta: string;
};

export async function fetchIndustryEvents(): Promise<IndustryEvent[]> {
  const res = await fetch(`${API_BASE_URL}/events`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load events (${res.status})`);
  const data = await res.json();
  return data.events || [];
}

export async function triggerEventCampaign(eventId: string) {
  const res = await fetch(`${API_BASE_URL}/events/trigger`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ event_id: eventId }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Event trigger failed (${res.status})`);
  }
  return res.json();
}

// --- Live Singapore OpenStreetMap Prospecting ---
export type LiveOsmBusiness = {
  id: string;
  name: string;
  address: string;
  lat?: number;
  lon?: number;
  category: string;
  phone: string;
  website: string;
  source: string;
  brand_fit: string;
};

export async function fetchLiveSingaporeBusinesses(
  brandId: string,
  limit = 10
): Promise<{ count: number; results: LiveOsmBusiness[]; source: string }> {
  const res = await fetch(`${API_BASE_URL}/leads/osm-live?brand_id=${brandId}&limit=${limit}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to fetch live OSM businesses (${res.status})`);
  return res.json();
}

// --- Insurtech 101 Knowledge Repurposing Agent ---
export type MasterclassTemplate = {
  id: string;
  brand_slug: string;
  title: string;
  category: string;
  source_type: string;
  content: string;
};

export type CarouselSlide = {
  slide_number: number;
  role: string;
  headline: string;
  body: string;
  visual_direction: string;
};

export type RepurposedNurtureKit = {
  executive_summary: string;
  target_audience: string;
  key_takeaways: string[];
  linkedin_brief: {
    headline: string;
    body: string;
    hashtags: string[];
  };
  carousel_deck: {
    title: string;
    slides: CarouselSlide[];
  };
  x_thread: {
    post_number: number;
    tweet: string;
  }[];
  outreach_email: {
    subject: string;
    body: string;
  };
  compliance_check: {
    passed: boolean;
    outcome: string;
    issues_found: any[];
  };
  brand: {
    id: string;
    name: string;
    slug: string;
  };
};

export async function fetchMasterclassTemplates(): Promise<MasterclassTemplate[]> {
  const res = await fetch(`${API_BASE_URL}/repurpose/templates`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch templates (${res.status})`);
  const data = await res.json();
  return data.templates || [];
}

export async function generateRepurposedContent(
  sourceText: string,
  brandSlug: string = "jade",
  title?: string
): Promise<RepurposedNurtureKit> {
  const res = await fetch(`${API_BASE_URL}/repurpose/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_text: sourceText, brand_slug: brandSlug, title }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Repurposing failed (${res.status})`);
  }
  return res.json();
}

export async function saveRepurposedAssetToQueue(
  brandSlug: string,
  platform: string,
  assetType: string,
  contentText: string,
  title?: string
) {
  const res = await fetch(`${API_BASE_URL}/repurpose/save-to-queue`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      brand_slug: brandSlug,
      platform,
      asset_type: assetType,
      content_text: contentText,
      title,
    }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Saving to queue failed (${res.status})`);
  }
  return res.json();
}

