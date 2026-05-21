const movies = [
  { id: 1, title: "Toy Story", year: 1995, genres: ["Animation", "Adventure", "Comedy"], popularity: 0.96, freshness: 0.28, vec: [0.93, 0.22], features: { genre: .92, similarity: .88, popularity: .78, novelty: .36, diversity: .42 } },
  { id: 2, title: "The Matrix", year: 1999, genres: ["Action", "Sci-Fi"], popularity: 0.94, freshness: 0.36, vec: [0.16, 0.92], features: { genre: .82, similarity: .93, popularity: .84, novelty: .42, diversity: .55 } },
  { id: 3, title: "Spirited Away", year: 2001, genres: ["Animation", "Fantasy"], popularity: 0.88, freshness: 0.42, vec: [0.78, 0.66], features: { genre: .88, similarity: .86, popularity: .71, novelty: .59, diversity: .74 } },
  { id: 4, title: "The Dark Knight", year: 2008, genres: ["Action", "Crime", "Drama"], popularity: 0.98, freshness: 0.55, vec: [0.2, 0.78], features: { genre: .78, similarity: .84, popularity: .91, novelty: .32, diversity: .49 } },
  { id: 5, title: "Arrival", year: 2016, genres: ["Sci-Fi", "Drama"], popularity: 0.82, freshness: 0.77, vec: [0.32, 0.86], features: { genre: .84, similarity: .89, popularity: .64, novelty: .72, diversity: .69 } },
  { id: 6, title: "Parasite", year: 2019, genres: ["Thriller", "Drama"], popularity: 0.91, freshness: 0.86, vec: [0.44, 0.57], features: { genre: .76, similarity: .71, popularity: .82, novelty: .63, diversity: .88 } },
  { id: 7, title: "Mad Max: Fury Road", year: 2015, genres: ["Action", "Adventure"], popularity: 0.86, freshness: 0.74, vec: [0.11, 0.69], features: { genre: .72, similarity: .79, popularity: .73, novelty: .61, diversity: .52 } },
  { id: 8, title: "Her", year: 2013, genres: ["Romance", "Sci-Fi", "Drama"], popularity: 0.74, freshness: 0.68, vec: [0.47, 0.81], features: { genre: .77, similarity: .76, popularity: .51, novelty: .73, diversity: .82 } },
  { id: 9, title: "Interstellar", year: 2014, genres: ["Sci-Fi", "Adventure", "Drama"], popularity: 0.93, freshness: 0.72, vec: [0.28, 0.91], features: { genre: .91, similarity: .94, popularity: .85, novelty: .45, diversity: .57 } },
  { id: 10, title: "The Grand Budapest Hotel", year: 2014, genres: ["Comedy", "Drama"], popularity: 0.71, freshness: 0.70, vec: [0.64, 0.34], features: { genre: .74, similarity: .63, popularity: .44, novelty: .68, diversity: .91 } },
  { id: 11, title: "Everything Everywhere All at Once", year: 2022, genres: ["Action", "Comedy", "Sci-Fi"], popularity: 0.89, freshness: 0.96, vec: [0.62, 0.75], features: { genre: .86, similarity: .81, popularity: .78, novelty: .76, diversity: .83 } },
  { id: 12, title: "Dune: Part Two", year: 2024, genres: ["Sci-Fi", "Adventure"], popularity: 0.92, freshness: 1.0, vec: [0.23, 0.97], features: { genre: .86, similarity: .91, popularity: .84, novelty: .79, diversity: .54 } },
  { id: 13, title: "Amélie", year: 2001, genres: ["Romance", "Comedy"], popularity: 0.68, freshness: 0.41, vec: [0.82, 0.29], features: { genre: .8, similarity: .66, popularity: .38, novelty: .7, diversity: .76 } },
  { id: 14, title: "Whiplash", year: 2014, genres: ["Drama", "Music"], popularity: 0.79, freshness: 0.71, vec: [0.5, 0.42], features: { genre: .7, similarity: .68, popularity: .6, novelty: .57, diversity: .71 } },
  { id: 15, title: "Coco", year: 2017, genres: ["Animation", "Family"], popularity: 0.84, freshness: 0.79, vec: [0.88, 0.43], features: { genre: .91, similarity: .8, popularity: .67, novelty: .52, diversity: .66 } },
  { id: 16, title: "Blade Runner 2049", year: 2017, genres: ["Sci-Fi", "Mystery"], popularity: 0.81, freshness: 0.8, vec: [0.24, 0.83], features: { genre: .81, similarity: .87, popularity: .61, novelty: .69, diversity: .62 } },
  { id: 17, title: "Knives Out", year: 2019, genres: ["Mystery", "Comedy"], popularity: 0.8, freshness: 0.87, vec: [0.69, 0.48], features: { genre: .69, similarity: .67, popularity: .58, novelty: .74, diversity: .85 } },
  { id: 18, title: "Inside Out", year: 2015, genres: ["Animation", "Family", "Comedy"], popularity: 0.85, freshness: 0.74, vec: [0.91, 0.37], features: { genre: .93, similarity: .82, popularity: .68, novelty: .45, diversity: .58 } },
  { id: 19, title: "The Social Network", year: 2010, genres: ["Drama"], popularity: 0.77, freshness: 0.61, vec: [0.49, 0.52], features: { genre: .66, similarity: .62, popularity: .55, novelty: .5, diversity: .64 } },
  { id: 20, title: "Inception", year: 2010, genres: ["Action", "Sci-Fi", "Thriller"], popularity: 0.95, freshness: 0.6, vec: [0.18, 0.88], features: { genre: .86, similarity: .9, popularity: .89, novelty: .38, diversity: .46 } },
  { id: 21, title: "Soul", year: 2020, genres: ["Animation", "Drama", "Music"], popularity: 0.76, freshness: 0.9, vec: [0.86, 0.5], features: { genre: .84, similarity: .77, popularity: .48, novelty: .78, diversity: .72 } },
  { id: 22, title: "Nope", year: 2022, genres: ["Horror", "Sci-Fi"], popularity: 0.67, freshness: 0.96, vec: [0.35, 0.75], features: { genre: .67, similarity: .65, popularity: .42, novelty: .88, diversity: .92 } },
  { id: 23, title: "Past Lives", year: 2023, genres: ["Romance", "Drama"], popularity: 0.63, freshness: 0.98, vec: [0.74, 0.51], features: { genre: .72, similarity: .61, popularity: .35, novelty: .86, diversity: .89 } },
  { id: 24, title: "John Wick", year: 2014, genres: ["Action", "Thriller"], popularity: 0.78, freshness: 0.7, vec: [0.07, 0.63], features: { genre: .73, similarity: .76, popularity: .59, novelty: .55, diversity: .45 } },
  { id: 25, title: "The Farewell", year: 2019, genres: ["Drama", "Comedy"], popularity: 0.62, freshness: 0.87, vec: [0.71, 0.4], features: { genre: .75, similarity: .58, popularity: .32, novelty: .82, diversity: .9 } },
  { id: 26, title: "Black Panther", year: 2018, genres: ["Action", "Adventure", "Sci-Fi"], popularity: 0.89, freshness: 0.83, vec: [0.18, 0.71], features: { genre: .8, similarity: .78, popularity: .79, novelty: .47, diversity: .61 } },
  { id: 27, title: "La La Land", year: 2016, genres: ["Romance", "Music", "Drama"], popularity: 0.75, freshness: 0.77, vec: [0.73, 0.35], features: { genre: .78, similarity: .64, popularity: .51, novelty: .62, diversity: .77 } },
  { id: 28, title: "The Batman", year: 2022, genres: ["Action", "Crime", "Drama"], popularity: 0.84, freshness: 0.95, vec: [0.2, 0.73], features: { genre: .76, similarity: .8, popularity: .68, novelty: .66, diversity: .52 } }
];

