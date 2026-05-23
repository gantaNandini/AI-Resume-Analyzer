# 🤖 AI Resume Analyzer

An AI-powered full-stack web application that analyzes resumes against job descriptions and provides ATS scoring, skill-gap analysis, semantic matching, and AI-generated resume improvement suggestions.

---

# 📌 Overview

AI Resume Analyzer helps job seekers optimize their resumes for Applicant Tracking Systems (ATS) and improve alignment with job descriptions using Natural Language Processing (NLP), semantic similarity analysis, and Large Language Models (LLMs).

The application evaluates resumes and provides:

- 📊 ATS Compatibility Score
- 🔍 Skill Gap Analysis
- 📈 Section-wise Similarity Matching
- 🤖 AI-generated Resume Improvement Suggestions
- 📥 Downloadable Analysis Reports

---

# ✨ Features

- 📄 Upload resumes in PDF or DOCX format
- 💼 Paste or upload job descriptions (PDF/DOCX/TXT)
- 📊 ATS Score (0–100)
- 🔍 Required vs Preferred Skill Analysis
- 📈 Experience, Skills & Education Matching
- 🤖 AI Suggestions powered by LLaMA 3.3 via Groq API
- 📥 Download PDF Analysis Reports
- 📋 View Previous Resume Analyses
- 🔐 JWT-based Authentication
- ⚡ Async Background Processing with Celery
- 🐳 Fully Dockerized Microservices Architecture

---

# 🖼️ Demo

## Upload Resume & Job Description

- Upload your resume
- Paste or upload job description
- Start ATS analysis

## Results Dashboard

- ATS Score
- Missing Skills
- Section Similarity
- AI Suggestions
- Resume Improvement Tips

---

# 🏗️ System Architecture

```text
Browser (React SPA)
        │
        ▼
Nginx Reverse Proxy
        │
        ├── Auth Service (JWT Authentication)
        ├── File Processor Service
        ├── NLP Pipeline Service
        ├── Scoring Engine Service
        └── LLM Suggestion Service

Additional Infrastructure:
        ├── PostgreSQL
        ├── Redis
        ├── RabbitMQ
        ├── Celery Worker
        └── Qdrant Vector Database
```

---

# 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite |
| UI | TailwindCSS, Framer Motion |
| Backend | FastAPI, Python 3.11 |
| ORM | SQLAlchemy, Alembic |
| AI/ML | spaCy, scikit-learn, sentence-transformers |
| LLM | Groq API + LLaMA 3.3 |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Queue | RabbitMQ + Celery |
| Vector DB | Qdrant |
| Containerization | Docker + Docker Compose |

---

# 📁 Project Structure

```text
AI-Resume-Analyzer/
│
├── frontend/                     # React Frontend
│
├── services/
│   ├── auth_service/             # JWT Authentication
│   ├── file_processor/           # Resume Parsing & Validation
│   ├── nlp_pipeline/             # NLP & Embedding Generation
│   ├── scoring_engine/           # ATS & Similarity Scoring
│   ├── llm_service/              # AI Suggestions
│   └── celery_worker/            # Async Task Processing
│
├── infra/
│   ├── docker/                   # Nginx Configuration
│   └── k8s/                      # Kubernetes Manifests
│
├── docker-compose.yml
├── .env.example
├── README.md
└── INTERVIEW_GUIDE.md
```

---

# 🚀 Quick Start

## Prerequisites

Install:

- Docker Desktop

Download here:

https://www.docker.com/products/docker-desktop/

---

# ⚙️ Installation

## Step 1 — Clone Repository

```bash
git clone https://github.com/gantaNandini/AI-Resume-Analyzer.git
cd AI-Resume-Analyzer
```

---

## Step 2 — Configure Environment Variables

### Windows

```bash
copy .env.example .env
```

### Mac/Linux

```bash
cp .env.example .env
```

Open `.env` and configure:

```env
JWT_SECRET_KEY=your_secret_key_here
OPENAI_API_KEY=gsk_your_groq_api_key
LLM_MODEL=llama-3.3-70b-versatile
```

---

# 🔑 Groq API Setup

1. Visit:
   https://console.groq.com

2. Sign up or log in

3. Navigate to:
   - API Keys
   - Create New API Key

4. Copy the generated key

5. Paste it inside `.env`

Example:

```env
OPENAI_API_KEY=gsk_xxxxxxxxxxxxxxxxx
```

---

# ▶️ Run the Application

Start all services:

```bash
docker compose up
```

---

# 🌐 Open the Application

Visit:

```text
http://localhost:3000
```

---

# ⏹️ Stop the Application

```bash
docker compose down
```

---

# ⚡ First Startup Notes

The first startup may take **5–10 minutes** because Docker downloads:

- Container images
- NLP models
- Dependencies

Subsequent startups are significantly faster.

---

# 📊 ATS Scoring Workflow

The scoring engine evaluates resumes using:

- Keyword Matching
- Skill Extraction
- Semantic Similarity
- Section Relevance
- Formatting Analysis
- TF-IDF Scoring
- Embedding-based Similarity

The final ATS score is generated on a scale of:

```text
0 – 100
```

### Score Categories

| Score Range | Rating |
|---|---|
| 0 – 40 | Poor |
| 41 – 70 | Fair |
| 71 – 100 | Strong |

---

# 🤖 AI Suggestions Engine

The LLM Service uses:

- Groq API
- LLaMA 3.3 70B

to generate:

- Resume improvement suggestions
- Missing keyword recommendations
- Experience enhancement tips
- ATS optimization guidance

---

# 🔐 Authentication

The application uses:

- JWT Authentication
- Secure Password Hashing
- Protected Routes
- Token-based Session Management

---

# 🐳 Dockerized Microservices

Each service runs independently inside Docker containers:

| Service | Port |
|---|---|
| Frontend | 3000 |
| Auth Service | 8001 |
| File Processor | 8002 |
| NLP Pipeline | 8003 |
| Scoring Engine | 8004 |
| LLM Service | 8005 |

---

# 🔧 Troubleshooting

## Check Running Containers

```bash
docker compose ps
```

---

## View Logs

```bash
docker compose logs auth_service
docker compose logs nlp_pipeline
docker compose logs scoring_engine
```

---

## AI Suggestions Not Working

Verify:

```env
OPENAI_API_KEY starts with gsk_
LLM_MODEL=llama-3.3-70b-versatile
```

Restart the LLM service:

```bash
docker compose restart llm_service
```

---

## Port 3000 Already in Use

Stop conflicting processes:

```bash
docker compose down
docker compose up
```

---

# 📖 Technical Documentation

Detailed technical documentation is available in:

```text
INTERVIEW_GUIDE.md
```

It includes:

- Architecture Explanation
- Database Schema
- NLP Pipeline Flow
- ATS Scoring Formula
- Microservices Communication
- Docker Workflow
- Common Interview Questions

---

# 📈 Future Improvements

- LinkedIn Profile Analysis
- Resume Template Builder
- Multi-language Resume Support
- Recruiter Dashboard
- Real-time Interview Suggestions
- AI Resume Rewriting
- Cover Letter Generator

---

# 👩‍💻 Author

### Nandini Ganta

GitHub Repository:

https://github.com/gantaNandini/AI-Resume-Analyzer

---

# ⭐ Support

If you found this project useful:

- ⭐ Star the repository
- 🍴 Fork the project
- 🛠️ Contribute improvements

---
