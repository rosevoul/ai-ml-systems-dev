import type { AppState } from '../data/types'

export function renderLigrMatrix(container: HTMLElement, state: AppState): void {
  container.innerHTML = ''
  const uid = state.selectedUserId
  const ligr = state.intrinsics[uid]?.ligr
  if (!ligr || !ligr.candidates.length) {
    container.innerHTML = '<p style="color:var(--text-muted);font-size:0.82rem;padding:1rem;">No LiGR data for this user.</p>'
    return
  }

  const cands = ligr.candidates.slice(0, 10)
  const maxRel = Math.max(...cands.map(c => c.relevance_score), 0.01)
  const greedy = ligr.greedy_genre_coverage
  const ligrCov = ligr.ligr_genre_coverage
  const gain = ligrCov - greedy

  container.innerHTML = `
    <div style="display:flex;flex-direction:column;gap:1rem;">

      <div style="display:flex;gap:1rem;margin-bottom:0.5rem;">
        <div style="flex:1;background:var(--bg-elevated);border:1px solid var(--border);border-radius:8px;padding:0.75rem;">
          <p style="font-size:0.7rem;color:var(--text-muted);margin-bottom:2px;">GREEDY TOP-5 COVERAGE</p>
          <p style="font-size:1.25rem;font-weight:500;font-family:var(--font-mono);">${greedy} <span style="font-size:0.75rem;color:var(--text-muted)">genres</span></p>
        </div>
        <div style="flex:1;background:var(--accent-dim);border:1px solid var(--accent-glow);border-radius:8px;padding:0.75rem;">
          <p style="font-size:0.7rem;color:var(--accent);margin-bottom:2px;">LiGR SET COVERAGE</p>
          <p style="font-size:1.25rem;font-weight:500;font-family:var(--font-mono);color:var(--accent);">${ligrCov} <span style="font-size:0.75rem">genres</span></p>
        </div>
        <div style="flex:1;background:var(--teal-dim);border:1px solid rgba(13,148,136,0.3);border-radius:8px;padding:0.75rem;">
          <p style="font-size:0.7rem;color:var(--teal);margin-bottom:2px;">DIVERSITY GAIN</p>
          <p style="font-size:1.25rem;font-weight:500;font-family:var(--font-mono);color:var(--teal);">+${gain} <span style="font-size:0.75rem">genres</span></p>
        </div>
      </div>

      <div>
        <p style="font-size:0.72rem;color:var(--text-muted);margin-bottom:0.5rem;letter-spacing:0.04em;">RELEVANCE vs DIVERSITY GAIN — top 10 candidates</p>
        <div style="display:flex;flex-direction:column;gap:6px;">
          ${cands.map(c => {
            const relW = Math.round((c.relevance_score / maxRel) * 100)
            const divW = Math.round(c.diversity_gain * 100)
            const isNew = c.is_new_genre_for_user
            return `
              <div style="display:grid;grid-template-columns:120px 1fr 1fr 60px;gap:8px;align-items:center;">
                <span style="font-size:0.78rem;color:var(--text-secondary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${c.title.slice(0, 18)}</span>
                <div style="height:8px;background:var(--bg-elevated);border-radius:4px;overflow:hidden;">
                  <div style="width:${relW}%;height:100%;background:var(--accent);border-radius:4px;"></div>
                </div>
                <div style="height:8px;background:var(--bg-elevated);border-radius:4px;overflow:hidden;">
                  <div style="width:${divW}%;height:100%;background:var(--teal);border-radius:4px;"></div>
                </div>
                <span style="font-size:0.7rem;color:${isNew ? 'var(--teal)' : 'var(--text-muted)'};white-space:nowrap;">${isNew ? 'new genre' : ''}</span>
              </div>
            `
          }).join('')}
        </div>
        <div style="display:flex;gap:1.5rem;margin-top:0.75rem;">
          <div style="display:flex;align-items:center;gap:6px;font-size:0.72rem;color:var(--text-muted);">
            <div style="width:12px;height:6px;background:var(--accent);border-radius:3px;"></div> Relevance
          </div>
          <div style="display:flex;align-items:center;gap:6px;font-size:0.72rem;color:var(--text-muted);">
            <div style="width:12px;height:6px;background:var(--teal);border-radius:3px;"></div> Diversity gain
          </div>
        </div>
      </div>
    </div>
  `
}
