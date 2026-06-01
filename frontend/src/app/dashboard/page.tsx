"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AuthGuard } from "@/components/auth/AuthGuard";
import { PerformanceCharts } from "@/components/dashboard/PerformanceCharts";
import { AppShell } from "@/components/layout/AppShell";
import { Alert } from "@/components/ui/Alert";
import {
  ApiRequestError,
  getInterviewAnalytics,
  getJobDescription,
  getResume,
  InterviewAnalytics,
  InterviewListItem,
  JobDescriptionRead,
  listInterviews,
  ResumeRead,
  startInterview,
} from "@/lib/api";

export default function DashboardPage() {
  return (
    <AuthGuard>
      <DashboardContent />
    </AuthGuard>
  );
}

function DashboardContent() {
  const router = useRouter();
  const [resume, setResume] = useState<ResumeRead | null>(null);
  const [jd, setJd] = useState<JobDescriptionRead | null>(null);
  const [interviews, setInterviews] = useState<InterviewListItem[]>([]);
  const [analytics, setAnalytics] = useState<InterviewAnalytics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);

  const canStartInterview = (resume?.has_resume ?? false) && (jd?.has_job_description ?? false);

  useEffect(() => {
    const load = async () => {
      try {
        const [resumeData, jdData, interviewList, analyticsData] = await Promise.all([
          getResume(),
          getJobDescription(),
          listInterviews(),
          getInterviewAnalytics(),
        ]);
        setResume(resumeData);
        setJd(jdData);
        setInterviews(interviewList.slice(0, 5));
        setAnalytics(analyticsData);
      } catch (err) {
        const message =
          err instanceof ApiRequestError ? err.message : "Failed to load dashboard data.";
        setError(message);
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  const handleStartInterview = async () => {
    if (!canStartInterview) return;

    setStarting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await startInterview();
      setSuccess("Generating tailored questions from your resume and job description...");
      router.push(`/interview/${response.session_id}`);
    } catch (err) {
      const message =
        err instanceof ApiRequestError
          ? err.message
          : "Failed to start interview. Please try again.";
      setError(message);
      setStarting(false);
    }
  };

  return (
    <AppShell
      title="Dashboard"
      subtitle="Track performance, upload materials, and run adaptive AI interviews"
    >
      {error && (
        <div className="mb-6">
          <Alert variant="error" message={error} onDismiss={() => setError(null)} />
        </div>
      )}
      {success && (
        <div className="mb-6">
          <Alert variant="success" message={success} onDismiss={() => setSuccess(null)} />
        </div>
      )}

      <div className="mb-8 overflow-hidden rounded-2xl border border-brand-200 bg-gradient-to-br from-brand-600 via-indigo-600 to-violet-700 p-6 text-white shadow-lg">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-bold">Adaptive AI Mock Interview</h2>
            <p className="mt-2 max-w-xl text-sm text-brand-100">
              Questions are generated from your resume and job description. Difficulty adapts
              from Easy → Medium → Hard based on your answers. Each answer is scored instantly.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void handleStartInterview()}
            disabled={!canStartInterview || starting}
            className="shrink-0 rounded-xl bg-white px-6 py-3 text-sm font-bold text-brand-700 shadow-md hover:bg-brand-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {starting ? "Starting..." : "Start Interview"}
          </button>
        </div>
        {!canStartInterview && !loading && (
          <p className="mt-3 text-xs text-brand-200">
            Upload resume and job description to enable interviews.
          </p>
        )}
      </div>

      {loading ? (
        <p className="text-slate-600">Loading dashboard...</p>
      ) : (
        <>
          {analytics && (
            <section className="mb-8">
              <h2 className="mb-4 text-lg font-semibold text-slate-900">Performance analytics</h2>
              <PerformanceCharts analytics={analytics} />
            </section>
          )}

          <div className="grid gap-6 md:grid-cols-2">
            <StatusCard
              title="Resume"
              uploaded={resume?.has_resume ?? false}
              detail={
                resume?.has_resume
                  ? `${resume.filename} · ${resume.character_count.toLocaleString()} characters`
                  : "No resume uploaded yet"
              }
              href="/resume-upload"
              actionLabel={resume?.has_resume ? "Update resume" : "Upload resume"}
            />
            <StatusCard
              title="Job Description"
              uploaded={jd?.has_job_description ?? false}
              detail={
                jd?.has_job_description
                  ? `${jd.title || "Untitled"} · ${jd.character_count.toLocaleString()} characters`
                  : "No job description saved yet"
              }
              href="/jd-upload"
              actionLabel={jd?.has_job_description ? "Edit job description" : "Add job description"}
            />
          </div>
        </>
      )}

      {interviews.length > 0 && (
        <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Recent interviews</h2>
          <ul className="mt-4 divide-y divide-slate-100">
            {interviews.map((item) => (
              <li key={item.id} className="flex items-center justify-between gap-4 py-4">
                <div>
                  <p className="text-sm font-medium text-slate-900">
                    {new Date(item.started_at).toLocaleDateString(undefined, {
                      dateStyle: "medium",
                    })}
                    {item.terminated_early && (
                      <span className="ml-2 text-xs text-amber-600">Ended early</span>
                    )}
                  </p>
                  <p className="text-xs text-slate-500">
                    {item.overall_score != null && (
                      <>
                        Score {Math.round(item.overall_score)}%
                        {item.readiness_score != null &&
                          ` · Readiness ${Math.round(item.readiness_score)}%`}
                        {item.grade && ` · ${item.grade}`}
                      </>
                    )}
                  </p>
                </div>
                {(item.status === "scored" ||
                  item.status === "completed" ||
                  item.status === "terminated_early") && (
                  <Link
                    href={`/interview/${item.id}/report`}
                    className="text-sm font-medium text-brand-600 hover:underline"
                  >
                    View report
                  </Link>
                )}
                {item.status === "in_progress" && (
                  <Link
                    href={`/interview/${item.id}`}
                    className="text-sm font-medium text-brand-600 hover:underline"
                  >
                    Continue
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </AppShell>
  );
}

type StatusCardProps = {
  title: string;
  uploaded: boolean;
  detail: string;
  href: string;
  actionLabel: string;
};

function StatusCard({ title, uploaded, detail, href, actionLabel }: StatusCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:shadow-md">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
            uploaded ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
          }`}
        >
          {uploaded ? "Complete" : "Pending"}
        </span>
      </div>
      <p className="mt-3 text-sm text-slate-600">{detail}</p>
      <Link
        href={href}
        className="mt-4 inline-flex rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
      >
        {actionLabel}
      </Link>
    </div>
  );
}
