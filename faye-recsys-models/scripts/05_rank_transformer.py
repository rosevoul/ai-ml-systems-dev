"""
05_rank_transformer.py — Rank Transformer
------------------------------------------
Global-context transformer that reranks candidates by attending over the
entire candidate set simultaneously, using retrieval rank as positional signal.

The key property visualised on the frontend: rank displacements — which
candidates moved up/down vs. their original Two-Tower position (bump chart).

Architecture:
  Input  : candidate embeddings (from Two-Tower movie tower) + sinusoidal
           positional encoding from retrieval rank
  Encoder: 2-layer Transformer encoder, 4 heads, d_model=64
  Output : scalar score per item (via linear head on each token)

Training: pointwise regression on normalised Two-Tower scores
          (the model learns to refine them with global context).

Outputs saved to rank_transformer.pkl:
  scores       : dict[uid, dict[mid, float]]
  rank_data    : dict[uid, list[{title, two_tower_rank, rank_transformer_rank,
                                  two_tower_score, rank_transformer_score}]]
"""

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))

D_MODEL = 64
N_HEADS = 4
N_LAYERS = 2
MAX_CANDS = 100
EPOCHS = 8
BATCH_SIZE = 128
LR = 5e-4
SEED = 42


def sinusoidal_pe(ranks: np.ndarray, d_model: int = D_MODEL) -> np.ndarray:
    """Sinusoidal positional encoding based on retrieval rank."""
    pe = np.zeros((len(ranks), d_model), dtype=np.float32)
    for i, rank in enumerate(ranks):
        for k in range(0, d_model, 2):
            pe[i, k] = np.sin(rank / (10000 ** (k / d_model)))
            if k + 1 < d_model:
                pe[i, k + 1] = np.cos(rank / (10000 ** (k / d_model)))
    return pe


class CandidateSetDataset(Dataset):
    def __init__(self, user_ids, candidates, tt_scores, movie_embs, max_cands=MAX_CANDS):
        self.samples = []
        for uid in user_ids:
            cands = candidates.get(uid, [])[:max_cands]
            if len(cands) < 5:
                continue
            embs, scores, ranks = [], [], []
            for rank, mid in enumerate(cands):
                if mid in movie_embs:
                    embs.append(movie_embs[mid])
                    scores.append(tt_scores.get(uid, {}).get(mid, 0.0))
                    ranks.append(rank)

            if len(embs) < 5:
                continue

            embs_arr = np.stack(embs)
            pe = sinusoidal_pe(np.array(ranks))
            x = embs_arr + pe  # additive positional encoding
            y = np.array(scores, dtype=np.float32)
            y = (y - y.min()) / (y.max() - y.min() + 1e-9)  # normalise to [0,1]

            self.samples.append((x.astype(np.float32), y, ranks, [cands[r] for r in range(len(embs))]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        x, y, ranks, mids = self.samples[idx]
        return torch.tensor(x), torch.tensor(y)


class RankTransformerModel(nn.Module):
    def __init__(self):
        super().__init__()
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=D_MODEL, nhead=N_HEADS, dim_feedforward=D_MODEL * 4,
            dropout=0.1, activation="gelu", batch_first=True, norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=N_LAYERS)
        self.score_head = nn.Linear(D_MODEL, 1)

    def forward(self, x):
        """x: (B, T, D) → scores: (B, T)"""
        out = self.encoder(x)
        return self.score_head(out).squeeze(-1)


def run_rank_transformer(data: dict, two_tower: dict, out_dir: Path):
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    user_ids = data["user_ids"]
    movie_meta = data["movie_meta"]
    candidates = two_tower["candidates"]
    tt_scores = two_tower["scores"]
    movie_embs = two_tower["movie_embeddings"]

    dataset = CandidateSetDataset(user_ids, candidates, tt_scores, movie_embs)
    # Pad/truncate sequences to a fixed length for batching
    max_len = max(s[0].shape[0] for s in dataset.samples) if dataset.samples else MAX_CANDS

    def collate(batch):
        xs, ys = zip(*batch)
        T = max(x.shape[0] for x in xs)
        xs_pad = torch.zeros(len(xs), T, D_MODEL)
        ys_pad = torch.zeros(len(ys), T)
        masks = torch.ones(len(xs), T, dtype=torch.bool)
        for i, (x, y) in enumerate(zip(xs, ys)):
            n = x.shape[0]
            xs_pad[i, :n] = x
            ys_pad[i, :n] = y
            masks[i, :n] = False
        return xs_pad, ys_pad, masks

    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate, num_workers=0)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = RankTransformerModel().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR)
    criterion = nn.MSELoss(reduction="none")

    print(f"Training Rank Transformer on {device} for {EPOCHS} epochs …")
    model.train()
    for epoch in range(1, EPOCHS + 1):
        total_loss = 0.0
        for x, y, mask in loader:
            x, y, mask = x.to(device), y.to(device), mask.to(device)
            optimizer.zero_grad()
            pred = model(x)
            loss_mat = criterion(pred, y)
            loss = (loss_mat * (~mask).float()).sum() / (~mask).float().sum()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"  Epoch {epoch:2d}/{EPOCHS}  loss={total_loss/len(loader):.4f}")

    # ── generate per-user re-ranked scores ────────────────────────────────
    print("Generating Rank Transformer scores …")
    model.eval()
    scores_out: dict[int, dict[int, float]] = {}
    rank_data_out: dict[int, list] = {}

    with torch.no_grad():
        for uid in tqdm(user_ids, desc="  RT inference"):
            cands = candidates.get(uid, [])
            if not cands:
                continue

            embs, valid_mids, ranks = [], [], []
            for rank, mid in enumerate(cands):
                if mid in movie_embs:
                    embs.append(movie_embs[mid])
                    valid_mids.append(mid)
                    ranks.append(rank)

            if not embs:
                continue

            embs_arr = np.stack(embs).astype(np.float32)
            pe = sinusoidal_pe(np.array(ranks))
            x = torch.tensor(embs_arr + pe).unsqueeze(0).to(device)
            rt_scores = model(x).squeeze(0).cpu().numpy()

            sc: dict[int, float] = {}
            for i, mid in enumerate(valid_mids):
                sc[mid] = float(rt_scores[i])
            scores_out[uid] = sc

            # Build bump chart data
            tt_sorted = sorted(valid_mids, key=lambda m: tt_scores.get(uid, {}).get(m, 0), reverse=True)
            rt_sorted = sorted(valid_mids, key=lambda m: sc.get(m, 0), reverse=True)
            tt_rank_map = {mid: rank for rank, mid in enumerate(tt_sorted)}
            rt_rank_map = {mid: rank for rank, mid in enumerate(rt_sorted)}

            rank_data_out[uid] = [
                {
                    "movieId": mid,
                    "title": movie_meta.get(mid, {}).get("title", "")[:40],
                    "two_tower_rank": tt_rank_map[mid],
                    "rank_transformer_rank": rt_rank_map[mid],
                    "two_tower_score": float(tt_scores.get(uid, {}).get(mid, 0)),
                    "rank_transformer_score": float(sc.get(mid, 0)),
                }
                for mid in valid_mids[:50]
            ]

    result = {"scores": scores_out, "rank_data": rank_data_out}
    out_path = out_dir / "rank_transformer.pkl"
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
    run_rank_transformer(data, two_tower, out_dir)
