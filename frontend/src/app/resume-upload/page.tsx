"use client";

import { FormEvent, useEffect, useState } from "react";

import { AuthGuard } from "@/components/auth/AuthGuard";
import { AppShell } from "@/components/layout/AppShell";
import { Alert } from "@/components/ui/Alert";
import {
  ApiRequestError,
  getResume,
  ResumeRead,
  uploadResume,
} from "@/lib/api";

export default function ResumeUploadPage() {
  return (
    <AuthGuard>
      <ResumeUploadContent />
    </AuthGuard>
  );
}

function ResumeUploadContent() {
  const [file, setFile] = useState<File | null>(null);
  const [existing, setExisting] = useState<ResumeRead | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getResume();
        setExisting(data);
      } catch (err) {
        const message =
          err instanceof ApiRequestError ? err.message : "Failed to load resume.";
        setError(message);
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  const handleFileChange = (selected: File | null) => {
    setFile(selected);
    setSuccess(null);
    setError(null);

    if (selected && !selected.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are allowed.");
      setFile(null);
    }
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!file) {
      setError("Please select a PDF file to upload.");
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await uploadResume(file);
      setSuccess(
        `${response.message} Extracted ${response.character_count.toLocaleString()} characters from "${response.filename}".`,
      );
      setExisting({
        id: response.id,
        filename: response.filename,
        text_preview: response.text_preview,
        character_count: response.character_count,
        has_resume: true,
        updated_at: response.updated_at,
      });
      setFile(null);
    } catch (err) {
      const message =
        err instanceof ApiRequestError ? err.message : "Resume upload failed. Please try again.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AppShell
      title="Upload Resume"
      subtitle="Upload a PDF resume. Text will be extracted and saved to your profile."
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
        <div className="space-y-6">
          {existing?.has_resume && (
            <div className="rounded-xl border border-slate-200 bg-white p-6">
              <h2 className="font-semibold text-slate-900">Current resume</h2>
              <p className="mt-1 text-sm text-slate-600">
                {existing.filename} · {existing.character_count.toLocaleString()} characters
              </p>
              {existing.text_preview && (
                <pre className="mt-4 max-h-48 overflow-auto rounded-lg bg-slate-50 p-4 text-xs text-slate-700 whitespace-pre-wrap">
                  {existing.text_preview}
                  {existing.character_count > 500 ? "\n\n…" : ""}
                </pre>
              )}
            </div>
          )}

          <form
            onSubmit={handleSubmit}
            className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <label
              htmlFor="resume"
              className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-12 transition hover:border-brand-400 hover:bg-brand-50/50"
            >
              <span className="text-4xl">📄</span>
              <span className="mt-3 text-sm font-medium text-slate-700">
                {file ? file.name : "Click to select a PDF resume"}
              </span>
              <span className="mt-1 text-xs text-slate-500">PDF only · Max 5MB</span>
              <input
                id="resume"
                type="file"
                accept="application/pdf,.pdf"
                className="sr-only"
                onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
              />
            </label>

            <button
              type="submit"
              disabled={submitting || !file}
              className="mt-6 w-full rounded-lg bg-brand-600 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
            >
              {submitting ? "Uploading & extracting..." : "Upload resume"}
            </button>
          </form>
        </div>
      )}
    </AppShell>
  );
}