const users = [
  { id: "U-104", label: "Animation loyalist", history: [1, 3, 15, 18], taste: [0.87, 0.42], segments: ["family-friendly", "high repeat rate", "low novelty"] },
  { id: "U-219", label: "Sci-fi explorer", history: [2, 5, 9, 16], taste: [0.25, 0.88], segments: ["sci-fi", "premium catalog", "medium novelty"] },
  { id: "U-307", label: "Action heavy watcher", history: [4, 7, 20, 24], taste: [0.15, 0.74], segments: ["action", "franchise affinity", "popularity sensitive"] },
  { id: "U-411", label: "Indie drama profile", history: [6, 14, 19, 23], taste: [0.58, 0.49], segments: ["drama", "award winners", "high novelty"] },
  { id: "U-512", label: "Comedy + romance", history: [10, 13, 17, 27], taste: [0.72, 0.37], segments: ["romance", "comedy", "diversity positive"] },
  { id: "U-628", label: "Fresh releases seeker", history: [11, 12, 22, 28], taste: [0.33, 0.85], segments: ["recent movies", "genre mixing", "high freshness"] },
  { id: "U-733", label: "Balanced mainstream", history: [1, 4, 9, 11], taste: [0.45, 0.67], segments: ["mainstream", "high confidence", "medium diversity"] },
  { id: "U-840", label: "Mystery and social drama", history: [6, 17, 19, 25], taste: [0.61, 0.47], segments: ["mystery", "drama", "discovery open"] },
  { id: "U-918", label: "Music and emotion", history: [14, 21, 23, 27], taste: [0.73, 0.44], segments: ["music", "emotional drama", "soft exploration"] },
  { id: "U-1002", label: "Superhero + sci-fi", history: [4, 12, 20, 26], taste: [0.21, 0.84], segments: ["sci-fi", "action", "high popularity"] },
  { id: "U-1120", label: "Animation + arthouse", history: [3, 10, 13, 21], taste: [0.78, 0.51], segments: ["animation", "international", "high diversity"] },
  { id: "U-1288", label: "Thriller discovery", history: [6, 20, 22, 24], taste: [0.32, 0.68], segments: ["thriller", "dark themes", "medium novelty"] }
];

