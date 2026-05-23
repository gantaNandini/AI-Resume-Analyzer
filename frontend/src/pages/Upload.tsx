import { useState, useCallback, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useDropzone, type FileRejection } from "react-dropzone";
import toast from "react-hot-toast";
import AnimatedPage from "@/components/AnimatedPage";
import { Button, Spinner } from "@/components/ui";
import apiClient from "@/lib/apiClient";

// ─── JD Validation ────────────────────────────────────────────────────────────

/**
 * Returns an error string if the JD text is not a real job description,
 * or null if it looks valid.
 *
 * Checks:
 *  1. At least 30 words
 *  2. At least 60% of words look like real English words (only letters, 2+ chars)
 */
function validateJdText(text: string): string | null {
  const words = text.trim().split(/\s+/).filter(Boolean);
  if (words.length < 30) {
    return `Job description is too short (${words.length} words). Please paste a real job description with at least 30 words.`;
  }
  const realWords = words.filter((w) => /^[a-zA-Z]{2,}$/.test(w));
  const ratio = realWords.length / words.length;
  if (ratio < 0.6) {
    return "This doesn't look like a valid job description. Please paste actual job description text.";
  }
  return null;
}

// ─── JD Text Input ─────────────────────────────────────────────────────────────

interface JdInputProps {
  jdFile: File | null;
  onFileChange: (file: File | null) => void;
}

