"""
03_mbar.py — MBAR: Multi-head Behaviour-Aware Ranker
-----------------------------------------------------
Sequential transformer that encodes a user's rated-movie history as a token
sequence.  The final hidden state is dotted with candidate embeddings to
produce scores, and the layer-2 self-attention weights are saved for the
frontend attention heatmap.

Architecture:
  Input  : sequence of movie embeddings (from Two-Tower movie tower), max len 20
  Encoder: 2-layer Transformer encoder, 4 heads, d_model=64
  Output : score(candidate) = dot(CLS_repr, candidate_emb)

Outputs saved to mbar.pkl:
  scores         : dict[uid, dict[mid, float]]
  attention_weights : dict[uid, {weights: [[float]], history_titles: [str], rec_titles: [str]}]
"""

import argparse
import math
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
MAX_SEQ = 20
EPOCHS = 10
BATCH_SIZE = 256
LR = 5e-4
SEED = 42
TOP_N_RECS = 10   # titles to store attention weights for


class SeqDataset(Dataset):
    """Each sample: user history tokens → predict a held-out positive."""

    def __init__(self, user_ids, user_history, movie_embs, movie_ids_set):
        self.samples = []
        rng = np.random.default_rng(SEED)
        movie_id_list = list(movie_ids_set)

        for uid in user_ids:
            hist = [h for h in user_history.get(uid, []) if h["movieId"] in movie_embs]
            if len(hist) < 3:
                continue
            # leave-one-out: last item is positive, rest is context
            context = hist[:-1][-MAX_SEQ:]
            pos_id = hist[-1]["movieId"]
            neg_id = rng.choice(movie_id_list)
            while neg_id in {h["movieId"] for h in hist}:
                neg_id = rng.choice(movie_id_list)

            seq = np.stack([movie_embs[h["movieId"]] for h in context])
            # Pad to MAX_SEQ
            pad_len = MAX_SEQ - len(seq)
            if pad_len > 0:
                seq = np.vstack([np.zeros((pad_len, D_MODEL), dtype=np.float32), seq])
            mask = np.array([True] * pad_len + [False] * len(context), dtype=bool)

            self.samples.append((seq, mask, movie_embs[pos_id], movie_embs[neg_id]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        seq, mask, pos, neg = self.samples[idx]
        return (
            torch.tensor(seq),
            torch.tensor(mask),
            torch.tensor(pos),
            torch.tensor(neg),
        )


class MBARModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.cls_token = nn.Parameter(torch.randn(1, 1, D_MODEL) * 0.02)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=D_MODEL, nhead=N_HEADS, dim_feedforward=D_MODEL * 4,
            dropout=0.1, activation="gelu", batch_first=True, norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=N_LAYERS)
        self.proj = nn.Linear(D_MODEL, D_MODEL)

    def forward(self, seq, src_key_padding_mask=None):
        """seq: (B, T, D)  mask: (B, T) True=pad"""
        B = seq.size(0)
        cls = self.cls_token.expand(B, -1, -1)
        # Prepend CLS; extend mask
        x = torch.cat([cls, seq], dim=1)
        if src_key_padding_mask is not None:
            cls_mask = torch.zeros(B, 1, dtype=torch.bool, device=seq.device)
            full_mask = torch.cat([cls_mask, src_key_padding_mask], dim=1)
        else:
            full_mask = None

        out = self.encoder(x, src_key_padding_mask=full_mask)
        user_repr = self.proj(out[:, 0, :])  # CLS position
        return nn.functional.normalize(user_repr, dim=-1)

    def get_attention_weights(self, seq, src_key_padding_mask=None):
        """Return attention weights from the last encoder layer (B, H, T+1, T+1)."""
        B = seq.size(0)
        cls = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls, seq], dim=1)
        if src_key_padding_mask is not None:
            cls_mask = torch.zeros(B, 1, dtype=torch.bool, device=seq.device)
            full_mask = torch.cat([cls_mask, src_key_padding_mask], dim=1)
        else:
            full_mask = None

        # Run through each layer, capture weights on last
        for i, layer in enumerate(self.encoder.layers):
            x_norm = layer.norm1(x)
            attn_out, attn_weights = layer.self_attn(
                x_norm, x_norm, x_norm,
                key_padding_mask=full_mask,
                need_weights=True,
                average_attn_weights=False,  # (B, H, T, T)
            )
            x = x + layer.dropout1(attn_out)
            x = x + layer.dropout2(layer.linear2(layer.dropout(layer.activation(layer.linear1(layer.norm2(x))))))

        return attn_weights  # (B, H, T+1, T+1)


