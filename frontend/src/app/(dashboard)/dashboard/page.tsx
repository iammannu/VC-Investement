"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Plus, FileText, TrendingUp, Clock, ArrowRight } from "lucide-react";
import { memoApi, startupApi } from "@/lib/api";
import { formatRelative, RECOMMENDATION_CONFIG } from "@/lib/utils";
import type { MemoListItem, StartupListItem, Recommendation } from "@/types";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
  const { data: memos = [], isLoading: memosLoading } = useQuery({
    queryKey: ["memos"],
    queryFn: () => memoApi.list(0, 20).then((r) => r.data),
  });

  const { data: startups = [] } = useQuery({
    queryKey: ["startups"],
    queryFn: () => startupApi.list(0, 20).then((r) => r.data),
  });

  const startupMap = Object.fromEntries(startups.map((s: StartupListItem) => [s.id, s]));

  const completedMemos = memos.filter((m: MemoListItem) => m.status === "complete");
  const processingMemos = memos.filter((m: MemoListItem) => m.status === "generating");

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Investment Memos</h1>
          <p className="text-gray-500 text-sm mt-0.5">Your AI-generated investment analyses</p>
        </div>
        <Link
          href="/upload"
          className="flex items-center gap-2 bg-slate-900 text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Memo
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {[
          { label: "Total Memos", value: memos.length, icon: FileText, color: "text-blue-600" },
          { label: "Completed", value: completedMemos.length, icon: TrendingUp, color: "text-emerald-600" },
          { label: "Processing", value: processingMemos.length, icon: Clock, color: "text-amber-600" },
        ].map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">{stat.label}</span>
              <stat.icon className={cn("w-5 h-5", stat.color)} />
            </div>
            <div className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</div>
          </div>
        ))}
      </div>

      {/* Memo list */}
      {memosLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 bg-white rounded-xl border border-gray-200 animate-pulse" />
          ))}
        </div>
      ) : memos.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="space-y-3">
          {memos.map((memo: MemoListItem) => {
            const startup = startupMap[memo.startup_id];
            return <MemoRow key={memo.id} memo={memo} startup={startup} />;
          })}
        </div>
      )}
    </div>
  );
}

function MemoRow({ memo, startup }: { memo: MemoListItem; startup?: StartupListItem }) {
  const rec = memo.recommendation
    ? RECOMMENDATION_CONFIG[memo.recommendation as Recommendation]
    : null;

  return (
    <Link href={`/memo/${memo.id}`}>
      <div className="bg-white rounded-xl border border-gray-200 p-5 hover:border-blue-300 hover:shadow-sm transition-all flex items-center justify-between group">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
            <FileText className="w-5 h-5 text-slate-500" />
          </div>
          <div>
            <div className="font-semibold text-gray-900">
              {startup?.name || "Unnamed Startup"}
            </div>
            <div className="text-sm text-gray-500 mt-0.5">
              {startup?.industry || "—"} · {startup?.stage || "—"} · {formatRelative(memo.created_at)}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Status */}
          {memo.status === "generating" && (
            <span className="flex items-center gap-1.5 text-amber-600 text-sm font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
              Processing
            </span>
          )}
          {memo.status === "failed" && (
            <span className="text-red-600 text-sm font-medium">Failed</span>
          )}

          {/* Recommendation badge */}
          {rec && memo.status === "complete" && (
            <span
              className={cn(
                "px-3 py-1 rounded-full text-xs font-semibold border",
                rec.bg,
                rec.color,
                rec.border
              )}
            >
              {rec.label}
            </span>
          )}

          {/* Confidence */}
          {memo.confidence_score && (
            <span className="text-sm text-gray-400">
              {Math.round(Number(memo.confidence_score) * 100)}% confidence
            </span>
          )}

          <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-blue-500 transition-colors" />
        </div>
      </div>
    </Link>
  );
}

function EmptyState() {
  return (
    <div className="bg-white rounded-2xl border border-dashed border-gray-300 p-16 text-center">
      <div className="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
        <FileText className="w-7 h-7 text-blue-500" />
      </div>
      <h3 className="font-semibold text-gray-900 text-lg mb-2">No memos yet</h3>
      <p className="text-gray-500 text-sm mb-6">
        Upload a pitch deck to generate your first investment memo
      </p>
      <Link
        href="/upload"
        className="inline-flex items-center gap-2 bg-slate-900 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors"
      >
        <Plus className="w-4 h-4" />
        Upload first deck
      </Link>
    </div>
  );
}
