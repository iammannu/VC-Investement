import Link from "next/link";
import { ArrowRight, Zap, Shield, BarChart3, FileText } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-5 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-navy-900 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-gray-900 text-lg">MemoAI</span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/login" className="text-gray-600 hover:text-gray-900 text-sm font-medium">
            Sign in
          </Link>
          <Link
            href="/register"
            className="bg-slate-900 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors"
          >
            Get started free
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-5xl mx-auto px-8 py-24 text-center">
        <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 px-4 py-1.5 rounded-full text-sm font-medium mb-8">
          <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          Built for VC firms & family offices
        </div>
        <h1 className="text-6xl font-bold text-gray-900 leading-tight mb-6">
          Investment memos in{" "}
          <span className="text-blue-600">3 minutes</span>
          <br />not 3 days
        </h1>
        <p className="text-xl text-gray-500 max-w-2xl mx-auto mb-10">
          Upload a pitch deck and startup website. Our AI generates a professional
          15-page investment memo with market research, competitor analysis,
          founder profiles, and a clear recommendation.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link
            href="/register"
            className="flex items-center gap-2 bg-slate-900 text-white px-6 py-3.5 rounded-xl font-semibold hover:bg-slate-800 transition-colors"
          >
            Generate your first memo free
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/login"
            className="text-gray-600 hover:text-gray-900 font-medium px-6 py-3.5"
          >
            Sign in →
          </Link>
        </div>

        {/* Social proof */}
        <p className="text-sm text-gray-400 mt-8">
          Used by analysts at VC firms across UAE, KSA & Europe
        </p>
      </section>

      {/* Features */}
      <section className="bg-gray-50 py-24">
        <div className="max-w-5xl mx-auto px-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-4">
            Everything an analyst does, in minutes
          </h2>
          <p className="text-center text-gray-500 mb-16">
            Stop spending 4 hours on first-pass analysis. Focus on decisions.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              {
                icon: FileText,
                title: "PDF Intelligence",
                desc: "Extracts text, tables, and metrics from any pitch deck — even scanned PDFs via OCR",
              },
              {
                icon: BarChart3,
                title: "Market Research",
                desc: "Auto-generates TAM/SAM/SOM estimates with sources, competitive dynamics, and market timing",
              },
              {
                icon: Shield,
                title: "Risk Analysis",
                desc: "Identifies market, execution, regulatory, and competitive risks with mitigation notes",
              },
              {
                icon: Zap,
                title: "Clear Recommendation",
                desc: "Strong Invest / Invest / Watch / Pass with confidence score and investment thesis",
              },
            ].map((f) => (
              <div key={f.title} className="bg-white rounded-2xl p-8 border border-gray-100">
                <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center mb-4">
                  <f.icon className="w-5 h-5 text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{f.title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 text-center">
        <div className="max-w-2xl mx-auto px-8">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Ready to 10x your deal analysis?
          </h2>
          <p className="text-gray-500 mb-8">
            Free trial includes 3 full investment memos. No credit card required.
          </p>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 bg-slate-900 text-white px-8 py-4 rounded-xl font-semibold hover:bg-slate-800 transition-colors text-lg"
          >
            Start for free
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      <footer className="border-t border-gray-100 py-8 text-center text-sm text-gray-400">
        © 2025 MemoAI. Built for investors.
      </footer>
    </div>
  );
}
