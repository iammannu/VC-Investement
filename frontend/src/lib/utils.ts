import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Recommendation } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatRelative(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export const RECOMMENDATION_CONFIG: Record<
  Recommendation,
  { label: string; color: string; bg: string; border: string }
> = {
  strong_invest: {
    label: "Strong Invest",
    color: "text-emerald-700",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
  },
  invest: {
    label: "Invest",
    color: "text-blue-700",
    bg: "bg-blue-50",
    border: "border-blue-200",
  },
  watch: {
    label: "Watch",
    color: "text-amber-700",
    bg: "bg-amber-50",
    border: "border-amber-200",
  },
  pass: {
    label: "Pass",
    color: "text-red-700",
    bg: "bg-red-50",
    border: "border-red-200",
  },
};

export const ANALYSIS_STEPS: Record<string, { label: string; order: number }> = {
  extracting_pdf: { label: "Extracting pitch deck", order: 1 },
  scraping_website: { label: "Scraping website", order: 2 },
  embedding_content: { label: "Processing & embedding content", order: 3 },
  extracting_startup_data: { label: "Extracting startup data", order: 4 },
  researching_market: { label: "Researching market size & trends", order: 5 },
  researching_competitors: { label: "Analyzing competitors", order: 6 },
  generating_memo: { label: "Generating investment memo", order: 7 },
  done: { label: "Complete", order: 8 },
};
