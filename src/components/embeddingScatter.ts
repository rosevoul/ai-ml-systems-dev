import * as d3 from 'd3'
import type { AppState, MoviePoint } from '../data/types'

const MARGIN = { top: 16, right: 16, bottom: 16, left: 16 }
const HEIGHT = 260

export function mountEmbeddingScatter(container: HTMLElement, state: AppState): void {
  container.innerHTML = ''
  const width = container.clientWidth || 800

  const { embeddings, recs, selectedUserId } = state
  const candidateIds = new Set(
    (recs.users[selectedUserId]?.recommendations ?? []).map(r => r.movieId)
  )

  // ── Scales ───────────────────────────────────────────────────────────────
  const allX = [...embeddings.movies.map(m => m.x), ...embeddings.users.map(u => u.x)]
  const allY = [...embeddings.movies.map(m => m.y), ...embeddings.users.map(u => u.y)]

  const xScale = d3.scaleLinear().domain(d3.extent(allX) as [number, number]).range([MARGIN.left, width - MARGIN.right])
  const yScale = d3.scaleLinear().domain(d3.extent(allY) as [number, number]).range([HEIGHT - MARGIN.bottom, MARGIN.top])

  // ── SVG ──────────────────────────────────────────────────────────────────
  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', HEIGHT)
    .style('background', 'var(--bg-surface)')
    .style('border-radius', '10px')
    .style('border', '1px solid var(--border)')

  const g = svg.append('g')

  // ── Zoom ─────────────────────────────────────────────────────────────────
  const zoom = d3.zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.5, 8])
    .on('zoom', (event) => g.attr('transform', event.transform))
  svg.call(zoom)

  // ── Tooltip ───────────────────────────────────────────────────────────────
  const tooltip = d3.select(container)
    .append('div')
    .attr('class', 'd3-tooltip')
    .style('opacity', 0)
    .style('position', 'absolute')
    .style('pointer-events', 'none')

  function showTip(event: MouseEvent, html: string) {
    const rect = container.getBoundingClientRect()
    tooltip
      .style('opacity', 1)
      .html(html)
      .style('left', `${event.clientX - rect.left + 12}px`)
      .style('top', `${event.clientY - rect.top - 28}px`)
  }
  function hideTip() { tooltip.style('opacity', 0) }

  // ── Movie dots ────────────────────────────────────────────────────────────
  const sample: MoviePoint[] = embeddings.movies.filter((_, i) => i % 5 === 0).slice(0, 400)

  g.selectAll<SVGCircleElement, MoviePoint>('.movie-dot')
    .data(sample)
    .join('circle')
    .attr('class', 'movie-dot')
    .attr('cx', d => xScale(d.x))
    .attr('cy', d => yScale(d.y))
    .attr('r', d => candidateIds.has(d.id) ? 5 : 3)
    .attr('fill', d => candidateIds.has(d.id) ? 'rgba(99,102,241,0.7)' : 'rgba(255,255,255,0.12)')
    .attr('stroke', d => candidateIds.has(d.id) ? 'rgba(99,102,241,1)' : 'none')
    .attr('stroke-width', 1.5)
    .style('cursor', 'pointer')
    .on('mouseover', (event, d) => {
      showTip(event, `<strong>${d.title}</strong><br/><span style="color:var(--text-muted);font-size:0.75rem">${d.genres.slice(0, 3).join(', ')}</span>`)
    })
    .on('mouseout', hideTip)

  // ── Selected user dot ─────────────────────────────────────────────────────
  const selUser = embeddings.users.find(u => String(u.id) === selectedUserId)
  if (selUser) {
    // Pulse ring
    g.append('circle')
      .attr('cx', xScale(selUser.x))
      .attr('cy', yScale(selUser.y))
      .attr('r', 14)
      .attr('fill', 'none')
      .attr('stroke', 'rgba(99,102,241,0.3)')
      .attr('stroke-width', 1)

    g.append('circle')
      .attr('cx', xScale(selUser.x))
      .attr('cy', yScale(selUser.y))
      .attr('r', 7)
      .attr('fill', '#6366f1')
      .attr('stroke', '#a5b4fc')
      .attr('stroke-width', 1.5)
      .on('mouseover', (event) => {
        showTip(event, `<strong>User ${selectedUserId}</strong><br/><span style="color:var(--text-muted);font-size:0.75rem">Selected user</span>`)
      })
      .on('mouseout', hideTip)
  }

  // ── Legend ────────────────────────────────────────────────────────────────
  const legend = svg.append('g').attr('transform', `translate(${width - 160}, 20)`)
  const items: { color: string; label: string; isUser?: boolean }[] = [
    { color: 'rgba(255,255,255,0.2)', label: 'All movies' },
    { color: '#6366f1', label: 'Retrieved candidates' },
    { color: '#6366f1', label: 'Selected user', isUser: true },
  ]
  items.forEach(({ color, label, isUser }, i) => {
    legend.append('circle').attr('cx', 0).attr('cy', i * 20).attr('r', isUser ? 5 : 3.5).attr('fill', color).attr('stroke', isUser ? '#a5b4fc' : 'none').attr('stroke-width', 1.5)
    legend.append('text').attr('x', 12).attr('y', i * 20 + 4.5).text(label).attr('fill', 'var(--text-secondary)').style('font-size', '11px').attr('font-family', 'Inter, system-ui, sans-serif')
  })
}
