# AI Resume Analyzer — Complete Interview Guide

> Everything you need to explain this project from scratch, pin to pin.

---

## 1. What Is This Project?

**AI Resume Analyzer** is a full-stack web application that helps job seekers understand how well their resume matches a job description. You upload your resume and paste or upload a job description, and the system gives you:

- An **ATS score** (0–100) — how likely an Applicant Tracking System would pass your resume
- A **skill gap analysis** — which required/preferred skills are missing
- **Section-level similarity scores** — how well each section (experience, education, skills) matches
- **AI-generated improvement suggestions** — specific, actionable advice from GPT-4o-mini

---

## 2. High-Level Architecture

The system is built as a **microservices architecture** — 7 independent services, each with a single responsibility, communicating over HTTP and a message queue.

```
Browser (React SPA)
        │
        ▼
   Nginx (port 80) ──── reverse proxy ────────────────────────────────────┐
        │                                                                  │
        ├──► Auth Service      (port 8001)  — register / login / JWT      │
        ├──► File Processor    (port 8002)  — upload / validate / enqueue │
        ├──► NLP Pipeline      (port 8003)  — preprocess / embed / skills │
        ├──► Scoring Engine    (port 8004)  — ATS score / skill gap       │
        └──► LLM Service       (port 8005)  — GPT suggestions             │
                                                                           │
   Celery Worker ──────────────────────────────────────────────────────────┘
        │  (orchestrates the full pipeline asynchronously)
        │
   ┌────┴──────────────────────────────────────────────────────────┐
   │  PostgreSQL 16   Redis 7   RabbitMQ 3.12   Qdrant 1.9         │
   │  (data store)   (cache)   (message broker) (vector store)     │
   └───────────────────────────────────────────────────────────────┘
```

**Why microservices?**
Each service can be scaled, deployed, and updated independently. The NLP pipeline is the heaviest (loads a 90MB ML model), so it can be scaled separately without touching auth or file upload. If the LLM service is down, the rest of the pipeline still works — suggestions just show as unavailable.

---

## 3. Technology Choices — Why Each One

### Backend: FastAPI (Python 3.11)
- **Why FastAPI over Flask/Django?** FastAPI is async-native, has automatic OpenAPI docs, and uses Pydantic for request/response validation. Every service gets `/docs` for free. It's also significantly faster than Flask for I/O-bound workloads.
- **Why Python?** The ML ecosystem (spaCy, sentence-transformers, scikit-learn) is Python-first. Using Python for all backend services means shared utilities and consistent tooling.

### Database: PostgreSQL 16
- **Why Postgres?** We need ACID transactions (job status updates must be atomic), UUID primary keys, JSONB columns for flexible result storage (section_scores, skill_gap, suggestions are all JSONB), and full-text indexing capability. Postgres handles all of this natively.
- **Why not MongoDB?** The data has clear relational structure — users → jobs → analysis_results. A relational model with foreign keys and cascade deletes is cleaner here.

### ORM: SQLAlchemy 2.0 + Alembic
- SQLAlchemy's mapped_column syntax (new in 2.0) gives type-safe models. Alembic handles schema migrations so the database evolves safely without manual SQL.

### Message Queue: RabbitMQ 3.12
- **Why RabbitMQ over Redis as broker?** RabbitMQ is a dedicated message broker with proper AMQP protocol, message acknowledgment, dead-letter queues, and management UI (port 15672). Analysis jobs take 30–60 seconds — we need guaranteed delivery and retry logic, not just a simple queue.
- **Why not Kafka?** Kafka is overkill for this scale. RabbitMQ is simpler to operate and perfectly suited for task queues.

### Task Queue: Celery 5.4
- **Why Celery?** The analysis pipeline (parse → NLP → score → LLM) takes 30–60 seconds. We can't block an HTTP request for that long. Celery lets the file_processor return a job_id immediately (HTTP 202 Accepted) and process the work asynchronously. It also handles retries with exponential backoff automatically.
- **Configuration choices:**
  - `task_acks_late=True` — task is only acknowledged after it completes, so if the worker crashes mid-job, RabbitMQ requeues it
  - `worker_prefetch_multiplier=1` — worker takes one task at a time (NLP is CPU-heavy)
  - `task_reject_on_worker_lost=True` — if worker dies, task goes back to queue

### Cache: Redis 7
- **Two uses:** (1) Celery result backend — stores task state, (2) Application cache — embeddings and ATS scores are cached by content hash. If you upload the same resume twice, embeddings are served from Redis in milliseconds instead of re-running the ML model.
- **Cache policy:** `allkeys-lru` with 256MB max — Redis evicts least-recently-used keys when full.

