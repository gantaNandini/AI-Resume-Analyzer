# Requirements Document

## Introduction

The AI-Powered Resume Intelligence Platform is a full-stack web application that enables job seekers to upload their resumes and job descriptions (JDs), then receive intelligent, AI-driven analysis including ATS compatibility scoring, skill gap detection, semantic similarity matching, and LLM-generated improvement suggestions. The platform is built on a scalable microservice architecture using NLP pipelines, vector embeddings, and a hybrid similarity engine, backed by a React/TypeScript frontend with a polished, animated UI.

The system spans five phases: Foundation (auth + UI), File Processing (upload + parsing), AI Pipeline (NLP + scoring + suggestions), Scalability (caching + async queues + vector DB), and Deployment (Docker + Kubernetes + CI/CD).

---

## Glossary

- **Platform**: The AI-Powered Resume Intelligence Platform as a whole.
- **User**: An authenticated individual using the Platform to analyze resumes.
- **Auth_Service**: The backend service responsible for user registration, login, and JWT issuance/validation.
- **File_Processor**: The backend service responsible for receiving, validating, and parsing uploaded resume and JD files.
- **NLP_Pipeline**: The backend service responsible for preprocessing text, extracting skills, and generating embeddings.
- **Scoring_Engine**: The backend service responsible for computing ATS scores, semantic similarity, and skill gap analysis.
- **LLM_Service**: The backend service responsible for generating natural-language improvement suggestions using a large language model.
- **Vector_Store**: The Qdrant-backed vector database used for semantic search and embedding storage.
- **Cache**: The Redis-backed caching layer used to store computed results and reduce redundant processing.
- **Task_Queue**: The Celery + RabbitMQ asynchronous task queue used to process AI pipeline jobs outside the request cycle.
- **Frontend**: The React + TypeScript single-page application served to the User.
- **Resume**: A PDF or DOCX document uploaded by the User representing their professional background.
- **Job_Description (JD)**: A PDF, DOCX, or plain-text document uploaded by the User representing a target job posting.
- **ATS_Score**: A numeric score (0–100) representing how well a Resume matches a JD from an Applicant Tracking System perspective.
- **Skill_Gap**: A set of skills present in the JD but absent or underrepresented in the Resume.
- **Embedding**: A high-dimensional vector representation of text produced by a sentence-transformer or equivalent model.
- **Hybrid_Similarity**: A combined similarity score derived from both keyword/TF-IDF matching and semantic embedding cosine similarity.
- **JWT**: A JSON Web Token used to authenticate and authorize API requests.
- **CI/CD_Pipeline**: The GitHub Actions workflow responsible for automated testing, building, and deploying the Platform.

---

## Requirements

---

### Requirement 1: User Registration

**User Story:** As a new visitor, I want to create an account, so that I can securely access the Platform's resume analysis features.

#### Acceptance Criteria

1. THE Auth_Service SHALL expose a registration endpoint that accepts a unique email address and a password of at least 8 characters.
2. WHEN a registration request is received with a valid email and password, THE Auth_Service SHALL store a bcrypt-hashed password and return a 201 status with a JWT.
3. IF a registration request is received with an email that already exists in the database, THEN THE Auth_Service SHALL return a 409 status with a descriptive error message.
4. IF a registration request is received with a password shorter than 8 characters, THEN THE Auth_Service SHALL return a 422 status with a descriptive validation error.
5. THE Frontend SHALL display a registration form with clearly labeled fields for email and password, and SHALL render inline validation errors without a full page reload.

---

### Requirement 2: User Login and JWT Authentication

**User Story:** As a registered user, I want to log in with my credentials, so that I can access my resume analysis history and submit new analyses.

#### Acceptance Criteria

1. WHEN a login request is received with a valid email and correct password, THE Auth_Service SHALL return a signed JWT with a 24-hour expiry and a 200 status.
2. IF a login request is received with an unrecognized email or incorrect password, THEN THE Auth_Service SHALL return a 401 status with a generic "invalid credentials" message.
3. THE Frontend SHALL store the JWT in memory or an HttpOnly cookie and SHALL attach it as a Bearer token on all subsequent authenticated API requests.
4. WHEN a JWT has expired, THE Auth_Service SHALL return a 401 status, and THE Frontend SHALL redirect the User to the login page.
5. THE Auth_Service SHALL validate the JWT signature and expiry on every protected endpoint before processing the request.

