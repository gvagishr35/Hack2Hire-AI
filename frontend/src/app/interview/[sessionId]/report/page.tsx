"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { AuthGuard } from "@/components/auth/AuthGuard";
import { Alert } from "@/components/ui/Alert";
import {
  ApiRequestError,
  downloadInterviewReportPdf,
  getInterviewReport,
  InterviewReport,
} from "@/lib/api";

const BAR_COLORS = ["#4f46e5", "#06b6d4", "#10b981"];

export default function InterviewReportPage() {
  return (
    <AuthGuard>
      <ReportContent />
    </AuthGuard>
  );
}

function ReportContent() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [report, setReport] = useState<InterviewReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getInterviewReport(sessionId);
        setReport(data);
      } catch (err) {
        const message =
          err instanceof ApiRequestError ? err.message : "Failed to load report.";
        setError(message);
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [sessionId]);

  const handleDownloadPdf = async () => {
    setDownloading(true);
    setError(null);
    try {
      await downloadInterviewReportPdf(sessionId);
    } catch (err) {
      const message =
        err instanceof ApiRequestError ? err.message : "PDF download failed.";
      setError(message);
    } finally {
      setDownloading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-indigo-50">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600" />
          <p className="mt-4 text-slate-600">Generating your interview report...</p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
        <div className="w-full max-w-md">
          <Alert variant="error" message={error ?? "Report not found"} />
          <Link
            href="/dashboard"
            className="mt-4 inline-block text-sm font-medium text-brand-600 hover:underline"
          >
            Back to dashboard
          </Link>
        </div>
      </div>
    );
  }

  const performanceData = Object.entries(report.performance_breakdown).map(
    ([key, value]) => ({
      name: key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      score: Math.round(value),
    }),
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50">
      <header className="border-b border-slate-200/80 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-5xl flex-col gap-4 px-4 py-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <Link href="/dashboard" className="text-sm font-medium text-brand-600 hover:underline">
              ← Dashboard
            </Link>
            <h1 className="mt-2 text-2xl font-bold text-slate-900">Interview Report</h1>
            <p className="mt-1 text-slate-600">AI evaluation tailored to your resume and job description</p>
          </div>
          <button
            type="button"
            onClick={() => void handleDownloadPdf()}
            disabled={downloading}
            className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 disabled:opacity-60"
          >
            {downloading ? "Preparing PDF..." : "Download PDF"}
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-4 py-8">
        {report.terminated_early && report.termination_reason && (
          <Alert variant="info" message={report.termination_reason} />
        )}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <ScoreCard label="Overall Score" value={`${Math.round(report.overall_score)}%`} accent />
          <ScoreCard label="Readiness" value={`${Math.round(report.readiness_score)}%`} />
          <ScoreCard label="Grade" value={report.grade} />
          <ScoreCard
            label="Answered"
            value={`${report.answers.length}/${report.questions.length}`}
          />
        </div>

        {performanceData.length > 0 && (
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Performance breakdown</h2>
            <p className="mt-1 text-sm text-slate-500">
              Technical · Communication · Time management
            </p>
            <div className="mt-6 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="score" radius={[8, 8, 0, 0]}>
                    {performanceData.map((_, i) => (
                      <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>
        )}

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Executive summary</h2>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
            {report.summary}
          </p>
        </section>

        <div className="grid gap-6 md:grid-cols-3">
          <InsightCard title="Strengths" items={report.strengths} variant="success" />
          <InsightCard title="Weaknesses" items={report.weaknesses} variant="warning" />
          <InsightCard title="Recommendations" items={report.improvements} variant="info" />
        </div>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Question-by-question review</h2>
          <div className="mt-6 space-y-6">
            {report.questions.map((question) => {
              const answer = report.answers.find(
                (a) => a.question_index === question.question_index,
              );
              return (
                <div
                  key={question.id}
                  className="rounded-xl border border-slate-100 bg-slate-50/80 p-5"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-bold uppercase text-brand-600">
                      Q{question.question_index + 1}
                    </span>
                    {question.difficulty && (
                      <span className="rounded-full bg-white px-2 py-0.5 text-xs font-medium capitalize text-slate-600 ring-1 ring-slate-200">
                        {question.difficulty}
                      </span>
                    )}
                    {question.category && (
                      <span className="text-xs text-slate-500">{question.category}</span>
                    )}
                    {answer?.score != null && (
                      <span className="ml-auto rounded-full bg-brand-100 px-3 py-0.5 text-sm font-bold text-brand-700">
                        {Math.round(answer.score)}%
                      </span>
                    )}
                  </div>
                  <p className="mt-3 font-medium text-slate-900">{question.question_text}</p>
                  <p className="mt-3 text-sm text-slate-700">
                    <span className="font-medium">Your answer: </span>
                    {answer?.answer_text ?? "—"}
                  </p>
                  {answer?.feedback && (
                    <p className="mt-2 rounded-lg bg-white p-3 text-sm text-slate-600 ring-1 ring-slate-100">
                      <span className="font-medium text-slate-800">AI feedback: </span>
                      {answer.feedback}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      </main>
    </div>
  );
}

function ScoreCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div
      className={`rounded-2xl border p-5 text-center shadow-sm ${
        accent
          ? "border-brand-200 bg-gradient-to-br from-brand-600 to-indigo-600 text-white"
          : "border-slate-200 bg-white"
      }`}
    >
      <p className={`text-xs font-medium uppercase tracking-wide ${accent ? "text-brand-100" : "text-slate-500"}`}>
        {label}
      </p>
      <p className={`mt-1 text-3xl font-bold ${accent ? "text-white" : "text-slate-900"}`}>{value}</p>
    </div>
  );
}

function InsightCard({
  title,
  items,
  variant,
}: {
  title: string;
  items: string[];
  variant: "success" | "warning" | "info";
}) {
  const styles = {
    success: "border-emerald-200 bg-emerald-50 text-emerald-900",
    warning: "border-amber-200 bg-amber-50 text-amber-900",
    info: "border-blue-200 bg-blue-50 text-blue-900",
  };
  return (
    <section className={`rounded-2xl border p-5 ${styles[variant]}`}>
      <h2 className="font-semibold">{title}</h2>
      <ul className="mt-3 list-inside list-disc space-y-2 text-sm">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