function JdInput({ jdFile, onFileChange }: JdInputProps) {
  const [mode, setMode] = useState<"paste" | "file">("paste");
  const [text, setText] = useState("");
  const [fileError, setFileError] = useState<string | null>(null);
  const [textError, setTextError] = useState<string | null>(null);

  // When switching to paste mode, clear any uploaded file
  const switchMode = (next: "paste" | "file") => {
    setMode(next);
    onFileChange(null);
    setText("");
    setFileError(null);
    setTextError(null);
  };

  // Convert textarea text → File blob so the rest of the submit logic is unchanged
  const handleTextChange = (value: string) => {
    setText(value);
    setTextError(null);
    if (value.trim()) {
      const err = validateJdText(value);
      if (err) {
        setTextError(err);
        onFileChange(null); // block submission
      } else {
        const blob = new Blob([value], { type: "text/plain" });
        onFileChange(new File([blob], "job_description.txt", { type: "text/plain" }));
      }
    } else {
      onFileChange(null);
    }
  };

  const handleDrop = useCallback(
    (accepted: File[], rejected: FileRejection[]) => {
      setFileError(null);
      if (rejected.length > 0) {
        const msg = rejected[0].errors[0]?.message ?? "Invalid file";
        setFileError(msg.includes("size") ? "File too large (max 2 MB)" : "Unsupported file type");
        return;
      }
      if (accepted[0]) onFileChange(accepted[0]);
    },
    [onFileChange]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
    maxSize: 2 * 1024 * 1024,
    multiple: false,
  });

  const formatSize = (bytes: number) =>
    bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-slate-300">Job Description</label>
        {/* Mode toggle */}
        <div className="flex items-center gap-0.5 p-0.5 rounded-lg bg-white/5 border border-white/10">
          {(["paste", "file"] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => switchMode(m)}
              className={[
                "px-3 py-1 rounded-md text-xs font-medium transition-all duration-150",
                mode === m
                  ? "bg-primary-600 text-white shadow"
                  : "text-slate-400 hover:text-slate-200",
              ].join(" ")}
            >
              {m === "paste" ? "✏️ Paste text" : "📎 Upload file"}
            </button>
          ))}
        </div>
      </div>

      <AnimatePresence mode="wait">
        {mode === "paste" ? (
          <motion.div
            key="paste"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.15 }}
          >
            <textarea
              value={text}
              onChange={(e) => handleTextChange(e.target.value)}
              placeholder="Paste the job description here…"
              rows={8}
              className={[
                "w-full rounded-2xl bg-white/[0.03] border px-4 py-3 text-sm text-slate-200 placeholder-slate-500",
                "resize-none focus:outline-none focus:ring-2 focus:ring-primary-500/50 transition-colors",
                text.trim() ? "border-primary-500/30" : "border-white/10 hover:border-white/20",
              ].join(" ")}
            />
            <div className="flex justify-between mt-1">
              <span className="text-xs text-slate-600">
                {text.trim() ? `${text.trim().split(/\s+/).length} words` : "Minimum 30 words required"}
              </span>
              {text.trim() && (
                <button
                  type="button"
                  onClick={() => handleTextChange("")}
                  className="text-xs text-slate-500 hover:text-red-400 transition-colors"
                >
                  Clear
                </button>
              )}
            </div>
            <AnimatePresence>
              {textError && (
                <motion.p
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="text-xs text-red-400 flex items-start gap-1.5 mt-1"
                  role="alert"
                >
                  <svg className="w-3.5 h-3.5 shrink-0 mt-0.5" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm0 3.5a.75.75 0 0 1 .75.75v3a.75.75 0 0 1-1.5 0v-3A.75.75 0 0 1 8 4.5zm0 6.5a.875.875 0 1 1 0-1.75A.875.875 0 0 1 8 11z" />
                  </svg>
                  {textError}
                </motion.p>
              )}
            </AnimatePresence>
          </motion.div>
        ) : (
          <motion.div
            key="file"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.15 }}
          >
            {jdFile ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex items-center gap-3 p-4 rounded-2xl bg-primary-500/10 border border-primary-500/30"
              >
                <div className="w-10 h-10 rounded-xl bg-primary-500/20 flex items-center justify-center text-xl shrink-0">
                  💼
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-200 truncate">{jdFile.name}</p>
                  <p className="text-xs text-slate-400">{formatSize(jdFile.size)}</p>
                </div>
                <button
                  type="button"
                  onClick={() => onFileChange(null)}
                  className="w-7 h-7 rounded-lg bg-white/5 hover:bg-red-500/20 flex items-center justify-center text-slate-400 hover:text-red-400 transition-colors"
                  aria-label="Remove file"
                >
                  <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z" />
                  </svg>
                </button>
              </motion.div>
            ) : (
              <div
                {...getRootProps()}
                className={[
                  "relative flex flex-col items-center justify-center gap-3 p-8 rounded-2xl border-2 border-dashed cursor-pointer transition-all duration-200",
                  isDragActive
                    ? "border-primary-400 bg-primary-500/10 scale-[1.01]"
                    : "border-white/10 hover:border-primary-500/40 hover:bg-white/[0.02]",
                ].join(" ")}
              >
                <input {...getInputProps()} />
                <div className="text-3xl">💼</div>
                <div className="text-center">
                  <p className="text-sm text-slate-300">
                    {isDragActive ? "Drop it here" : "Drag & drop or click to browse"}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">PDF, DOCX, or TXT · Max 2 MB</p>
                </div>
              </div>
            )}
            <AnimatePresence>
              {fileError && (
                <motion.p
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="text-xs text-red-400 flex items-center gap-1 mt-1"
                  role="alert"
                >
                  <svg className="w-3.5 h-3.5 shrink-0" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm0 3.5a.75.75 0 0 1 .75.75v3a.75.75 0 0 1-1.5 0v-3A.75.75 0 0 1 8 4.5zm0 6.5a.875.875 0 1 1 0-1.75A.875.875 0 0 1 8 11z" />
                  </svg>
                  {fileError}
                </motion.p>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Types ────────────────────────────────────────────────────────────────────

interface JobStatusResponse {
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  result: Record<string, unknown> | null;
}

// ─── File Drop Zone ────────────────────────────────────────────────────────────

interface DropZoneProps {
  label: string;
  accept: Record<string, string[]>;
  maxSize: number;
  file: File | null;
  onDrop: (file: File) => void;
  onRemove: () => void;
  icon: string;
  hint: string;
}

function FileDropZone({ label, accept, maxSize, file, onDrop, onRemove, icon, hint }: DropZoneProps) {
  const [error, setError] = useState<string | null>(null);

  const handleDrop = useCallback(
    (accepted: File[], rejected: FileRejection[]) => {
      setError(null);
      if (rejected.length > 0) {
        const msg = rejected[0].errors[0]?.message ?? "Invalid file";
        setError(msg.includes("size") ? `File too large (max ${maxSize / 1024 / 1024} MB)` : "Unsupported file type");
        return;
      }
      if (accepted[0]) onDrop(accepted[0]);
    },
    [onDrop, maxSize]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleDrop,
    accept,
    maxSize,
    multiple: false,
  });

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-slate-300">{label}</label>

      {file ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex items-center gap-3 p-4 rounded-2xl bg-primary-500/10 border border-primary-500/30"
        >
          <div className="w-10 h-10 rounded-xl bg-primary-500/20 flex items-center justify-center text-xl shrink-0">
            {icon}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-200 truncate">{file.name}</p>
            <p className="text-xs text-slate-400">{formatSize(file.size)}</p>
          </div>
          <button
            type="button"
            onClick={onRemove}
            className="w-7 h-7 rounded-lg bg-white/5 hover:bg-red-500/20 flex items-center justify-center text-slate-400 hover:text-red-400 transition-colors"
            aria-label="Remove file"
          >
            <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="currentColor">
              <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z" />
            </svg>
          </button>
        </motion.div>
      ) : (
        <div
          {...getRootProps()}
          className={[
            "relative flex flex-col items-center justify-center gap-3 p-8 rounded-2xl border-2 border-dashed cursor-pointer transition-all duration-200",
            isDragActive
              ? "border-primary-400 bg-primary-500/10 scale-[1.01]"
              : "border-white/10 hover:border-primary-500/40 hover:bg-white/[0.02]",
          ].join(" ")}
        >
          <input {...getInputProps()} />
          <div className="text-3xl">{icon}</div>
          <div className="text-center">
            <p className="text-sm text-slate-300">
              {isDragActive ? "Drop it here" : "Drag & drop or click to browse"}
            </p>
            <p className="text-xs text-slate-500 mt-1">{hint}</p>
          </div>
        </div>
      )}

      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="text-xs text-red-400 flex items-center gap-1"
            role="alert"
          >
            <svg className="w-3.5 h-3.5 shrink-0" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm0 3.5a.75.75 0 0 1 .75.75v3a.75.75 0 0 1-1.5 0v-3A.75.75 0 0 1 8 4.5zm0 6.5a.875.875 0 1 1 0-1.75A.875.875 0 0 1 8 11z" />
            </svg>
            {error}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Progress Steps ────────────────────────────────────────────────────────────

const STEPS = ["Uploading", "Parsing", "Analyzing", "Scoring", "Generating insights"];

function AnalysisProgress({ step }: { step: number }) {
  return (
    <div className="flex flex-col items-center gap-6 py-8">
      <div className="relative w-20 h-20">
        <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
          <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="6" />
          <motion.circle
            cx="40" cy="40" r="34"
            fill="none"
            stroke="url(#progressGrad)"
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={213.6}
            initial={{ strokeDashoffset: 213.6 }}
            animate={{ strokeDashoffset: 213.6 * (1 - (step + 1) / STEPS.length) }}
            transition={{ duration: 0.6, ease: "easeInOut" }}
          />
          <defs>
            <linearGradient id="progressGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#6366f1" />
              <stop offset="100%" stopColor="#a855f7" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <Spinner size="sm" className="text-primary-400" />
        </div>
      </div>

      <div className="text-center">
        <p className="text-slate-200 font-medium">{STEPS[step] ?? "Processing…"}</p>
        <p className="text-slate-500 text-sm mt-1">Step {step + 1} of {STEPS.length}</p>
      </div>

      <div className="flex gap-2">
        {STEPS.map((_, i) => (
          <motion.div
            key={i}
            className={["w-2 h-2 rounded-full transition-colors", i <= step ? "bg-primary-400" : "bg-white/10"].join(" ")}
            animate={i === step ? { scale: [1, 1.3, 1] } : {}}
            transition={{ duration: 1, repeat: Infinity }}
          />
        ))}
      </div>
    </div>
  );
}

// ─── Upload Page ───────────────────────────────────────────────────────────────

export default function Upload() {
  const navigate = useNavigate();

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [progressStep, setProgressStep] = useState(0);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const startPolling = useCallback(
    (id: string) => {
      setProgressStep(1);
      let step = 1;

      pollRef.current = setInterval(async () => {
        try {
          const { data } = await apiClient.get<JobStatusResponse>(`/files/jobs/${id}/status`);

          if (data.status === "completed") {
            clearInterval(pollRef.current!);
            setProgressStep(4);
            setTimeout(() => navigate(`/results/${id}`), 600);
          } else if (data.status === "failed") {
            clearInterval(pollRef.current!);
            setIsUploading(false);
            toast.error("Analysis failed. Please try again.");
          } else {
            step = Math.min(step + 1, STEPS.length - 2);
            setProgressStep(step);
          }
        } catch {
          clearInterval(pollRef.current!);
          setIsUploading(false);
          toast.error("Lost connection. Please try again.");
        }
      }, 3000);
    },
    [navigate]
  );

  const handleSubmit = async () => {
    if (!resumeFile || !jdFile) return;

    setIsUploading(true);
    setProgressStep(0);

    const formData = new FormData();
    formData.append("resume", resumeFile);
    formData.append("jd", jdFile);

    try {
      const { data } = await apiClient.post<{ job_id: string; status: string }>(
        "/files/upload",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      toast.success("Files uploaded! Analyzing…");
      startPolling(data.job_id);
    } catch (err: unknown) {
      setIsUploading(false);
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Upload failed. Please check your files and try again.";
      toast.error(msg);
    }
  };

  const canSubmit = !!resumeFile && !!jdFile && !isUploading;

  return (
    <AnimatedPage className="min-h-screen bg-dark-950 relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
        <motion.div className="absolute w-96 h-96 rounded-full bg-primary-600/10 blur-3xl" style={{ top: "-5%", right: "10%" }}
          animate={{ scale: [1, 1.1, 1] }} transition={{ duration: 10, repeat: Infinity }} />
        <motion.div className="absolute w-80 h-80 rounded-full bg-violet-600/10 blur-3xl" style={{ bottom: "5%", left: "5%" }}
          animate={{ scale: [1, 1.08, 1] }} transition={{ duration: 12, repeat: Infinity, delay: 2 }} />
      </div>

      <div className="relative max-w-2xl mx-auto px-4 py-12">
        {/* Header */}
        <motion.div className="text-center mb-10" initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }}>
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-600 to-violet-600 shadow-glow mb-4">
            <svg className="w-7 h-7 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold gradient-text mb-2">Analyze Your Resume</h1>
          <p className="text-slate-400">Upload your resume and job description to get your ATS score and AI insights</p>
        </motion.div>

        {/* Card */}
        <motion.div className="glass rounded-3xl p-8" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <AnimatePresence mode="wait">
            {isUploading ? (
              <motion.div key="progress" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <AnalysisProgress step={progressStep} />
              </motion.div>
            ) : (
              <motion.div key="form" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
                <FileDropZone
                  label="Resume"
                  accept={{ "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"] }}
                  maxSize={5 * 1024 * 1024}
                  file={resumeFile}
                  onDrop={setResumeFile}
                  onRemove={() => setResumeFile(null)}
                  icon="📄"
                  hint="PDF or DOCX · Max 5 MB"
                />

                <JdInput jdFile={jdFile} onFileChange={setJdFile} />

                {/* Info banner */}
                <div className="flex items-start gap-3 p-4 rounded-xl bg-primary-500/5 border border-primary-500/15">
                  <svg className="w-4 h-4 text-primary-400 mt-0.5 shrink-0" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm0 3.5a.75.75 0 0 1 .75.75v3a.75.75 0 0 1-1.5 0v-3A.75.75 0 0 1 8 4.5zm0 6.5a.875.875 0 1 1 0-1.75A.875.875 0 0 1 8 11z" />
                  </svg>
                  <p className="text-xs text-slate-400">
                    Analysis typically takes 30–60 seconds. You'll get an ATS score, skill gap analysis, and AI-powered improvement suggestions.
                  </p>
                </div>

                <Button
                  variant="primary"
                  size="lg"
                  className="w-full"
                  disabled={!canSubmit}
                  onClick={handleSubmit}
                >
                  {!resumeFile || !jdFile ? "Select both files to continue" : "Analyze Resume"}
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </AnimatedPage>
  );
}
