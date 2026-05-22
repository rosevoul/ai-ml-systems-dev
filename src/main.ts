import './styles/main.css'
import { loadAll, pickRandomUser } from './data/loader'
import type { AllData } from './data/loader'
import type { AppState, ModelKey } from './data/types'

import { mountArchitecture } from './components/architecture'
import { mountUserPanel, updateUserPanel } from './components/userPanel'
import { mountEmbeddingScatter } from './components/embeddingScatter'
import { mountModelTabs, updateModelTabs, renderCandidateList } from './components/modelTabs'
import { renderAttentionHeatmap } from './components/attentionHeatmap'
import { renderLigrMatrix } from './components/ligrMatrix'
import { renderBumpChart } from './components/bumpChart'
import { renderGraphViz } from './components/graphViz'
import { mountAgenticTrace, updateAgenticTrace } from './components/agenticTrace'
import { mountRagInspector, updateRagInspector } from './components/ragInspector'
import { mountRecommendations, updateRecommendations } from './components/recommendations'
import { mountCandidateFunnel, updateCandidateFunnel } from './components/candidateFunnel'
import { mountFeatureChart, updateFeatureChart } from './components/featureChart'
import { mountPipelineTrace } from './components/pipelineTrace'

// ── Element refs ──────────────────────────────────────────────────────────────
const $ = (id: string) => document.getElementById(id)!

async function init() {
  let data: AllData
  try {
    data = await loadAll()
  } catch (e) {
    console.error('Failed to load data:', e)
    hideLoading()
    $('loading-overlay').innerHTML = `
      <p style="color:#f87171;font-size:0.9rem;max-width:400px;text-align:center;padding:2rem;">
        Could not load data files.<br/>
        Run the ML pipeline first to generate <code>assets/data/*.json</code>,<br/>
        then serve with <code>npm run dev</code>.
      </p>
    `
    return
  }

  const state: AppState = {
    selectedUserId: pickRandomUser(data),
    activeModel: 'mbar',
    recs: data.recs,
    embeddings: data.embeddings,
    trace: data.trace,
    intrinsics: data.intrinsics,
  }

  // ── Mount static components ───────────────────────────────────────────────
  mountArchitecture($('arch-diagram'))
  mountPipelineTrace($('pipeline-trace-list'), state)

  // ── Mount user-dependent components ───────────────────────────────────────
  mountAll(state, data)

  hideLoading()
}

function mountAll(state: AppState, data: AllData) {
  // User panel
  mountUserPanel($('user-panel'), state, data, (newId) => {
    state.selectedUserId = newId
    onUserChange(state, data)
  })

  // Embedding scatter
  mountEmbeddingScatter($('embedding-scatter'), state)

  // Model tabs + candidate list + viz panel
  mountModelTabs($('model-tabs'), state, (key: ModelKey) => {
    state.activeModel = key
    onModelChange(state)
  })
  renderCandidateList($('candidate-list-panel'), state)
  renderModelViz($('model-viz-panel'), state)

  // Agentic trace
  mountAgenticTrace($('agentic-trace'), state)

  // RAG inspector
  mountRagInspector($('rag-inspector'), state)

  // Recommendations
  mountRecommendations($('rec-grid'), state)

  // Intrinsics
  mountCandidateFunnel($('candidate-funnel'), state)
  mountFeatureChart($('feature-chart'), state)
}

function onUserChange(state: AppState, data: AllData) {
  updateUserPanel($('user-panel'), state, data, (newId) => {
    state.selectedUserId = newId
    onUserChange(state, data)
  })

  // Re-render all user-dependent panels
  mountEmbeddingScatter($('embedding-scatter'), state)
  renderCandidateList($('candidate-list-panel'), state)
  renderModelViz($('model-viz-panel'), state)
  updateAgenticTrace($('agentic-trace'), state)
  updateRagInspector($('rag-inspector'), state)
  updateRecommendations($('rec-grid'), state)
  updateCandidateFunnel($('candidate-funnel'), state)
  updateFeatureChart($('feature-chart'), state)
}

function onModelChange(state: AppState) {
  updateModelTabs($('model-tabs'), state, (key: ModelKey) => {
    state.activeModel = key
    onModelChange(state)
  })
  renderCandidateList($('candidate-list-panel'), state)
  renderModelViz($('model-viz-panel'), state)
}

function renderModelViz(container: HTMLElement, state: AppState) {
  container.innerHTML = ''
  const wrap = document.createElement('div')
  wrap.className = 'viz-panel'

  const titleMap: Record<ModelKey, string> = {
    two_tower:        'Two-Tower embedding similarity',
    mbar:             'Attention weights — history → recommendations',
    ligr:             'Set diversity — relevance vs coverage gain',
    rank_transformer: 'Rank displacement — Two-Tower vs Rank Transformer',
    graph_transformer:'User-item interaction graph',
  }

  const titleEl = document.createElement('p')
  titleEl.className = 'viz-title'
  titleEl.textContent = titleMap[state.activeModel]
  wrap.appendChild(titleEl)

  container.appendChild(wrap)

  switch (state.activeModel) {
    case 'mbar':              renderAttentionHeatmap(wrap, state); break
    case 'ligr':              renderLigrMatrix(wrap, state); break
    case 'rank_transformer':  renderBumpChart(wrap, state); break
    case 'graph_transformer': renderGraphViz(wrap, state); break
    case 'two_tower':
      wrap.innerHTML += '<p style="color:var(--text-muted);font-size:0.82rem;">See the embedding scatter above — Two-Tower retrieval projects users and movies into shared embedding space. Retrieved candidates are highlighted in indigo.</p>'
      break
  }
}

function hideLoading() {
  const overlay = $('loading-overlay')
  overlay.classList.add('hidden')
  setTimeout(() => overlay.remove(), 500)
}

init()