def run_mbar(data: dict, two_tower: dict, out_dir: Path):
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    user_history = data["user_history"]
    user_ids = data["user_ids"]
    movie_meta = data["movie_meta"]
    movie_embs = two_tower["movie_embeddings"]
    candidates = two_tower["candidates"]

    movie_ids_set = set(movie_embs.keys())
    dataset = SeqDataset(user_ids, user_history, movie_embs, movie_ids_set)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = MBARModel().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR)

    print(f"Training MBAR on {device} for {EPOCHS} epochs …")
    model.train()
    for epoch in range(1, EPOCHS + 1):
        total_loss = 0.0
        for seq, mask, pos, neg in loader:
            seq, mask, pos, neg = seq.to(device), mask.to(device), pos.to(device), neg.to(device)
            optimizer.zero_grad()
            u = model(seq, mask)
            pos_s = (u * pos).sum(-1)
            neg_s = (u * neg).sum(-1)
            loss = -torch.log(torch.sigmoid(pos_s - neg_s) + 1e-9).mean()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"  Epoch {epoch:2d}/{EPOCHS}  loss={total_loss/len(loader):.4f}")

    # ── score candidates ──────────────────────────────────────────────────
    print("Scoring candidates …")
    model.eval()
    scores_out: dict[int, dict[int, float]] = {}
    attention_out: dict[int, dict] = {}

    with torch.no_grad():
        for uid in tqdm(user_ids, desc="  MBAR inference"):
            hist = [h for h in user_history.get(uid, []) if h["movieId"] in movie_embs]
            if not hist:
                continue
            context = hist[-MAX_SEQ:]
            seq_np = np.stack([movie_embs[h["movieId"]] for h in context])
            pad_len = MAX_SEQ - len(seq_np)
            if pad_len > 0:
                seq_np = np.vstack([np.zeros((pad_len, D_MODEL), dtype=np.float32), seq_np])
            mask_np = np.array([True] * pad_len + [False] * len(context), dtype=bool)

            seq_t = torch.tensor(seq_np).unsqueeze(0).to(device)
            mask_t = torch.tensor(mask_np).unsqueeze(0).to(device)

            u_repr = model(seq_t, mask_t).squeeze(0).cpu().numpy()

            cands = candidates.get(uid, [])
            sc: dict[int, float] = {}
            for mid in cands:
                if mid in movie_embs:
                    sc[mid] = float(np.dot(u_repr, movie_embs[mid]))
            scores_out[uid] = sc

            # ── attention weights for top recs ────────────────────────────
            attn_weights = model.get_attention_weights(seq_t, mask_t)
            # Mean over heads, take CLS row (idx 0), drop CLS column, take token positions
            w = attn_weights[0].mean(0)[0, 1:].cpu().numpy()  # (T+1_seq,)
            # Trim to actual (non-padded) history
            actual_w = w[pad_len:]  # (len(context),)

            # Build matrix: rows = history items, cols = top rec items
            top_recs = sorted(sc, key=sc.get, reverse=True)[:TOP_N_RECS]
            attn_matrix = []
            for _ in top_recs:
                # Each rec column gets the attention distribution over history
                # (attention source = history item attending to CLS → representative)
                attn_matrix.append(actual_w.tolist())
            # Transpose: rows=history, cols=recs
            attn_matrix_T = list(map(list, zip(*attn_matrix))) if attn_matrix else []

            attention_out[uid] = {
                "history_titles": [h["title"][:30] for h in context],
                "rec_titles": [movie_meta.get(mid, {}).get("title", "")[:30] for mid in top_recs],
                "weights": attn_matrix_T,  # shape: [len(context), TOP_N_RECS]
            }

    result = {"scores": scores_out, "attention": attention_out}
    out_path = out_dir / "mbar.pkl"
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
    run_mbar(data, two_tower, out_dir)
