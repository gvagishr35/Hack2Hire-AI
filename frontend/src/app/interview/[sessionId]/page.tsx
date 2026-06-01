"use client";

import { useParams, useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useRef, useState } from "react";

import { AuthGuard } from "@/components/auth/AuthGuard";
import { DifficultyBadge } from "@/components/interview/DifficultyBadge";
import { QuestionTimer } from "@/components/interview/QuestionTimer";
import { Alert } from "@/components/ui/Alert";
import { useTimer } from "@/hooks/useTimer";
import {
  ApiRequestError,
  getInterview,
  InterviewSession,
  submitAnswer,
} from "@/lib/api";

export default function InterviewPage() {
  return (
    <AuthGuard>
      <InterviewRoom />
    </AuthGuard>
  );
}

function InterviewRoom() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [session, setSession] = useState<InterviewSession | null>(null);
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [lastFeedback, setLastFeedback] = useState<{
    score: number;
    feedback: string;
    earlyTerminated?: boolean;
    reason?: string | null;
  } | null>(null);

  const answerRef = useRef(answer);
  const sessionRef = useRef(session);
  const submittingRef = useRef(submitting);
  const expiredHandledRef = useRef(false);

  answerRef.current = answer;
  sessionRef.current = session;
  submittingRef.current = submitting;

  const loadSession = useCallback(async () => {
    const data = await getInterview(sessionId);
    setSession(data);
    return data;
  }, [sessionId]);

  const timer = useTimer(120);

  const handleSubmit = useCallback(
    async (forcedAnswer?: string) => {
      const currentSession = sessionRef.current;
      if (!currentSession?.current_question || submittingRef.current) return;

      const text = (forcedAnswer ?? answerRef.current).trim();
      if (!text) {
        setError("Please enter an answer before submitting.");
        return;
      }

      setSubmitting(true);
      setError(null);
      timer.stop();

      const timeTaken = Math.max(
        currentSession.time_per_question_seconds - timer.secondsLeft,
        1,
      );

      try {
        const response = await submitAnswer(sessionId, text, timeTaken);
        setAnswer("");

        if (response.answer_score != null && response.answer_feedback) {
          setLastFeedback({
            score: response.answer_score,
            feedback: response.answer_feedback,
            earlyTerminated: response.early_terminated,
            reason: response.termination_reason,
          });
        }

        if (
          response.is_complete ||
          response.status === "scored" ||
          response.early_terminated
        ) {
          if (response.early_terminated) {
            await new Promise((r) => setTimeout(r, 2500));
          }
          router.push(`/interview/${sessionId}/report`);
          return;
        }

        await new Promise((r) => setTimeout(r, 2000));
        setLastFeedback(null);

        const updated = await loadSession();
        timer.reset(updated.time_per_question_seconds);
      } catch (err) {
        const message =
          err instanceof ApiRequestError ? err.message : "Failed to submit answer.";
        setError(message);
        timer.reset(currentSession.time_per_question_seconds);
      } finally {
        setSubmitting(false);
      }
    },
    [sessionId, router, loadSession, timer],
  );

  const handleSubmitRef = useRef(handleSubmit);
  handleSubmitRef.current = handleSubmit;

  useEffect(() => {
    const init = async () => {
      try {
        const data = await loadSession();
        if (data.status === "scored" || data.status === "completed") {
          router.replace(`/interview/${sessionId}/report`);
          return;
        }
        if (data.current_question) {
          timer.reset(data.time_per_question_seconds);
        }
      } catch (err) {
        const message =
          err instanceof ApiRequestError ? err.message : "Failed to load interview.";
        setError(message);
      } finally {
        setLoading(false);
      }
    };
    void init();
  }, [loadSession, router, sessionId, timer]);

  useEffect(() => {
    expiredHandledRef.current = false;
    if (session?.current_question && session.time_per_question_seconds) {
      timer.reset(session.time_per_question_seconds);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session?.current_question_index]);

  useEffect(() => {
    if (!session?.current_question) return;
    if (timer.secondsLeft > 0) return;
    if (submittingRef.current || expiredHandledRef.current) return;

    expiredHandledRef.current = true;
    const text = answerRef.current.trim() || "No answer submitted — time expired.";
    void handleSubmitRef.current(text);
  }, [session?.current_question, session?.current_question_index, timer.secondsLeft]);

  const handleFormSubmit = (event: FormEvent) => {
    event.preventDefault();
    void handleSubmit();
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-900 text-white">
        <p>Preparing your interview...</p>
      </div>
    );
  }

  if (!session?.current_question) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-900 px-4 text-white">
        <div className="text-center">
          {error && <p className="mb-4 text-red-300">{error}</p>}
          <p>Generating your score report...</p>
        </div>
      </div>
    );
  }

  const questionNumber = session.current_question.question_index + 1;

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <header className="border-b border-slate-700 bg-slate-800/80 px-4 py-4">
        <div className="mx-auto flex max-w-3xl items-center justify-between">
          <div>
            <p className="text-sm text-slate-400">Hack2Hire Mock Interview</p>
            <h1 className="text-lg font-semibold">
              Question {questionNumber} of {session.total_questions}
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <DifficultyBadge
              difficulty={session.current_question.difficulty ?? session.current_difficulty}
            />
            {session.current_question.category && (
              <span className="rounded-full bg-slate-700 px-3 py-1 text-xs font-medium text-slate-300">
                {session.current_question.category}
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-8">
        {error && (
          <div className="mb-6">
            <Alert variant="error" message={error} onDismiss={() => setError(null)} />
          </div>
        )}

        <QuestionTimer
          secondsLeft={timer.secondsLeft}
          totalSeconds={session.time_per_question_seconds}
        />

        {lastFeedback && (
          <div className="mt-4 rounded-xl border border-brand-500/40 bg-brand-950/50 p-4">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-brand-200">Answer scored</p>
              <span className="text-lg font-bold text-white">
                {Math.round(lastFeedback.score)}%
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-300">{lastFeedback.feedback}</p>
            {lastFeedback.earlyTerminated && lastFeedback.reason && (
              <p className="mt-2 text-xs text-amber-300">{lastFeedback.reason}</p>
            )}
          </div>
        )}

        <div className="mt-6 rounded-xl border border-slate-700 bg-slate-800 p-6">
          <p className="text-lg leading-relaxed text-slate-100">
            {session.current_question.question_text}
          </p>
        </div>

        <form onSubmit={handleFormSubmit} className="mt-6 space-y-4">
          <div>
            <label htmlFor="answer" className="block text-sm font-medium text-slate-300">
              Your answer
            </label>
            <textarea
              id="answer"
              rows={8}
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              disabled={submitting}
              placeholder="Type your answer here..."
              className="mt-2 w-full resize-y rounded-lg border border-slate-600 bg-slate-800 px-4 py-3 text-sm text-white placeholder:text-slate-500 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 disabled:opacity-60"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-brand-600 py-3 text-sm font-semibold text-white hover:bg-brand-500 disabled:opacity-60"
          >
            {submitting
              ? "Submitting..."
              : questionNumber === session.total_questions
                ? "Submit final answer"
                : "Submit & next question"}
          </button>
        </form>
      </main>
    </div>
  );
}
