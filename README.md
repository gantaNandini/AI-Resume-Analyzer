🤖 AI Resume Analyzer
An AI-powered full-stack web application that analyzes your resume against a job description and gives you:

ATS Score (0–100) — how likely your resume passes Applicant Tracking Systems
Skill Gap Analysis — which required/preferred skills are missing
Section-level Similarity — how well each section matches the JD
AI Improvement Suggestions — specific, actionable advice powered by LLaMA 3.3 (free via Groq)
🖥️ Demo Screenshots
Upload	Results
Upload your resume + paste JD	Get ATS score, skill gap & AI suggestions
🚀 Quick Start (Run Locally)
Only requirement: Docker Desktop

Step 1 — Install Docker Desktop
Download and install from docker.com/products/docker-desktop

Step 2 — Clone the repository
git clone [https://github.com/gantaNandini/Resume_Analyzer.git](https://github.com/gantaNandini/AI-Resume-Analyzer)
cd Resume_Analyzer
Step 3 — Set up environment variables
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
Now open .env and fill in your values:

JWT_SECRET_KEY=any-long-random-string-here
OPENAI_API_KEY=gsk_your_groq_key_here
LLM_MODEL=llama-3.3-70b-versatile
Get a FREE Groq API key (no credit card needed):

Go to console.groq.com
Sign up → API Keys → Create new key
Copy and paste it as OPENAI_API_KEY
Step 4 — Start everything
docker compose up
First run takes 5–10 minutes (downloads Docker images and the ML model). Subsequent runs start in ~30 seconds.

Step 5 — Open in browser
http://localhost:3000
Stop the app
docker compose down
✨ Features
📄 Upload resume as PDF or DOCX
💼 Paste job description directly or upload as PDF/DOCX/TXT
📊 ATS Score with Poor / Fair / Strong band
🔍 Skill Gap Analysis — required vs preferred missing skills
📈 Section Scores — experience, education, skills similarity
🤖 AI Suggestions — 3–10 specific improvement tips
📥 Download PDF Report — save your analysis
📋 History — view all your previous analyses
🔐 Auth — secure login with JWT
🏗️ Architecture
Browser (React SPA)
       │
       ▼
  Nginx (port 80) ── reverse proxy
       │
       ├── Auth Service      (port 8001)  — register / login / JWT
       ├── File Processor    (port 8002)  — upload / validate / parse
       ├── NLP Pipeline      (port 8003)  — preprocess / embed / skills
       ├── Scoring Engine    (port 8004)  — ATS score / skill gap
       └── LLM Service       (port 8005)  — AI suggestions (Groq/LLaMA)

Celery Worker — async job orchestration
PostgreSQL — users, jobs, results
Redis — caching, task backend
RabbitMQ — message broker
Qdrant — vector store for embeddings
🛠️ Tech Stack
Layer	Technology
Frontend	React 18, TypeScript, Vite, TailwindCSS, Framer Motion
Backend	FastAPI (Python 3.11), SQLAlchemy, Alembic
AI/ML	spaCy, sentence-transformers (all-MiniLM-L6-v2), scikit-learn
LLM	Groq (LLaMA 3.3 70B) — free
Database	PostgreSQL 16
Cache	Redis 7
Queue	RabbitMQ 3.12 + Celery 5
Vector DB	Qdrant 1.9
Container	Docker + Docker Compose
📁 Project Structure
Resume_Analyzer/
├── frontend/                  # React SPA
├── services/
│   ├── auth_service/          # User auth & JWT
│   ├── file_processor/        # File upload & parsing
│   ├── nlp_pipeline/          # NLP & embeddings
│   ├── scoring_engine/        # ATS scoring
│   ├── llm_service/           # AI suggestions
│   └── celery_worker/         # Async job processing
├── infra/
│   ├── docker/nginx.conf      # Reverse proxy config
│   └── k8s/                   # Kubernetes manifests
├── docker-compose.yml
├── .env.example
└── INTERVIEW_GUIDE.md         # Full technical documentation
🔧 Troubleshooting
App not starting?

# Check which containers are running
docker compose ps

# Check logs for a specific service
docker compose logs auth_service
docker compose logs nlp_pipeline
AI suggestions not showing?

Make sure your Groq API key starts with gsk_
Make sure LLM_MODEL=llama-3.3-70b-versatile in .env
Restart: docker compose restart llm_service
Port 3000 already in use?

# Stop whatever is using port 3000, then retry
docker compose down
docker compose up
First run is slow?

Normal — Docker is downloading images (~2GB total) and the ML model (~90MB)
Subsequent runs are fast
📖 Full Technical Documentation
See INTERVIEW_GUIDE.md for a complete explanation of every technology choice, the full data flow, database schema, scoring formula, and common interview Q&A.

