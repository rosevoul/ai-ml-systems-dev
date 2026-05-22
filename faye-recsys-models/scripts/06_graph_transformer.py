"""
06_graph_transformer.py — Graph Transformer
--------------------------------------------
Graph-attention-based scoring that propagates collaborative signals through
the user-item bipartite graph.

Algorithm:
  1. Build bipartite graph from high-rated interactions (≥ 3.5 stars).
  2. For each user, aggregate movie embeddings of rated items (message passing).
  3. For each candidate, aggregate user embeddings of co-raters (2-hop).
  4. Final score = cosine(aggregated_user_repr, aggregated_candidate_repr)
     boosted by number of shared neighbours (collaborative signal strength).
  5. Export per-user subgraph for the force-directed graph visualisation.

This is a 2-layer graph attention approximation that runs efficiently in
numpy — no torch-geometric dependency required.

Outputs saved to graph_transformer.pkl:
  scores     : dict[uid, dict[mid, float]]
  graph_data : dict[uid, subgraph dict matching frontend schema]
"""

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.graph_builder import BipartiteGraph

MIN_RATING = 3.5
ATTN_TEMP = 0.1    # softmax temperature for attention aggregation


def attention_aggregate(
    embs: list[np.ndarray],
    weights: list[float],
    query: np.ndarray,
    temp: float = ATTN_TEMP,
) -> np.ndarray:
    """
    Attention-weighted aggregation of embeddings.
    Attention score ∝ exp(dot(query, emb) / temp).
    """
    if not embs:
        return np.zeros_like(query)

    emb_mat = np.stack(embs)  # (N, D)
    q_norm = query / (np.linalg.norm(query) + 1e-9)
    e_norm = emb_mat / (np.linalg.norm(emb_mat, axis=1, keepdims=True) + 1e-9)
    raw_attn = (e_norm @ q_norm) / temp
    raw_attn = np.array(weights) * np.exp(raw_attn - raw_attn.max())
    attn = raw_attn / (raw_attn.sum() + 1e-9)
    return (emb_mat * attn[:, None]).sum(0)


def run_graph_transformer(data: dict, two_tower: dict, out_dir: Path):
    user_history = data["user_history"]
    user_ids = data["user_ids"]
    movie_meta = data["movie_meta"]
    train_ratings = data["train_ratings"]
    candidates = two_tower["candidates"]
    movie_embs = two_tower["movie_embeddings"]
    user_embs = two_tower["user_embeddings"]

    print("Building bipartite graph …")
    graph = BipartiteGraph(train_ratings, min_rating=MIN_RATING)

    # ── Layer 1: user repr from rated movie embeddings ─────────────────────
    print("Graph Transformer layer 1: user aggregation …")
    user_graph_repr: dict[int, np.ndarray] = {}
    for uid in tqdm(user_ids, desc="  L1 user"):
        rated = graph.user_neighbors(uid)
        rated_embs = [movie_embs[mid] for mid in rated if mid in movie_embs]
        rated_weights = [graph.edge_weights.get((uid, mid), 0.5) for mid in rated if mid in movie_embs]
        if not rated_embs:
            user_graph_repr[uid] = user_embs.get(uid, np.zeros(64))
            continue
        base = user_embs.get(uid, np.zeros(64))
        aggregated = attention_aggregate(rated_embs, rated_weights, base)
        # Combine base Two-Tower repr with graph aggregation
        user_graph_repr[uid] = 0.5 * base + 0.5 * aggregated

    # ── Layer 2: candidate score from co-rater neighbourhood ──────────────
    print("Graph Transformer layer 2: candidate scoring …")
    scores_out: dict[int, dict[int, float]] = {}

    for uid in tqdm(user_ids, desc="  L2 candidate"):
        cands = candidates.get(uid, [])
        if not cands:
            continue

        u_repr = user_graph_repr[uid]
        u_repr_norm = u_repr / (np.linalg.norm(u_repr) + 1e-9)
        two_hop = graph.two_hop_movies(uid, max_users=30)

        sc: dict[int, float] = {}
        for mid in cands:
            if mid not in movie_embs:
                continue
            m_emb = movie_embs[mid]
            # Base cosine similarity
            m_norm = m_emb / (np.linalg.norm(m_emb) + 1e-9)
            base_score = float(np.dot(u_repr_norm, m_norm))
            # Collaborative signal boost from 2-hop neighbourhood
            collab = two_hop.get(mid, 0.0)
            # Normalise collaborative signal (log scale, cap at 1)
            collab_norm = np.log1p(collab) / np.log1p(50)
            # Combined score
            sc[mid] = 0.7 * base_score + 0.3 * float(collab_norm)

        scores_out[uid] = sc

    # ── Subgraph extraction for visualisation ─────────────────────────────
    print("Extracting subgraphs …")
    graph_data_out: dict[int, dict] = {}

    for uid in tqdm(user_ids[:200], desc="  subgraph extract"):
        top_recs = sorted(scores_out.get(uid, {}).items(), key=lambda x: x[1], reverse=True)[:5]
        rec_ids = [mid for mid, _ in top_recs]
        subgraph = graph.user_subgraph(uid, rec_ids, movie_meta)
        graph_data_out[uid] = subgraph

    result = {"scores": scores_out, "graph_data": graph_data_out}
    out_path = out_dir / "graph_transformer.pkl"
    with open(out_path, "wb") as f:
        pickle.dump(result, f)
    print(f"Saved → {out_path}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="outputs")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    with open(out_dir / "preprocessed.pkl", "rb") as f:
        data = pickle.load(f)
    with open(out_dir / "two_tower.pkl", "rb") as f:
        two_tower = pickle.load(f)
    run_graph_transformer(data, two_tower, out_dir)
