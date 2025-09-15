# backend/services/vector_service.py
from __future__ import annotations

import os
import uuid
import logging
from dataclasses import dataclass
from typing import List, Optional, Protocol, TypedDict

import psycopg
from psycopg.rows import dict_row

# Optional: choose one embedder implementation
# OpenAI (cloud) or a local model (e.g., sentence-transformers)
try:
    from openai import OpenAI  # openai>=1.30
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

# Try to import Ollama embedder
try:
    from .ollama_embedder import OllamaEmbedder
    OLLAMA_AVAILABLE = True
except Exception:  # pragma: no cover
    OllamaEmbedder = None
    OLLAMA_AVAILABLE = False

logger = logging.getLogger(__name__)


# -------------------------------
# Types
# -------------------------------

class RetrievedFragment(TypedDict):
    fragment_id: str
    node_id: str
    text: str
    score: float
    commit_id: Optional[str]
    created_at: str


@dataclass(frozen=True)
class VectorConfig:
    # DB
    pg_dsn: str  # e.g., "postgresql://user:pass@localhost:5432/llm"
    embedding_dim: int = 1536
    # Similarity/search
    distance_metric: str = "cosine"  # "cosine" | "l2" | "ip"
    top_k_default: int = 5
    # Embedder
    embedder: str = "openai"  # "openai" | "local"
    openai_model: str = "text-embedding-3-small"
    openai_api_key: Optional[str] = None


# -------------------------------
# Embedder Abstraction
# -------------------------------

class Embedder(Protocol):
    def embed(self, text: str) -> List[float]:
        ...


class OpenAIEmbedder:
    def __init__(self, model: str, api_key: Optional[str] = None) -> None:
        if OpenAI is None:
            raise RuntimeError("openai package not available. Install openai>=1.30.")
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set.")
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def embed(self, text: str) -> List[float]:
        # OpenAI SDK v1.30+ embeddings API
        resp = self.client.embeddings.create(model=self.model, input=text)
        return resp.data[0].embedding  # type: ignore[no-any-return]


# Placeholder for a local embedder (e.g., sentence-transformers)
class LocalEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        try:
            from sentence_transformers import SentenceTransformer  # lazy import
        except Exception as e:  # pragma: no cover
            raise RuntimeError("Install sentence-transformers to use LocalEmbedder") from e
        self.model = SentenceTransformer(model_name)

    def embed(self, text: str) -> List[float]:
        vec = self.model.encode([text], normalize_embeddings=True)[0]
        return vec.tolist()


# -------------------------------
# Vector Service (pgvector backend)
# -------------------------------

