import type { AppState } from '../data/types'

const STAGES = [
  { key: 'pool',       label: 'Movie pool',      color: 'rgba(255,255,255,0.15)' },
  { key: 'two_tower',  label: 'Two-Tower top-k',  color: 'var(--teal)' },
  { key: 'reranked',   label: 'Transformer re-ranked', color: 'var(--accent)' },
  { key: 'final',      label: 'Final recommendations', color: '#818cf8' },
] as const

export function mountCandidateFunnel(container: HTMLElement, state: AppState): void {
  renderFunnel(container, state)
}

export function updateCandidateFunnel(container: HTMLElement, state: AppState): void {
  renderFunnel(container, state)
}

function renderFunnel(container: HTMLElement, state: AppState) {
  const uid = state.selectedUserId
  const funnel = state.intrinsics[uid]?.candidate_funnel
  if (!funnel) { container.innerHTML = ''; return }

  const rows = STAGES.map(s => ({ ...s, count: funnel[s.key] }))

  // Log scale so the pool→candidates drop doesn't crush the small bars
  const logVal = (n: number) => Math.log10(Math.max(n, 1))
  const maxLog = logVal(rows[0].count)
  const pctOf  = (n: number) => Math.max(Math.round((logVal(n) / maxLog) * 100), 6)

  container.innerHTML = `
    <div class="funnel-wrap">
      ${rows.map(row => {
        const pct = pctOf(row.count)
        const label = row.count >= 1000
          ? `${(row.count / 1000).toFixed(1)}k`
          : row.count.toLocaleString()
        return `
          <div class="funnel-stage">
            <span class="funnel-label">${row.label}</span>
            <div class="funnel-bar-bg">
              <div class="funnel-bar-fill" data-width="${pct}" style="width:0%;background:${row.color};"></div>
            </div>
            <span class="funnel-count">${label}</span>
          </div>
        `
      }).join('')}
      <p style="margin-top:0.6rem;font-size:0.72rem;color:var(--text-muted);">Bar scale is logarithmic</p>
    </div>
  `

  requestAnimationFrame(() => {
    container.querySelectorAll<HTMLElement>('.funnel-bar-fill').forEach(bar => {
      bar.style.width = (bar.dataset['width'] ?? '0') + '%'
    })
  })
}