---

### Requirement 3: Attractive and Animated Frontend UI

**User Story:** As a user, I want a visually polished and responsive interface, so that the Platform feels professional and engaging to use.

#### Acceptance Criteria

1. THE Frontend SHALL be implemented using React 18+, TypeScript, Tailwind CSS, and Framer Motion.
2. THE Frontend SHALL render all primary views — Login, Signup, Dashboard, Upload, and Results — with smooth page-transition animations using Framer Motion.
3. THE Frontend SHALL be fully responsive, rendering correctly on viewport widths from 320px to 2560px.
4. WHEN an asynchronous operation is in progress (file upload, analysis), THE Frontend SHALL display a loading indicator that communicates progress to the User.
5. THE Frontend SHALL meet WCAG 2.1 AA color contrast requirements for all text and interactive elements.
6. THE Frontend SHALL display toast notifications for success and error events without blocking the primary content area.

---

### Requirement 4: Resume and Job Description Upload

**User Story:** As a user, I want to upload my resume and a job description, so that the Platform can analyze how well I match the role.

#### Acceptance Criteria

1. THE File_Processor SHALL accept resume uploads in PDF and DOCX formats with a maximum file size of 5 MB per file.
2. THE File_Processor SHALL accept JD uploads in PDF, DOCX, and plain-text (.txt) formats with a maximum file size of 2 MB per file.
3. WHEN a file is uploaded, THE File_Processor SHALL validate the MIME type and file extension before processing.
4. IF an uploaded file exceeds the size limit or has an unsupported format, THEN THE File_Processor SHALL return a 422 status with a descriptive error identifying the specific violation.
5. THE Frontend SHALL allow the User to upload both a Resume and a JD in a single submission flow, with drag-and-drop support and file-type filtering.
6. WHEN both files are successfully received and validated, THE File_Processor SHALL enqueue an analysis job on the Task_Queue and return a job ID with a 202 status.

---

### Requirement 5: PDF and DOCX Parsing

**User Story:** As a user, I want the Platform to accurately extract text from my uploaded documents, so that the AI analysis is based on complete and correct content.

#### Acceptance Criteria

1. WHEN a PDF file is received, THE File_Processor SHALL extract all readable text content, preserving paragraph and section structure where detectable.
2. WHEN a DOCX file is received, THE File_Processor SHALL extract all text content including headers, body paragraphs, and bullet lists.
3. IF a PDF file is image-only (scanned) and contains no extractable text layer, THEN THE File_Processor SHALL return a 422 status informing the User that the file requires a text-based PDF.
4. THE File_Processor SHALL normalize extracted text by removing non-printable characters and collapsing excessive whitespace before passing it to the NLP_Pipeline.
5. FOR ALL valid Resume and JD documents, parsing then re-serializing the extracted text SHALL produce a string that contains all substantive content from the original document (round-trip completeness property).

---

### Requirement 6: NLP Preprocessing

**User Story:** As a platform operator, I want raw document text to be cleaned and normalized before AI processing, so that downstream models receive consistent, high-quality input.

#### Acceptance Criteria

1. WHEN raw text is received from the File_Processor, THE NLP_Pipeline SHALL tokenize, lowercase, and remove stop words from the text.
2. THE NLP_Pipeline SHALL perform lemmatization on all tokens to reduce words to their base forms.
3. THE NLP_Pipeline SHALL detect and preserve named entities (organizations, job titles, technologies) during preprocessing.
4. WHEN preprocessing is complete, THE NLP_Pipeline SHALL produce a structured document object containing the cleaned token list, named entities, and original section boundaries.
5. THE NLP_Pipeline SHALL process a document of up to 10,000 words within 5 seconds on standard hardware.

---

### Requirement 7: Skill Extraction

**User Story:** As a user, I want the Platform to identify the skills in my resume and the job description, so that I can understand what competencies are being compared.

#### Acceptance Criteria

