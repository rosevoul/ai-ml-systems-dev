import * as d3 from 'd3'
import type { AppState } from '../data/types'

export function renderAttentionHeatmap(container: HTMLElement, state: AppState): void {
  container.innerHTML = ''
  const uid = state.selectedUserId
  const attn = state.intrinsics[uid]?.mbar
  if (!attn || !attn.weights.length) {
    container.innerHTML = '<p style="color:var(--text-muted);font-size:0.82rem;padding:1rem;">No attention data for this user.</p>'
    return
  }

  const rows = attn.history_titles   // history items (rows)
  const cols = attn.rec_titles       // rec items (cols)
  const weights = attn.weights       // [rows × cols]

  const CELL = 36
  const LEFT_PAD = 130
  const TOP_PAD = 90
  const width = LEFT_PAD + cols.length * CELL + 20
  const height = TOP_PAD + rows.length * CELL + 20

  const colorScale = d3.scaleSequential(d3.interpolate('#1a1a2e', '#818cf8'))
    .domain([0, d3.max(weights.flat()) ?? 1])

  const svg = d3.select(container)
    .append('svg')
    .attr('width', '100%')
    .attr('viewBox', `0 0 ${width} ${height}`)
    .style('overflow', 'visible')

  // ── Column headers (rec titles) ──────────────────────────────────────────
  const colG = svg.append('g').attr('transform', `translate(${LEFT_PAD}, 0)`)
  cols.forEach((title, j) => {
    colG.append('text')
      .attr('x', j * CELL + CELL / 2)
      .attr('y', TOP_PAD - 10)
      .attr('text-anchor', 'end')
      .attr('transform', `rotate(-45, ${j * CELL + CELL / 2}, ${TOP_PAD - 10})`)
      .attr('fill', 'var(--text-secondary)')
      .style('font-size', '9.5px')
      .style('font-family', 'Inter, system-ui, sans-serif')
      .text(title.slice(0, 18))
  })

  // ── Row labels (history titles) ──────────────────────────────────────────
  rows.forEach((title, i) => {
    svg.append('text')
      .attr('x', LEFT_PAD - 8)
      .attr('y', TOP_PAD + i * CELL + CELL / 2 + 4)
      .attr('text-anchor', 'end')
      .attr('fill', 'var(--text-secondary)')
      .style('font-size', '9.5px')
      .style('font-family', 'Inter, system-ui, sans-serif')
      .text(title.slice(0, 20))
  })

  // ── Tooltip ───────────────────────────────────────────────────────────────
  const tip = d3.select(container)
    .append('div')
    .attr('class', 'd3-tooltip')
    .style('opacity', 0)
    .style('position', 'absolute')
    .style('pointer-events', 'none')

  // ── Cells ─────────────────────────────────────────────────────────────────
  const cellG = svg.append('g').attr('transform', `translate(${LEFT_PAD}, ${TOP_PAD})`)
  rows.forEach((rowTitle, i) => {
    cols.forEach((colTitle, j) => {
      const w = weights[i]?.[j] ?? 0
      cellG.append('rect')
        .attr('x', j * CELL + 2)
        .attr('y', i * CELL + 2)
        .attr('width', CELL - 4)
        .attr('height', CELL - 4)
        .attr('rx', 3)
        .attr('fill', colorScale(w))
        .attr('stroke', w > 0.4 ? 'rgba(129,140,248,0.5)' : 'none')
        .attr('stroke-width', 1)
        .style('cursor', 'pointer')
        .on('mouseover', (event) => {
          const rect = container.getBoundingClientRect()
          tip.style('opacity', 1)
            .html(`<strong>${rowTitle}</strong> → <strong>${colTitle}</strong><br/>attention: <strong style="color:var(--accent)">${w.toFixed(3)}</strong>`)
            .style('left', `${event.clientX - rect.left + 12}px`)
            .style('top', `${event.clientY - rect.top - 10}px`)
        })
        .on('mouseout', () => tip.style('opacity', 0))
    })
  })

  // ── Colour scale legend ───────────────────────────────────────────────────
  const legendW = 100, legendH = 8
  const defs = svg.append('defs')
  const grad = defs.append('linearGradient').attr('id', 'attn-grad')
  grad.append('stop').attr('offset', '0%').attr('stop-color', '#1a1a2e')
  grad.append('stop').attr('offset', '100%').attr('stop-color', '#818cf8')
  const legG = svg.append('g').attr('transform', `translate(${LEFT_PAD}, ${height - 18})`)
  legG.append('rect').attr('width', legendW).attr('height', legendH).attr('rx', 3).attr('fill', 'url(#attn-grad)')
  legG.append('text').attr('x', 0).attr('y', legendH + 12).attr('fill', 'var(--text-muted)').style('font-size', '9px').text('low')
  legG.append('text').attr('x', legendW).attr('y', legendH + 12).attr('text-anchor', 'end').attr('fill', 'var(--text-muted)').style('font-size', '9px').text('high attention')
}
