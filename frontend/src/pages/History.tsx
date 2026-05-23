import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import AnimatedPage from "@/components/AnimatedPage";
import { Button, Badge, Spinner } from "@/components/ui";
import apiClient from "@/lib/apiClient";

interface JobListItem {
  job_id: string;
  status: string;
  resume_filename: string;
  jd_filename: string;
  created_at: string;
  ats_score: number | null;
  band: string | null;
}

interface JobListResponse {
  jobs: JobListItem[];
  total: number;
  page: number;
  page_size: number;
}

const bandVariant: Record<string, "success" | "warning" | "error" | "info"> = {
  Strong: "success",
  Fair: "warning",
  Poor: "error",
};

export default function History() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const { data, isLoading, error } = useQuery<JobListResponse>({
    queryKey: ["jobs", page],
    queryFn: async () => {
      const { data } = await apiClient.get(`/files/jobs?page=${page}&page_size=${pageSize}`);
      return data;
    },
  });

  const totalPages = data ? Math.ceil(data.total / pageSize) : 1;

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });

  return (
    <AnimatedPage className="min-h-screen bg-dark-950 pb-16">
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute w-96 h-96 rounded-full bg-violet-600/8 blur-3xl top-0 left-0" />
      </div>

      <div className="relative max-w-4xl mx-auto px-4 py-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold gradient-text">Analysis History</h1>
            <p className="text-slate-400 text-sm mt-1">All your previous resume analyses</p>
          </div>
          <Button variant="primary" size="sm" onClick={() => navigate("/upload")}>
            <svg className="w-4 h-4 mr-1.5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            New Analysis
          </Button>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Spinner size="lg" className="text-primary-400" />
          </div>
        ) : error ? (
          <div className="glass rounded-3xl p-10 text-center">
            <p className="text-red-400 mb-4">Failed to load history</p>
            <Button variant="outline" onClick={() => window.location.reload()}>Retry</Button>
          </div>
        ) : !data || data.jobs.length === 0 ? (
          <div className="glass rounded-3xl p-16 text-center">
            <div className="text-5xl mb-4">📋</div>
            <h2 className="text-lg font-semibold text-slate-200 mb-2">No analyses yet</h2>
            <p className="text-slate-400 text-sm mb-6">Upload your resume and a job description to get started</p>
            <Button variant="primary" onClick={() => navigate("/upload")}>Analyze My Resume</Button>
          </div>
        ) : (
          <>
            <div className="space-y-3">
              {data.jobs.map((job, i) => (
                <motion.div
                  key={job.job_id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="glass rounded-2xl p-5 hover:border-primary-500/20 transition-colors"
                >
                  <div className="flex items-center justify-between gap-4 flex-wrap">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="text-sm font-medium text-slate-200 truncate max-w-xs">{job.resume_filename}</span>
                        <svg className="w-3 h-3 text-slate-500 shrink-0" viewBox="0 0 16 16" fill="currentColor">
                          <path fillRule="evenodd" d="M4 8a.5.5 0 0 1 .5-.5h5.793L8.146 5.354a.5.5 0 1 1 .708-.708l3 3a.5.5 0 0 1 0 .708l-3 3a.5.5 0 0 1-.708-.708L10.293 8.5H4.5A.5.5 0 0 1 4 8z" clipRule="evenodd" />
                        </svg>
                        <span className="text-sm text-slate-400 truncate max-w-xs">{job.jd_filename}</span>
                      </div>
                      <p className="text-xs text-slate-500">{formatDate(job.created_at)}</p>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      {job.ats_score !== null && job.band ? (
                        <>
                          <div className="text-right">
                            <p className="text-lg font-bold text-slate-100">{job.ats_score}</p>
                            <p className="text-xs text-slate-500">ATS Score</p>
                          </div>
                          <Badge variant={bandVariant[job.band] ?? "info"}>{job.band}</Badge>
                        </>
                      ) : (
                        <Badge variant="info">{job.status}</Badge>
                      )}

                      {job.status === "completed" && (
                        <Link to={`/results/${job.job_id}`}>
                          <Button variant="outline" size="sm">View</Button>
                        </Link>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-3 mt-8">
                <Button variant="secondary" size="sm" disabled={page === 1} onClick={() => setPage(p => p - 1)}>
                  ← Previous
                </Button>
                <span className="text-sm text-slate-400">Page {page} of {totalPages}</span>
                <Button variant="secondary" size="sm" disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>
                  Next →
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </AnimatedPage>
  );
}
