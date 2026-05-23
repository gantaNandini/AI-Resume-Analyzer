"""
Canonical skill taxonomy mapping raw variants to canonical names.
Requirements: 7.3
"""
from __future__ import annotations
import difflib

# Maps lowercase raw variant -> canonical name
SKILL_TAXONOMY: dict[str, str] = {
    # Python
    "python": "Python", "python3": "Python", "py": "Python",
    # JavaScript
    "javascript": "JavaScript", "js": "JavaScript", "es6": "JavaScript", "es2015": "JavaScript",
    # TypeScript
    "typescript": "TypeScript", "ts": "TypeScript",
    # Java
    "java": "Java", "java8": "Java", "java11": "Java", "java17": "Java",
    # Go
    "go": "Go", "golang": "Go",
    # Rust
    "rust": "Rust",
    # C++
    "c++": "C++", "cpp": "C++", "c plus plus": "C++",
    # C#
    "c#": "C#", "csharp": "C#", "c sharp": "C#",
    # Ruby
    "ruby": "Ruby", "ruby on rails": "Ruby on Rails", "rails": "Ruby on Rails",
    # PHP
    "php": "PHP",
    # Swift
    "swift": "Swift",
    # Kotlin
    "kotlin": "Kotlin",
    # Scala
    "scala": "Scala",
    # R
    "r": "R", "r language": "R",
    # SQL
    "sql": "SQL", "mysql": "MySQL", "postgresql": "PostgreSQL", "postgres": "PostgreSQL",
    "sqlite": "SQLite", "mssql": "SQL Server", "sql server": "SQL Server",
    # NoSQL
    "mongodb": "MongoDB", "mongo": "MongoDB", "redis": "Redis",
    "cassandra": "Cassandra", "dynamodb": "DynamoDB", "elasticsearch": "Elasticsearch",
    # Frontend
    "react": "React", "reactjs": "React", "react.js": "React",
    "vue": "Vue.js", "vuejs": "Vue.js", "vue.js": "Vue.js",
    "angular": "Angular", "angularjs": "Angular",
    "svelte": "Svelte", "nextjs": "Next.js", "next.js": "Next.js",
    "nuxt": "Nuxt.js", "nuxtjs": "Nuxt.js",
    "html": "HTML", "html5": "HTML", "css": "CSS", "css3": "CSS",
    "sass": "Sass", "scss": "Sass", "tailwind": "Tailwind CSS", "tailwindcss": "Tailwind CSS",
    # Backend
    "fastapi": "FastAPI", "django": "Django", "flask": "Flask",
    "express": "Express.js", "expressjs": "Express.js", "express.js": "Express.js",
    "node": "Node.js", "nodejs": "Node.js", "node.js": "Node.js",
    "spring": "Spring", "spring boot": "Spring Boot", "springboot": "Spring Boot",
    "laravel": "Laravel", "nestjs": "NestJS",
    # Cloud
    "aws": "AWS", "amazon web services": "AWS",
    "gcp": "GCP", "google cloud": "GCP", "google cloud platform": "GCP",
    "azure": "Azure", "microsoft azure": "Azure",
    # DevOps / Infra
    "docker": "Docker", "kubernetes": "Kubernetes", "k8s": "Kubernetes",
    "terraform": "Terraform", "ansible": "Ansible", "jenkins": "Jenkins",
    "git": "Git", "github": "GitHub", "gitlab": "GitLab",
    "ci/cd": "CI/CD", "cicd": "CI/CD", "github actions": "GitHub Actions",
    "helm": "Helm", "nginx": "Nginx", "apache": "Apache",
    # ML / AI
    "tensorflow": "TensorFlow", "tf": "TensorFlow",
    "pytorch": "PyTorch", "torch": "PyTorch",
    "scikit-learn": "scikit-learn", "sklearn": "scikit-learn",
    "spacy": "spaCy", "nltk": "NLTK",
    "hugging face": "Hugging Face", "huggingface": "Hugging Face",
    "openai": "OpenAI", "gpt": "GPT", "llm": "LLM",
    "machine learning": "Machine Learning", "ml": "Machine Learning",
    "deep learning": "Deep Learning", "dl": "Deep Learning",
    "nlp": "NLP", "natural language processing": "NLP",
    "computer vision": "Computer Vision", "cv": "Computer Vision",
    "data science": "Data Science", "data analysis": "Data Analysis",
    "pandas": "Pandas", "numpy": "NumPy", "matplotlib": "Matplotlib",
    # Message queues
    "rabbitmq": "RabbitMQ", "kafka": "Apache Kafka", "celery": "Celery",
    # Monitoring
    "prometheus": "Prometheus", "grafana": "Grafana", "datadog": "Datadog",
    # Soft skills
    "leadership": "Leadership", "communication": "Communication",
    "teamwork": "Teamwork", "collaboration": "Collaboration",
    "problem solving": "Problem Solving", "problem-solving": "Problem Solving",
    "agile": "Agile", "scrum": "Scrum", "kanban": "Kanban",
    "project management": "Project Management",
    # Certifications
    "aws certified": "AWS Certified", "cka": "CKA", "ckad": "CKAD",
    "pmp": "PMP", "cissp": "CISSP",
}

_LOWER_TAXONOMY = {k.lower(): v for k, v in SKILL_TAXONOMY.items()}
_ALL_KEYS = list(_LOWER_TAXONOMY.keys())


def canonicalize(skill: str) -> str | None:
    """
    Map a raw skill string to its canonical name.
    Returns None if no match found (even fuzzy).
    """
    normalized = skill.lower().strip()
    # Exact match
    if normalized in _LOWER_TAXONOMY:
        return _LOWER_TAXONOMY[normalized]
    # Fuzzy match
    matches = difflib.get_close_matches(normalized, _ALL_KEYS, n=1, cutoff=0.82)
    if matches:
        return _LOWER_TAXONOMY[matches[0]]
    return None
