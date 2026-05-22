"""
04_ligr.py — LiGR: List-wise Genre-Aware Re-ranker
---------------------------------------------------
Set-wise re-ranker using Maximal Marginal Relevance (MMR) to balance
relevance (Two-Tower score) against intra-set diversity (genre coverage).

The key property visualised on the frontend: LiGR produces a set where
genre coverage is higher than greedy top-K by score alone.

Algorithm:
  1. Start with Two-Tower top-100 candidates.
  2. Iteratively select the next item maximising:
       λ · relevance(i) + (1-λ) · diversity_gain(i, S)
     where diversity_gain = 1 − max_cosine_sim(genre_vec_i, genre_vecs in S)
  3. Record per-item relevance_score, diversity_gain, final LiGR rank.

Outputs saved to ligr.pkl:
  scores   : dict[uid, dict[mid, float]]   LiGR combined score
  set_data : dict[uid, {candidates, user_history_genres,
                         greedy_genre_coverage, ligr_genre_coverage}]
"""

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.embeddings import genre_overlap_score

LAMBDA = 0.6          # relevance weight; (1-LAMBDA) = diversity weight
FINAL_K = 20          # set size to select


def genre_vec(genres: list[str], vocab: list[str]) -> np.ndarray:
    v = np.zeros(len(vocab), dtype=np.float32)
    for g in genres:
        if g in vocab:
            v[vocab.index(g)] = 1.0
    n = v.sum()
    return v / n if n > 0 else v


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def mmr_select(
    candidate_ids: list[int],
    relevance_scores: dict[int, float],
    genre_vecs_map: dict[int, np.ndarray],
    k: int,
    lam: float,
) -> tuple[list[int], dict[int, float], dict[int, float]]:
    """
    Returns (selected_ids, relevance_scores_norm, diversity_gain_scores).
    """
    max_rel = max(relevance_scores.values()) if relevance_scores else 1.0
    rel_norm = {mid: v / (max_rel + 1e-9) for mid, v in relevance_scores.items()}

    selected: list[int] = []
    remaining = list(candidate_ids)
    diversity_gain: dict[int, float] = {}

    while remaining and len(selected) < k:
        best_id, best_score = None, -1.0
        for mid in remaining:
            rel = rel_norm.get(mid, 0.0)
            if not selected:
                div = 1.0
            else:
                gv = genre_vecs_map.get(mid, np.zeros(20))
                max_sim = max(cosine(gv, genre_vecs_map.get(s, np.zeros(20))) for s in selected)
                div = 1.0 - max_sim

            score = lam * rel + (1 - lam) * div
            if score > best_score:
                best_score = score
                best_id = mid

        if best_id is None:
            break

        gv = genre_vecs_map.get(best_id, np.zeros(20))
        div_val = 1.0
        if selected:
            max_sim = max(cosine(gv, genre_vecs_map.get(s, np.zeros(20))) for s in selected)
            div_val = 1.0 - max_sim

        diversity_gain[best_id] = div_val
        selected.append(best_id)
        remaining.remove(best_id)

    # Fill diversity_gain for unselected
    for mid in remaining:
        if mid not in diversity_gain:
            gv = genre_vecs_map.get(mid, np.zeros(20))
            if selected:
                max_sim = max(cosine(gv, genre_vecs_map.get(s, np.zeros(20))) for s in selected[:5])
                diversity_gain[mid] = 1.0 - max_sim
            else:
                diversity_gain[mid] = 0.5

    return selected, rel_norm, diversity_gain


def run_ligr(data: dict, two_tower: dict, out_dir: Path):
    genre_vocab = data["genre_vocab"]
    movie_meta = data["movie_meta"]
    user_history = data["user_history"]
    user_ids = data["user_ids"]
    candidates = two_tower["candidates"]
    tt_scores = two_tower["scores"]

    # Pre-build genre vectors for all movies
    gv_map: dict[int, np.ndarray] = {
        mid: genre_vec(meta.get("genres", []), genre_vocab)
        for mid, meta in movie_meta.items()
    }

    scores_out: dict[int, dict[int, float]] = {}
    set_data_out: dict[int, dict] = {}

    print("Running LiGR set-wise re-ranking …")
    for uid in tqdm(user_ids):
        cands = candidates.get(uid, [])
        if not cands:
            continue

        rel_scores = {mid: tt_scores.get(uid, {}).get(mid, 0.0) for mid in cands}
        selected, rel_norm, div_gain = mmr_select(cands, rel_scores, gv_map, FINAL_K, LAMBDA)

        # Combined LiGR score (for ranking)
        ligr_scores: dict[int, float] = {}
        for rank, mid in enumerate(selected):
            ligr_scores[mid] = LAMBDA * rel_norm.get(mid, 0) + (1 - LAMBDA) * div_gain.get(mid, 0)
        for mid in cands:
            if mid not in ligr_scores:
                ligr_scores[mid] = LAMBDA * rel_norm.get(mid, 0) + (1 - LAMBDA) * div_gain.get(mid, 0.3)
        scores_out[uid] = ligr_scores

        # Genre coverage comparison
        hist = user_history.get(uid, [])
        user_genres = set(g for h in hist for g in h.get("genres", []))
        user_history_genres = sorted(user_genres)

        def genre_coverage(item_ids: list[int]) -> int:
            covered: set[str] = set()
            for mid in item_ids:
                covered.update(movie_meta.get(mid, {}).get("genres", []))
            return len(covered)

        # Greedy top-K by relevance alone
        greedy_top = sorted(rel_scores, key=rel_scores.get, reverse=True)[:FINAL_K]
        greedy_cov = genre_coverage(greedy_top[:5])
        ligr_cov = genre_coverage(selected[:5])

        # Build candidate data for frontend
        candidate_data = []
        for mid in cands[:30]:
            meta = movie_meta.get(mid, {})
            genres = meta.get("genres", [])
            new_genre = any(g not in user_genres for g in genres)
            candidate_data.append({
                "movieId": mid,
                "title": meta.get("title", ""),
                "relevance_score": float(rel_norm.get(mid, 0)),
                "diversity_gain": float(div_gain.get(mid, 0)),
                "genres": genres,
                "is_new_genre_for_user": new_genre,
            })

        set_data_out[uid] = {
            "candidates": candidate_data,
            "user_history_genres": user_history_genres,
            "greedy_genre_coverage": greedy_cov,
            "ligr_genre_coverage": ligr_cov,
        }

    result = {"scores": scores_out, "set_data": set_data_out}
    out_path = out_dir / "ligr.pkl"
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
    run_ligr(data, two_tower, out_dir)
