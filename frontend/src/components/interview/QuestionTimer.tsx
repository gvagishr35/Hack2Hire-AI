"use client";

import { formatTimer } from "@/hooks/useTimer";

type QuestionTimerProps = {
  secondsLeft: number;
  totalSeconds: number;
};

export function QuestionTimer({ secondsLeft, totalSeconds }: QuestionTimerProps) {
  const progress = totalSeconds > 0 ? (secondsLeft / totalSeconds) * 100 : 0;
  const isLow = secondsLeft <= 30;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-slate-700">Time remaining</span>
        <span
          className={`font-mono text-lg font-bold ${
            isLow ? "text-red-600" : "text-brand-700"
          }`}
        >
          {formatTimer(secondsLeft)}
        </span>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full transition-all duration-1000 ${
            isLow ? "bg-red-500" : "bg-brand-600"
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