### Vector Store: Qdrant 1.9
- **Why Qdrant?** We store 384-dimensional embeddings for every resume and JD. Qdrant is purpose-built for vector similarity search — it's faster and more memory-efficient than storing vectors in Postgres. It also supports metadata filtering (filter by job_id, user_id) which we use for cleanup when a job is deleted.
- **Why not pgvector?** pgvector works but Qdrant has better performance at scale and a cleaner API for our use case.

### NLP: spaCy 3.7.4
- **Why spaCy?** Industrial-strength NLP with a clean Python API. We use it for tokenization, lemmatization, stop word removal, and Named Entity Recognition (NER). The `en_core_web_sm` model is 12MB and handles all our needs.
- **What we use it for:** Detecting section headings (EXPERIENCE, EDUCATION, SKILLS), extracting organization/product names as potential skills, and producing clean token lists for TF-IDF.

### Embeddings: sentence-transformers (all-MiniLM-L6-v2)
- **Why this model?** `all-MiniLM-L6-v2` produces 384-dimensional embeddings, is fast on CPU (no GPU needed), and is specifically trained for semantic similarity tasks — exactly what we need to compare resume text to job description text.
- **Why not OpenAI embeddings?** Cost and latency. This model runs locally, so every analysis is free and fast. OpenAI embeddings would add API cost and network latency to every job.

### Scoring: scikit-learn 1.5
- Used for TF-IDF vectorization and cosine similarity computation. The `TfidfVectorizer` converts token lists to weighted term vectors, and `cosine_similarity` measures how similar the resume and JD are at the keyword level.

### LLM: OpenAI GPT-4o-mini
- **Why gpt-4o-mini over gpt-4?** Cost-performance tradeoff. gpt-4o-mini is 10x cheaper and fast enough for generating 3–10 improvement suggestions. The quality is sufficient for this use case.
- **Graceful degradation:** If the API key is missing or the request times out (30s limit), the system returns `available: false` and the rest of the analysis still works. LLM suggestions are a bonus, not a dependency.

### Frontend: React 18 + TypeScript + Vite
- **Why React?** Component-based UI with a rich ecosystem. The results page has complex interactive components (animated gauge, collapsible suggestions, score bars) that are easy to build with React.
- **Why TypeScript?** Type safety catches bugs at compile time. All API response shapes are typed, so if the backend changes a field name, the frontend shows a type error immediately.
- **Why Vite over CRA?** Vite is 10–100x faster for development builds. Hot module replacement is near-instant.

### Styling: TailwindCSS 3.4
- Utility-first CSS means no context-switching between CSS files and components. The dark glassmorphism theme is built entirely with Tailwind utilities.

### Animations: Framer Motion 11
- Used for page transitions, the animated ATS gauge (SVG stroke animation), progress bars, and collapsible suggestion cards. Framer Motion's `AnimatePresence` handles enter/exit animations cleanly.

### Data Fetching: TanStack React Query 5
- Handles server state — caching, background refetching, loading/error states. The History page uses React Query for paginated job lists. The Results page fetches analysis data with automatic retry on failure.

### Auth: JWT (PyJWT 2.8) + bcrypt 4.1
- **JWT:** Stateless authentication — no session store needed. The token contains user ID and email, signed with HS256. Expires in 24 hours.
- **bcrypt:** Industry-standard password hashing with salt. The cost factor makes brute-force attacks computationally expensive.

### Containerization: Docker + Docker Compose
- Every service runs in its own container with pinned image versions. Docker Compose orchestrates all 11 containers (7 app services + 4 infrastructure) with health checks and dependency ordering.

### Reverse Proxy: Nginx
- Single entry point on port 80. Routes `/api/auth/` → auth_service, `/api/files/` → file_processor, etc. Handles `client_max_body_size 20M` for file uploads.

### Observability: Prometheus + prometheus-fastapi-instrumentator
- Every FastAPI service exposes `/metrics` with request count, latency histograms, and error rates. The instrumentator adds this with one line of code.

---

## 4. Complete Data Flow — Step by Step

### Step 1: User Registration / Login
```
Browser → POST /api/auth/register { email, password }
        → Auth Service validates with Pydantic
        → bcrypt.hashpw(password)
        → INSERT INTO users (id, email, hashed_password)
        → create_access_token(user_id, email) → JWT
        → Response: { access_token, token_type: "bearer" }
Browser stores JWT in sessionStorage
```

