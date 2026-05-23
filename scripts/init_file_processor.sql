CREATE TYPE jobstatus AS ENUM ('pending','processing','completed','failed');

CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    status jobstatus NOT NULL DEFAULT 'pending',
    resume_filename VARCHAR(512) NOT NULL,
    jd_filename VARCHAR(512) NOT NULL,
    resume_path VARCHAR(1024),
    jd_path VARCHAR(1024),
    failure_reason VARCHAR(2048),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_jobs_user_id ON jobs(user_id);
CREATE INDEX ix_jobs_status ON jobs(status);

CREATE TABLE analysis_results (
    id UUID PRIMARY KEY,
    job_id UUID NOT NULL UNIQUE REFERENCES jobs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    ats_score INTEGER NOT NULL,
    band VARCHAR(16) NOT NULL,
    hybrid_similarity FLOAT NOT NULL,
    section_scores JSONB NOT NULL DEFAULT '{}',
    skill_gap JSONB NOT NULL DEFAULT '{}',
    suggestions JSONB NOT NULL DEFAULT '{}',
    keyword_density FLOAT,
    skill_coverage FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_analysis_results_job_id ON analysis_results(job_id);
CREATE INDEX ix_analysis_results_user_id ON analysis_results(user_id);

CREATE TABLE IF NOT EXISTS alembic_version_file_processor (version_num VARCHAR(32) NOT NULL PRIMARY KEY);
INSERT INTO alembic_version_file_processor (version_num) VALUES ('001');
