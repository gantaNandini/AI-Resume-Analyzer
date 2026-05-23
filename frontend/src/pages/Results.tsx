import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useRef } from "react";
import toast from "react-hot-toast";
import AnimatedPage from "@/components/AnimatedPage";
import { Button, Badge, Spinner } from "@/components/ui";
import apiClient from "@/lib/apiClient";
import jsPDF from "jspdf";

// ─── Types ────────────────────────────────────────────────────────────────────

interface AnalysisResult {
  job_id: string;
  ats_score: number;
  band: "Poor" | "Fair" | "Strong";
  hybrid_similarity: number;
  section_scores: Record<string, number>;
  skill_gap: { required_missing: string[]; preferred_missing: string[]; full_coverage: boolean };
  suggestions: { suggestions: { title: string; explanation: string; example: string }[]; available: boolean; error?: string };
  keyword_density: number;
  skill_coverage: number;
  created_at?: string;
}

// ─── ATS Gauge ────────────────────────────────────────────────────────────────

function ATSGauge({ score, band }: { score: number; band: string }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const bandColors: Record<string, { stroke: string; text: string; bg: string }> = {
    Poor: { stroke: "#ef4444", text: "text-red-400", bg: "bg-red-500/10 border-red-500/20" },
    Fair: { stroke: "#f59e0b", text: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
    Strong: { stroke: "#10b981", text: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  };
  const colors = bandColors[band] ?? bandColors.Poor;

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative w-40 h-40">
        <svg className="w-40 h-40 -rotate-90" viewBox="0 0 128 128">
          <circle cx="64" cy="64" r={radius} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
          <motion.circle
            cx="64" cy="64" r={radius}
            fill="none"
            stroke={colors.stroke}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: circumference * (1 - score / 100) }}
            transition={{ duration: 1.5, ease: "easeOut", delay: 0.3 }}
            style={{ filter: `drop-shadow(0 0 8px ${colors.stroke}60)` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            className={`text-4xl font-bold ${colors.text}`}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5, duration: 0.4 }}
          >
            {score}
          </motion.span>
          <span className="text-xs text-slate-500 mt-0.5">/ 100</span>
        </div>
      </div>
      <div className={`px-4 py-1.5 rounded-full border text-sm font-semibold ${colors.bg} ${colors.text}`}>
        {band} ATS Match
      </div>
    </div>
  );
}

// ─── Suggestion Card ──────────────────────────────────────────────────────────

function SuggestionCard({ title, explanation, example, index }: { title: string; explanation: string; example: string; index: number }) {
  const [open, setOpen] = useState(false);
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.07 }}
      className="glass rounded-2xl overflow-hidden"
    >
      <button
        className="w-full flex items-center justify-between gap-3 p-4 text-left hover:bg-white/[0.03] transition-colors"
        onClick={() => setOpen(v => !v)}
        aria-expanded={open}
      >
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-primary-500/20 flex items-center justify-center text-primary-400 text-xs font-bold shrink-0">
            {index + 1}
          </div>
          <span className="text-sm font-medium text-slate-200">{title}</span>
        </div>
        <motion.svg
          className="w-4 h-4 text-slate-400 shrink-0"
          viewBox="0 0 16 16" fill="currentColor"
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <path d="M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z" />
        </motion.svg>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-3 border-t border-white/5 pt-3">
              <p className="text-sm text-slate-300">{explanation}</p>
              <div className="p-3 rounded-xl bg-primary-500/5 border border-primary-500/15">
                <p className="text-xs text-slate-400 mb-1 font-medium uppercase tracking-wide">Example</p>
                <p className="text-sm text-slate-300">{example}</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ─── Skill Gap Panel ──────────────────────────────────────────────────────────

