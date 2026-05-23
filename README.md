# AI-Powered Resume Intelligence Platform

A full-stack web application that enables job seekers to upload resumes and job descriptions, then receive intelligent AI-driven analysis including ATS compatibility scoring, skill gap detection, semantic similarity matching, and LLM-generated improvement suggestions.

## Architecture

The platform is built on a scalable microservice architecture:

| Service | Description |
|---|---|
| `frontend/` | React 18 + TypeScript + Vite SPA |
| `services/auth_service/` | FastAPI — user registration, login, JWT issuance |
| `services/file_processor/` | FastAPI — file upload, validation, parsing |
| `services/nlp_pipeline/` | FastAPI — NLP preprocessing, skill extraction, embeddings |
| `services/scoring_engine/` | FastAPI — ATS scoring, hybrid similarity, skill gap |
| `services/llm_service/` | FastAPI — LLM-generated improvement suggestions |
| `services/celery_worker/` | Celery — async job processing |
| `shared/` | Shared Python utilities (logging, JWT, base models) |
| `infra/docker/` | Docker Compose and Dockerfiles |
| `infra/k8s/` | Kubernetes manifests |
| `.github/workflows/` | CI/CD pipelines |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.11+

### Run the full stack

```bash
make up
```

### Stop all services

```bash
make down
```

### Run all tests

```bash
make test
```

### Run frontend only (development)

```bash
make frontend-dev
```

### Run a specific service

```bash
make service SERVICE=auth_service
```

## Development

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend services

Each service has its own `requirements.txt` and can be run independently:

```bash
cd services/auth_service
pip install -r requirements.txt
uvicorn main:app --reload
```

### Environment variables

Copy `.env.example` files in each service directory and fill in the required values.

## Tech Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS, Framer Motion, Vite, React Query
- **Backend**: FastAPI (Python 3.11), PostgreSQL 16, Redis 7, RabbitMQ 3.12, Qdrant 1.9
- **AI/ML**: spaCy, sentence-transformers, scikit-learn, OpenAI / LiteLLM
- **Infrastructure**: Docker, Kubernetes, GitHub Actions, Prometheus, Grafana

## License

MIT
