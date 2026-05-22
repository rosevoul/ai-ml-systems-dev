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

  const maxCount = funnel.pool
  const rows = STAGES.map(s => ({ ...s, count: funnel[s.key] }))

  container.innerHTML = `
    <div class="funnel-wrap">
      ${rows.map(row => {
        const pct = Math.max(Math.round((row.count / maxCount) * 100), 2)
        return `
          <div class="funnel-stage">
            <span class="funnel-label">${row.label}</span>
            <div class="funnel-bar-bg">
              <div class="funnel-bar-fill" data-width="${pct}" style="width:0%;background:${row.color};"></div>
            </div>
            <span class="funnel-count">${row.count.toLocaleString()}</span>
          </div>
        `
      }).join('')}
    </div>
  `

  requestAnimationFrame(() => {
    container.querySelectorAll<HTMLElement>('.funnel-bar-fill').forEach(bar => {
      bar.style.width = (bar.dataset['width'] ?? '0') + '%'
    })
  })
}