### Step 2: File Upload
```
Browser → POST /api/files/upload (multipart/form-data)
          Authorization: Bearer <JWT>
        → File Processor validates JWT (decodes, checks expiry)
        → python-magic detects MIME type from file bytes (not extension)
          Resume: application/pdf or .docx only
          JD: pdf, docx, or text/plain
        → Validates file size (resume ≤5MB, JD ≤2MB)
        → Saves files to /tmp/uploads/{job_id}_resume_{filename}
        → INSERT INTO jobs (id, user_id, status='pending', ...)
        → process_analysis_job.delay(job_id)  ← enqueues to RabbitMQ
        → Response: { job_id, status: "pending" }  ← HTTP 202 immediately
```

### Step 3: Frontend Polling
```
Browser polls GET /api/files/jobs/{job_id}/status every 3 seconds
        → Returns { status: "pending"|"processing"|"completed"|"failed" }
        → When completed, navigates to /results/{job_id}
```

### Step 4: Celery Worker — Full Pipeline
```
Celery picks up task from RabbitMQ
│
├─ UPDATE jobs SET status='processing'
│
├─ Parse documents
│   ├─ python-magic detects MIME
│   ├─ PDF → PyMuPDF (fitz) extracts text
│   ├─ DOCX → python-docx extracts paragraphs
│   └─ TXT → plain read
│
├─ POST /nlp/preprocess (resume_text)
│   ├─ spaCy: tokenize, lemmatize, remove stop words
│   ├─ NER: extract ORG, PRODUCT, GPE entities
│   ├─ Section detection: scan for heading-like lines
│   └─ Returns: { tokens, entities, sections, original_text }
│
├─ POST /nlp/preprocess (jd_text)  [same process]
│
├─ POST /nlp/extract-skills (resume_doc)
│   ├─ Generate 1-gram, 2-gram, 3-gram combinations from tokens
│   ├─ Match against skill taxonomy (canonicalize)
│   ├─ Confidence: exact=1.0, NER-assisted=0.85, fuzzy=0.75
│   └─ Returns: { skills: [{ canonical_name, confidence, classification }] }
│
├─ POST /nlp/extract-skills (jd_doc)
│   └─ Same + classifies each skill as required/preferred/general
│      based on surrounding context ("must have", "preferred", etc.)
│
├─ POST /nlp/embed (resume_text)
│   ├─ Check Redis cache (key = SHA256(text))
│   ├─ If miss: sentence-transformers.encode(text, normalize=True)
│   │   → 384-dimensional float vector
│   ├─ Also embed each section separately
│   ├─ Store in Redis cache
│   ├─ Upsert to Qdrant (job_id, doc_type, user_id metadata)
│   └─ Returns: { full_document: [384 floats], sections: {...} }
│
├─ POST /nlp/embed (jd_text)  [same process]
│
├─ POST /scoring/ats-score
│   ├─ Check Redis cache (key = hash(resume_text + jd_text))
│   ├─ semantic = cosine_similarity(resume_embedding, jd_embedding)
│   ├─ tfidf = TfidfVectorizer([resume_tokens, jd_tokens]) → cosine
│   ├─ hybrid = 0.60 × semantic + 0.40 × tfidf
│   ├─ keyword_density = |resume_tokens ∩ jd_tokens| / |jd_tokens|
│   ├─ skill_coverage = |resume_skills ∩ jd_skills| / |jd_skills|
│   ├─ formatting = heuristic (section count, bullet points, length)
│   ├─ ATS = 40%×hybrid + 25%×keyword + 25%×skill + 10%×formatting
│   ├─ band: ≥75 → Strong, ≥50 → Fair, <50 → Poor
│   └─ Returns: { score, band, hybrid_similarity, section_scores, ... }
│
├─ POST /scoring/skill-gap
│   ├─ required_missing = JD required skills NOT in resume skills
│   ├─ preferred_missing = JD preferred skills NOT in resume skills
│   └─ Returns: { required_missing, preferred_missing, full_coverage }
│
├─ POST /llm/suggestions (with 30s timeout, graceful fallback)
│   ├─ Builds prompt: ATS score, missing skills, section scores,
│   │   resume text (truncated to 3000 chars), JD (2000 chars)
│   ├─ OpenAI gpt-4o-mini → JSON array of suggestions
│   ├─ Each suggestion: { title, explanation, example }
│   ├─ Enforces 3–10 suggestions
│   └─ Returns: { suggestions: [...], available: true }
│
├─ INSERT INTO analysis_results (all scores, JSONB fields)
├─ UPDATE jobs SET status='completed'
└─ Task complete
```

