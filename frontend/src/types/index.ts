// ── Auth ───────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ── Startup ────────────────────────────────────────────────
export type StartupStatus = "pending" | "processing" | "done" | "failed";

export interface Startup {
  id: string;
  name: string | null;
  website_url: string | null;
  industry: string | null;
  stage: string | null;
  geography: string | null;
  founding_year: number | null;
  extracted_data: Record<string, unknown> | null;
  status: StartupStatus;
  created_at: string;
  updated_at: string;
}

export interface StartupListItem {
  id: string;
  name: string | null;
  industry: string | null;
  stage: string | null;
  status: StartupStatus;
  created_at: string;
}

// ── Analysis ───────────────────────────────────────────────
export interface AnalysisJob {
  job_id: string;
  startup_id: string;
  celery_task_id: string | null;
  current_step: string | null;
  steps_completed: string[];
  total_steps: number;
  memo_id: string | null;
  error_message: string | null;
  created_at: string;
}

export interface JobStreamEvent {
  job_id: string;
  current_step: string;
  steps_completed: string[];
  total_steps: number;
  memo_id: string | null;
  error?: string;
}

// ── Memo ───────────────────────────────────────────────────
export type MemoStatus = "generating" | "complete" | "failed";
export type Recommendation = "strong_invest" | "invest" | "watch" | "pass";

export interface MemoSection {
  id: string;
  section_key: string;
  section_order: number;
  title: string;
  content: string | null;
  content_json: Record<string, unknown> | null;
  citations: Array<{ url: string }> | null;
  is_edited: boolean;
  created_at: string;
}

export interface Memo {
  id: string;
  startup_id: string;
  version: number;
  status: MemoStatus;
  recommendation: Recommendation | null;
  confidence_score: number | null;
  total_tokens_used: number | null;
  generation_time_seconds: number | null;
  error_message: string | null;
  sections: MemoSection[];
  created_at: string;
  updated_at: string;
}

export interface MemoListItem {
  id: string;
  startup_id: string;
  status: MemoStatus;
  recommendation: Recommendation | null;
  confidence_score: number | null;
  version: number;
  created_at: string;
}

// ── UI helpers ─────────────────────────────────────────────
export interface DashboardMemo extends MemoListItem {
  startup?: StartupListItem;
}
