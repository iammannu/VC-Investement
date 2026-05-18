"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import {
  Download, Edit3, RefreshCw, ChevronRight, ArrowLeft,
  ExternalLink, CheckCircle, Loader2
} from "lucide-react";
import toast from "react-hot-toast";
import { memoApi, startupApi, exportApi } from "@/lib/api";
import { cn, RECOMMENDATION_CONFIG, formatDate } from "@/lib/utils";
import type { Memo, MemoSection, Recommendation } from "@/types";

export default function MemoPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const qc = useQueryClient();
  const [activeSection, setActiveSection] = useState<string>("executive_summary");
  const [editingSection, setEditingSection] = useState<string | null>(null);
  const [editContent, setEditContent] = useState("");

  const { data: memo, isLoading } = useQuery({
    queryKey: ["memo", id],
    queryFn: () => memoApi.get(id).then((r) => r.data),
    enabled: !!id,
  });

  const { data: startup } = useQuery({
    queryKey: ["startup", memo?.startup_id],
    queryFn: () => startupApi.get(memo!.startup_id).then((r) => r.data),
    enabled: !!memo?.startup_id,
  });

  const updateMutation = useMutation({
    mutationFn: ({ key, content }: { key: string; content: string }) =>
      memoApi.updateSection(id, key, content),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["memo", id] });
      toast.success("Section saved");
      setEditingSection(null);
    },
  });

  const regenMutation = useMutation({
    mutationFn: (key: string) => memoApi.regenerateSection(id, key),
    onSuccess: () => {
      toast.success("Regeneration queued — refresh in ~30s");
    },
  });

  if (isLoading) return <MemoSkeleton />;
  if (!memo) return <div className="p-8 text-gray-500">Memo not found</div>;

  const sections = [...memo.sections].sort((a, b) => a.section_order - b.section_order);
  const currentSection = sections.find((s) => s.section_key === activeSection) || sections[0];
  const rec = memo.recommendation ? RECOMMENDATION_CONFIG[memo.recommendation as Recommendation] : null;
  const confidencePct = Math.round(Number(memo.confidence_score || 0) * 100);

  const handleExportPDF = () => {
    window.open(exportApi.pdfUrl(id), "_blank");
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="px-4 py-4 border-b border-gray-200">
          <button
            onClick={() => router.push("/dashboard")}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 mb-3"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <div className="font-semibold text-gray-900 truncate">
            {startup?.name || "Investment Memo"}
          </div>
          <div className="text-xs text-gray-400 mt-0.5">
            {startup?.industry} · {formatDate(memo.created_at)}
          </div>
        </div>

        {/* Recommendation */}
        {rec && (
          <div className={cn("mx-4 mt-3 px-3 py-2 rounded-lg border text-center", rec.bg, rec.border)}>
            <div className={cn("text-xs font-bold uppercase tracking-wide", rec.color)}>
              {rec.label}
            </div>
            <div className="text-xs text-gray-500 mt-0.5">{confidencePct}% confidence</div>
          </div>
        )}

        {/* Sections nav */}
        <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5">
          {sections.map((s) => (
            <button
              key={s.section_key}
              onClick={() => setActiveSection(s.section_key)}
              className={cn(
                "w-full text-left flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-colors",
                activeSection === s.section_key
                  ? "bg-blue-50 text-blue-700 font-medium"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              {s.is_edited && <CheckCircle className="w-3 h-3 text-emerald-500 flex-shrink-0" />}
              <span className="truncate">{s.title}</span>
            </button>
          ))}
        </nav>

        {/* Actions */}
        <div className="px-3 py-4 border-t border-gray-200 space-y-2">
          <button
            onClick={handleExportPDF}
            className="w-full flex items-center justify-center gap-2 bg-slate-900 text-white py-2 rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors"
          >
            <Download className="w-4 h-4" />
            Export PDF
          </button>
          {startup?.website_url && (
            <a
              href={startup.website_url}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full flex items-center justify-center gap-2 border border-gray-200 text-gray-600 py-2 rounded-lg text-sm hover:bg-gray-50 transition-colors"
            >
              <ExternalLink className="w-3 h-3" />
              Visit website
            </a>
          )}
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto bg-gray-50">
        {currentSection && (
          <div className="max-w-3xl mx-auto py-8 px-6">
            <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
              {/* Section header */}
              <div className="flex items-center justify-between px-8 py-5 border-b border-gray-100">
                <h2 className="text-xl font-bold text-gray-900">{currentSection.title}</h2>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      regenMutation.mutate(currentSection.section_key);
                    }}
                    disabled={regenMutation.isPending}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    {regenMutation.isPending
                      ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      : <RefreshCw className="w-3.5 h-3.5" />}
                    Regenerate
                  </button>
                  <button
                    onClick={() => {
                      setEditContent(currentSection.content || "");
                      setEditingSection(currentSection.section_key);
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                    Edit
                  </button>
                </div>
              </div>

              {/* Section content */}
              <div className="px-8 py-6">
                {editingSection === currentSection.section_key ? (
                  <div className="space-y-3">
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      rows={20}
                      className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={() =>
                          updateMutation.mutate({
                            key: currentSection.section_key,
                            content: editContent,
                          })
                        }
                        disabled={updateMutation.isPending}
                        className="flex items-center gap-1.5 px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium"
                      >
                        {updateMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                        Save
                      </button>
                      <button
                        onClick={() => setEditingSection(null)}
                        className="px-4 py-2 border border-gray-200 text-gray-600 rounded-lg text-sm"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-li:text-gray-700">
                    <ReactMarkdown>
                      {currentSection.content || "*No content generated*"}
                    </ReactMarkdown>
                  </div>
                )}
              </div>

              {/* Citations */}
              {currentSection.citations && currentSection.citations.length > 0 && (
                <div className="px-8 py-4 bg-gray-50 border-t border-gray-100">
                  <div className="text-xs text-gray-500 font-medium mb-2">Sources</div>
                  <div className="space-y-1">
                    {currentSection.citations.map((c, i) => (
                      <a
                        key={i}
                        href={c.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1.5 text-xs text-blue-600 hover:underline"
                      >
                        <ExternalLink className="w-3 h-3" />
                        {c.url}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Next section nav */}
            {sections.indexOf(currentSection) < sections.length - 1 && (
              <button
                onClick={() => {
                  const next = sections[sections.indexOf(currentSection) + 1];
                  setActiveSection(next.section_key);
                }}
                className="mt-4 w-full flex items-center justify-center gap-2 py-3 text-sm text-gray-500 hover:text-gray-900 transition-colors"
              >
                Next: {sections[sections.indexOf(currentSection) + 1]?.title}
                <ChevronRight className="w-4 h-4" />
              </button>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

function MemoSkeleton() {
  return (
    <div className="flex h-screen">
      <aside className="w-64 bg-white border-r border-gray-200">
        <div className="p-4 space-y-3">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-8 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      </aside>
      <main className="flex-1 p-8">
        <div className="max-w-3xl mx-auto bg-white rounded-2xl border border-gray-200 p-8 space-y-4">
          <div className="h-8 bg-gray-100 rounded animate-pulse w-1/3" />
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-4 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      </main>
    </div>
  );
}
