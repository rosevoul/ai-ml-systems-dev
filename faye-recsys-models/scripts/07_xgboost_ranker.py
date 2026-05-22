"""
07_xgboost_ranker.py — XGBoost Feature Ranker
----------------------------------------------
Combines features from all upstream models into a single trained ranker.
Acts as the Agentic Responder's final scoring step.

Features:
  two_tower_score, mbar_score, rank_transformer_score, graph_transformer_score,
  movie_avg_rating, movie_popularity, genre_overlap, user_avg_rating,
  rating_count, recency_score

Training: binary classification (rating ≥ 4.0 = positive) on held-out test set.
Inference: probability score as final recommendation score.

Falls back to sklearn GradientBoostingClassifier if xgboost is not installed.

Outputs saved to xgboost.pkl:
  scores              : dict[uid, dict[mid, float]]   final xgb score
  feature_importances : dict[str, float]
  feature_contributions : dict[uid, dict[str, float]] for the top rec per user
"""

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.embeddings import genre_overlap_score

FEATURE_NAMES = [
    "two_tower_score",
    "mbar_score",
    "rank_transformer_score",
    "graph_transformer_score",
    "movie_avg_rating",
    "movie_popularity",
    "genre_overlap",
    "user_avg_rating",
    "log_rating_count",
    "recency_score",
]


def build_features(
    uid: int,
    mid: int,
    user_history: list[dict],
    movie_meta: dict,
    tt_scores: dict,
    mbar_scores: dict,
    rt_scores: dict,
    gt_scores: dict,
) -> np.ndarray:
    meta = movie_meta.get(mid, {})
    user_ratings = [h["rating"] for h in user_history]
    user_avg = np.mean(user_ratings) if user_ratings else 3.5

    # Recency: timestamp of last rating in history (normalised)
    timestamps = [h.get("timestamp", 0) for h in user_history]
    max_ts = max(timestamps) if timestamps else 1
    recency = max_ts / 1e9  # normalise unix timestamp

    return np.array([
        tt_scores.get(uid, {}).get(mid, 0.0),
        mbar_scores.get(uid, {}).get(mid, 0.0),
        rt_scores.get(uid, {}).get(mid, 0.0),
        gt_scores.get(uid, {}).get(mid, 0.0),
        meta.get("avg_rating", 3.5) / 5.0,
        meta.get("popularity", 0.0),
        genre_overlap_score(user_history, meta),
        user_avg / 5.0,
        np.log1p(meta.get("rating_count", 0)) / np.log1p(10000),
        recency,
    ], dtype=np.float32)


def run_xgboost_ranker(data: dict, two_tower: dict, mbar: dict, rank_transformer: dict, graph_transformer: dict, out_dir: Path):
    user_history = data["user_history"]
    user_ids = data["user_ids"]
    movie_meta = data["movie_meta"]
    test_ratings = data["test_ratings"]
    candidates = two_tower["candidates"]
    tt_scores = two_tower["scores"]
    mbar_scores = mbar["scores"]
    rt_scores = rank_transformer["scores"]
    gt_scores = graph_transformer["scores"]

    print("Building training features from test ratings …")
    X, y = [], []
    uid_mid_pairs = []

    for uid in tqdm(user_ids[:300], desc="  feature building"):
        hist = user_history.get(uid, [])
        cands = candidates.get(uid, [])
        if not cands:
            continue

        # Positive examples: highly-rated test items that are in candidates
        pos_ids = set(
            r.movieId for r in test_ratings[test_ratings["userId"] == uid].itertuples()
            if r.rating >= 4.0 and r.movieId in set(cands)
        )

        for mid in cands[:50]:
            feat = build_features(uid, mid, hist, movie_meta, tt_scores, mbar_scores, rt_scores, gt_scores)
            X.append(feat)
            y.append(1.0 if mid in pos_ids else 0.0)
            uid_mid_pairs.append((uid, mid))

    X = np.stack(X)
    y = np.array(y, dtype=np.float32)
    print(f"  Training samples: {len(X)}  (positives: {int(y.sum())})")

    # ── train model ────────────────────────────────────────────────────────
    try:
        import xgboost as xgb
        model = xgb.XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            use_label_encoder=False, eval_metric="logloss",
            random_state=42, verbosity=0,
        )
        model.fit(X, y)
        importances = dict(zip(FEATURE_NAMES, model.feature_importances_.tolist()))
        print("  XGBoost trained successfully.")
    except ImportError:
        from sklearn.ensemble import GradientBoostingClassifier
        model = GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)
        model.fit(X, y)
        importances = dict(zip(FEATURE_NAMES, model.feature_importances_.tolist()))
        print("  XGBoost not found — using sklearn GradientBoostingClassifier.")

    # ── score all candidates ───────────────────────────────────────────────
    print("Scoring all candidates …")
    scores_out: dict[int, dict[int, float]] = {}
    feat_contrib_out: dict[int, dict] = {}

    for uid in tqdm(user_ids, desc="  XGB inference"):
        hist = user_history.get(uid, [])
        cands = candidates.get(uid, [])
        if not cands:
            continue

        X_inf = np.stack([
            build_features(uid, mid, hist, movie_meta, tt_scores, mbar_scores, rt_scores, gt_scores)
            for mid in cands
        ])
        probs = model.predict_proba(X_inf)[:, 1] if hasattr(model, "predict_proba") else model.predict(X_inf)

        sc: dict[int, float] = {mid: float(probs[i]) for i, mid in enumerate(cands)}
        scores_out[uid] = sc

        # Feature contribution for top rec
        top_mid = max(sc, key=sc.get)
        top_feat = build_features(uid, top_mid, hist, movie_meta, tt_scores, mbar_scores, rt_scores, gt_scores)
        feat_contrib_out[uid] = {
            fname: float(top_feat[i]) * importances.get(fname, 0.0)
            for i, fname in enumerate(FEATURE_NAMES)
        }

    # Normalise feature contributions per user to sum to 1
    for uid in feat_contrib_out:
        total = sum(abs(v) for v in feat_contrib_out[uid].values()) or 1.0
        feat_contrib_out[uid] = {k: v / total for k, v in feat_contrib_out[uid].items()}

    result = {
        "scores": scores_out,
        "feature_importances": importances,
        "feature_contributions": feat_contrib_out,
    }
    out_path = out_dir / "xgboost.pkl"
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

    run_xgboost_ranker(
        load("preprocessed"), load("two_tower"), load("mbar"),
        load("rank_transformer"), load("graph_transformer"), out_dir,
    )
