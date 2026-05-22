import * as d3 from 'd3'
import type { AppState, RtCandidate } from '../data/types'

export function renderBumpChart(container: HTMLElement, state: AppState): void {
  container.innerHTML = ''
  const uid = state.selectedUserId
  const rtData = state.intrinsics[uid]?.rank_transformer?.candidates
  if (!rtData || !rtData.length) {
    container.innerHTML = '<p style="color:var(--text-muted);font-size:0.82rem;padding:1rem;">No Rank Transformer data.</p>'
    return
  }

  const items = rtData.slice(0, 20)
  const H = 360
  const W = container.clientWidth || 500
  const LEFT_PAD = 160
  const RIGHT_PAD = 160
  const INNER_W = W - LEFT_PAD - RIGHT_PAD
  const INNER_H = H - 40

  const maxRank = Math.max(...items.map(d => Math.max(d.two_tower_rank, d.rank_transformer_rank))) + 1
  const yScale = d3.scaleLinear().domain([0, maxRank]).range([0, INNER_H])

  const svg = d3.select(container)
    .append('svg')
    .attr('width', '100%')
    .attr('viewBox', `0 0 ${W} ${H}`)
    .style('overflow', 'visible')

  const g = svg.append('g').attr('transform', 'translate(0, 20)')

  // Column headers
  svg.append('text').attr('x', LEFT_PAD / 2).attr('y', 14).attr('text-anchor', 'middle').attr('fill', 'var(--text-muted)').style('font-size', '10px').text('Two-Tower rank')
  svg.append('text').attr('x', W - RIGHT_PAD / 2).attr('y', 14).attr('text-anchor', 'middle').attr('fill', 'var(--text-muted)').style('font-size', '10px').text('Rank Transformer')

  // Tooltip
  const tip = d3.select(container).append('div').attr('class', 'd3-tooltip').style('opacity', 0).style('position', 'absolute').style('pointer-events', 'none')

  items.forEach((d: RtCandidate) => {
    const y1 = yScale(d.two_tower_rank)
    const y2 = yScale(d.rank_transformer_rank)
    const delta = d.two_tower_rank - d.rank_transformer_rank
    const color = delta > 0 ? '#34d399' : delta < 0 ? '#f87171' : '#505065'

    // Connecting line
    g.append('path')
      .attr('d', `M ${LEFT_PAD} ${y1} C ${LEFT_PAD + INNER_W / 2} ${y1}, ${LEFT_PAD + INNER_W / 2} ${y2}, ${LEFT_PAD + INNER_W} ${y2}`)
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', Math.abs(delta) > 3 ? 2 : 1.2)
      .attr('stroke-opacity', 0.5)

    // Left dot
    g.append('circle').attr('cx', LEFT_PAD).attr('cy', y1).attr('r', 3).attr('fill', 'var(--text-muted)')
    // Right dot
    g.append('circle').attr('cx', LEFT_PAD + INNER_W).attr('cy', y2).attr('r', 3.5).attr('fill', color)

    // Right label
    const label = g.append('text')
      .attr('x', LEFT_PAD + INNER_W + 8)
      .attr('y', y2 + 4)
      .attr('fill', Math.abs(delta) >= 3 ? color : 'var(--text-muted)')
      .style('font-size', '9.5px')
      .style('font-family', 'Inter, system-ui, sans-serif')
      .text(d.title.slice(0, 22))
      .style('cursor', 'pointer')

    label.on('mouseover', (event) => {
      const rect = container.getBoundingClientRect()
      tip.style('opacity', 1)
        .html(`<strong>${d.title}</strong><br/>Two-Tower: #${d.two_tower_rank + 1}<br/>After RT: #${d.rank_transformer_rank + 1}<br/><span style="color:${color}">Δ ${delta > 0 ? '+' : ''}${delta}</span>`)
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 10}px`)
    }).on('mouseout', () => tip.style('opacity', 0))

    // Left rank number
    g.append('text')
      .attr('x', LEFT_PAD - 8)
      .attr('y', y1 + 4)
      .attr('text-anchor', 'end')
      .attr('fill', 'var(--text-muted)')
      .style('font-size', '9px')
      .text(`#${d.two_tower_rank + 1}`)
  })

  // Legend
  const leg = svg.append('g').attr('transform', `translate(${LEFT_PAD}, ${H - 10})`)
  const legItems = [{ color: '#34d399', label: 'promoted' }, { color: '#f87171', label: 'demoted' }, { color: '#505065', label: 'unchanged' }]
  legItems.forEach(({ color, label }, i) => {
    leg.append('circle').attr('cx', i * 90).attr('cy', 0).attr('r', 4).attr('fill', color)
    leg.append('text').attr('x', i * 90 + 10).attr('y', 4).attr('fill', 'var(--text-muted)').style('font-size', '9px').text(label)
  })
}