### Step 5: Results Display
```
Browser → GET /api/files/jobs/{job_id}/result
        → File Processor queries analysis_results JOIN jobs
        → Returns full result JSON
Browser renders:
  - Animated SVG gauge (ATS score)
  - Score breakdown bars (hybrid, keyword, skill coverage, sections)
  - Skill gap chips (red = required missing, amber = preferred missing)
  - Collapsible suggestion cards (title → expand → explanation + example)
  - Download PDF button (jsPDF generates client-side PDF)
```

---

## 5. Database Schema

### users
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | auto-generated |
| email | VARCHAR(320) | unique, indexed |
| hashed_password | VARCHAR(72) | bcrypt hash |
| created_at | TIMESTAMPTZ | server default now() |
| updated_at | TIMESTAMPTZ | auto-updated |

### jobs
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | auto-generated |
| user_id | UUID | indexed |
| status | ENUM | pending/processing/completed/failed, indexed |
| resume_filename | VARCHAR(512) | |
| jd_filename | VARCHAR(512) | |
| resume_path | VARCHAR(1024) | filesystem path |
| jd_path | VARCHAR(1024) | filesystem path |
| failure_reason | VARCHAR(2048) | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### analysis_results
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| job_id | UUID (FK → jobs, CASCADE DELETE) | unique, indexed |
| user_id | UUID | indexed |
| ats_score | INTEGER | 0–100 |
| band | VARCHAR(16) | Poor/Fair/Strong |
| hybrid_similarity | FLOAT | 0.0–1.0 |
| section_scores | JSONB | { experience: 0.72, skills: 0.85, ... } |
| skill_gap | JSONB | { required_missing: [...], preferred_missing: [...] } |
| suggestions | JSONB | { suggestions: [{title, explanation, example}], available } |
| keyword_density | FLOAT | |
| skill_coverage | FLOAT | |
| created_at | TIMESTAMPTZ | |

**Why JSONB for section_scores, skill_gap, suggestions?**
These fields have variable structure — the number of sections varies per resume, the number of suggestions varies per analysis. JSONB lets us store them without schema changes and query inside them with Postgres operators if needed.

---

## 6. ATS Scoring Formula — Explained

```
ATS Score = (0.40 × hybrid_similarity
           + 0.25 × keyword_density
           + 0.25 × skill_coverage
           + 0.10 × formatting_score) × 100
```

**hybrid_similarity** (40% weight — most important)
= 0.60 × semantic_cosine + 0.40 × tfidf_cosine

Semantic cosine measures *meaning* similarity (two resumes saying "built REST APIs" and "developed web services" score high). TF-IDF measures *keyword* overlap (exact term matching). Combining both catches both semantic matches and exact keyword matches that ATS systems look for.

**keyword_density** (25% weight)
= |resume_tokens ∩ jd_tokens| / |jd_tokens|

What fraction of the JD's keywords appear in the resume. Real ATS systems heavily weight exact keyword matches.

**skill_coverage** (25% weight)
= |resume_skills ∩ jd_skills| / |jd_skills|

What fraction of the JD's skills (from our taxonomy) appear in the resume. More precise than keyword density because it uses canonical skill names.

**formatting_score** (10% weight)
Heuristic: does the resume have clear sections, appropriate length, bullet points? ATS systems parse structured resumes better.

**Bands:**
- Strong (≥75): Good match, likely to pass ATS
- Fair (50–74): Partial match, needs improvement
- Poor (<50): Significant gaps, likely to be filtered

---

## 7. Security Design

### Authentication
- Passwords hashed with **bcrypt** (cost factor 12) — computationally expensive to brute-force
- **JWT tokens** signed with HS256, expire in 24 hours, stored in sessionStorage (not localStorage — cleared when tab closes)
- Every protected endpoint validates the JWT signature and expiry before processing

### File Validation
- **MIME type detection** uses `python-magic` which reads the file's magic bytes, not the filename extension. A user can't rename a `.exe` to `.pdf` and upload it.
- **Size limits** enforced server-side (5MB resume, 2MB JD)
- Files stored with UUID-prefixed names to prevent path traversal

### Authorization
- Every job query checks `job.user_id == current_user.id` — users can only see their own jobs
- Returns 403 (not 404) on ownership mismatch to avoid information leakage

