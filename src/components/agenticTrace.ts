import type { AppState, TraceStep } from '../data/types'

const ICONS: Record<string, string> = {
  Planner: 'P', Retriever: 'R', Aligner: 'Al', Summarizer: 'S', Ranker: 'Rk', Responder: 'Re',
}

let animTimer: ReturnType<typeof setTimeout> | null = null

export function mountAgenticTrace(container: HTMLElement, state: AppState): void {
  const steps = state.trace[state.selectedUserId]?.steps ?? []
  renderTrace(container, steps, -1)
}

export function updateAgenticTrace(container: HTMLElement, state: AppState): void {
  if (animTimer) clearTimeout(animTimer)
  const steps = state.trace[state.selectedUserId]?.steps ?? []
  renderTrace(container, steps, -1)
}

function renderTrace(container: HTMLElement, steps: TraceStep[], activeIdx: number) {
  const totalLatency = steps.reduce((s, st) => s + st.latency_ms, 0)

  container.innerHTML = `
    <div class="trace-controls">
      <button class="trace-play-btn" id="trace-play">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>
        Play trace
      </button>
      <span style="font-size:0.78rem;color:var(--text-muted);font-family:var(--font-mono);">Total: ${totalLatency}ms</span>
    </div>
    <div class="trace-steps">
      ${steps.map((step, i) => `
        <div class="trace-step${i <= activeIdx ? ' active' : ''}" data-step="${i}">
          <div class="trace-step-icon">${ICONS[step.agent] ?? step.agent[0]}</div>
          <div class="trace-step-body">
            <p class="trace-agent-name">${step.agent}</p>
            <div class="trace-step-io">
              <div class="trace-io-block">
                <p class="trace-io-label">Input</p>
                <p class="trace-io-text">${step.input}</p>
              </div>
              <div class="trace-io-block">
                <p class="trace-io-label">Output</p>
                <p class="trace-io-text">${step.output}</p>
              </div>
            </div>
            <p class="trace-latency">${step.latency_ms}ms · ${step.data_used}</p>
          </div>
        </div>
      `).join('')}
    </div>
  `

  container.querySelector('#trace-play')?.addEventListener('click', () => {
    playAnimation(container, steps)
  })
}

function playAnimation(container: HTMLElement, steps: TraceStep[]) {
  if (animTimer) clearTimeout(animTimer)

  // Reset all to inactive
  container.querySelectorAll('.trace-step').forEach(el => el.classList.remove('active'))

  let i = 0
  function activateNext() {
    if (i >= steps.length) return
    const stepEl = container.querySelector(`.trace-step[data-step="${i}"]`)
    stepEl?.classList.add('active')
    stepEl?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    i++
    animTimer = setTimeout(activateNext, steps[i - 1]?.latency_ms ? Math.max(steps[i - 1].latency_ms * 3, 600) : 800)
  }

  activateNext()
}