1. WHEN a preprocessed Resume document is received, THE NLP_Pipeline SHALL extract a deduplicated list of technical skills, soft skills, tools, and certifications.
2. WHEN a preprocessed JD document is received, THE NLP_Pipeline SHALL extract a deduplicated list of required and preferred skills.
3. THE NLP_Pipeline SHALL map extracted skill tokens to a canonical skill taxonomy to normalize variations (e.g., "JS", "JavaScript", "javascript" → "JavaScript").
4. THE NLP_Pipeline SHALL assign a confidence score between 0.0 and 1.0 to each extracted skill indicating extraction certainty.
5. WHEN skill extraction is complete, THE NLP_Pipeline SHALL return a structured skill manifest containing canonical skill names and their confidence scores.

---

### Requirement 8: Embedding Generation

**User Story:** As a platform operator, I want resume and JD text to be converted into vector embeddings, so that semantic similarity can be computed beyond keyword matching.

#### Acceptance Criteria

1. WHEN a preprocessed document is received, THE NLP_Pipeline SHALL generate a dense vector Embedding using a sentence-transformer model (minimum 384 dimensions).
2. THE NLP_Pipeline SHALL generate embeddings at both the full-document level and the section level (e.g., Experience, Education, Skills).
3. WHEN an Embedding is generated, THE NLP_Pipeline SHALL store it in the Vector_Store indexed by the job ID and document type.
4. IF an Embedding for the same document content already exists in the Cache, THEN THE NLP_Pipeline SHALL retrieve it from the Cache instead of recomputing it.
5. THE NLP_Pipeline SHALL generate a full-document Embedding for a 10,000-word document within 10 seconds.

---

### Requirement 9: Hybrid Similarity Engine

**User Story:** As a user, I want my resume to be compared against the job description using both keyword and semantic methods, so that the match score reflects both explicit and contextual alignment.

#### Acceptance Criteria

1. WHEN Resume and JD embeddings are available, THE Scoring_Engine SHALL compute a cosine similarity score between the full-document embeddings, producing a value between 0.0 and 1.0.
2. THE Scoring_Engine SHALL compute a TF-IDF keyword overlap score between the Resume and JD token lists, producing a value between 0.0 and 1.0.
3. THE Scoring_Engine SHALL compute the Hybrid_Similarity score as a weighted combination of the semantic score (60% weight) and the keyword score (40% weight).
4. THE Scoring_Engine SHALL also compute section-level similarity scores for Experience, Education, and Skills sections independently.
5. FOR ALL Resume and JD pairs, the Hybrid_Similarity score SHALL be a value in the closed interval [0.0, 1.0].

---

### Requirement 10: ATS Score Computation

**User Story:** As a user, I want to receive an ATS compatibility score, so that I know how likely my resume is to pass automated screening systems.

#### Acceptance Criteria

1. WHEN Hybrid_Similarity scores and skill extraction results are available, THE Scoring_Engine SHALL compute an ATS_Score as an integer between 0 and 100.
2. THE Scoring_Engine SHALL derive the ATS_Score from a weighted formula incorporating: Hybrid_Similarity (40%), keyword density match (25%), required skill coverage (25%), and formatting signals (10%).
3. THE Scoring_Engine SHALL classify the ATS_Score into one of three bands: Poor (0–49), Fair (50–74), and Strong (75–100).
4. THE Frontend SHALL display the ATS_Score prominently with the score band label and a visual gauge or progress indicator.
5. WHEN the ATS_Score is computed, THE Scoring_Engine SHALL store the result in the Cache keyed by job ID with a TTL of 1 hour.

---

### Requirement 11: Skill Gap Detection

**User Story:** As a user, I want to know which skills from the job description are missing from my resume, so that I can target my upskilling efforts.

#### Acceptance Criteria

1. WHEN skill manifests for both the Resume and JD are available, THE Scoring_Engine SHALL compute the Skill_Gap as the set of canonical skills present in the JD manifest but absent from the Resume manifest.
2. THE Scoring_Engine SHALL classify each Skill_Gap item as either "Required" or "Preferred" based on its classification in the JD skill manifest.
3. THE Scoring_Engine SHALL rank Skill_Gap items by their frequency and prominence in the JD, with the most critical skills listed first.
4. THE Frontend SHALL display the Skill_Gap as a categorized list distinguishing Required and Preferred missing skills.
5. WHEN the Resume skill manifest is a superset of the JD skill manifest, THE Scoring_Engine SHALL return an empty Skill_Gap and indicate full skill coverage.

