"""
build_all.py — Full Pipeline Orchestrator
------------------------------------------
Runs all 10 pipeline stages in sequence.

Usage:
  # from repo root:
  python scripts/build_all.py
  python scripts/build_all.py --data-dir data/ml-latest-small
  python scripts/build_all.py --from-step 5   # resume from step N
  python scripts/build_all.py --json-out-dir ../faye-recsys/assets/data

Steps:
  1  preprocess          Load and clean MovieLens data
  2  two_tower           Train Two-Tower retrieval + generate embeddings
  3  mbar                Train MBAR sequential transformer
  4  ligr                Run LiGR set-wise re-ranking
  5  rank_transformer    Train Rank Transformer
  6  graph_transformer   Run Graph Transformer scoring
  7  xgboost             Train XGBoost feature ranker
  8  agentic             Build agentic orchestration traces
  9  rag                 Assemble RAG context and explanations
  10 export              Export all JSON files for the frontend
"""

import argparse
import importlib.util
import pickle
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def import_script(filename: str):
    """Import a script by filename (handles leading-digit names)."""
    path = ROOT / filename
    spec = importlib.util.spec_from_file_location(f"_step_{filename}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_pkl(out_dir: Path, name: str):
    p = out_dir / f"{name}.pkl"
    if not p.exists():
        raise FileNotFoundError(
            f"Missing {p.name} — run earlier steps first or lower --from-step."
        )
    with open(p, "rb") as f:
        return pickle.load(f)


def section(n: int, total: int, label: str):
    print(f"\n{'─'*60}")
    print(f"Step {n} / {total}  ·  {label}")
    print(f"{'─'*60}")


def run_pipeline(data_dir: str, out_dir: str, json_out_dir: str, from_step: int = 1):
    od = Path(out_dir)
    od.mkdir(parents=True, exist_ok=True)
    timings: dict[str, float] = {}

    def should_run(n: int) -> bool:
        return n >= from_step

    # ── Step 1 ────────────────────────────────────────────────────────────
    if should_run(1):
        section(1, 10, "Preprocessing")
        t0 = time.time()
        mod = import_script("01_preprocess.py")
        mod.load_and_preprocess(data_dir, out_dir)
        timings["preprocess"] = time.time() - t0

    # ── Step 2 ────────────────────────────────────────────────────────────
    if should_run(2):
        section(2, 10, "Two-Tower Retrieval")
        t0 = time.time()
        mod = import_script("02_two_tower.py")
        d = load_pkl(od, "preprocessed")
        mod.train_two_tower(d, od)
        timings["two_tower"] = time.time() - t0

    # ── Step 3 ────────────────────────────────────────────────────────────
    if should_run(3):
        section(3, 10, "MBAR Sequential Transformer")
        t0 = time.time()
        mod = import_script("03_mbar.py")
        d  = load_pkl(od, "preprocessed")
        tt = load_pkl(od, "two_tower")
        mod.run_mbar(d, tt, od)
        timings["mbar"] = time.time() - t0

    # ── Step 4 ────────────────────────────────────────────────────────────
    if should_run(4):
        section(4, 10, "LiGR Set-wise Re-ranking")
        t0 = time.time()
        mod = import_script("04_ligr.py")
        d  = load_pkl(od, "preprocessed")
        tt = load_pkl(od, "two_tower")
        mod.run_ligr(d, tt, od)
        timings["ligr"] = time.time() - t0

    # ── Step 5 ────────────────────────────────────────────────────────────
    if should_run(5):
        section(5, 10, "Rank Transformer")
        t0 = time.time()
        mod = import_script("05_rank_transformer.py")
        d  = load_pkl(od, "preprocessed")
        tt = load_pkl(od, "two_tower")
        mod.run_rank_transformer(d, tt, od)
        timings["rank_transformer"] = time.time() - t0

    # ── Step 6 ────────────────────────────────────────────────────────────
    if should_run(6):
        section(6, 10, "Graph Transformer")
        t0 = time.time()
        mod = import_script("06_graph_transformer.py")
        d  = load_pkl(od, "preprocessed")
        tt = load_pkl(od, "two_tower")
        mod.run_graph_transformer(d, tt, od)
        timings["graph_transformer"] = time.time() - t0

    # ── Step 7 ────────────────────────────────────────────────────────────
    if should_run(7):
        section(7, 10, "XGBoost Feature Ranker")
        t0 = time.time()
        mod = import_script("07_xgboost_ranker.py")
        d   = load_pkl(od, "preprocessed")
        tt  = load_pkl(od, "two_tower")
        mb  = load_pkl(od, "mbar")
        rtr = load_pkl(od, "rank_transformer")
        gtr = load_pkl(od, "graph_transformer")
        mod.run_xgboost_ranker(d, tt, mb, rtr, gtr, od)
        timings["xgboost"] = time.time() - t0

    # ── Step 8 ────────────────────────────────────────────────────────────
    if should_run(8):
        section(8, 10, "Agentic Orchestration Traces")
        t0 = time.time()
        mod = import_script("08_agentic_pipeline.py")
        d   = load_pkl(od, "preprocessed")
        tt  = load_pkl(od, "two_tower")
        xgb = load_pkl(od, "xgboost")
        mod.run_agentic_pipeline(d, tt, xgb, od)
        timings["agentic"] = time.time() - t0

    # ── Step 9 ────────────────────────────────────────────────────────────
    if should_run(9):
        section(9, 10, "RAG Context Assembly")
        t0 = time.time()
        mod = import_script("09_rag_assembly.py")
        d   = load_pkl(od, "preprocessed")
        tt  = load_pkl(od, "two_tower")
        xgb = load_pkl(od, "xgboost")
        mb  = load_pkl(od, "mbar")
        mod.run_rag_assembly(d, tt, xgb, mb, od)
        timings["rag"] = time.time() - t0

    # ── Step 10 ───────────────────────────────────────────────────────────
    if should_run(10):
        section(10, 10, "Export JSON")
        t0 = time.time()
        mod = import_script("10_export_json.py")
        mod.export_json(od, Path(json_out_dir))
        timings["export"] = time.time() - t0

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"\n{'═'*60}")
    print("Pipeline complete.")
    total = sum(timings.values())
    for name, elapsed in timings.items():
        print(f"  {name:<24} {elapsed:6.1f}s")
    print(f"  {'TOTAL':<24} {total:6.1f}s")
    print(f"{'═'*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Faye RecSys — full ML pipeline")
    parser.add_argument("--data-dir",     default="data/ml-latest-small")
    parser.add_argument("--out-dir",      default="outputs")
    parser.add_argument("--json-out-dir", default="../faye-recsys/assets/data")
    parser.add_argument("--from-step", type=int, default=1,
                        help="Resume pipeline from step N (1-10)")
    args = parser.parse_args()
    run_pipeline(args.data_dir, args.out_dir, args.json_out_dir, args.from_step)
