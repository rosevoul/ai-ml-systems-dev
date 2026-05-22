"""
01_preprocess.py
----------------
Loads and preprocesses MovieLens latest-small.

Outputs (saved to outputs/):
  preprocessed.pkl  — dict with keys:
    ratings         pd.DataFrame  (userId, movieId, rating, timestamp)
    movies          pd.DataFrame  (movieId, title, year, genres list)
    tags            pd.DataFrame  (userId, movieId, tag)
    user_history    dict[int, list[dict]]   sorted by timestamp asc
    movie_meta      dict[int, dict]         genre vec, avg_rating, popularity
    genre_vocab     list[str]               ordered genre names
    user_ids        list[int]               users with >= MIN_RATINGS
    movie_ids       list[int]               all movies present in ratings
    train_ratings   pd.DataFrame
    test_ratings    pd.DataFrame            last HELD_OUT ratings per user
"""

import argparse
import os
import pickle
import re
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

MIN_RATINGS = 20          # users with fewer ratings are excluded
HELD_OUT = 5              # last N ratings per user reserved for evaluation
RANDOM_SEED = 42

GENRE_VOCAB = [
    "Action", "Adventure", "Animation", "Children", "Comedy",
    "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir",
    "Horror", "Musical", "Mystery", "Romance", "Sci-Fi",
    "Thriller", "War", "Western", "IMAX", "(no genres listed)",
]


def extract_year(title: str):
    m = re.search(r"\((\d{4})\)\s*$", title)
    return int(m.group(1)) if m else None


def clean_title(title: str) -> str:
    return re.sub(r"\s*\(\d{4}\)\s*$", "", title).strip()


def genre_vector(genre_list: list[str], vocab: list[str]) -> np.ndarray:
    vec = np.zeros(len(vocab), dtype=np.float32)
    for g in genre_list:
        if g in vocab:
            vec[vocab.index(g)] = 1.0
    norm = vec.sum()
    return vec / norm if norm > 0 else vec


def load_and_preprocess(data_dir: str, out_dir: str):
    data_dir = Path(data_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading MovieLens files …")
    ratings = pd.read_csv(data_dir / "ratings.csv", dtype={"userId": int, "movieId": int})
    movies_raw = pd.read_csv(data_dir / "movies.csv", dtype={"movieId": int})

    tags_path = data_dir / "tags.csv"
    tags = pd.read_csv(tags_path, dtype={"userId": int, "movieId": int}) if tags_path.exists() else pd.DataFrame()

    # ── movies ──────────────────────────────────────────────────────────────
    movies_raw["year"] = movies_raw["title"].apply(extract_year)
    movies_raw["clean_title"] = movies_raw["title"].apply(clean_title)
    movies_raw["genres"] = movies_raw["genres"].apply(lambda g: g.split("|"))

    movies = movies_raw[["movieId", "clean_title", "year", "genres"]].copy()
    movies = movies.rename(columns={"clean_title": "title"})

    # ── filter users ─────────────────────────────────────────────────────────
    counts = ratings.groupby("userId")["movieId"].count()
    valid_users = counts[counts >= MIN_RATINGS].index.tolist()
    ratings = ratings[ratings["userId"].isin(valid_users)].copy()
    print(f"  {len(valid_users)} users with >= {MIN_RATINGS} ratings")

    # ── train / test split (time-based) ──────────────────────────────────────
    ratings = ratings.sort_values(["userId", "timestamp"])
    test_rows = ratings.groupby("userId").tail(HELD_OUT)
    train_rows = ratings.drop(test_rows.index)

    # ── movie stats ───────────────────────────────────────────────────────────
    movie_stats = (
        train_rows.groupby("movieId")["rating"]
        .agg(avg_rating="mean", rating_count="count")
        .reset_index()
    )
    max_count = movie_stats["rating_count"].max()
    movie_stats["popularity"] = np.log1p(movie_stats["rating_count"]) / np.log1p(max_count)

    movie_meta = {}
    movie_df = movies.set_index("movieId")
    stats_df = movie_stats.set_index("movieId")

    for mid in tqdm(movies["movieId"].tolist(), desc="Building movie metadata"):
        row = movie_df.loc[mid] if mid in movie_df.index else None
        stat = stats_df.loc[mid] if mid in stats_df.index else None
        genres = row["genres"] if row is not None else ["(no genres listed)"]
        movie_meta[mid] = {
            "title": row["title"] if row is not None else f"Movie {mid}",
            "year": int(row["year"]) if row is not None and pd.notna(row["year"]) else None,
            "genres": genres,
            "genre_vec": genre_vector(genres, GENRE_VOCAB).tolist(),
            "avg_rating": float(stat["avg_rating"]) if stat is not None else 3.5,
            "rating_count": int(stat["rating_count"]) if stat is not None else 0,
            "popularity": float(stat["popularity"]) if stat is not None else 0.0,
        }

    # ── user history ─────────────────────────────────────────────────────────
    user_history = {}
    for uid, group in tqdm(train_rows.groupby("userId"), desc="Building user histories"):
        group = group.sort_values("timestamp")
        user_history[uid] = [
            {
                "movieId": int(r.movieId),
                "title": movie_meta.get(r.movieId, {}).get("title", f"Movie {r.movieId}"),
                "genres": movie_meta.get(r.movieId, {}).get("genres", []),
                "rating": float(r.rating),
                "timestamp": int(r.timestamp),
            }
            for r in group.itertuples()
        ]

    movie_ids = sorted(movies["movieId"].tolist())

    result = {
        "ratings": ratings,
        "movies": movies,
        "tags": tags,
        "train_ratings": train_rows.reset_index(drop=True),
        "test_ratings": test_rows.reset_index(drop=True),
        "user_history": user_history,
        "movie_meta": movie_meta,
        "genre_vocab": GENRE_VOCAB,
        "user_ids": valid_users,
        "movie_ids": movie_ids,
    }

    out_path = out_dir / "preprocessed.pkl"
    with open(out_path, "wb") as f:
        pickle.dump(result, f)

    print(f"  Saved → {out_path}")
    print(f"  Users: {len(valid_users)}  |  Movies: {len(movie_ids)}  |  Ratings: {len(train_rows)}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/ml-latest-small")
    parser.add_argument("--out-dir", default="outputs")
    args = parser.parse_args()
    load_and_preprocess(args.data_dir, args.out_dir)
