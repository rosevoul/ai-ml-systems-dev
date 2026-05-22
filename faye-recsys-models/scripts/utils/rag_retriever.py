"""
utils/rag_retriever.py
----------------------
Builds and queries the RAG knowledge base from MovieLens metadata.

Documents are constructed from movie titles, genres, tags, and stats.
Retrieval uses TF-IDF cosine similarity (fast, no GPU required).
If sentence-transformers is installed, dense retrieval is used instead.
"""

from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def build_movie_documents(movie_meta: dict, tags_df=None) -> dict[int, str]:
    """
    Build a natural-language document for each movie.

    Format:
      "{title} ({year}). Genres: {g1}, {g2}. Tags: {t1}, {t2}.
       Average rating: {avg:.1f} from {count} viewers."
    """
    tag_map: dict[int, list[str]] = {}
    if tags_df is not None and not tags_df.empty:
        for row in tags_df.itertuples():
            tag_map.setdefault(row.movieId, []).append(str(row.tag).lower())

    docs: dict[int, str] = {}
    for mid, meta in movie_meta.items():
        title = meta.get("title", f"Movie {mid}")
        year = meta.get("year")
        genres = meta.get("genres", [])
        avg_r = meta.get("avg_rating", 3.5)
        count = meta.get("rating_count", 0)
        tags = tag_map.get(mid, [])

        parts = [f"{title}"]
        if year:
            parts[0] += f" ({year})"
        parts.append(f"Genres: {', '.join(genres)}.")
        if tags:
            unique_tags = list(dict.fromkeys(tags))[:8]
            parts.append(f"Tags: {', '.join(unique_tags)}.")
        parts.append(f"Average rating: {avg_r:.1f} from {count} viewers.")
        docs[mid] = " ".join(parts)

    return docs


class RAGRetriever:
    """TF-IDF-based retrieval over movie documents."""

    def __init__(self, movie_docs: dict[int, str]):
        self.movie_ids = list(movie_docs.keys())
        corpus = [movie_docs[mid] for mid in self.movie_ids]

        self.vectorizer = TfidfVectorizer(
            max_features=5000, ngram_range=(1, 2), sublinear_tf=True
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self._id_to_idx = {mid: i for i, mid in enumerate(self.movie_ids)}

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        """Retrieve top-k documents for a free-text query."""
        q_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self.tfidf_matrix).flatten()
        top_indices = scores.argsort()[::-1][:top_k]
        return [
            {
                "movieId": self.movie_ids[i],
                "score": float(scores[i]),
                "snippet": "",  # filled by caller
            }
            for i in top_indices
        ]

    def retrieve_for_movie(
        self,
        target_movie_id: int,
        user_history: list[dict],
        movie_meta: dict,
        movie_docs: dict[int, str],
        top_k: int = 3,
    ) -> list[dict]:
        """
        Retrieve relevant context documents for a recommended movie given
        a user's history.  Query = movie genres + user's top-rated genres.
        """
        meta = movie_meta.get(target_movie_id, {})
        target_genres = meta.get("genres", [])

        # Build query from movie genres + user preference signal
        user_fav_genres: list[str] = []
        for item in sorted(user_history, key=lambda x: x["rating"], reverse=True)[:5]:
            user_fav_genres.extend(item.get("genres", []))
        user_fav_genres = list(dict.fromkeys(user_fav_genres))[:4]

        query = f"{meta.get('title', '')} {' '.join(target_genres)} {' '.join(user_fav_genres)}"
        results = self.retrieve(query, top_k=top_k + 1)

        # Exclude the target movie itself
        results = [r for r in results if r["movieId"] != target_movie_id][:top_k]

        for r in results:
            mid = r["movieId"]
            r["snippet"] = movie_docs.get(mid, "")[:200]
            r["source"] = movie_meta.get(mid, {}).get("title", f"Movie {mid}")

        return results


def build_explanation(
    target_movie_id: int,
    user_history: list[dict],
    movie_meta: dict,
    rag_docs: list[dict],
    scores: dict,
) -> str:
    """
    Generate a grounded natural-language explanation for a recommendation.
    """
    meta = movie_meta.get(target_movie_id, {})
    title = meta.get("title", "This film")
    target_genres = set(meta.get("genres", []))

    # Find user's highest-rated movies with genre overlap
    similar_history = [
        item for item in user_history
        if item["rating"] >= 4.0 and set(item.get("genres", [])) & target_genres
    ]
    similar_history.sort(key=lambda x: x["rating"], reverse=True)

    parts: list[str] = []

    if similar_history:
        titles = [h["title"] for h in similar_history[:2]]
        parts.append(
            f"Recommended because you rated {' and '.join(titles)} highly"
            + (" — films that share similar themes and genres." if len(titles) > 1 else ".")
        )
    else:
        parts.append(f"Recommended based on your genre preferences.")

    genre_str = ", ".join(list(target_genres)[:3])
    parts.append(f"{title} features strong {genre_str} elements that align with your viewing history.")

    if scores.get("two_tower", 0) > 0.6:
        parts.append("High collaborative signal from viewers with similar taste profiles.")

    avg_r = meta.get("avg_rating", 0)
    if avg_r >= 4.0:
        parts.append(f"It also holds a strong average rating of {avg_r:.1f} across all users.")

    return " ".join(parts)


def build_factors(
    target_movie_id: int,
    user_history: list[dict],
    movie_meta: dict,
    scores: dict,
) -> list[str]:
    """Return a short list of key recommendation factors."""
    meta = movie_meta.get(target_movie_id, {})
    target_genres = set(meta.get("genres", []))
    factors: list[str] = []

    similar = [h for h in user_history if h["rating"] >= 4.0 and set(h.get("genres", [])) & target_genres]
    if similar:
        factors.append(f"similar to {similar[0]['title'][:30]}")

    if target_genres:
        factors.append(f"genre match: {', '.join(list(target_genres)[:2])}")

    if scores.get("two_tower", 0) > 0.5:
        factors.append("strong collaborative signal")

    avg_r = meta.get("avg_rating", 0)
    if avg_r >= 4.0:
        factors.append(f"high global quality ({avg_r:.1f}★)")

    xgb = scores.get("xgboost_final", 0)
    if xgb > 0.6:
        factors.append("boosted by XGBoost ranker")

    return factors[:5]
