"""
utils/embeddings.py
-------------------
Shared utilities for building feature vectors and projecting embeddings to 2D.
"""

from __future__ import annotations

import numpy as np


def user_feature_vector(
    history: list[dict],
    movie_meta: dict,
    genre_vocab: list[str],
) -> np.ndarray:
    """
    Build a dense user feature vector from their rating history.

    Features:
      - Weighted average of rated movie genre vectors (weight = rating / 5)
      - Mean rating
      - Rating standard deviation
      - Log-normalised rating count
      - Recency weight: mean timestamp rank (0=oldest, 1=most recent)
    """
    if not history:
        n = len(genre_vocab)
        return np.zeros(n + 4, dtype=np.float32)

    genre_vecs, weights = [], []
    ratings_vals = []
    for i, item in enumerate(history):
        meta = movie_meta.get(item["movieId"], {})
        gv = np.array(meta.get("genre_vec", [0.0] * len(genre_vocab)), dtype=np.float32)
        w = item["rating"] / 5.0
        genre_vecs.append(gv * w)
        weights.append(w)
        ratings_vals.append(item["rating"])

    total_weight = sum(weights) or 1.0
    genre_part = np.sum(genre_vecs, axis=0) / total_weight

    mean_r = np.mean(ratings_vals)
    std_r = np.std(ratings_vals) if len(ratings_vals) > 1 else 0.0
    log_count = np.log1p(len(history)) / np.log1p(1000)
    recency = 0.5  # placeholder; overridden if timestamps used

    return np.concatenate([genre_part, [mean_r / 5.0, std_r / 2.5, log_count, recency]]).astype(np.float32)


def movie_feature_vector(meta: dict, genre_vocab: list[str]) -> np.ndarray:
    """
    Build a dense movie feature vector.

    Features:
      - Genre one-hot (normalised)
      - Average rating (/ 5)
      - Popularity (0-1 log-normalised)
      - Rating count log-normalised
    """
    gv = np.array(meta.get("genre_vec", [0.0] * len(genre_vocab)), dtype=np.float32)
    avg_r = meta.get("avg_rating", 3.5) / 5.0
    pop = meta.get("popularity", 0.0)
    log_count = np.log1p(meta.get("rating_count", 0)) / np.log1p(10000)
    return np.concatenate([gv, [avg_r, pop, log_count]]).astype(np.float32)


def cosine_similarity_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Row-wise cosine similarity between each row in A and all rows in B."""
    A_norm = A / (np.linalg.norm(A, axis=1, keepdims=True) + 1e-9)
    B_norm = B / (np.linalg.norm(B, axis=1, keepdims=True) + 1e-9)
    return A_norm @ B_norm.T


def project_umap(embeddings: np.ndarray, n_neighbors: int = 15, min_dist: float = 0.1, seed: int = 42) -> np.ndarray:
    """Project high-dimensional embeddings to 2D via UMAP (falls back to PCA)."""
    try:
        import umap
        reducer = umap.UMAP(n_components=2, n_neighbors=n_neighbors, min_dist=min_dist, random_state=seed)
        return reducer.fit_transform(embeddings).astype(np.float32)
    except ImportError:
        from sklearn.decomposition import PCA
        pca = PCA(n_components=2, random_state=seed)
        return pca.fit_transform(embeddings).astype(np.float32)


def genre_overlap_score(user_history: list[dict], movie_meta: dict) -> float:
    """
    Fraction of the movie's genres that appear in the user's top-rated history.
    """
    user_genres: set[str] = set()
    for item in user_history:
        if item["rating"] >= 4.0:
            user_genres.update(item.get("genres", []))

    movie_genres = set(movie_meta.get("genres", []))
    if not movie_genres:
        return 0.0
    return len(user_genres & movie_genres) / len(movie_genres)
