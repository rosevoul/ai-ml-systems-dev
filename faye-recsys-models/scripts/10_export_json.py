"""
10_export_json.py — Assemble and Export All Frontend JSON Files
---------------------------------------------------------------
Reads all intermediate .pkl outputs and writes the final JSON files
consumed by the faye-recsys frontend site.

Output files (written to --json-out-dir, default: ../faye-recsys/assets/data/):
  recommendations.json
  users.json
  movies.json
  embeddings_2d.json
  pipeline_trace.json
  model_intrinsics.json
"""

import argparse
import json
import pickle
import sys
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))

TOP_RECS = 10        # recommendations per user in output JSON
MAX_USERS = 500      # cap users exported (keeps JSON size manageable)


def load(out_dir: Path, name: str):
    with open(out_dir / f"{name}.pkl", "rb") as f:
        return pickle.load(f)


def export_json(out_dir: Path, json_dir: Path):
    json_dir.mkdir(parents=True, exist_ok=True)

    print("Loading all intermediate outputs …")
    data = load(out_dir, "preprocessed")
    tt = load(out_dir, "two_tower")
    mbar = load(out_dir, "mbar")
    ligr = load(out_dir, "ligr")
    rt = load(out_dir, "rank_transformer")
    gt = load(out_dir, "graph_transformer")
    xgb = load(out_dir, "xgboost")
    agentic = load(out_dir, "agentic")
    rag = load(out_dir, "rag")

    user_history = data["user_history"]
    movie_meta = data["movie_meta"]
    user_ids = data["user_ids"][:MAX_USERS]

    # ── movies.json ────────────────────────────────────────────────────────
    print("Exporting movies.json …")
    movies_out = {}
    for mid, meta in movie_meta.items():
        movies_out[str(mid)] = {
            "movieId": mid,
            "title": meta["title"],
            "year": meta.get("year"),
            "genres": meta.get("genres", []),
            "avg_rating": round(meta.get("avg_rating", 3.5), 2),
            "rating_count": meta.get("rating_count", 0),
            "popularity": round(meta.get("popularity", 0.0), 4),
        }
    _write(json_dir / "movies.json", movies_out)

    # ── users.json ─────────────────────────────────────────────────────────
    print("Exporting users.json …")
    users_out = {}
    for uid in user_ids:
        hist = user_history.get(uid, [])
        users_out[str(uid)] = {
            "userId": uid,
            "history": [
                {
                    "movieId": h["movieId"],
                    "title": h["title"],
                    "genres": h["genres"],
                    "rating": h["rating"],
                    "timestamp": h.get("timestamp", 0),
                }
                for h in hist[-20:]  # last 20 for display
            ],
        }
    _write(json_dir / "users.json", users_out)

    # ── embeddings_2d.json ─────────────────────────────────────────────────
    print("Exporting embeddings_2d.json …")
    _write(json_dir / "embeddings_2d.json", {
        "users": list(tt["umap_users"].values()),
        "movies": list(tt["umap_movies"].values()),
    })

    # ── recommendations.json ──────────────────────────────────────────────
    print("Exporting recommendations.json …")
    recs_out: dict[str, dict] = {}

    for uid in tqdm(user_ids, desc="  building recs"):
        xgb_sc = xgb["scores"].get(uid, {})
        top_mids = sorted(xgb_sc, key=xgb_sc.get, reverse=True)[:TOP_RECS]
        rag_ctx = rag["rag_context"].get(uid, {})

        recs = []
        for mid in top_mids:
            meta = movie_meta.get(mid, {})
            ctx = rag_ctx.get(mid, {})
            recs.append({
                "movieId": mid,
                "title": meta.get("title", ""),
                "year": meta.get("year"),
                "genres": meta.get("genres", []),
                "scores": {
                    "two_tower": round(tt["scores"].get(uid, {}).get(mid, 0.0), 4),
                    "mbar": round(mbar["scores"].get(uid, {}).get(mid, 0.0), 4),
                    "ligr": round(ligr["scores"].get(uid, {}).get(mid, 0.0), 4),
                    "rank_transformer": round(rt["scores"].get(uid, {}).get(mid, 0.0), 4),
                    "graph_transformer": round(gt["scores"].get(uid, {}).get(mid, 0.0), 4),
                    "xgboost_final": round(xgb_sc.get(mid, 0.0), 4),
                },
                "explanation": ctx.get("explanation", ""),
                "factors": ctx.get("factors", []),
                "rag_docs": ctx.get("rag_docs", []),
            })

        recs_out[str(uid)] = {
            "history": users_out[str(uid)]["history"],
            "recommendations": recs,
        }

    _write(json_dir / "recommendations.json", {"users": recs_out})

    # ── pipeline_trace.json ───────────────────────────────────────────────
    print("Exporting pipeline_trace.json …")
    trace_out = {
        str(uid): {"steps": agentic["trace"].get(uid, [])}
        for uid in user_ids
    }
    _write(json_dir / "pipeline_trace.json", trace_out)

    # ── model_intrinsics.json ─────────────────────────────────────────────
    print("Exporting model_intrinsics.json …")
    intrinsics_out: dict[str, dict] = {}

    for uid in tqdm(user_ids, desc="  building intrinsics"):
        xgb_sc = xgb["scores"].get(uid, {})
        top_mids = sorted(xgb_sc, key=xgb_sc.get, reverse=True)[:5]

        # MBAR attention
        attn = mbar["attention"].get(uid, {})

        # LiGR set data
        ligr_set = ligr["set_data"].get(uid, {})

        # Rank Transformer bump chart
        rt_ranks = rt["rank_data"].get(uid, [])[:50]

        # Graph Transformer subgraph
        gt_graph = gt["graph_data"].get(uid, {})

        # Candidate funnel
        n_pool = len(movie_meta)
        n_tt = len(tt["candidates"].get(uid, []))
        n_reranked = 20
        n_final = 5

        # Feature contributions for top rec
        feat_contrib = xgb["feature_contributions"].get(uid, {})

        intrinsics_out[str(uid)] = {
            "mbar": {
                "history_titles": attn.get("history_titles", []),
                "rec_titles": attn.get("rec_titles", []),
                "weights": attn.get("weights", []),
            },
            "ligr": {
                "candidates": ligr_set.get("candidates", [])[:20],
                "user_history_genres": ligr_set.get("user_history_genres", []),
                "greedy_genre_coverage": ligr_set.get("greedy_genre_coverage", 0),
                "ligr_genre_coverage": ligr_set.get("ligr_genre_coverage", 0),
            },
            "rank_transformer": {
                "candidates": rt_ranks,
            },
            "graph_transformer": gt_graph,
            "candidate_funnel": {
                "pool": n_pool,
                "two_tower": n_tt,
                "reranked": n_reranked,
                "final": n_final,
            },
            "feature_contributions": feat_contrib,
        }

    _write(json_dir / "model_intrinsics.json", intrinsics_out)

    print(f"\nAll JSON files written to {json_dir}")
    print("  recommendations.json")
    print("  users.json")
    print("  movies.json")
    print("  embeddings_2d.json")
    print("  pipeline_trace.json")
    print("  model_intrinsics.json")


def _write(path: Path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, separators=(",", ":"), ensure_ascii=False)
    size_kb = path.stat().st_size / 1024
    print(f"    → {path.name}  ({size_kb:.0f} KB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="outputs")
    parser.add_argument("--json-out-dir", default="../faye-recsys/assets/data")
    args = parser.parse_args()
    export_json(Path(args.out_dir), Path(args.json_out_dir))
