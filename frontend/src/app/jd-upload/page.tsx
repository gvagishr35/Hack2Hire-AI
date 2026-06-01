"use client";

import { FormEvent, useEffect, useState } from "react";

import { AuthGuard } from "@/components/auth/AuthGuard";
import { AppShell } from "@/components/layout/AppShell";
import { Alert } from "@/components/ui/Alert";
import {
  ApiRequestError,
  getJobDescription,
  JobDescriptionRead,
  uploadJobDescription,
} from "@/lib/api";

const MIN_CHARS = 20;

export default function JobDescriptionUploadPage() {
  return (
    <AuthGuard>
      <JobDescriptionUploadContent />
    </AuthGuard>
  );
}

function JobDescriptionUploadContent() {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [existing, setExisting] = useState<JobDescriptionRead | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getJobDescription();
        setExisting(data);
        if (data.has_job_description) {
          setTitle(data.title ?? "");
          setContent(data.content ?? "");
        }
      } catch (err) {
        const message =
          err instanceof ApiRequestError ? err.message : "Failed to load job description.";
        setError(message);
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    if (content.trim().length < MIN_CHARS) {
      setError(`Job description must be at least ${MIN_CHARS} characters.`);
      return;
    }

    setSubmitting(true);

    try {
      const response = await uploadJobDescription(
        content.trim(),
        title.trim() || undefined,
      );
      setSuccess(
        `${response.message} Saved ${response.character_count.toLocaleString()} characters.`,
      );
      setExisting({
        id: response.id,
        title: response.title,
        content: content.trim(),
        content_preview: response.content_preview,
        character_count: response.character_count,
        has_job_description: true,
        updated_at: response.updated_at,
      });
    } catch (err) {
      const message =
        err instanceof ApiRequestError
          ? err.message
          : "Failed to save job description. Please try again.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AppShell
      title="Job Description"
      subtitle="Paste the job description you are applying for. It will be used to tailor your mock interview."
    >
      {success && (
        <div className="mb-6">
          <Alert variant="success" message={success} onDismiss={() => setSuccess(null)} />
        </div>
      )}
      {error && (
        <div className="mb-6">
          <Alert variant="error" message={error} onDismiss={() => setError(null)} />
        </div>
      )}

      {loading ? (
        <p className="text-slate-600">Loading...</p>
      ) : (
        <form
          onSubmit={handleSubmit}
          className="space-y-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          {existing?.has_job_description && (
            <Alert
              variant="info"
              message="You have a saved job description. Update the fields below and save to replace it."
            />
          )}

          <div>
            <label htmlFor="title" className="block text-sm font-medium text-slate-700">
              Job title (optional)
            </label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Senior Backend Engineer"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            />
          </div>

          <div>
            <div className="flex items-center justify-between">
              <label htmlFor="content" className="block text-sm font-medium text-slate-700">
                Job description
              </label>
              <span className="text-xs text-slate-500">
                {content.trim().length.toLocaleString()} characters
              </span>
            </div>
            <textarea
              id="content"
              required
              rows={16}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste the full job description here — responsibilities, requirements, qualifications..."
              className="mt-1 w-full resize-y rounded-lg border border-slate-300 px-3 py-2 text-sm leading-relaxed focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            />
            <p className="mt-1 text-xs text-slate-500">Minimum {MIN_CHARS} characters required</p>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-brand-600 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {submitting ? "Saving..." : "Save job description"}
          </button>
        </form>
      )}
    </AppShell>
  );
}