function SkillGapPanel({ skillGap }: { skillGap: AnalysisResult["skill_gap"] }) {
  if (skillGap.full_coverage) {
    return (
      <div className="flex items-center gap-2 p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
        <svg className="w-5 h-5 text-emerald-400" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
        <span className="text-emerald-400 font-medium text-sm">Full skill coverage — your resume matches all required skills!</span>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div>
        <p className="text-xs font-semibold text-red-400 uppercase tracking-wide mb-2">Required Missing ({skillGap.required_missing.length})</p>
        <div className="flex flex-wrap gap-2">
          {skillGap.required_missing.length === 0
            ? <span className="text-xs text-slate-500">None</span>
            : skillGap.required_missing.map(s => (
              <span key={s} className="px-2.5 py-1 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium">{s}</span>
            ))}
        </div>
      </div>
      <div>
        <p className="text-xs font-semibold text-amber-400 uppercase tracking-wide mb-2">Preferred Missing ({skillGap.preferred_missing.length})</p>
        <div className="flex flex-wrap gap-2">
          {skillGap.preferred_missing.length === 0
            ? <span className="text-xs text-slate-500">None</span>
            : skillGap.preferred_missing.map(s => (
              <span key={s} className="px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-medium">{s}</span>
            ))}
        </div>
      </div>
    </div>
  );
}

// ─── Score Bar ────────────────────────────────────────────────────────────────

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-300 font-medium">{pct}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-primary-500 to-violet-500"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, ease: "easeOut", delay: 0.4 }}
        />
      </div>
    </div>
  );
}

// ─── Results Page ─────────────────────────────────────────────────────────────