const weights = {
  similarity: 0.42,
  genre: 0.2,
  popularity: 0.14,
  novelty: 0.12,
  diversity: 0.08,
  freshness: 0.04
};

let state = {
  userIndex: 1,
  topRecs: [],
  selectedRec: null,
  jitter: 0.005
};

const $ = id => document.getElementById(id);
const userSelect = $("userSelect");

function init() {
  users.forEach((user, idx) => {
    const option = document.createElement("option");
    option.value = idx;
    option.textContent = `${user.id} · ${user.label}`;
    userSelect.appendChild(option);
  });

  userSelect.value = state.userIndex;
  $("metricUsers").textContent = users.length;
  $("metricMovies").textContent = movies.length;

  ["modelSelect", "userSelect", "noveltySlider", "diversitySlider"].forEach(id => {
    $(id).addEventListener("input", () => {
      if (id === "userSelect") state.userIndex = Number(userSelect.value);
      render();
    });
  });

  $("randomUserBtn").addEventListener("click", () => {
    state.userIndex = Math.floor(Math.random() * users.length);
    userSelect.value = state.userIndex;
    render();
  });

  $("rerunBtn").addEventListener("click", () => {
    state.jitter = Math.random() * 0.02;
    render();
  });

  $("saveKeyBtn").addEventListener("click", saveApiKey);
  $("clearKeyBtn").addEventListener("click", clearApiKey);
  restoreApiStatus();
  render();
}

function cosine(a, b) {
  const dot = a[0] * b[0] + a[1] * b[1];
  const na = Math.sqrt(a[0] ** 2 + a[1] ** 2);
  const nb = Math.sqrt(b[0] ** 2 + b[1] ** 2);
  return dot / (na * nb);
}

function genreOverlap(user, movie) {
  const historyGenres = new Set(user.history.flatMap(id => movieById(id).genres));
  const overlap = movie.genres.filter(g => historyGenres.has(g)).length;
  return overlap / Math.max(movie.genres.length, 1);
}

function movieById(id) {
  return movies.find(m => m.id === id);
}