---

### Requirement 12: LLM-Generated Improvement Suggestions

**User Story:** As a user, I want actionable, natural-language suggestions for improving my resume, so that I can make targeted edits that increase my match score.

#### Acceptance Criteria

1. WHEN ATS_Score, Skill_Gap, and section-level similarity scores are available, THE LLM_Service SHALL generate a structured set of improvement suggestions.
2. THE LLM_Service SHALL produce at least 3 and at most 10 suggestions per analysis, each targeting a specific, identifiable weakness in the Resume.
3. WHEN the ATS_Score is below 50, THE LLM_Service SHALL include at least one suggestion addressing keyword optimization for ATS parsing.
4. THE LLM_Service SHALL format each suggestion with a title, a one-to-two sentence explanation, and a concrete example of the recommended change.
5. IF the LLM_Service fails to respond within 30 seconds, THEN THE Scoring_Engine SHALL return the ATS_Score and Skill_Gap results without suggestions and SHALL include a flag indicating suggestions are unavailable.
6. THE LLM_Service SHALL not reproduce verbatim content from the uploaded Resume or JD in its suggestions.

---

### Requirement 13: Asynchronous Job Processing

**User Story:** As a user, I want the analysis to run in the background, so that I am not blocked waiting for a long-running AI pipeline to complete.

#### Acceptance Criteria

1. WHEN a valid upload is received, THE File_Processor SHALL enqueue an analysis job on the Task_Queue within 500ms of file validation completing.
2. THE Task_Queue SHALL process analysis jobs using Celery workers backed by RabbitMQ as the message broker.
3. WHEN a job is enqueued, THE Platform SHALL return a job ID to the Frontend, which SHALL poll a status endpoint at 3-second intervals.
4. WHEN a job transitions to "completed" or "failed" status, THE Platform SHALL notify the Frontend via the status endpoint response.
5. IF a Celery worker fails during job processing, THEN THE Task_Queue SHALL retry the job up to 3 times with exponential backoff before marking it as permanently failed.
6. WHILE a job is in "processing" status, THE Frontend SHALL display an animated progress indicator communicating that analysis is underway.

---

### Requirement 14: Redis Caching

**User Story:** As a platform operator, I want frequently requested analysis results to be cached, so that repeated queries are served quickly without re-running the AI pipeline.

#### Acceptance Criteria

1. WHEN an analysis result is computed, THE Scoring_Engine SHALL store the full result in the Cache keyed by a hash of the Resume and JD content, with a TTL of 1 hour.
2. WHEN an analysis request is received and a Cache entry exists for the same Resume and JD content hash, THE Platform SHALL return the cached result within 200ms without re-running the pipeline.
3. THE Cache SHALL evict entries using an LRU policy when memory limits are reached.
4. WHEN a Cache entry is served, THE Platform SHALL include a response header indicating the result was served from cache.
5. IF the Cache is unavailable, THEN THE Platform SHALL fall back to full pipeline processing and SHALL log the Cache unavailability event.

---

### Requirement 15: Vector Store and Semantic Search

**User Story:** As a platform operator, I want embeddings stored in a vector database, so that semantic similarity queries are fast and scalable across large numbers of documents.

#### Acceptance Criteria

1. THE Vector_Store SHALL use Qdrant as the vector database engine.
2. WHEN an Embedding is generated, THE NLP_Pipeline SHALL upsert it into the Vector_Store with metadata including job ID, document type, and creation timestamp.
3. WHEN a semantic search query is issued, THE Vector_Store SHALL return the top-K most similar embeddings (K configurable, default 10) within 100ms for a collection of up to 1 million vectors.
4. THE Vector_Store SHALL support filtered search by document type (Resume or JD) and by User ID.
5. WHEN a job is deleted by the User, THE Platform SHALL remove the associated embeddings from the Vector_Store within 60 seconds.

---

### Requirement 16: Logging and Monitoring

**User Story:** As a platform operator, I want comprehensive logging and monitoring, so that I can detect failures, track performance, and diagnose issues in production.

#### Acceptance Criteria