export default function Results() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const resultRef = useRef<HTMLDivElement>(null);

  const { data, isLoading, error } = useQuery<AnalysisResult>({
    queryKey: ["result", jobId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/files/jobs/${jobId}/result`);
      return data;
    },
    enabled: !!jobId,
    retry: 2,
  });

  const downloadPDF = () => {
    if (!data) return;
    const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
    const margin = 20;
    let y = margin;

    doc.setFontSize(20);
    doc.setTextColor(99, 102, 241);
    doc.text("Resume Analysis Report", margin, y);
    y += 10;

    doc.setFontSize(11);
    doc.setTextColor(100, 100, 100);
    doc.text(`Generated: ${new Date().toLocaleDateString()}`, margin, y);
    y += 12;

    doc.setFontSize(14);
    doc.setTextColor(30, 30, 30);
    doc.text(`ATS Score: ${data.ats_score}/100 (${data.band})`, margin, y);
    y += 8;
    doc.text(`Hybrid Similarity: ${Math.round(data.hybrid_similarity * 100)}%`, margin, y);
    y += 8;
    doc.text(`Keyword Density: ${Math.round(data.keyword_density * 100)}%`, margin, y);
    y += 8;
    doc.text(`Skill Coverage: ${Math.round(data.skill_coverage * 100)}%`, margin, y);
    y += 12;

    doc.setFontSize(13);
    doc.setTextColor(99, 102, 241);
    doc.text("Skill Gap", margin, y);
    y += 7;
    doc.setFontSize(11);
    doc.setTextColor(50, 50, 50);
    if (data.skill_gap.full_coverage) {
      doc.text("Full coverage — all required skills present.", margin, y);
      y += 7;
    } else {
      doc.text(`Required missing: ${data.skill_gap.required_missing.join(", ") || "None"}`, margin, y);
      y += 7;
      doc.text(`Preferred missing: ${data.skill_gap.preferred_missing.join(", ") || "None"}`, margin, y);
      y += 7;
    }
    y += 5;

    if (data.suggestions.available && data.suggestions.suggestions.length > 0) {
      doc.setFontSize(13);
      doc.setTextColor(99, 102, 241);
      doc.text("AI Improvement Suggestions", margin, y);
      y += 7;
      data.suggestions.suggestions.forEach((s, i) => {
        if (y > 260) { doc.addPage(); y = margin; }
        doc.setFontSize(11);
        doc.setTextColor(30, 30, 30);
        doc.text(`${i + 1}. ${s.title}`, margin, y);
        y += 6;
        doc.setFontSize(10);
        doc.setTextColor(80, 80, 80);
        const lines = doc.splitTextToSize(s.explanation, 170);
        doc.text(lines, margin, y);
        y += lines.length * 5 + 3;
        const exLines = doc.splitTextToSize(`Example: ${s.example}`, 170);
        doc.text(exLines, margin, y);
        y += exLines.length * 5 + 5;
      });
    }

    doc.save(`resume-analysis-${jobId?.slice(0, 8)}.pdf`);
    toast.success("Report downloaded!");
  };

  if (isLoading) {
    return (
      <AnimatedPage className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="text-center">
          <Spinner size="lg" className="text-primary-400 mx-auto mb-4" />
          <p className="text-slate-400">Loading your results…</p>
        </div>
      </AnimatedPage>
    );
  }

  if (error || !data) {
    return (
      <AnimatedPage className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="text-center glass rounded-3xl p-10 max-w-md">
          <p className="text-red-400 text-lg font-semibold mb-2">Results not found</p>
          <p className="text-slate-400 text-sm mb-6">The analysis may still be processing or an error occurred.</p>
          <Button variant="primary" onClick={() => navigate("/upload")}>Try Again</Button>
        </div>
      </AnimatedPage>
    );
  }

  return (
    <AnimatedPage className="min-h-screen bg-dark-950 pb-16">
      {/* Background */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute w-96 h-96 rounded-full bg-primary-600/8 blur-3xl top-0 right-0" />
        <div className="absolute w-80 h-80 rounded-full bg-violet-600/8 blur-3xl bottom-0 left-0" />
      </div>

      <div className="relative max-w-4xl mx-auto px-4 py-10" ref={resultRef}>
        {/* Header */}
        <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold gradient-text">Analysis Results</h1>
            <p className="text-slate-400 text-sm mt-1">Your resume has been analyzed against the job description</p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" size="sm" onClick={() => navigate("/upload")}>New Analysis</Button>
            <Button variant="primary" size="sm" onClick={downloadPDF}>
              <svg className="w-4 h-4 mr-1.5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
              Download Report
            </Button>
          </div>
        </div>

        {/* Top row: ATS gauge + score breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <motion.div className="glass rounded-3xl p-8 flex flex-col items-center justify-center" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <ATSGauge score={data.ats_score} band={data.band} />
          </motion.div>

          <motion.div className="glass rounded-3xl p-6 flex flex-col justify-center gap-4" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">Score Breakdown</h2>
            <ScoreBar label="Hybrid Similarity" value={data.hybrid_similarity} />
            <ScoreBar label="Keyword Density" value={data.keyword_density} />
            <ScoreBar label="Skill Coverage" value={data.skill_coverage} />
            {Object.entries(data.section_scores).slice(0, 3).map(([k, v]) => (
              <ScoreBar key={k} label={`${k.charAt(0).toUpperCase() + k.slice(1)} Section`} value={v} />
            ))}
          </motion.div>
        </div>

        {/* Skill Gap */}
        <motion.div className="glass rounded-3xl p-6 mb-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-4">Skill Gap Analysis</h2>
          <SkillGapPanel skillGap={data.skill_gap} />
        </motion.div>

        {/* AI Suggestions */}
        <motion.div className="glass rounded-3xl p-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">AI Improvement Suggestions</h2>
            {data.suggestions.available && (
              <Badge variant="info">{data.suggestions.suggestions.length} suggestions</Badge>
            )}
          </div>

          {!data.suggestions.available ? (
            <div className="flex items-center gap-3 p-4 rounded-xl bg-amber-500/5 border border-amber-500/15">
              <svg className="w-4 h-4 text-amber-400 shrink-0" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm0 3.5a.75.75 0 0 1 .75.75v3a.75.75 0 0 1-1.5 0v-3A.75.75 0 0 1 8 4.5zm0 6.5a.875.875 0 1 1 0-1.75A.875.875 0 0 1 8 11z" />
              </svg>
              <p className="text-sm text-amber-400">AI suggestions are temporarily unavailable. Your ATS score and skill gap analysis are still accurate.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {data.suggestions.suggestions.map((s, i) => (
                <SuggestionCard key={i} index={i} title={s.title} explanation={s.explanation} example={s.example} />
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </AnimatedPage>
  );
}