### CORS
- Configured per-service with explicit allowed origins
- Credentials allowed only for same-origin requests

---

## 8. Frontend Architecture

### Routing
```
/ (Home)          — public
/login            — public
/signup           — public
/upload           — protected (requires JWT)
/results/:jobId   — protected
/history          — protected
```

`ProtectedRoute` component checks `isAuthenticated` from AuthContext. If not authenticated, redirects to `/login`.

### State Management
- **AuthContext** — JWT token + user object, persisted in sessionStorage, wired to Axios interceptors
- **React Query** — all server data (job list, results). Handles caching, loading states, error states, retries
- **Local state** — form inputs, UI toggles

### API Client (Axios)
- Base URL from `VITE_API_BASE_URL` env var (defaults to `/api`)
- Request interceptor: attaches `Authorization: Bearer <token>` to every request
- Response interceptor: on 401, clears auth state and redirects to `/login`

### Key UX Decisions
- **JD paste mode** — most users copy JDs from job portals, so paste is the default. The text is converted to a `File` blob client-side so the backend API is unchanged.
- **Polling** — frontend polls job status every 3 seconds. Chosen over WebSockets for simplicity — the job takes 30–60s so polling overhead is negligible.
- **PDF export** — jsPDF generates the report client-side. No server round-trip needed.
- **Lazy loading** — all page components are `React.lazy()` loaded. Initial bundle is small; pages load on demand.

---

## 9. Infrastructure & Deployment

### Docker Compose (local)
11 containers total:
- 4 infrastructure: postgres, redis, rabbitmq, qdrant
- 7 application: auth_service, file_processor, nlp_pipeline, scoring_engine, llm_service, celery_worker, frontend
- 1 reverse proxy: nginx

Shared environment variables via YAML anchor (`&common-env`) — DATABASE_URL, RABBITMQ_URL, REDIS_URL, JWT_SECRET_KEY are defined once and merged into every service.

Health checks on all services — Docker waits for postgres/redis/rabbitmq to be healthy before starting dependent services.

### Kubernetes (production)
Manifests in `infra/k8s/`:
- Namespace isolation
- Deployments for each service
- ConfigMap for non-secret env vars
- Secrets for JWT key, OpenAI key
- Services for internal DNS resolution

### CI/CD (GitHub Actions)
- `ci.yml` — runs on every PR: lint, type-check, tests
- `build.yml` — builds and pushes Docker images
- `deploy.yml` — deploys to Kubernetes on merge to main

---

## 10. Common Interview Questions & Answers

**Q: Why microservices instead of a monolith?**
The NLP pipeline loads a 90MB ML model and is CPU-intensive. Separating it means we can scale it independently (run 3 NLP workers, 1 auth service). Also, if the LLM service is down, auth and file upload still work. A monolith would couple all these concerns together.

**Q: How does the ATS score work?**
It's a weighted formula: 40% semantic similarity (meaning-based, using sentence-transformer embeddings), 25% keyword density (exact term overlap), 25% skill coverage (taxonomy-matched skills), 10% formatting. The semantic component catches paraphrasing; the keyword component catches exact ATS keyword matching.

**Q: Why RabbitMQ instead of just Redis for the queue?**
RabbitMQ is a proper message broker with AMQP protocol, message acknowledgment, and dead-letter queues. With `task_acks_late=True`, if the Celery worker crashes mid-analysis, RabbitMQ requeues the task automatically. Redis-as-broker doesn't have the same reliability guarantees.

**Q: What happens if the OpenAI API is down?**
The Celery task wraps the LLM call in a try/except with a 30-second timeout. If it fails, `suggestions_result = { suggestions: [], available: false }` is stored. The frontend shows a warning banner but the ATS score, skill gap, and section scores are all still displayed correctly.

**Q: How do you prevent users from seeing each other's results?**
Every database query for jobs and results includes `WHERE user_id = current_user.id`. The JWT contains the user's UUID, which is validated on every request. Even if someone guesses a job_id UUID, they get a 403.

**Q: Why store embeddings in Qdrant instead of Postgres?**
Qdrant is purpose-built for vector similarity search. It uses HNSW (Hierarchical Navigable Small World) indexing which makes nearest-neighbor search O(log n) instead of O(n). For 384-dimensional vectors, Postgres with pgvector would work at small scale but Qdrant is faster and has better memory efficiency at scale.

