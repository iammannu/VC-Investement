"use client";
import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, Globe, X, Loader2, Zap } from "lucide-react";
import toast from "react-hot-toast";
import { cn } from "@/lib/utils";
import { uploadApi, analysisApi } from "@/lib/api";

type UploadState = "idle" | "uploading" | "starting_analysis" | "redirecting";

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [state, setState] = useState<UploadState>("idle");

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
    onDropRejected: (r) => {
      const err = r[0]?.errors[0];
      if (err?.code === "file-too-large") toast.error("File must be under 50MB");
      else if (err?.code === "file-invalid-type") toast.error("Please upload a PDF file");
      else toast.error("Invalid file");
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) { toast.error("Please upload a pitch deck PDF"); return; }

    setState("uploading");
    try {
      const { data: startup } = await uploadApi.uploadDeck(file, websiteUrl || undefined);
      toast.success("Deck uploaded successfully");

      setState("starting_analysis");
      const { data: job } = await analysisApi.start(startup.id);
      toast.success("Analysis started — this takes 2-4 minutes");

      setState("redirecting");
      router.push(`/analysis/${job.job_id}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail || "Upload failed";
      toast.error(msg);
      setState("idle");
    }
  };

  const isLoading = state !== "idle";

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">New Investment Memo</h1>
        <p className="text-gray-500 text-sm mt-1">
          Upload a pitch deck and we&apos;ll generate a professional investment memo in ~3 minutes
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* PDF Upload Zone */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Pitch Deck (PDF) <span className="text-red-500">*</span>
          </label>
          {file ? (
            <div className="flex items-center gap-3 p-4 bg-blue-50 border border-blue-200 rounded-xl">
              <FileText className="w-8 h-8 text-blue-500 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="font-medium text-gray-900 truncate">{file.name}</div>
                <div className="text-sm text-gray-500">
                  {(file.size / 1024 / 1024).toFixed(1)} MB
                </div>
              </div>
              <button
                type="button"
                onClick={() => setFile(null)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          ) : (
            <div
              {...getRootProps()}
              className={cn(
                "border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors",
                isDragActive
                  ? "border-blue-400 bg-blue-50"
                  : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"
              )}
            >
              <input {...getInputProps()} />
              <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-700 font-medium">Drop your pitch deck here</p>
              <p className="text-sm text-gray-400 mt-1">or click to browse · PDF up to 50MB</p>
            </div>
          )}
        </div>

        {/* Website URL */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Globe className="w-4 h-4 inline mr-1.5 text-gray-400" />
            Startup Website
            <span className="text-gray-400 font-normal ml-1">(optional, improves memo quality)</span>
          </label>
          <input
            type="url"
            value={websiteUrl}
            onChange={(e) => setWebsiteUrl(e.target.value)}
            placeholder="https://startup.com"
            className="w-full px-3.5 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
          />
        </div>

        {/* What will be generated */}
        <div className="bg-gray-50 rounded-xl p-5 border border-gray-200">
          <div className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
            <Zap className="w-4 h-4 text-blue-500" />
            What we&apos;ll generate
          </div>
          <div className="grid grid-cols-2 gap-2">
            {[
              "Executive Summary",
              "Market Analysis (TAM/SAM/SOM)",
              "Competitor Analysis",
              "Founder Profiles",
              "Risk Analysis",
              "Investment Recommendation",
            ].map((item) => (
              <div key={item} className="flex items-center gap-2 text-sm text-gray-600">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                {item}
              </div>
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={isLoading || !file}
          className="w-full flex items-center justify-center gap-2 bg-slate-900 text-white py-3 rounded-xl font-semibold hover:bg-slate-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              {state === "uploading" ? "Uploading deck..." : "Starting analysis..."}
            </>
          ) : (
            <>
              <Zap className="w-4 h-4" />
              Generate Investment Memo
            </>
          )}
        </button>
        <p className="text-center text-xs text-gray-400">
          Takes ~3 minutes · Cites all sources · Edit any section
        </p>
      </form>
    </div>
  );
}
