import { API_BASE_URL } from "@/lib/constants";
import { clearTokens, getAccessToken } from "@/lib/auth";

export type ApiError = {
  code: string;
  message: string;
};

export class ApiRequestError extends Error {
  code: string;
  status: number;

  constructor(message: string, code: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

async function parseError(response: Response): Promise<ApiRequestError> {
  try {
    const data = await response.json();
    const error = data?.error;
    return new ApiRequestError(
      error?.message ?? "Request failed",
      error?.code ?? "REQUEST_FAILED",
      response.status,
    );
  } catch {
    return new ApiRequestError("Request failed", "REQUEST_FAILED", response.status);
  }
}

type RequestOptions = {
  method?: string;
  body?: BodyInit | null;
  headers?: Record<string, string>;
  auth?: boolean;
};

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body = null, headers = {}, auth = true } = options;

  const requestHeaders: Record<string, string> = { ...headers };

  if (auth) {
    const token = getAccessToken();
    if (token) {
      requestHeaders.Authorization = `Bearer ${token}`;
    }
  }

  if (body && !(body instanceof FormData)) {
    requestHeaders["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: requestHeaders,
    body,
  });

  if (response.status === 401 && auth) {
    clearTokens();
  }

  if (!response.ok) {
    throw await parseError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

// Auth
export type User = {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AuthResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
};

export function login(email: string, password: string) {
  return apiRequest<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
    auth: false,
  });
}

export function register(email: string, password: string) {
  return apiRequest<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
    auth: false,
  });
}

export function getMe() {
  return apiRequest<User>("/auth/me");
}

// Resume
export type ResumeUploadResponse = {
  message: string;
  id: string;
  filename: string;
  text_preview: string;
  character_count: number;
  updated_at: string;
};

export type ResumeRead = {
  id: string | null;
  filename: string | null;
  text_preview: string | null;
  character_count: number;
  has_resume: boolean;
  updated_at: string | null;
};

export function uploadResume(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest<ResumeUploadResponse>("/resume/upload", {
    method: "POST",
    body: formData,
  });
}

export function getResume() {
  return apiRequest<ResumeRead>("/resume");
}

// Job Description
export type JobDescriptionUploadResponse = {
  message: string;
  id: string;
  title: string | null;
  content_preview: string;
  character_count: number;
  updated_at: string;
};

export type JobDescriptionRead = {
  id: string | null;
  title: string | null;
  content: string | null;
  content_preview: string | null;
  character_count: number;
  has_job_description: boolean;
  updated_at: string | null;
};

export function uploadJobDescription(content: string, title?: string) {
  return apiRequest<JobDescriptionUploadResponse>("/jd/upload", {
    method: "POST",
    body: JSON.stringify({ content, title: title || null }),
  });
}

export function getJobDescription() {
  return apiRequest<JobDescriptionRead>("/jd");
}

// Interviews
export type InterviewStatus =
  | "in_progress"
  | "completed"
  | "scored"
  | "failed"
  | "terminated_early";

export type InterviewQuestion = {
  id: string;
  question_index: number;
  question_text: string;
  category: string | null;
  difficulty?: string | null;
};

export type InterviewStartResponse = {
  message: string;
  session_id: string;
  total_questions: number;
  time_per_question_seconds: number;
  current_question_index: number;
  current_difficulty: string;
  status: InterviewStatus;
};

export type InterviewSession = {
  id: string;
  status: InterviewStatus;
  total_questions: number;
  current_question_index: number;
  time_per_question_seconds: number;
  current_difficulty: string;
  current_question: InterviewQuestion | null;
  answered_count: number;
  started_at: string;
  completed_at: string | null;
  terminated_early?: boolean;
};

export type SubmitAnswerResponse = {
  message: string;
  session_id: string;
  question_index: number;
  is_complete: boolean;
  next_question_index: number | null;
  status: InterviewStatus;
  answer_score?: number | null;
  answer_feedback?: string | null;
  early_terminated?: boolean;
  termination_reason?: string | null;
  next_difficulty?: string | null;
};

export type InterviewAnswer = {
  id: string;
  question_index: number;
  answer_text: string;
  time_taken_seconds: number;
  submitted_at: string;
  score?: number | null;
  feedback?: string | null;
  score_breakdown?: Record<string, number> | null;
};

export type InterviewReport = {
  session_id: string;
  status: InterviewStatus;
  overall_score: number;
  readiness_score: number;
  grade: string;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  improvements: string[];
  dimension_scores: Record<string, number>;
  performance_breakdown: Record<string, number>;
  questions: InterviewQuestion[];
  answers: InterviewAnswer[];
  scored_at: string | null;
  completed_at: string | null;
  terminated_early?: boolean;
  termination_reason?: string | null;
};

export type InterviewListItem = {
  id: string;
  status: InterviewStatus;
  overall_score: number | null;
  readiness_score?: number | null;
  grade: string | null;
  total_questions: number;
  started_at: string;
  completed_at: string | null;
  terminated_early?: boolean;
};

export type InterviewAnalytics = {
  total_interviews: number;
  completed_interviews: number;
  average_overall_score: number | null;
  average_readiness_score: number | null;
  score_trend: {
    session_id: string;
    date: string;
    overall_score: number | null;
    readiness_score: number | null;
  }[];
  performance_averages: Record<string, number>;
  dimension_averages: Record<string, number>;
  recent_scores: {
    id: string;
    overall_score: number | null;
    readiness_score: number | null;
    grade: string | null;
    date: string;
  }[];
};

export function startInterview() {
  return apiRequest<InterviewStartResponse>("/interviews/start", { method: "POST" });
}

export function getInterview(sessionId: string) {
  return apiRequest<InterviewSession>(`/interviews/${sessionId}`);
}

export function submitAnswer(
  sessionId: string,
  answerText: string,
  timeTakenSeconds: number,
) {
  return apiRequest<SubmitAnswerResponse>(`/interviews/${sessionId}/answers`, {
    method: "POST",
    body: JSON.stringify({
      answer_text: answerText,
      time_taken_seconds: timeTakenSeconds,
    }),
  });
}

export function getInterviewReport(sessionId: string) {
  return apiRequest<InterviewReport>(`/interviews/${sessionId}/report`);
}

export function listInterviews() {
  return apiRequest<InterviewListItem[]>("/interviews");
}

export function getInterviewAnalytics() {
  return apiRequest<InterviewAnalytics>("/interviews/analytics");
}

export async function downloadInterviewReportPdf(sessionId: string): Promise<void> {
  const { getAccessToken } = await import("@/lib/auth");
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/interviews/${sessionId}/report/pdf`,
    {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    },
  );
  if (!response.ok) {
    throw new ApiRequestError("Failed to download PDF", "DOWNLOAD_FAILED", response.status);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `hack2hire-interview-${sessionId}.pdf`;
  link.click();
  URL.revokeObjectURL(url);
}