function scoreMovie(user, movie) {
  const watched = user.history.includes(movie.id);
  const noveltyPref = Number($("noveltySlider").value) / 100;
  const diversityPref = Number($("diversitySlider").value) / 100;
  const similarity = Math.max(0, cosine(user.taste, movie.vec));
  const genre = genreOverlap(user, movie);
  const novelty = (movie.features.novelty * 0.6 + noveltyPref * 0.4);
  const diversity = (movie.features.diversity * 0.55 + diversityPref * 0.45);
  const base =
    weights.similarity * similarity +
    weights.genre * genre +
    weights.popularity * movie.popularity +
    weights.novelty * novelty +
    weights.diversity * diversity +
    weights.freshness * movie.freshness +
    deterministicJitter(user.id, movie.id);

  return {
    ...movie,
    score: watched ? -1 : Math.min(0.99, base + state.jitter),
    components: {
      similarity,
      genre,
      popularity: movie.popularity,
      novelty,
      diversity,
      freshness: movie.freshness
    }
  };
}

function deterministicJitter(userId, movieId) {
  const raw = [...`${userId}-${movieId}`].reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
  return (raw % 17) / 1000;
}

function getRecommendations() {
  const user = users[state.userIndex];
  const retrievalCandidates = movies
    .map(movie => ({ ...movie, retrievalScore: cosine(user.taste, movie.vec) }))
    .filter(movie => !user.history.includes(movie.id))
    .sort((a, b) => b.retrievalScore - a.retrievalScore)
    .slice(0, 12);

  const ranked = retrievalCandidates
    .map(movie => scoreMovie(user, movie))
    .sort((a, b) => b.score - a.score)
    .slice(0, 6);

  state.topRecs = ranked;
  state.selectedRec = ranked[0];
  return { user, retrievalCandidates, ranked };
}

function render() {
  const { user, retrievalCandidates, ranked } = getRecommendations();
  renderUser(user);
  renderTrace(user, retrievalCandidates, ranked);
  renderRecommendations(ranked, user);
  renderEmbedding(user, ranked);
  renderFeatureBars(state.selectedRec || ranked[0]);
}

function renderUser(user) {
  const history = user.history.map(movieById);
  $("userProfile").innerHTML = `
    <p class="muted"><strong>${user.id}</strong> · ${user.label}</p>
    <div class="user-history">
      ${history.map(m => `<span class="movie-chip">${m.title}</span>`).join("")}
    </div>
    <div class="user-history">
      ${user.segments.map(s => `<span class="genre-chip">${s}</span>`).join("")}
    </div>
  `;
}

function renderTrace(user, candidates, ranked) {
  $("pipelineTrace").innerHTML = `
    <li><strong>User tower:</strong> compresses watched movies into taste vector [${user.taste.map(v => v.toFixed(2)).join(", ")}].</li>
    <li><strong>Item tower:</strong> embeds ${movies.length} movies using genre, year, popularity, and synthetic MovieLens-style signals.</li>
    <li><strong>Retrieval:</strong> keeps top ${candidates.length} nearest candidates by user-item embedding similarity.</li>
    <li><strong>XGBoost ranker:</strong> reranks candidates with similarity, genre overlap, popularity, novelty, diversity, and freshness.</li>
    <li><strong>Explanation layer:</strong> exposes the strongest positive drivers for the top ${ranked.length} recommendations.</li>
  `;
}

function renderRecommendations(ranked, user) {
  $("recommendations").innerHTML = ranked.map((movie, idx) => {
    const drivers = topDrivers(movie.components, 3);
    const genreText = movie.genres.map(g => `<span class="genre-chip">${g}</span>`).join("");
    return `
      <article class="rec-card" data-movie-id="${movie.id}">
        <span class="rec-rank">#${idx + 1} recommendation</span>
        <div class="rec-title">${movie.title} <span class="muted">(${movie.year})</span></div>
        <div class="user-history">${genreText}</div>
        <div class="score-row"><span>Rank score</span><strong>${movie.score.toFixed(3)}</strong></div>
        <div class="score-bar"><span style="width:${Math.round(movie.score * 100)}%"></span></div>
        <p class="explanation">${buildExplanation(user, movie, drivers)}</p>
      </article>
    `;
  }).join("");

  document.querySelectorAll(".rec-card").forEach(card => {
    card.addEventListener("click", () => {
      state.selectedRec = state.topRecs.find(m => m.id === Number(card.dataset.movieId));
      renderFeatureBars(state.selectedRec);
      document.querySelectorAll(".rec-card").forEach(c => c.style.borderColor = "rgba(148, 163, 184, 0.22)");
      card.style.borderColor = "rgba(103, 232, 249, 0.8)";
    });
  });
}