1. THE Platform SHALL emit structured JSON logs for every API request, including request ID, endpoint, HTTP method, status code, and response time in milliseconds.
2. WHEN an unhandled exception occurs in any service, THE Platform SHALL log the full stack trace at ERROR level with the associated request ID.
3. THE Platform SHALL expose a /health endpoint on each service that returns a 200 status and a JSON body indicating the service's operational status and dependency health.
4. THE Platform SHALL expose Prometheus-compatible metrics at a /metrics endpoint, including request count, error rate, and pipeline processing duration.
5. WHEN a Celery job fails permanently (after all retries), THE Platform SHALL emit an alert-level log entry containing the job ID, failure reason, and retry history.

---

### Requirement 17: Containerization and Orchestration

**User Story:** As a platform operator, I want all services containerized and orchestrated, so that the Platform can be deployed consistently across environments.

#### Acceptance Criteria

1. THE Platform SHALL provide a Dockerfile for each service (Frontend, Auth_Service, File_Processor, NLP_Pipeline, Scoring_Engine, LLM_Service, Task_Queue worker).
2. THE Platform SHALL provide a docker-compose.yml file that starts all services, including PostgreSQL, Redis, RabbitMQ, and Qdrant, with a single command.
3. THE Platform SHALL provide Kubernetes manifests (Deployments, Services, ConfigMaps, Secrets) for all services.
4. WHEN deployed to Kubernetes, each service SHALL define resource requests and limits for CPU and memory.
5. THE Platform SHALL support horizontal scaling of the NLP_Pipeline and Scoring_Engine services by running multiple replicas behind a Kubernetes Service.

---

### Requirement 18: CI/CD Pipeline

**User Story:** As a platform operator, I want automated testing and deployment, so that code changes are validated and shipped to production reliably.

#### Acceptance Criteria

1. THE CI/CD_Pipeline SHALL run on every pull request to the main branch, executing unit tests, integration tests, and linting checks.
2. WHEN all CI checks pass on a merge to main, THE CI/CD_Pipeline SHALL build Docker images for all services and push them to a container registry.
3. THE CI/CD_Pipeline SHALL deploy updated images to the production Kubernetes cluster using a rolling update strategy with zero downtime.
4. IF any CI check fails, THEN THE CI/CD_Pipeline SHALL block the merge and SHALL post a summary of failures to the pull request.
5. THE CI/CD_Pipeline SHALL run security scanning on all Docker images using a vulnerability scanner before pushing to the registry.

---

### Requirement 19: Results Dashboard

**User Story:** As a user, I want a clear, visual dashboard showing my analysis results, so that I can quickly understand my resume's strengths and areas for improvement.

#### Acceptance Criteria

1. WHEN an analysis job completes, THE Frontend SHALL display the ATS_Score, Hybrid_Similarity score, Skill_Gap list, and LLM suggestions on a single Results page.
2. THE Frontend SHALL render the ATS_Score as an animated circular gauge that fills to the score value on page load.
3. THE Frontend SHALL render the Skill_Gap as two color-coded columns: Required Missing Skills (red) and Preferred Missing Skills (amber).
4. THE Frontend SHALL render LLM suggestions as expandable cards, each showing the title by default and the full explanation and example on expansion.
5. THE Frontend SHALL provide a "Download Report" button that exports the full analysis result as a formatted PDF.
6. WHEN the User navigates to the Dashboard, THE Frontend SHALL display a paginated history of all previous analyses with their ATS_Score and submission date.

---

### Requirement 20: Data Persistence and User History

**User Story:** As a user, I want my past analyses saved, so that I can review and compare results over time.

#### Acceptance Criteria

1. THE Platform SHALL use PostgreSQL as the primary relational database for storing User accounts, job submissions, and analysis results.
2. WHEN an analysis job completes, THE Platform SHALL persist the full result — including ATS_Score, Skill_Gap, Hybrid_Similarity scores, and LLM suggestions — to PostgreSQL linked to the User's account.
3. THE Platform SHALL retain analysis results for a minimum of 90 days from the submission date.
4. WHEN a User requests deletion of an analysis, THE Platform SHALL remove the associated record from PostgreSQL and the associated embeddings from the Vector_Store within 60 seconds.
5. THE Platform SHALL enforce row-level access control so that a User can only retrieve analysis records associated with their own account.
```
