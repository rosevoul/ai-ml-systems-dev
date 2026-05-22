import type { AppState, ModelKey } from '../data/types'

interface TabDef { key: ModelKey; label: string }

const TABS: TabDef[] = [
  { key: 'mbar',              label: 'MBAR' },
  { key: 'ligr',              label: 'LiGR' },
  { key: 'rank_transformer',  label: 'Rank Transformer' },
  { key: 'graph_transformer', label: 'Graph Transformer' },
]

export function mountModelTabs(
  container: HTMLElement,
  state: AppState,
  onTabChange: (key: ModelKey) => void,
): void {
  container.innerHTML = `
    <div class="model-tabs" role="tablist">
      ${TABS.map(t => `
        <button
          class="model-tab${state.activeModel === t.key ? ' active' : ''}"
          data-tab="${t.key}"
          role="tab"
          aria-selected="${state.activeModel === t.key}"
        >${t.label}</button>
      `).join('')}
    </div>
  `

  container.querySelectorAll<HTMLButtonElement>('.model-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      onTabChange(btn.dataset['tab'] as ModelKey)
    })
  })
}

export function updateModelTabs(container: HTMLElement, state: AppState, onTabChange: (key: ModelKey) => void): void {
  mountModelTabs(container, state, onTabChange)
}

// ── Candidate list with animated reorder ─────────────────────────────────────
export function renderCandidateList(container: HTMLElement, state: AppState): void {
  const uid = state.selectedUserId
  const recs = state.recs.users[uid]?.recommendations ?? []

  // Sort candidates by active model score
  const modelKey = state.activeModel
  const sorted = [...recs].sort((a, b) => {
    const sa = a.scores[modelKey as keyof typeof a.scores] ?? 0
    const sb = b.scores[modelKey as keyof typeof b.scores] ?? 0
    return sb - sa
  })

  // Get Two-Tower order for delta badges
  const ttSorted = [...recs].sort((a, b) => (b.scores.two_tower ?? 0) - (a.scores.two_tower ?? 0))
  const ttRank: Record<number, number> = {}
  ttSorted.forEach((r, i) => { ttRank[r.movieId] = i + 1 })

  const maxScore = Math.max(...sorted.map(r => r.scores[modelKey as keyof typeof r.scores] ?? 0)) || 1

  container.innerHTML = `
    <div style="margin-bottom:0.75rem;">
      <p class="viz-title">Ranked candidates — ${TABS.find(t => t.key === modelKey)?.label}</p>
    </div>
    <div class="candidate-list">
      ${sorted.slice(0, 12).map((r, rank) => {
        const score = (r.scores[modelKey as keyof typeof r.scores] ?? 0) as number
        const tt = ttRank[r.movieId] ?? rank + 1
        const delta = tt - (rank + 1)
        const deltaStr = delta > 0 ? `+${delta}` : delta < 0 ? `${delta}` : '–'
        const deltaClass = delta > 0 ? 'delta-up' : delta < 0 ? 'delta-down' : 'delta-same'
        const barWidth = Math.round((score / maxScore) * 100)
        return `
          <div class="candidate-row">
            <span class="candidate-rank">${rank + 1}</span>
            <span class="candidate-title">${r.title}</span>
            <div style="width:60px;height:3px;background:var(--bg-elevated);border-radius:2px;overflow:hidden;flex-shrink:0;">
              <div style="width:${barWidth}%;height:100%;background:var(--accent);border-radius:2px;"></div>
            </div>
            <span class="delta-badge ${deltaClass}">${deltaStr}</span>
          </div>
        `
      }).join('')}
    </div>
  `
}