function topDrivers(components, k) {
  return Object.entries(components)
    .sort((a, b) => b[1] - a[1])
    .slice(0, k)
    .map(([name, value]) => ({ name, value }));
}

function buildExplanation(user, movie, drivers) {
  const driverText = drivers.map(d => `${label(d.name)} ${d.value.toFixed(2)}`).join(", ");
  const seenGenres = new Set(user.history.flatMap(id => movieById(id).genres));
  const overlap = movie.genres.filter(g => seenGenres.has(g));
  const overlapText = overlap.length ? `It matches prior ${overlap.join("/")} behavior` : "It adds catalog diversity beyond the user history";
  return `${overlapText}. Main score drivers: ${driverText}.`;
}

function label(name) {
  return name.replace(/([A-Z])/g, " $1").replace(/^./, c => c.toUpperCase());
}

function renderEmbedding(user, ranked) {
  const svg = $("embeddingSvg");
  const width = 520;
  const height = 360;
  const pad = 42;
  const x = v => pad + v * (width - pad * 2);
  const y = v => height - pad - v * (height - pad * 2);
  const topIds = new Set(ranked.map(m => m.id));
  const historyIds = new Set(user.history);

  svg.innerHTML = `
    <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="rgba(148,163,184,.28)" />
    <line x1="${pad}" y1="${height - pad}" x2="${pad}" y2="${pad}" stroke="rgba(148,163,184,.28)" />
    <text x="${width - 148}" y="${height - 14}" fill="#94a3b8" font-size="12">latent dimension 1</text>
    <text x="12" y="30" fill="#94a3b8" font-size="12">latent dimension 2</text>
    ${movies.map(movie => {
      const isTop = topIds.has(movie.id);
      const isHistory = historyIds.has(movie.id);
      const fill = isHistory ? "#fb923c" : isTop ? "#67e8f9" : "#64748b";
      const r = isHistory ? 7 : isTop ? 8 : 4;
      return `<g><circle cx="${x(movie.vec[0])}" cy="${y(movie.vec[1])}" r="${r}" fill="${fill}" opacity="${isTop || isHistory ? 1 : .42}" />${isTop ? `<text x="${x(movie.vec[0]) + 10}" y="${y(movie.vec[1]) + 4}" fill="#e2e8f0" font-size="11">${movie.title}</text>` : ""}</g>`;
    }).join("")}
    <circle cx="${x(user.taste[0])}" cy="${y(user.taste[1])}" r="12" fill="#a78bfa" stroke="#fff" stroke-width="2" />
    <text x="${x(user.taste[0]) + 14}" y="${y(user.taste[1]) - 12}" fill="#f8fafc" font-size="13" font-weight="700">User embedding</text>
  `;
}

function renderFeatureBars(movie) {
  if (!movie) return;
  const features = Object.entries(movie.components)
    .sort((a, b) => b[1] - a[1]);

  $("featureBars").innerHTML = `
    <p class="muted">Selected movie: <strong>${movie.title}</strong>. These are the current ranking features feeding the simulated XGBoost layer.</p>
    ${features.map(([name, value]) => `
      <div class="feature-row">
        <span>${label(name)}</span>
        <div class="feature-track"><span style="width:${Math.round(value * 100)}%"></span></div>
        <strong>${value.toFixed(2)}</strong>
      </div>
    `).join("")}
  `;
}

function saveApiKey() {
  const value = $("apiKeyInput").value.trim();
  if (!value) return;
  sessionStorage.setItem("openai_api_key", value);
  $("apiKeyInput").value = "";
  restoreApiStatus();
}

function clearApiKey() {
  sessionStorage.removeItem("openai_api_key");
  restoreApiStatus();
}

function restoreApiStatus() {
  const hasKey = Boolean(sessionStorage.getItem("openai_api_key"));
  $("apiStatus").textContent = hasKey
    ? "Session key stored in this browser tab. Do not use this pattern for a public production site."
    : "No key stored. Demo explanations use local deterministic logic.";
}

document.addEventListener("DOMContentLoaded", init);
