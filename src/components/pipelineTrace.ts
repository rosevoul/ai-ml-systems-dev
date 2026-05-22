import type { AppState } from '../data/types'

const STEPS = [
  { name: 'User Context',       desc: 'User history, preferences, and behavioural signals assembled from the ratings database.' },
  { name: 'Query Understanding', desc: 'User intent extracted from preference profile. Query rewritten for retrieval.' },
  { name: 'Retrieval',          desc: 'Two-Tower model encodes user and movie embeddings. Top-100 candidates retrieved via FAISS.' },
  { name: 'Candidate Generation', desc: 'Hybrid retrieval combines vector search with metadata filters. Candidate set deduplicated.' },
  { name: 'Re-ranking',         desc: 'MBAR, LiGR, Rank Transformer, and Graph Transformer each produce refined orderings. XGBoost fuses features.' },
  { name: 'Reasoning / RAG',    desc: 'Knowledge base queried. Relevant documents retrieved and used to ground explanations.' },
  { name: 'Final Output',       desc: 'Agentic Responder assembles personalised recommendations with explanations, factors, and RAG context.' },
]

export function mountPipelineTrace(container: HTMLElement, _state: AppState): void {
  render(container)
}

export function updatePipelineTrace(container: HTMLElement, _state: AppState): void {
  render(container)
}

function render(container: HTMLElement) {
  container.innerHTML = `
    <div class="pipeline-trace">
      ${STEPS.map(s => `
        <div class="pipe-step">
          <div class="pipe-connector">
            <div class="pipe-dot"></div>
            <div class="pipe-line"></div>
          </div>
          <div class="pipe-body">
            <p class="pipe-name">${s.name}</p>
            <p class="pipe-desc">${s.desc}</p>
          </div>
        </div>
      `).join('')}
    </div>
  `
}
