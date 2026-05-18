"use client";
import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { CheckCircle2, Circle, Loader2, XCircle, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { analysisApi } from "@/lib/api";
import { ANALYSIS_STEPS } from "@/lib/utils";
import type { JobStreamEvent } from "@/types";

export default function AnalysisPage() {
  const router = useRouter();
  const { jobId } = useParams<{ jobId: string }>();
  const [event, setEvent] = useState<JobStreamEvent | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token") || "";
    const url = `${analysisApi.streamUrl(jobId)}?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);

    es.onmessage = (e) => {
      const data: JobStreamEvent = JSON.parse(e.data);
      setEvent(data);

      if (data.error) {
        setError(data.error);
        es.close();
        return;
      }
      if (data.current_step === "done" && data.memo_id) {
        es.close();
        router.push(`/memo/${data.memo_id}`);
      }
    };

    es.onerror = () => {
      setError("Connection lost. Please refresh.");
      es.close();
    };

    return () => es.close();
  }, [jobId, router]);

  const steps = Object.entries(ANALYSIS_STEPS).filter(([k]) => k !== "done");
  const completedSet = new Set(event?.steps_completed || []);
  const currentStep = event?.current_step || "queued";

  const progress = event
    ? Math.round((event.steps_completed.length / event.total_steps) * 100)
    : 0;

  return (
    <div className="p-8 max-w-xl mx-auto">
      <div className="text-center mb-10">
        <div className="inline-flex w-14 h-14 rounded-2xl bg-blue-50 items-center justify-center mb-4">
          <Zap className="w-7 h-7 text-blue-500" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Generating Investment Memo</h1>
        <p className="text-gray-500 text-sm mt-1">This usually takes 2–4 minutes</p>
      </div>

      {error ? (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <XCircle className="w-8 h-8 text-red-500 mx-auto mb-3" />
          <div className="font-medium text-red-700">{error}</div>
        </div>
      ) : (
        <>
          {/* Progress bar */}
          <div className="mb-8">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-gray-600 font-medium">
                {ANALYSIS_STEPS[currentStep]?.label || "Starting..."}
              </span>
              <span className="text-gray-400">{progress}%</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-700"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Steps */}
          <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
            {steps.map(([key, step], i) => {
              const isDone = completedSet.has(key);
              const isActive = currentStep === key;
              const isPending = !isDone && !isActive;

              return (
                <div
                  key={key}
                  className={cn(
                    "flex items-center gap-4 px-5 py-4 border-b border-gray-100 last:border-0",
                    isActive && "bg-blue-50"
                  )}
                >
                  <div className="flex-shrink-0">
                    {isDone ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                    ) : isActive ? (
                      <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                    ) : (
                      <Circle className="w-5 h-5 text-gray-200" />
                    )}
                  </div>
                  <span
                    className={cn(
                      "text-sm font-medium",
                      isDone ? "text-gray-700" : isActive ? "text-blue-700" : "text-gray-400"
                    )}
                  >
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>

          <p className="text-center text-xs text-gray-400 mt-6">
            You can safely close this tab — we&apos;ll save your memo when done
          </p>
        </>
      )}
    </div>
  );
}
