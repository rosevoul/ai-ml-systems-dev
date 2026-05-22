import type { AppState } from '../data/types'
import { pickRandomUser } from '../data/loader'
import type { AllData } from '../data/loader'

export function mountUserPanel(
  container: HTMLElement,
  state: AppState,
  data: AllData,
  onUserChange: (userId: string) => void,
): void {
  render(container, state, data, onUserChange)
}

export function updateUserPanel(
  container: HTMLElement,
  state: AppState,
  data: AllData,
  onUserChange: (userId: string) => void,
): void {
  render(container, state, data, onUserChange)
}

function render(container: HTMLElement, state: AppState, data: AllData, onUserChange: (id: string) => void) {
  const user = data.recs.users[state.selectedUserId]
  if (!user) return

  const history = [...user.history].sort((a, b) => b.rating - a.rating).slice(0, 8)

  container.innerHTML = `
    <div class="card" style="display:flex;flex-direction:column;gap:1rem;">
      <div class="user-meta">
        <span class="user-id-label">Active user</span>
        <span class="user-id-value">user_${state.selectedUserId}</span>
        <p style="font-size:0.82rem;color:var(--text-muted);margin-top:2px;">${user.history.length} ratings in training history</p>
      </div>
      <button class="new-user-btn" id="new-user-btn">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>
        New random user
      </button>
    </div>
    <div class="card">
      <p style="font-size:0.78rem;font-weight:500;color:var(--text-secondary);margin-bottom:0.75rem;letter-spacing:0.04em;">RATING HISTORY — top rated</p>
      <div class="history-list">
        ${history.map(h => `
          <div class="history-item">
            <span class="history-rating">${h.rating.toFixed(1)}★</span>
            <span class="history-title">${h.title}</span>
            <span class="history-genres">${h.genres.slice(0, 2).join(', ')}</span>
          </div>
        `).join('')}
      </div>
    </div>
  `

  container.style.display = 'grid'
  container.style.gridTemplateColumns = '1fr 2fr'
  container.style.gap = '1.5rem'
  container.style.alignItems = 'start'

  container.querySelector('#new-user-btn')?.addEventListener('click', () => {
    const next = pickRandomUser(data, state.selectedUserId)
    onUserChange(next)
  })
}
