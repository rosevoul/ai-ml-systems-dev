"""
generate_test_data.py — Synthetic MovieLens-format data generator
------------------------------------------------------------------
Creates a minimal but structurally complete dataset so you can run
the full pipeline immediately without downloading MovieLens.

The generated data uses real MovieLens column names and formats.
Models will train on small data — useful for verifying the pipeline
end-to-end and checking JSON output shapes.

Usage:
  python generate_test_data.py
  python generate_test_data.py --out-dir data/ml-test --n-users 150 --n-movies 300

Then run the pipeline against it:
  python scripts/build_all.py --data-dir data/ml-test
"""

import argparse
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42

GENRES_LIST = [
    "Action", "Adventure", "Animation", "Children", "Comedy",
    "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir",
    "Horror", "Musical", "Mystery", "Romance", "Sci-Fi",
    "Thriller", "War", "Western",
]

TITLE_WORDS = [
    "Dark", "Rising", "Lost", "Return", "Last", "First", "Blue",
    "Red", "Silent", "Broken", "Wild", "Long", "Deep", "Far",
    "Strange", "Hidden", "Golden", "Iron", "White", "Black",
]
TITLE_NOUNS = [
    "Star", "Night", "Rain", "Path", "World", "Fire", "River",
    "City", "Dream", "Shadow", "Wind", "Light", "Storm", "Wave",
    "Heart", "Road", "Fall", "Bridge", "Gate", "Hour",
]

TAGS = [
    "atmospheric", "twist ending", "slow burn", "cult classic",
    "visually stunning", "thought-provoking", "based on true story",
    "ensemble cast", "psychological", "underrated", "acclaimed",
    "genre-defining", "character study", "dark humor", "epic",
]


def generate(out_dir: str, n_users: int, n_movies: int, n_ratings_per_user: int):
    rng = np.random.default_rng(SEED)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Generating synthetic MovieLens-format data")
    print(f"  Users: {n_users}  |  Movies: {n_movies}  |  ~{n_ratings_per_user} ratings/user")
    print(f"  Output: {out.resolve()}")
    print()

    # ── movies.csv ────────────────────────────────────────────────────────
    movie_ids = list(range(1, n_movies + 1))
    titles, genres_col = [], []
    for mid in movie_ids:
        rng2 = np.random.default_rng(mid)
        word = TITLE_WORDS[mid % len(TITLE_WORDS)]
        noun = TITLE_NOUNS[(mid * 3) % len(TITLE_NOUNS)]
        year = int(rng2.integers(1980, 2023))
        title = f"The {word} {noun} ({year})"
        n_genres = int(rng2.integers(1, 4))
        selected = rng2.choice(GENRES_LIST, size=n_genres, replace=False).tolist()
        titles.append(title)
        genres_col.append("|".join(selected))

    movies_df = pd.DataFrame({
        "movieId": movie_ids,
        "title": titles,
        "genres": genres_col,
    })
    movies_df.to_csv(out / "movies.csv", index=False)
    print(f"  ✓  movies.csv        ({len(movies_df)} movies)")

    # ── ratings.csv ───────────────────────────────────────────────────────
    base_ts = int(time.mktime(time.strptime("2018-01-01", "%Y-%m-%d")))
    user_ids, item_ids, ratings_vals, timestamps = [], [], [], []

    for uid in range(1, n_users + 1):
        u_rng = np.random.default_rng(uid + 1000)
        n_rated = int(u_rng.integers(n_ratings_per_user, n_ratings_per_user * 2))
        sampled_movies = u_rng.choice(movie_ids, size=min(n_rated, n_movies), replace=False)
        ts = base_ts
        for mid in sampled_movies:
            rating = float(u_rng.choice([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
                                         p=[0.02, 0.03, 0.05, 0.08, 0.10, 0.15, 0.17, 0.20, 0.12, 0.08]))
            user_ids.append(uid)
            item_ids.append(int(mid))
            ratings_vals.append(rating)
            timestamps.append(ts)
            ts += int(u_rng.integers(3600 * 24, 3600 * 24 * 30))  # 1–30 days apart

    ratings_df = pd.DataFrame({
        "userId":    user_ids,
        "movieId":   item_ids,
        "rating":    ratings_vals,
        "timestamp": timestamps,
    })
    ratings_df.to_csv(out / "ratings.csv", index=False)
    print(f"  ✓  ratings.csv       ({len(ratings_df):,} ratings)")

    # ── tags.csv ──────────────────────────────────────────────────────────
    tag_rows = []
    for uid in rng.choice(range(1, n_users + 1), size=min(n_users // 2, 100), replace=False):
        for mid in rng.choice(movie_ids, size=rng.integers(1, 6), replace=False):
            tag = rng.choice(TAGS)
            ts = base_ts + int(rng.integers(0, 3600 * 24 * 365))
            tag_rows.append({"userId": int(uid), "movieId": int(mid), "tag": tag, "timestamp": ts})
    tags_df = pd.DataFrame(tag_rows)
    tags_df.to_csv(out / "tags.csv", index=False)
    print(f"  ✓  tags.csv          ({len(tags_df)} tags)")

    # ── links.csv (minimal — required by some scripts) ────────────────────
    links_df = pd.DataFrame({
        "movieId": movie_ids,
        "imdbId":  [f"{1000000 + mid:07d}" for mid in movie_ids],
        "tmdbId":  [str(500000 + mid) for mid in movie_ids],
    })
    links_df.to_csv(out / "links.csv", index=False)
    print(f"  ✓  links.csv         ({len(links_df)} entries)")

    print()
    print("Done. Run the pipeline with:")
    print()
    print(f"  python scripts/build_all.py --data-dir {out_dir}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic MovieLens-format test data")
    parser.add_argument("--out-dir",             default="data/ml-test")
    parser.add_argument("--n-users",   type=int, default=200)
    parser.add_argument("--n-movies",  type=int, default=500)
    parser.add_argument("--ratings-per-user", type=int, default=25)
    args = parser.parse_args()
    generate(args.out_dir, args.n_users, args.n_movies, args.ratings_per_user)
