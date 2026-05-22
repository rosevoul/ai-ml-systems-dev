"""
08_agentic_pipeline.py — Agentic Orchestration Trace
------------------------------------------------------
Simulates the six-agent orchestration loop for each user, producing a
structured trace that the frontend "Agentic Trace Player" animates step by step.

Agents and their roles:
  Planner    → decomposes the recommendation request into sub-tasks
  Retriever  → calls Two-Tower retrieval and RAG knowledge base
  Aligner    → reconciles retrieval results with user preference profile
  Summarizer → produces natural-language context summaries
  Ranker     → applies the active transformer re-ranker
  Responder  → assembles final recommendations + explanations

Each step includes: input, output, data used, latency_ms (realistic estimate).

Outputs saved to agentic.pkl:
  trace : dict[uid, list[{agent, input, output, data_used, latency_ms}]]
"""

import argparse
import pickle
import random
import sys
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))

random.seed(42)

# Realistic latency ranges per agent (ms)
LATENCY = {
    "Planner":    (12, 35),
    "Retriever":  (45, 120),
    "Aligner":    (30, 80),
    "Summarizer": (60, 150),
    "Ranker":     (40, 100),
    "Responder":  (55, 130),
}


def rand_latency(agent: str) -> int:
    lo, hi = LATENCY[agent]
    return random.randint(lo, hi)


def fmt_genres(genres: list[str]) -> str:
    if not genres:
        return "mixed genres"
    return ", ".join(genres[:3]) + ("…" if len(genres) > 3 else "")


def build_trace(
    uid: int,
    user_history: list[dict],
    movie_meta: dict,
    candidates: list[int],
    final_recs: list[int],
) -> list[dict]:
    if not user_history:
        return []

    # User profile summary
    top_rated = sorted(user_history, key=lambda h: h["rating"], reverse=True)[:3]
    top_titles = [h["title"][:30] for h in top_rated]
    top_genres = list(dict.fromkeys(g for h in top_rated for g in h.get("genres", [])))[:4]
    avg_rating = sum(h["rating"] for h in user_history) / len(user_history)

    # Final rec titles
    rec_titles = [movie_meta.get(mid, {}).get("title", f"Movie {mid}")[:30] for mid in final_recs[:3]]

    trace = [
        {
            "agent": "Planner",
            "input": f"New recommendation request for user {uid}.",
            "output": (
                f"Sub-tasks identified: (1) retrieve user preference profile, "
                f"(2) run Two-Tower candidate retrieval, (3) fetch contextual documents "
                f"from knowledge base, (4) align candidates with user profile, "
                f"(5) apply transformer re-ranker, (6) generate explanations."
            ),
            "data_used": f"User ID {uid}, session context",
            "latency_ms": rand_latency("Planner"),
        },
        {
            "agent": "Retriever",
            "input": (
                f"User profile: avg rating {avg_rating:.1f}★, "
                f"preferred genres [{', '.join(top_genres)}]. "
                f"Fetch top-100 candidates and relevant KB documents."
            ),
            "output": (
                f"Two-Tower retrieval complete: {len(candidates)} candidates retrieved. "
                f"RAG index queried for '{fmt_genres(top_genres)}' — "
                f"top-3 contextual documents fetched per candidate."
            ),
            "data_used": "Two-Tower movie embeddings, FAISS index, RAG document index",
            "latency_ms": rand_latency("Retriever"),
        },
        {
            "agent": "Aligner",
            "input": (
                f"{len(candidates)} raw candidates. "
                f"User's top-rated films: {', '.join(top_titles)}. "
                f"Align candidate set to preference signal."
            ),
            "output": (
                f"Alignment complete. Candidates filtered to {min(len(candidates), 40)} "
                f"items with genre overlap ≥ 0.3 or collaborative signal > threshold. "
                f"Low-quality and already-seen items removed."
            ),
            "data_used": "User rating history, genre overlap scores, collaborative filter scores",
            "latency_ms": rand_latency("Aligner"),
        },
        {
            "agent": "Summarizer",
            "input": (
                f"Produce preference summary and per-candidate context for "
                f"{min(len(candidates), 40)} aligned candidates."
            ),
            "output": (
                f"User preference summary: strong affinity for "
                f"{fmt_genres(top_genres)} films with above-average ratings. "
                f"Per-candidate context assembled from KB documents "
                f"(genre descriptions, tags, viewer sentiment)."
            ),
            "data_used": "Retrieved KB documents, user history, genre taxonomy",
            "latency_ms": rand_latency("Summarizer"),
        },
        {
            "agent": "Ranker",
            "input": (
                f"Re-rank {min(len(candidates), 40)} aligned candidates using "
                f"Rank Transformer with MBAR attention weights and graph signals."
            ),
            "output": (
                f"Re-ranking complete. Top recommendations: "
                f"{', '.join(rec_titles)}. "
                f"XGBoost feature fusion applied as final scoring step."
            ),
            "data_used": "MBAR attention weights, Rank Transformer scores, Graph Transformer collaborative signal, XGBoost feature ranker",
            "latency_ms": rand_latency("Ranker"),
        },
        {
            "agent": "Responder",
            "input": f"Assemble final output for top-5 recommendations with explanations.",
            "output": (
                f"Final response assembled: {len(final_recs)} personalised recommendations "
                f"with grounded explanations, key factors, and RAG-sourced supporting context. "
                f"Pipeline trace logged."
            ),
            "data_used": "Ranked candidates, RAG context, feature contributions, user preference summary",
            "latency_ms": rand_latency("Responder"),
        },
    ]
    return trace


def run_agentic_pipeline(data: dict, two_tower: dict, xgboost: dict, out_dir: Path):
    user_history = data["user_history"]
    user_ids = data["user_ids"]
    movie_meta = data["movie_meta"]
    candidates = two_tower["candidates"]
    xgb_scores = xgboost["scores"]

    print("Building agentic pipeline traces …")
    trace_out: dict[int, list[dict]] = {}

    for uid in tqdm(user_ids):
        hist = user_history.get(uid, [])
        cands = candidates.get(uid, [])
        sc = xgb_scores.get(uid, {})
        final_recs = sorted(sc, key=sc.get, reverse=True)[:5]

        trace_out[uid] = build_trace(uid, hist, movie_meta, cands, final_recs)

    result = {"trace": trace_out}
    out_path = out_dir / "agentic.pkl"
    with open(out_path, "wb") as f:
        pickle.dump(result, f)
    print(f"Saved → {out_path}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="outputs")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)

    def load(name):
        with open(out_dir / f"{name}.pkl", "rb") as f:
            return pickle.load(f)

    run_agentic_pipeline(load("preprocessed"), load("two_tower"), load("xgboost"), out_dir)