**Q: How does skill extraction work?**
We generate 1-gram, 2-gram, and 3-gram combinations from the lemmatized tokens, then match them against a canonical skill taxonomy. For example, "machine learning" (2-gram) maps to canonical name "Machine Learning". We also use spaCy's NER to catch organization/product names that might be skills (like "TensorFlow", "AWS"). Each skill gets a confidence score: exact match=1.0, NER-assisted=0.85, fuzzy=0.75.

**Q: Why is the JD skill classification (required/preferred) important?**
Real job postings distinguish between "must have Python" and "nice to have Kubernetes". We detect this by looking at the 120-character window around each skill mention for keywords like "required", "must have", "mandatory" vs "preferred", "nice to have", "bonus". This lets us show the user which missing skills are blockers vs nice-to-haves.

**Q: How does caching work?**
Two levels: (1) Embedding cache — key is SHA256(text), value is the 384-dim vector. If you upload the same resume twice, embeddings are served from Redis instantly. (2) ATS score cache — key is hash(resume_text + jd_text). The scoring endpoint returns an `X-Cache: HIT` or `MISS` header. Cache policy is LRU with 256MB max.

**Q: Walk me through what happens when I click "Analyze Resume".**
1. Frontend sends `POST /api/files/upload` with resume + JD as multipart form data, JWT in header
2. File Processor validates MIME types and sizes, saves files, creates a Job record (status: pending), enqueues a Celery task, returns job_id immediately (HTTP 202)
3. Frontend starts polling `/api/files/jobs/{job_id}/status` every 3 seconds
4. Celery worker picks up the task from RabbitMQ, updates status to "processing"
5. Worker calls NLP Pipeline to preprocess both documents (tokenize, lemmatize, NER, section detection)
6. Worker calls NLP Pipeline to extract skills from both documents
7. Worker calls NLP Pipeline to generate embeddings (sentence-transformers, cached in Redis, stored in Qdrant)
8. Worker calls Scoring Engine to compute ATS score (semantic + TF-IDF + keyword + skill + formatting)
9. Worker calls Scoring Engine for skill gap analysis
10. Worker calls LLM Service for improvement suggestions (GPT-4o-mini, 30s timeout)
11. Worker persists all results to PostgreSQL, updates job status to "completed"
12. Frontend poll returns "completed", navigates to /results/{job_id}
13. Results page fetches full result and renders gauge, breakdowns, skill gap, suggestions

---

## 11. Tech Stack Summary Table

| Category | Technology | Version | Why |
|----------|-----------|---------|-----|
| Frontend framework | React | 18.3.1 | Component model, rich ecosystem |
| Language (frontend) | TypeScript | 5.4.5 | Type safety, better DX |
| Build tool | Vite | 5.3.1 | Fast HMR, optimized builds |
| Styling | TailwindCSS | 3.4.4 | Utility-first, no CSS files |
| Animations | Framer Motion | 11.2.10 | Declarative animations |
| Data fetching | React Query | 5.40.0 | Server state management |
| HTTP client | Axios | 1.7.2 | Interceptors for JWT |
| PDF export | jsPDF | 2.5.1 | Client-side PDF generation |
| Backend framework | FastAPI | 0.111–0.115 | Async, auto-docs, Pydantic |
| Language (backend) | Python | 3.11 | ML ecosystem |
| ORM | SQLAlchemy | 2.0.30 | Type-safe models |
| Migrations | Alembic | 1.13.1 | Schema versioning |
| Task queue | Celery | 5.4.0 | Async job processing |
| Message broker | RabbitMQ | 3.12 | Reliable task delivery |
| Primary database | PostgreSQL | 16 | ACID, JSONB, UUID |
| Cache | Redis | 7 | Embedding cache, Celery backend |
| Vector store | Qdrant | 1.9.0 | Embedding similarity search |
| NLP | spaCy | 3.7.4 | Tokenization, NER, lemmatization |
| Embeddings | sentence-transformers | 2.2.2 | Semantic similarity |
| ML utilities | scikit-learn | 1.5.0 | TF-IDF, cosine similarity |
| LLM | OpenAI GPT-4o-mini | — | Improvement suggestions |
| Auth | PyJWT + bcrypt | 2.8 + 4.1 | Stateless auth, secure hashing |
| File parsing | PyMuPDF + python-docx | — | PDF and DOCX text extraction |
| MIME detection | python-magic | 0.4.27 | Secure file type validation |
| Containerization | Docker + Compose | — | Reproducible environments |
| Reverse proxy | Nginx | alpine | Routing, load balancing |
| Observability | Prometheus | — | Metrics on every service |
| CI/CD | GitHub Actions | — | Automated test and deploy |
