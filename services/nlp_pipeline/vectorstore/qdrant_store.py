"""
Qdrant vector store client.
Requirements: 8.3, 15.1–15.5
"""
from __future__ import annotations
import logging
import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

load_dotenv()

logger = logging.getLogger("nlp_pipeline")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = "resume_embeddings"
VECTOR_SIZE = 384


@lru_cache(maxsize=1)
def _get_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)


def ensure_collection() -> None:
    """Create collection if it doesn't exist."""
    client = _get_client()
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION not in existing:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=qmodels.VectorParams(
                size=VECTOR_SIZE,
                distance=qmodels.Distance.COSINE,
            ),
        )
        logger.info("Created Qdrant collection", extra={"collection": COLLECTION})


def upsert_embedding(
    job_id: str,
    doc_type: str,
    user_id: str,
    vector: list[float],
    metadata: Optional[dict] = None,
) -> None:
    client = _get_client()
    point_id = abs(hash(f"{job_id}:{doc_type}")) % (2**63)
    payload = {"job_id": job_id, "doc_type": doc_type, "user_id": user_id}
    if metadata:
        payload.update(metadata)
    client.upsert(
        collection_name=COLLECTION,
        points=[qmodels.PointStruct(id=point_id, vector=vector, payload=payload)],
    )


def search_similar(
    query_vector: list[float],
    doc_type: str,
    user_id: str,
    top_k: int = 10,
) -> list[dict]:
    client = _get_client()
    results = client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        query_filter=qmodels.Filter(
            must=[
                qmodels.FieldCondition(key="doc_type", match=qmodels.MatchValue(value=doc_type)),
                qmodels.FieldCondition(key="user_id", match=qmodels.MatchValue(value=user_id)),
            ]
        ),
        limit=top_k,
    )
    return [{"id": str(r.id), "score": r.score, "payload": r.payload} for r in results]


def delete_by_job_id(job_id: str) -> None:
    client = _get_client()
    client.delete(
        collection_name=COLLECTION,
        points_selector=qmodels.FilterSelector(
            filter=qmodels.Filter(
                must=[qmodels.FieldCondition(key="job_id", match=qmodels.MatchValue(value=job_id))]
            )
        ),
    )
    logger.info("Deleted vectors for job", extra={"job_id": job_id})
