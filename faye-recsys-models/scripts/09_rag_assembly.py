"""
09_rag_assembly.py — RAG Context Assembly
------------------------------------------
Builds the knowledge base from MovieLens metadata and retrieves
context documents for each recommended movie.

For each user's top recommendations, we retrieve the 3 most relevant
document snippets and generate a grounded explanation.

Outputs saved to rag.pkl:
  rag_context : dict[uid, dict[mid, {explanation, factors, rag_docs}]]
  movie_docs  : dict[mid, str]   full document strings
"""

import argparse
import pickle
import sys
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.rag_retriever import (
    RAGRetriever,
    build_explanation,
    build_factors,
    build_movie_documents,
)

TOP_RECS_PER_USER = 10


def run_rag_assembly(data: dict, two_tower: dict, xgboost: dict, mbar: dict, out_dir: Path):
    user_history = data["user_history"]
    user_ids = data["user_ids"]
    movie_meta = data["movie_meta"]
    tags = data.get("tags")
    candidates = two_tower["candidates"]
    tt_scores = two_tower["scores"]
    xgb_scores = xgboost["scores"]

    print("Building movie document corpus …")
    movie_docs = build_movie_documents(movie_meta, tags_df=tags if tags is not None and not (hasattr(tags, 'empty') and tags.empty) else None)

    print("Building TF-IDF retrieval index …")
    retriever = RAGRetriever(movie_docs)

    print("Assembling RAG context per user …")
    rag_context_out: dict[int, dict] = {}

    for uid in tqdm(user_ids):
        hist = user_history.get(uid, [])
        sc = xgb_scores.get(uid, tt_scores.get(uid, {}))
        top_mids = sorted(sc, key=sc.get, reverse=True)[:TOP_RECS_PER_USER]

        user_ctx: dict[int, dict] = {}
        for mid in top_mids:
            meta = movie_meta.get(mid, {})
            all_scores = {
                "two_tower": tt_scores.get(uid, {}).get(mid, 0.0),
                "xgboost_final": sc.get(mid, 0.0),
            }

            # Retrieve context documents
            rag_docs = retriever.retrieve_for_movie(mid, hist, movie_meta, movie_docs, top_k=3)

            # Generate explanation and factors
            explanation = build_explanation(mid, hist, movie_meta, rag_docs, all_scores)
            factors = build_factors(mid, hist, movie_meta, all_scores)

            user_ctx[mid] = {
                "explanation": explanation,
                "factors": factors,
                "rag_docs": rag_docs,
            }

        rag_context_out[uid] = user_ctx

    result = {"rag_context": rag_context_out, "movie_docs": movie_docs}
    out_path = out_dir / "rag.pkl"
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

    run_rag_assembly(load("preprocessed"), load("two_tower"), load("xgboost"), load("mbar"), out_dir)
