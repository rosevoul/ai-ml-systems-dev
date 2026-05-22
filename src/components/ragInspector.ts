import type { AppState, Recommendation } from '../data/types'

export function mountRagInspector(container: HTMLElement, state: AppState): void {
  renderRag(container, state)
}

export function updateRagInspector(container: HTMLElement, state: AppState): void {
  renderRag(container, state)
}

function renderRag(container: HTMLElement, state: AppState) {
  const uid = state.selectedUserId
  const recs = state.recs.users[uid]?.recommendations ?? []
  const topRec = recs[0]
  if (!topRec) { container.innerHTML = ''; return }

  renderForRec(container, topRec, 0)
}

function renderForRec(container: HTMLElement, rec: Recommendation, selectedDocIdx: number) {
  const docs = rec.rag_docs ?? []

  container.innerHTML = `
    <div style="margin-bottom:1rem;">
      <span style="font-size:0.72rem;color:var(--text-muted);">Top recommendation: </span>
      <strong style="font-size:0.9rem;color:var(--text-primary);">${rec.title}</strong>
    </div>
    <div class="rag-layout">
      <div>
        <p style="font-size:0.72rem;font-weight:500;color:var(--text-muted);margin-bottom:0.5rem;letter-spacing:0.04em;">RETRIEVED DOCUMENTS</p>
        <div class="rag-docs-list">
          ${docs.length ? docs.map((doc, i) => `
            <div class="rag-doc-item${i === selectedDocIdx ? ' selected' : ''}" data-doc="${i}">
              <p class="rag-doc-source">${doc.source}</p>
              <p class="rag-doc-snippet">${(doc.snippet ?? '').slice(0, 120)}…</p>
            </div>
          `).join('') : '<p style="color:var(--text-muted);font-size:0.82rem;">No documents retrieved.</p>'}
        </div>
      </div>
      <div>
        <p style="font-size:0.72rem;font-weight:500;color:var(--text-muted);margin-bottom:0.5rem;letter-spacing:0.04em;">GROUNDED EXPLANATION</p>
        <p class="rag-explanation">${highlightExplanation(rec.explanation, docs, selectedDocIdx)}</p>
        ${docs[selectedDocIdx] ? `
          <div style="margin-top:1rem;padding:0.75rem;background:var(--bg-elevated);border:1px solid var(--border);border-radius:8px;">
            <p style="font-size:0.7rem;color:var(--text-muted);margin-bottom:4px;">FULL DOCUMENT SNIPPET</p>
            <p style="font-size:0.8rem;color:var(--text-secondary);line-height:1.6;">${docs[selectedDocIdx]?.snippet ?? ''}</p>
          </div>
        ` : ''}
      </div>
    </div>
  `

  container.querySelectorAll<HTMLElement>('.rag-doc-item').forEach(el => {
    el.addEventListener('click', () => {
      const idx = parseInt(el.dataset['doc'] ?? '0', 10)
      renderForRec(container, rec, idx)
    })
  })
}

function highlightExplanation(explanation: string, docs: Recommendation['rag_docs'], selectedIdx: number): string {
  if (!docs[selectedIdx]?.source) return explanation
  const source = docs[selectedIdx]!.source
  // Highlight sentences that relate to the selected document source (movie title match)
  const words = source.split(' ').filter(w => w.length > 4).slice(0, 3)
  let result = explanation
  words.forEach(word => {
    result = result.replace(new RegExp(word, 'gi'), `<mark class="rag-highlight">${word}</mark>`)
  })
  return result
}