class VectorService:
    """
    VectorService provides a simple API for:
      - add_fragment(node_id, text, commit_id, offset)
      - search(node_id, query, top_k)
    Backends can be swapped by implementing the same interface if needed.
    """

    def __init__(self, cfg: VectorConfig) -> None:
        self.cfg = cfg
        self._conn = psycopg.connect(cfg.pg_dsn, row_factory=dict_row)  # sync connection
        self._conn.execute("SET application_name = 'vector_service'")
        self._conn.commit()

        # Choose embedder
        if cfg.embedder == "openai":
            self._embedder: Embedder = OpenAIEmbedder(
                model=cfg.openai_model, api_key=cfg.openai_api_key
            )
        elif cfg.embedder == "local":
            self._embedder = LocalEmbedder()
        elif cfg.embedder == "ollama" and OLLAMA_AVAILABLE:
            self._embedder = OllamaEmbedder()
        else:
            raise ValueError(f"Unknown embedder: {cfg.embedder}")
        
        # Store the default embedder for dynamic switching
        self._default_embedder = self._embedder
        
    def _get_embedder_for_provider(self, provider: Optional[str] = None) -> Embedder:
        """
        Get embedder for the specified provider or return the default embedder.
        """
        if not provider:
            return self._default_embedder
        
        if provider == "openai":
            return OpenAIEmbedder(
                model=self.cfg.openai_model, api_key=self.cfg.openai_api_key
            )
        elif provider == "local":
            return LocalEmbedder()
        elif provider == "ollama" and OLLAMA_AVAILABLE:
            return OllamaEmbedder()
        else:
            raise ValueError(f"Unknown provider: {provider}")

        # Precompute operator
        self._op = {
            "cosine": "<=>",   # lower is closer (cosine distance)
            "l2": "<->",       # Euclidean distance
            "ip": "<#>",       # negative inner product (distance)
        }[cfg.distance_metric]

    # --------------- Public API ---------------

    def add_fragment(
        self,
        node_id: str,
        text: str,
        commit_id: Optional[str] = None,
        offset: int = 0,
    ) -> str:
        """
        Embeds text and stores it with metadata. Returns fragment_id.
        """
        if not text or not node_id:
            raise ValueError("node_id and text are required.")

        embedder = self._get_embedder_for_provider()
        emb = embedder.embed(text)
        if len(emb) != self.cfg.embedding_dim:
            # Defensive check to avoid silent mismatch with VECTOR(N)
            raise ValueError(
                f"Embedding dimension {len(emb)} != configured {self.cfg.embedding_dim}"
            )

        fid = str(uuid.uuid4())
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO fragments (fragment_id, node_id, text, embedding, commit_id, offset)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (fid, node_id, text, emb, commit_id, offset),
            )
        self._conn.commit()
        return fid

    def add_fragments_bulk(
        self,
        node_id: str,
        items: List[tuple[str, Optional[str], int]],  # list of (text, commit_id, offset)
    ) -> List[str]:
        """
        Bulk-embed and insert a batch of fragments.
        Returns the created fragment IDs.
        """
        ids: List[str] = []
        with self._conn.cursor() as cur:
            for (text, commit_id, offset) in items:
                if not text:
                    continue
                embedder = self._get_embedder_for_provider()
                emb = embedder.embed(text)
                if len(emb) != self.cfg.embedding_dim:
                    raise ValueError(
                        f"Embedding dimension {len(emb)} != configured {self.cfg.embedding_dim}"
                    )
                fid = str(uuid.uuid4())
                ids.append(fid)
                cur.execute(
                    """
                    INSERT INTO fragments (fragment_id, node_id, text, embedding, commit_id, offset)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (fid, node_id, text, emb, commit_id, offset),
                )
        self._conn.commit()
        return ids

    def search(
        self,
        node_id: str,
        query: str,
        top_k: Optional[int] = None,
        since_commit: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> List[RetrievedFragment]:
        """
        Returns top_k fragments for the given node_id ranked by vector similarity.
        Score is similarity (higher better). We convert distance to similarity.
        """
        if not query or not node_id:
            return []

        embedder = self._get_embedder_for_provider(provider)
        q_emb = embedder.embed(query)
        if len(q_emb) != self.cfg.embedding_dim:
            raise ValueError(
                f"Embedding dimension {len(q_emb)} != configured {self.cfg.embedding_dim}"
            )

        k = top_k or self.cfg.top_k_default
        op = self._op

        # distance -> similarity conversion:
        #   cosine: sim = 1 - dist (dist in [0, 2] but for normalized embeddings it’s [0, 2] and often ~[0, 1])
        #   l2:     sim = -dist  (monotonic)
        #   ip:     sim = -dist  (pgvector stores negative inner product as distance)
        sim_expr = {
            "<=>": "1.0 - (f.embedding <=> %(qv)s)",  # cosine
            "<->": "- (f.embedding <-> %(qv)s)",      # l2
            "<#>": "- (f.embedding <#> %(qv)s)",      # ip
        }[op]

        base_sql = f"""
            SELECT
              f.fragment_id,
              f.node_id,
              f.text,
              {sim_expr} AS score,
              f.commit_id,
              f.created_at
            FROM fragments f
            WHERE f.node_id = %(node_id)s
        """

        params: dict = {"node_id": node_id, "qv": q_emb, "k": k}

        if since_commit:
            base_sql += " AND f.commit_id >= %(since_commit)s"
            params["since_commit"] = since_commit

        order_limit = " ORDER BY (f.embedding " + op + " %(qv)s) ASC LIMIT %(k)s"
        sql = base_sql + order_limit

        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        results: List[RetrievedFragment] = []
        for r in rows:
            results.append(
                RetrievedFragment(
                    fragment_id=str(r["fragment_id"]),
                    node_id=r["node_id"],
                    text=r["text"],
                    score=float(r["score"]),
                    commit_id=r.get("commit_id"),
                    created_at=r["created_at"].isoformat(),
                )
            )
        return results

    def global_search(
        self,
        query: str,
        top_k: Optional[int] = None,
        exclude_node_id: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> List[RetrievedFragment]:
        """
        Returns top_k fragments across all nodes ranked by vector similarity.
        Score is similarity (higher better). We convert distance to similarity.
        """
        if not query:
            return []

        embedder = self._get_embedder_for_provider(provider)
        q_emb = embedder.embed(query)
        if len(q_emb) != self.cfg.embedding_dim:
            raise ValueError(
                f"Embedding dimension {len(q_emb)} != configured {self.cfg.embedding_dim}"
            )

        k = top_k or self.cfg.top_k_default
        op = self._op

        # distance -> similarity conversion:
        #   cosine: sim = 1 - dist (dist in [0, 2] but for normalized embeddings it's [0, 2] and often ~[0, 1])
        #   l2:     sim = -dist  (monotonic)
        #   ip:     sim = -dist  (pgvector stores negative inner product as distance)
        sim_expr = {
            "<=>": "1.0 - (f.embedding <=> %(qv)s)",  # cosine
            "<->": "- (f.embedding <-> %(qv)s)",      # l2
            "<#>": "- (f.embedding <#> %(qv)s)",      # ip
        }[op]

        base_sql = f"""
            SELECT
              f.fragment_id,
              f.node_id,
              f.text,
              {sim_expr} AS score,
              f.commit_id,
              f.created_at
            FROM fragments f
        """

        params: dict = {"qv": q_emb, "k": k}

        if exclude_node_id:
            base_sql += " WHERE f.node_id != %(exclude_node_id)s"
            params["exclude_node_id"] = exclude_node_id

        order_limit = " ORDER BY (f.embedding " + op + " %(qv)s) ASC LIMIT %(k)s"
        sql = base_sql + order_limit

        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        results: List[RetrievedFragment] = []
        for r in rows:
            results.append(
                RetrievedFragment(
                    fragment_id=str(r["fragment_id"]),
                    node_id=r["node_id"],
                    text=r["text"],
                    score=float(r["score"]),
                    commit_id=r.get("commit_id"),
                    created_at=r["created_at"].isoformat(),
                )
            )
        return results

    def delete_node_fragments(self, node_id: str) -> int:
        """
        Deletes all fragments for a node. Returns number of rows deleted.
        """
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM fragments WHERE node_id = %s", (node_id,))
            deleted = cur.rowcount or 0
        self._conn.commit()
        return deleted

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:  # pragma: no cover
            pass


# -------------------------------
# Factory
# -------------------------------

def make_vector_service_from_env() -> VectorService:
    """
    Convenience factory that reads config from environment variables.
    """
    dsn = os.getenv("PG_DSN") or os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("PG_DSN or DATABASE_URL must be set for pgvector.")

    cfg = VectorConfig(
        pg_dsn=dsn,
        embedding_dim=int(os.getenv("EMBEDDING_DIM", "1536")),
        distance_metric=os.getenv("VECTOR_DISTANCE", "cosine"),
        top_k_default=int(os.getenv("VECTOR_TOP_K", "5")),
        embedder=os.getenv("EMBEDDER", "openai"),
        openai_model=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
    return VectorService(cfg)