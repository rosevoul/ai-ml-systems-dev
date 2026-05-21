# FAYE RECSYS: End‑to‑End Transformer Recommendation Demo

This repository contains a small, self‑contained demo for a modern recommendation
system built on top of the MovieLens dataset. The goal is to showcase how
retrieval, various transformer‑based ranking models and generative retrieval
(RAG) can be combined into an interactive user experience. The site is static
and can be hosted on GitHub Pages or any static file server.

## Features

* **Interactive demo** – choose between five models (Two‑Tower + XGBoost,
  MBT4R/Transformers4Rec, LiGR, Rank Transformer and Graph Transformer) and
  view the top recommendations for a sample user along with a short
  explanation.
* **Dark‑themed layout** – inspired by modern ML dashboards, featuring a
  hero section, navigation bar and cards for each recommendation.
* **Modular design** – the code is organised into HTML, CSS and JavaScript
  files with a small JSON file holding precomputed recommendations. This
  makes it easy to swap in your own data.

## Getting Started

1. Clone or download this repository.
2. Open `index.html` in your browser to preview the project locally.
3. Click **Explore Demo** to jump to the interactive demo page.
4. Use the dropdown to select a model and see recommendations.

### Deploy to GitHub Pages

1. Create a new repository on GitHub (for example
   `your‑username/your‑recsys‑demo`).
2. Copy the contents of `faye_recsys_project` into the root of your new
   repository.
3. Commit and push all files.
4. In your repository’s **Settings** → **Pages**, select the branch to serve the
   site (usually `main`) and set the root as the source. GitHub will build
   and publish your site. After a few minutes, it will be accessible at
   `https://your‑username.github.io/your‑recsys‑demo/`.

### Training Your Own Models (Optional)

The JSON file `recommendations.json` contains placeholder recommendations.
To generate real recommendations from the MovieLens dataset:

1. Download the MovieLens dataset (e.g. the **ml‑latest‑small** set) from
   the [official site](https://grouplens.org/datasets/movielens/).
2. Use your preferred ML framework (e.g. PyTorch or TensorFlow) to train
   models described in your portfolio:
   * **Two‑Tower Retrieval + XGBoost** – learn user and item embeddings using
     matrix factorisation or two‑tower architecture, then train a gradient
     boosted decision tree ranker on candidate pairs.
   * **MBT4R/Transformers4Rec** – implement a sequential transformer model for
     session‑based recommendation.
   * **LiGR** – implement the LinkedIn Generative Ranking architecture for
     set‑wise ranking.
   * **Rank Transformer** – implement a permutation‑invariant ranking model
     with listwise objectives.
   * **Graph Transformer** – sequentialise user–item graphs and apply
     transformer attention across relational data.
3. Export the top recommendations and explanations to a JSON file in the
   same format as `recommendations.json` and drop it into the project
   directory. Update `demo.js` if necessary.

### Notes

* The demo uses placeholder explanations and movie titles. Replace these
  entries with outputs from your trained models to reflect their true
  behaviour.
* This is a static demo and does not include the full RAG or agentic
  workflow; however, the architecture has been designed to accommodate
  future expansion.

Enjoy building your portfolio!