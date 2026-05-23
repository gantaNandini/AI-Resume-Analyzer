# Design Document: AI-Powered Resume Intelligence Platform

## Overview

The AI-Powered Resume Intelligence Platform is a production-grade, cloud-native web application that enables job seekers to upload resumes and job descriptions (JDs) and receive deep AI-driven analysis: ATS compatibility scoring, semantic similarity matching, skill gap detection, and LLM-generated improvement suggestions.

The platform is architected as a set of loosely coupled microservices communicating over HTTP/REST and an asynchronous task queue. Each service owns its domain, scales independently, and is deployed as a container. The frontend is a React 18 + TypeScript single-page application with Framer Motion animations and Tailwind CSS styling.

### Key Design Goals

- **Correctness**: ATS scores are deterministic and reproducible for the same inputs.
- **Performance**: Cached results are served in under 200 ms; uncached pipeline completes in under 60 seconds.
- **Scalability**: NLP_Pipeline and Scoring_Engine scale horizontally via Kubernetes replicas.
- **Observability**: Every service emits structured JSON logs and Prometheus metrics.
- **Security**: JWT authentication on all protected endpoints; row-level data isolation per user.
- **Developer Experience**: Single docker compose up starts the full stack; GitHub Actions CI/CD on every PR.

### Technology Summary

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Tailwind CSS, Framer Motion, Vite, React Query |
| Auth Service | FastAPI (Python), PostgreSQL, bcrypt, PyJWT |
| File Processor | FastAPI (Python), PyMuPDF, python-docx, Celery |
| NLP Pipeline | FastAPI (Python), spaCy, sentence-transformers, scikit-learn |
| Scoring Engine | FastAPI (Python), NumPy, scikit-learn |
| LLM Service | FastAPI (Python), OpenAI SDK / LiteLLM |
| Task Queue | Celery 5, RabbitMQ 3.12 |
| Primary DB | PostgreSQL 16 |
| Cache | Redis 7 |
| Vector Store | Qdrant 1.9 |
| Container Runtime | Docker, Kubernetes (K8s 1.29) |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus, Grafana, structured JSON logs |