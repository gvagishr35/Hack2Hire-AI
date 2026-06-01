"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { InterviewAnalytics } from "@/lib/api";

const CHART_COLORS = ["#4f46e5", "#06b6d4", "#10b981", "#f59e0b"];

type PerformanceChartsProps = {
  analytics: InterviewAnalytics;
};

export function PerformanceCharts({ analytics }: PerformanceChartsProps) {
  const trendData = analytics.score_trend.map((item, index) => ({
    name: `Interview ${index + 1}`,
    overall: item.overall_score ?? 0,
    readiness: item.readiness_score ?? 0,
  }));

  const performanceData = Object.entries(analytics.performance_averages).map(
    ([key, value]) => ({
      name: formatLabel(key),
      score: Math.round(value),
    }),
  );

  const radarData = Object.entries(analytics.performance_averages).map(
    ([key, value]) => ({
      subject: formatLabel(key),
      score: Math.round(value),
      fullMark: 100,
    }),
  );

  if (analytics.completed_interviews === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
        Complete your first interview to see performance charts and trends.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Interviews"
          value={String(analytics.completed_interviews)}
          sub={`of ${analytics.total_interviews} total`}
        />
        <MetricCard
          label="Avg. Score"
          value={
            analytics.average_overall_score != null
              ? `${Math.round(analytics.average_overall_score)}%`
              : "—"
          }
        />
        <MetricCard
          label="Readiness"
          value={
            analytics.average_readiness_score != null
              ? `${Math.round(analytics.average_readiness_score)}%`
              : "—"
          }
        />
        <MetricCard
          label="Latest Grade"
          value={analytics.recent_scores[0]?.grade ?? "—"}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {trendData.length > 0 && (
          <ChartCard title="Score trend">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="overall"
                  stroke="#4f46e5"
                  strokeWidth={2}
                  name="Overall"
                />
                <Line
                  type="monotone"
                  dataKey="readiness"
                  stroke="#06b6d4"
                  strokeWidth={2}
                  name="Readiness"
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        )}

        {performanceData.length > 0 && (
          <ChartCard title="Performance breakdown">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="score" radius={[6, 6, 0, 0]}>
                  {performanceData.map((_, index) => (
                    <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        )}
      </div>

      {radarData.length > 0 && (
        <ChartCard title="Skills radar">
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
              <Radar
                name="Score"
                dataKey="score"
                stroke="#4f46e5"
                fill="#4f46e5"
                fillOpacity={0.35}
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </ChartCard>
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-slate-500">{sub}</p>}
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-slate-900">{title}</h3>
      {children}
    </div>
  );
}

function formatLabel(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
