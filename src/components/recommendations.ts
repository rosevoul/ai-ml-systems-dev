import type { AppState, Recommendation } from '../data/types'

export function mountRecommendations(container: HTMLElement, state: AppState): void {
  renderRecs(container, state)
}

export function updateRecommendations(container: HTMLElement, state: AppState): void {
  renderRecs(container, state)
}

function renderRecs(container: HTMLElement, state: AppState) {
  const uid = state.selectedUserId
  const recs = (state.recs.users[uid]?.recommendations ?? []).slice(0, 6)

  container.innerHTML = `
    <div class="rec-grid">
      ${recs.map((r, i) => recCard(r, i)).join('')}
    </div>
  `

  // Animate score bars after render
  requestAnimationFrame(() => {
    container.querySelectorAll<HTMLElement>('.score-bar-fill').forEach(bar => {
      const target = bar.dataset['width'] ?? '0'
      bar.style.width = target + '%'
    })
  })
}

function recCard(r: Recommendation, rank: number): string {
  const score = r.scores.xgboost_final ?? r.scores.rank_transformer ?? 0
  const maxScore = 1
  const barW = Math.round((score / maxScore) * 100)
  const yearStr = r.year ? ` (${r.year})` : ''

  return `
    <div class="rec-card">
      <span class="rec-rank">#${rank + 1}</span>
      <div>
        <p class="rec-title">${r.title}<span class="rec-year">${yearStr}</span></p>
        <div class="rec-genres">
          ${r.genres.slice(0, 3).map(g => `<span class="genre-pill">${g}</span>`).join('')}
        </div>
      </div>
      <div class="score-bar-wrap">
        <span class="score-label">${score.toFixed(2)}</span>
        <div class="score-bar-bg">
          <div class="score-bar-fill" data-width="${barW}" style="width:0%"></div>
        </div>
      </div>
      <p class="rec-explanation">${r.explanation}</p>
      <div class="rec-factors">
        ${r.factors.slice(0, 4).map(f => `<span class="factor-item">${f}</span>`).join('')}
      </div>
    </div>
  `
}
