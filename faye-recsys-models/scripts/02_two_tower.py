"""
02_two_tower.py
---------------
Two-Tower retrieval model.

Architecture:
  User tower  : MLP(user_feat_dim → 128 → 64)
  Movie tower : MLP(movie_feat_dim → 128 → 64)
  Training    : BPR loss with in-batch negatives
  Retrieval   : FAISS flat-IP index (fallback: cosine numpy)

Outputs (added to preprocessed.pkl or saved separately as two_tower.pkl):
  user_embeddings   : dict[int, np.ndarray(64,)]
  movie_embeddings  : dict[int, np.ndarray(64,)]
  umap_users        : dict[int, {x, y}]
  umap_movies       : dict[int, {x, y}]
  candidates        : dict[int, list[int]]   top-100 per user
  scores            : dict[int, dict[int, float]]  two-tower score per candidate
"""

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.embeddings import (
    movie_feature_vector,
    project_umap,
    user_feature_vector,
)

EMBED_DIM = 64
HIDDEN_DIM = 128
EPOCHS = 15
BATCH_SIZE = 512
LR = 1e-3
NUM_NEGATIVES = 4
SEED = 42
TOP_K = 100


# ── Dataset ──────────────────────────────────────────────────────────────────

class BPRDataset(Dataset):
    def __init__(self, user_ids, user_feat, movie_ids, movie_feat, user_history):
        self.samples = []
        movie_id_list = list(movie_feat.keys())
        user_movie_sets = {uid: set(h["movieId"] for h in hist) for uid, hist in user_history.items()}

        rng = np.random.default_rng(SEED)
        for uid in user_ids:
            pos_movies = [h["movieId"] for h in user_history.get(uid, []) if h["movieId"] in movie_feat]
            if not pos_movies:
                continue
            uf = user_feat[uid]
            watched = user_movie_sets.get(uid, set())
            for pos_mid in pos_movies:
                for _ in range(NUM_NEGATIVES):
                    neg_mid = rng.choice(movie_id_list)
                    while neg_mid in watched:
                        neg_mid = rng.choice(movie_id_list)
                    self.samples.append((uf, movie_feat[pos_mid], movie_feat[neg_mid]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        uf, pos_mf, neg_mf = self.samples[idx]
        return (
            torch.tensor(uf),
            torch.tensor(pos_mf),
            torch.tensor(neg_mf),
        )


# ── Model ─────────────────────────────────────────────────────────────────────

class Tower(nn.Module):
    def __init__(self, in_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, HIDDEN_DIM),
            nn.LayerNorm(HIDDEN_DIM),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(HIDDEN_DIM, EMBED_DIM),
        )

    def forward(self, x):
        emb = self.net(x)
        return nn.functional.normalize(emb, dim=-1)


class TwoTowerModel(nn.Module):
    def __init__(self, user_dim: int, movie_dim: int):
        super().__init__()
        self.user_tower = Tower(user_dim)
        self.movie_tower = Tower(movie_dim)

    def forward(self, user_feat, pos_feat, neg_feat):
        u = self.user_tower(user_feat)
        p = self.movie_tower(pos_feat)
        n = self.movie_tower(neg_feat)
        pos_score = (u * p).sum(dim=-1)
        neg_score = (u * n).sum(dim=-1)
        loss = -torch.log(torch.sigmoid(pos_score - neg_score) + 1e-9).mean()
        return loss


# ── Training ──────────────────────────────────────────────────────────────────

def train_two_tower(data: dict, out_dir: Path):
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    genre_vocab = data["genre_vocab"]
    movie_meta = data["movie_meta"]
    user_history = data["user_history"]
    user_ids = data["user_ids"]
    movie_ids = data["movie_ids"]

    print("Building feature vectors …")
    user_feat: dict[int, np.ndarray] = {}
    for uid in tqdm(user_ids, desc="  user features"):
        user_feat[uid] = user_feature_vector(user_history.get(uid, []), movie_meta, genre_vocab)

    movie_feat: dict[int, np.ndarray] = {}
    for mid in tqdm(movie_ids, desc="  movie features"):
        movie_feat[mid] = movie_feature_vector(movie_meta.get(mid, {}), genre_vocab)

    user_dim = next(iter(user_feat.values())).shape[0]
    movie_dim = next(iter(movie_feat.values())).shape[0]
    print(f"  user_dim={user_dim}  movie_dim={movie_dim}")

    dataset = BPRDataset(user_ids, user_feat, movie_ids, movie_feat, user_history)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = TwoTowerModel(user_dim, movie_dim).to(device)
    optimizer = optim.AdamW(model.parameters(), lr=LR)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    print(f"Training on {device} for {EPOCHS} epochs …")
    model.train()
    for epoch in range(1, EPOCHS + 1):
        total_loss = 0.0
        for uf, pos_mf, neg_mf in loader:
            uf, pos_mf, neg_mf = uf.to(device), pos_mf.to(device), neg_mf.to(device)
            optimizer.zero_grad()
            loss = model(uf, pos_mf, neg_mf)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        scheduler.step()
        print(f"  Epoch {epoch:2d}/{EPOCHS}  loss={total_loss/len(loader):.4f}")

    # ── generate embeddings ────────────────────────────────────────────────
    print("Generating embeddings …")
    model.eval()
    with torch.no_grad():
        user_embs: dict[int, np.ndarray] = {}
        for uid in tqdm(user_ids, desc="  user embeddings"):
            uf = torch.tensor(user_feat[uid]).unsqueeze(0).to(device)
            user_embs[uid] = model.user_tower(uf).squeeze(0).cpu().numpy()

        movie_embs: dict[int, np.ndarray] = {}
        movie_id_list = list(movie_feat.keys())
        movie_feat_batch = torch.tensor(
            np.stack([movie_feat[mid] for mid in movie_id_list])
        ).to(device)
        movie_embs_arr = model.movie_tower(movie_feat_batch).cpu().numpy()
        for i, mid in enumerate(movie_id_list):
            movie_embs[mid] = movie_embs_arr[i]

    # ── retrieval (FAISS or numpy) ─────────────────────────────────────────
    print(f"Retrieving top-{TOP_K} candidates …")
    user_movies_watched = {uid: set(h["movieId"] for h in hist) for uid, hist in user_history.items()}

    movie_embs_matrix = np.stack([movie_embs[mid] for mid in movie_id_list]).astype(np.float32)

    try:
        import faiss
        index = faiss.IndexFlatIP(EMBED_DIM)
        faiss.normalize_L2(movie_embs_matrix)
        index.add(movie_embs_matrix)
        use_faiss = True
    except ImportError:
        use_faiss = False

    candidates: dict[int, list[int]] = {}
    scores_map: dict[int, dict[int, float]] = {}

    for uid in tqdm(user_ids, desc="  retrieval"):
        ue = user_embs[uid].astype(np.float32).reshape(1, -1)
        watched = user_movies_watched.get(uid, set())

        if use_faiss:
            faiss.normalize_L2(ue)
            raw_scores, raw_indices = index.search(ue, TOP_K + len(watched) + 10)
            sims = raw_scores[0]
            idxs = raw_indices[0]
        else:
            ue_norm = ue / (np.linalg.norm(ue) + 1e-9)
            sims_all = (movie_embs_matrix @ ue_norm.T).flatten()
            idxs = np.argsort(-sims_all)
            sims = sims_all[idxs]

        cands, sc = [], {}
        for i, idx in enumerate(idxs):
            mid = movie_id_list[idx]
            if mid not in watched and len(cands) < TOP_K:
                cands.append(mid)
                sc[mid] = float(sims[i])

        candidates[uid] = cands
        scores_map[uid] = sc

    # ── UMAP projections ──────────────────────────────────────────────────
    print("Projecting embeddings to 2D …")
    # Sample at most 2000 movies for UMAP to keep it fast
    sample_ids = movie_id_list[:2000]
    sample_embs = np.stack([movie_embs[mid] for mid in sample_ids])
    proj_2d = project_umap(sample_embs)

    umap_movies = {
        mid: {"id": mid, "title": movie_meta.get(mid, {}).get("title", ""), "genres": movie_meta.get(mid, {}).get("genres", []), "x": float(proj_2d[i, 0]), "y": float(proj_2d[i, 1])}
        for i, mid in enumerate(sample_ids)
    }

    user_sample = user_ids[:500]
    user_embs_arr = np.stack([user_embs[uid] for uid in user_sample])
    user_proj = project_umap(user_embs_arr)
    umap_users = {
        uid: {"id": uid, "x": float(user_proj[i, 0]), "y": float(user_proj[i, 1])}
        for i, uid in enumerate(user_sample)
    }

    result = {
        "user_embeddings": user_embs,
        "movie_embeddings": movie_embs,
        "umap_movies": umap_movies,
        "umap_users": umap_users,
        "candidates": candidates,
        "scores": scores_map,
    }

    out_path = out_dir / "two_tower.pkl"
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
    train_two_tower(data, out_dir)
