# faye-recsys-models

Offline ML pipeline for the [faye-recsys](../faye-recsys) portfolio site.
Trains all models, runs the full pipeline, and exports precomputed JSON files
consumed by the static frontend.

---

## Requirements

- Python 3.10+
- MovieLens latest-small dataset

```bash
pip install -r requirements.txt
```

Core dependencies are `torch`, `numpy`, `pandas`, `scikit-learn`, and `tqdm`.
`xgboost`, `faiss-cpu`, and `umap-learn` are optional but recommended — the
pipeline falls back gracefully if they are missing.

---

## Setup

### 1. Get MovieLens data

Download [MovieLens latest-small](https://grouplens.org/datasets/movielens/latest/)
and extract it:

```bash
mkdir -p data/ml-latest-small
# Place ratings.csv, movies.csv, tags.csv, links.csv here
```

### 2. Run the full pipeline

```bash
python scripts/build_all.py \
  --data-dir data/ml-latest-small \
  --out-dir outputs \
  --json-out-dir ../faye-recsys/assets/data
```

This takes ~10–20 minutes on a CPU (M-series Mac or modern laptop).
With a CUDA GPU, the neural model steps complete in under 3 minutes.

### 3. Resume from a specific step

If a step fails, resume without re-running earlier steps:

```bash
python scripts/build_all.py --from-step 5
```

---

## Pipeline Steps

| Step | Script | Output |
|------|--------|--------|
| 1 | `01_preprocess.py` | `outputs/preprocessed.pkl` |
| 2 | `02_two_tower.py` | `outputs/two_tower.pkl` |
| 3 | `03_mbar.py` | `outputs/mbar.pkl` |
| 4 | `04_ligr.py` | `outputs/ligr.pkl` |
| 5 | `05_rank_transformer.py` | `outputs/rank_transformer.pkl` |
| 6 | `06_graph_transformer.py` | `outputs/graph_transformer.pkl` |
| 7 | `07_xgboost_ranker.py` | `outputs/xgboost.pkl` |
| 8 | `08_agentic_pipeline.py` | `outputs/agentic.pkl` |
| 9 | `09_rag_assembly.py` | `outputs/rag.pkl` |
| 10 | `10_export_json.py` | `assets/data/*.json` |

Each script can also be run standalone for development:

```bash
python scripts/02_two_tower.py --out-dir outputs
```

---

## Output JSON Files

| File | Description |
|------|-------------|
| `recommendations.json` | Per-user top-10 recommendations with all model scores, explanations, and RAG context |
| `users.json` | User IDs and rating histories |
| `movies.json` | Movie metadata (title, year, genres, stats) |
| `embeddings_2d.json` | UMAP-projected user and movie embeddings for the scatter plot |
| `pipeline_trace.json` | Per-user agentic orchestration trace (6 agent steps) |
| `model_intrinsics.json` | Per-user visualisation data: MBAR attention weights, LiGR set coverage, Rank Transformer bump chart data, Graph Transformer subgraph |

---

## Model Design Notes

### Two-Tower Retrieval
Lightweight PyTorch MLP trained with BPR (Bayesian Personalized Ranking) loss
on MovieLens interaction data. User tower encodes genre preference + rating
behaviour; movie tower encodes genre, popularity, and average rating.
Retrieval uses FAISS flat-IP index (or numpy cosine as fallback). Embeddings
are projected to 2D with UMAP for the scatter visualisation.

### MBAR (Sequential)
2-layer Transformer encoder over the user's rated movie sequence. The CLS
token representation is dotted with candidate embeddings to produce scores.
Layer-2 self-attention weights are exported directly as the heatmap data
shown on the frontend.

### LiGR (Set-wise)
Maximal Marginal Relevance re-ranking that balances relevance (Two-Tower
score) against intra-set genre diversity. The frontend visualises the coverage
gain vs. greedy top-K selection.

### Rank Transformer (Global)
Transformer encoder over the full candidate set, using retrieval rank as
sinusoidal positional encoding. Each item's final score comes from a linear
head over its contextualised representation. Rank displacements vs. Two-Tower
are exported for the bump chart.

### Graph Transformer
Two-layer graph attention approximation on the user-item bipartite graph.
User representations are assembled by attention-weighted aggregation of rated
movie embeddings; candidate scores incorporate 2-hop collaborative signals.
User ego-subgraphs are exported for the force-directed graph visualisation.

### XGBoost Ranker
Gradient-boosted tree trained on a 10-dimensional feature set combining all
upstream model scores with movie quality and user affinity features.
Acts as the final stage of the agentic Ranker step. Feature importances and
per-recommendation SHAP-style contributions are exported for the bar chart.

---

## Future Extensions (v2)

- Replace MBAR with a full BERT4Rec implementation
- Replace LiGR MMR with a learned set transformer (SetRank)
- Add LightGCN as an alternative graph-based retrieval model
- Online feedback loop: log implicit signals from the frontend and fine-tune
  the XGBoost ranker periodically via a GitHub Actions workflow
- Dense RAG retrieval with sentence-transformers replacing TF-IDF

---

## Repo Structure

```
faye-recsys-models/
  scripts/
    build_all.py              Orchestrates all 10 steps
    01_preprocess.py
    02_two_tower.py
    03_mbar.py
    04_ligr.py
    05_rank_transformer.py
    06_graph_transformer.py
    07_xgboost_ranker.py
    08_agentic_pipeline.py
    09_rag_assembly.py
    10_export_json.py
    utils/
      embeddings.py           Feature vector builders + UMAP/PCA projection
      graph_builder.py        Bipartite graph + subgraph extraction
      rag_retriever.py        TF-IDF document index + explanation generator
  data/
    ml-latest-small/          Place MovieLens CSV files here
  outputs/                    Intermediate .pkl files (git-ignored)
  requirements.txt
  README.md
```
