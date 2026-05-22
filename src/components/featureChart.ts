import type { AppState } from '../data/types'

const LABELS: Record<string, string> = {
  two_tower_score:        'Two-Tower score',
  mbar_score:             'MBAR score',
  rank_transformer_score: 'Rank Transformer',
  graph_transformer_score:'Graph Transformer',
  movie_avg_rating:       'Avg movie rating',
  movie_popularity:       'Popularity',
  genre_overlap:          'Genre overlap',
  user_avg_rating:        'User avg rating',
  log_rating_count:       'Rating count',
  recency_score:          'Recency',
}

export function mountFeatureChart(container: HTMLElement, state: AppState): void {
  renderChart(container, state)
}

export function updateFeatureChart(container: HTMLElement, state: AppState): void {
  renderChart(container, state)
}

function renderChart(container: HTMLElement, state: AppState) {
  const uid = state.selectedUserId
  const contrib = state.intrinsics[uid]?.feature_contributions
  if (!contrib) { container.innerHTML = ''; return }

  const entries = Object.entries(contrib)
    .map(([k, v]) => ({ key: k, label: LABELS[k] ?? k, value: v }))
    .sort((a, b) => b.value - a.value)

  const maxVal = Math.max(...entries.map(e => Math.abs(e.value)), 0.01)

  container.innerHTML = `
    <div class="feat-chart-wrap">
      ${entries.map(e => {
        const pct = Math.round((Math.abs(e.value) / maxVal) * 100)
        return `
          <div class="feat-row">
            <span class="feat-label">${e.label}</span>
            <div class="feat-bar-bg">
              <div class="feat-bar-fill" data-width="${pct}" style="width:0%;"></div>
            </div>
            <span class="feat-val">${(e.value * 100).toFixed(1)}%</span>
          </div>
        `
      }).join('')}
    </div>
  `

  requestAnimationFrame(() => {
    container.querySelectorAll<HTMLElement>('.feat-bar-fill').forEach(bar => {
      bar.style.width = (bar.dataset['width'] ?? '0') + '%'
    })
  })
}
