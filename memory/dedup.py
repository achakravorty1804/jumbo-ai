"""Session 6: duplicate/update detection using sentence embeddings.

Same news event covered by different outlets (or updated the next day) should not
appear as a brand-new story. We embed each story's headline+summary and compare
against recent stories already in the DB using cosine similarity.
"""
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.65  # tune after seeing real scores; starting conservative

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(headline: str, summary: str) -> bytes:
    """Text -> float32 vector -> raw bytes, ready for the `embedding` BLOB column."""
    text = f"{headline}. {summary}"
    vector = get_model().encode(text, normalize_embeddings=True)
    return np.asarray(vector, dtype=np.float32).tobytes()


def _to_vector(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    # Vectors are already normalized at encode time, so dot product = cosine similarity.
    return float(np.dot(vec_a, vec_b))


def find_best_match(conn, new_embedding: bytes, exclude_run_id, lookback_days=4):
    """
    Compares new_embedding against embedded stories from other runs in the lookback
    window. Returns (story_id, similarity) for the closest match, or (None, 0.0)
    if nothing is close enough to matter (caller decides against SIMILARITY_THRESHOLD).
    """
    rows = conn.execute(
        """
        SELECT s.id, s.embedding FROM stories s
        JOIN runs r ON r.id = s.run_id
        WHERE s.embedding IS NOT NULL
          AND s.run_id != ?
          AND r.run_date >= date('now', ?)
        """,
        (exclude_run_id, f"-{lookback_days} days"),
    ).fetchall()

    new_vec = _to_vector(new_embedding)
    best_id, best_sim = None, 0.0
    for row in rows:
        sim = cosine_similarity(new_vec, _to_vector(row["embedding"]))
        if sim > best_sim:
            best_id, best_sim = row["id"], sim
    return best_id, best_sim