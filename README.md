# Faye RecSys Lab — GitHub Pages Portfolio Demo

Static portfolio demo for a modern recommender systems stack.

Implemented first model:

- Two-Tower retrieval
- XGBoost-style ranking
- MovieLens-style random users
- Recommendation output cards
- Local deterministic explanations
- One intrinsic model visual: embedding space + ranking feature contribution
- Homepage architecture diagram only, not a whole website mock

## Upload to GitHub Pages

1. Unzip this package.
2. Copy `index.html` and the `assets/` folder into your GitHub Pages repository root.
3. Commit and push.
4. Open your GitHub Pages URL.

This is a static site. No build step is required.

## Local preview

Run any simple static server from the unzipped folder:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

## OpenAI API key setup

Do not commit an OpenAI API key into this repository.

The page includes a private testing field where you can paste a temporary key. It is stored only in `sessionStorage` for the current browser tab. This is useful for quick local testing, but it is not safe for a public production site because browser code exposes credentials.

Recommended production setup:

```text
GitHub Pages frontend
        ↓
Serverless proxy endpoint on Vercel, Netlify, Cloudflare Workers, or Render
        ↓
OpenAI API
```

Store the key only on the server side:

```bash
OPENAI_API_KEY=sk-...
```

Then make the browser call your proxy, not OpenAI directly.

## Files

```text
index.html
assets/
  app.js
  styles.css
  architecture.svg
README.md
```

## Extend next

Recommended next models to add:

1. MBTR
2. LiGR
3. Rank Transformer
4. Graph Transformer

Each model should add exactly one intrinsic visual:

- MBTR: multi-behavior transition graph
- LiGR: user-item interaction graph with learned edge weights
- Rank Transformer: attention heatmap over user history and candidates
- Graph Transformer: neighborhood aggregation and message passing visual
