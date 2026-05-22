"""
check_setup.py — Environment validation
----------------------------------------
Run this before the full pipeline to confirm all dependencies are present.

  python check_setup.py

Prints a pass/fail table and exact install commands for anything missing.
"""

import importlib
import subprocess
import sys
from pathlib import Path

# ── colour helpers ────────────────────────────────────────────────────────────
def green(s):  return f"\033[32m{s}\033[0m"
def red(s):    return f"\033[31m{s}\033[0m"
def yellow(s): return f"\033[33m{s}\033[0m"
def bold(s):   return f"\033[1m{s}\033[0m"
def dim(s):    return f"\033[2m{s}\033[0m"

# ── packages to check ─────────────────────────────────────────────────────────
REQUIRED = [
    ("numpy",        "numpy>=1.24",       True),
    ("pandas",       "pandas>=2.0",       True),
    ("sklearn",      "scikit-learn>=1.3", True),
    ("tqdm",         "tqdm>=4.65",        True),
    ("torch",        "torch>=2.0",        True),
]

OPTIONAL = [
    ("xgboost",      "xgboost>=1.7",      "XGBoost ranker (falls back to sklearn GBT)"),
    ("faiss",        "faiss-cpu>=1.7.4",  "FAISS retrieval (falls back to numpy cosine)"),
    ("umap",         "umap-learn>=0.5.3", "UMAP 2D projection (falls back to PCA)"),
]


def check_pkg(import_name: str):
    try:
        mod = importlib.import_module(import_name)
        version = getattr(mod, "__version__", "?")
        return True, version
    except ImportError:
        return False, None


def check_python():
    v = sys.version_info
    ok = v >= (3, 10)
    return ok, f"{v.major}.{v.minor}.{v.micro}"


def check_data_dir():
    candidates = [
        Path("data/ml-latest-small"),
        Path("../data/ml-latest-small"),
    ]
    required_files = ["ratings.csv", "movies.csv"]
    for d in candidates:
        if all((d / f).exists() for f in required_files):
            return True, str(d)
    return False, None


def main():
    print()
    print(bold("  faye-recsys-models — environment check"))
    print(dim("  " + "─" * 50))
    print()

    all_ok = True
    missing_required = []
    missing_optional = []

    # ── Python version ────────────────────────────────────────────────────
    py_ok, py_ver = check_python()
    status = green("  ✓") if py_ok else red("  ✗")
    note = f"  {py_ver}" if py_ok else f"  {py_ver}  (need 3.10+)"
    print(f"{status}  Python           {note}")
    if not py_ok:
        all_ok = False

    print()
    print(dim("  Required packages"))

    # ── Required packages ─────────────────────────────────────────────────
    for import_name, install_name, _ in REQUIRED:
        ok, version = check_pkg(import_name)
        status = green("  ✓") if ok else red("  ✗")
        ver_str = dim(f"  {version}") if ok else red("  not found")
        label = import_name.ljust(16)
        print(f"{status}  {label}{ver_str}")
        if not ok:
            all_ok = False
            missing_required.append(install_name)

    print()
    print(dim("  Optional packages  (pipeline falls back gracefully if missing)"))

    # ── Optional packages ─────────────────────────────────────────────────
    for import_name, install_name, note in OPTIONAL:
        ok, version = check_pkg(import_name)
        status = green("  ✓") if ok else yellow("  –")
        ver_str = dim(f"  {version}") if ok else dim(f"  not installed  ({note})")
        label = import_name.ljust(16)
        print(f"{status}  {label}{ver_str}")
        if not ok:
            missing_optional.append(install_name)

    # ── MovieLens data ────────────────────────────────────────────────────
    print()
    print(dim("  Data"))
    data_ok, data_path = check_data_dir()
    status = green("  ✓") if data_ok else red("  ✗")
    note = dim(f"  found at {data_path}") if data_ok else red("  not found")
    print(f"{status}  MovieLens data   {note}")
    if not data_ok:
        all_ok = False

    # ── Output dir ────────────────────────────────────────────────────────
    outputs_ok = Path("outputs").exists() or True  # will be created by pipeline
    print(f"{green('  ✓')}  outputs/         {dim('  will be created automatically')}")

    # ── Summary ───────────────────────────────────────────────────────────
    print()
    print(dim("  " + "─" * 50))

    if missing_required:
        print()
        print(red("  Missing required packages — install with:"))
        print()
        print(f"    pip install {' '.join(missing_required)}")
        print()

    if missing_optional:
        print(yellow("  Optional packages (recommended):"))
        print()
        print(f"    pip install {' '.join(missing_optional)}")
        print()

    if not data_ok:
        print(red("  MovieLens data not found."))
        print()
        print("  Download from:  https://grouplens.org/datasets/movielens/latest/")
        print("  Extract into:   data/ml-latest-small/")
        print()
        print("  Or run the dry-run generator first:")
        print("    python generate_test_data.py")
        print()

    if all_ok and not missing_required:
        print(green(bold("  ✓  All checks passed. Ready to run:")))
        print()
        print("    python scripts/build_all.py --data-dir data/ml-latest-small")
    else:
        print(yellow("  Fix the issues above, then run:"))
        print()
        print("    python scripts/build_all.py --data-dir data/ml-latest-small")

    print()


if __name__ == "__main__":
    main()
