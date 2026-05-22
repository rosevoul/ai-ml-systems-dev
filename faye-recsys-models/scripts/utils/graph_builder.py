"""
utils/graph_builder.py
----------------------
Builds the user-item bipartite graph and related data structures used by the
Graph Transformer model and the frontend graph visualisation.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np


class BipartiteGraph:
    """Lightweight user-item graph built from rating data."""

    def __init__(self, train_ratings, min_rating: float = 3.5):
        """
        Parameters
        ----------
        train_ratings : pd.DataFrame  columns: userId, movieId, rating
        min_rating    : float         only include edges above this threshold
        """
        self.user_to_movies: dict[int, list[int]] = defaultdict(list)
        self.movie_to_users: dict[int, list[int]] = defaultdict(list)
        self.edge_weights:   dict[tuple[int, int], float] = {}

        for row in train_ratings.itertuples():
            if row.rating >= min_rating:
                self.user_to_movies[row.userId].append(row.movieId)
                self.movie_to_users[row.movieId].append(row.userId)
                self.edge_weights[(row.userId, row.movieId)] = row.rating / 5.0

    # ── neighbourhood queries ──────────────────────────────────────────────

    def user_neighbors(self, user_id: int) -> list[int]:
        """Movies rated highly by this user."""
        return self.user_to_movies.get(user_id, [])

    def movie_neighbors(self, movie_id: int) -> list[int]:
        """Users who rated this movie highly."""
        return self.movie_to_users.get(movie_id, [])

    def two_hop_movies(self, user_id: int, max_users: int = 50) -> dict[int, float]:
        """
        Movies reachable in 2 hops: user → rated movies → similar users → their movies.
        Returns {movieId: collaborative_score}.
        """
        user_movies = set(self.user_to_movies.get(user_id, []))
        neighbor_scores: dict[int, float] = defaultdict(float)

        for mid in user_movies:
            for neighbor_uid in self.movie_to_users.get(mid, [])[:max_users]:
                if neighbor_uid == user_id:
                    continue
                shared_w = self.edge_weights.get((neighbor_uid, mid), 0.5)
                for candidate_mid in self.user_to_movies.get(neighbor_uid, []):
                    if candidate_mid not in user_movies:
                        w = self.edge_weights.get((neighbor_uid, candidate_mid), 0.5)
                        neighbor_scores[candidate_mid] += shared_w * w

        return dict(neighbor_scores)

    # ── subgraph extraction (for front-end visualisation) ──────────────────

    def user_subgraph(
        self,
        user_id: int,
        recommended_ids: list[int],
        movie_meta: dict,
        max_neighbors: int = 8,
        max_neighbor_users: int = 5,
    ) -> dict:
        """
        Extract the ego subgraph around a user for the Graph Transformer viz.

        Returns a dict matching the frontend schema:
          user_node, rated_movies, recommended_movies, neighbor_users, edges
        """
        user_movies = self.user_to_movies.get(user_id, [])

        # ── rated movie nodes ────────────────────────────────────────────
        rated_nodes = [
            {
                "id": mid,
                "title": movie_meta.get(mid, {}).get("title", f"Movie {mid}"),
                "rating": self.edge_weights.get((user_id, mid), 0.5) * 5.0,
            }
            for mid in user_movies[:20]
        ]

        # ── recommended movie nodes + bridge info ────────────────────────
        rec_nodes = []
        for mid in recommended_ids:
            bridge_users = self.movie_to_users.get(mid, [])
            shared = [m for m in user_movies if mid in self.user_to_movies.get(
                next((u for u in bridge_users if u != user_id), -1), []
            )]
            # simpler: count users who rated both this movie and any of the user's movies
            connecting_users = [
                u for u in bridge_users
                if u != user_id and any(m in self.user_to_movies.get(u, []) for m in user_movies[:10])
            ]
            bridge_titles = [
                movie_meta.get(m, {}).get("title", f"Movie {m}")
                for m in user_movies[:3]
                if any(m in self.user_to_movies.get(u, []) for u in connecting_users[:3])
            ]
            rec_nodes.append({
                "id": mid,
                "title": movie_meta.get(mid, {}).get("title", f"Movie {mid}"),
                "shared_users": len(connecting_users),
                "bridge_movies": bridge_titles[:3],
            })

        # ── neighbor user nodes ──────────────────────────────────────────
        user_movie_set = set(user_movies)
        neighbor_score: dict[int, int] = defaultdict(int)
        for mid in user_movies[:10]:
            for nu in self.movie_to_users.get(mid, []):
                if nu != user_id:
                    neighbor_score[nu] += 1

        top_neighbors = sorted(neighbor_score, key=neighbor_score.get, reverse=True)[:max_neighbors]
        neighbor_nodes = [
            {"id": nu, "shared_movies": list(user_movie_set & set(self.user_to_movies.get(nu, [])))}
            for nu in top_neighbors
        ]

        # ── edges ────────────────────────────────────────────────────────
        edges: list[dict] = []
        for mid in user_movies[:20]:
            edges.append({
                "source": f"u_{user_id}",
                "target": f"m_{mid}",
                "weight": float(self.edge_weights.get((user_id, mid), 0.5)),
                "type": "user_rated",
            })
        for nu in top_neighbors[:max_neighbor_users]:
            shared = list(user_movie_set & set(self.user_to_movies.get(nu, [])))
            for mid in shared[:3]:
                edges.append({
                    "source": f"u_{nu}",
                    "target": f"m_{mid}",
                    "weight": float(self.edge_weights.get((nu, mid), 0.3)),
                    "type": "neighbor_rated",
                })
        for mid in recommended_ids:
            edges.append({
                "source": f"u_{user_id}",
                "target": f"rec_{mid}",
                "weight": 0.8,
                "type": "recommended",
            })

        return {
            "user_node": {"id": user_id},
            "rated_movies": rated_nodes,
            "recommended_movies": rec_nodes,
            "neighbor_users": neighbor_nodes,
            "edges": edges,
        }
