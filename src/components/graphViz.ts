import * as d3 from 'd3'
import type { AppState, GraphEdge } from '../data/types'

interface SimNode extends d3.SimulationNodeDatum { id: string; type: 'user' | 'rated' | 'rec' | 'neighbor'; label: string; rating?: number }
interface SimLink { source: string; target: string; weight: number; type: GraphEdge['type'] }

export function renderGraphViz(container: HTMLElement, state: AppState): void {
  container.innerHTML = ''
  const uid = state.selectedUserId
  const gData = state.intrinsics[uid]?.graph_transformer
  if (!gData || !gData.edges?.length) {
    container.innerHTML = '<p style="color:var(--text-muted);font-size:0.82rem;padding:1rem;">No graph data for this user.</p>'
    return
  }

  const W = container.clientWidth || 500
  const H = 360

  // ── Build node / link arrays ──────────────────────────────────────────────
  const nodes: SimNode[] = []
  const nodeSet = new Set<string>()
  const addNode = (id: string, type: SimNode['type'], label: string, rating?: number) => {
    if (!nodeSet.has(id)) { nodes.push({ id, type, label, rating }); nodeSet.add(id) }
  }

  addNode(`u_${uid}`, 'user', `User ${uid}`)
  gData.rated_movies.slice(0, 10).forEach(m => addNode(`m_${m.id}`, 'rated', String(m.title ?? m.id).slice(0, 18), m.rating))
  gData.recommended_movies.slice(0, 5).forEach(m => addNode(`rec_${m.id}`, 'rec', String(m.title ?? m.id).slice(0, 18)))
  gData.neighbor_users.slice(0, 6).forEach(u => addNode(`u_${u.id}`, 'neighbor', `u_${u.id}`))

  const links: SimLink[] = gData.edges
    .filter(e => nodeSet.has(e.source) && nodeSet.has(e.target))
    .slice(0, 40)
    .map(e => ({ ...e }))

  // ── SVG ──────────────────────────────────────────────────────────────────
  const svg = d3.select(container)
    .append('svg')
    .attr('width', '100%')
    .attr('viewBox', `0 0 ${W} ${H}`)
    .style('border-radius', '8px')

  svg.append('defs').append('marker')
    .attr('id', 'g-arrow').attr('markerWidth', 6).attr('markerHeight', 6).attr('refX', 6).attr('refY', 3).attr('orient', 'auto')
    .append('path').attr('d', 'M0,0 L0,6 L6,3 z').attr('fill', 'rgba(99,102,241,0.3)')

  const linkLayer = svg.append('g')
  const nodeLayer = svg.append('g')

  // Tooltip
  const tip = d3.select(container).append('div').attr('class', 'd3-tooltip').style('opacity', 0).style('position', 'absolute').style('pointer-events', 'none')

  // ── Force simulation ──────────────────────────────────────────────────────
  const sim = d3.forceSimulation<SimNode>(nodes)
    .force('link', d3.forceLink<SimNode, SimLink>(links).id(d => d.id).distance(60).strength(0.4))
    .force('charge', d3.forceManyBody().strength(-120))
    .force('center', d3.forceCenter(W / 2, H / 2))
    .force('collision', d3.forceCollide(18))

  const linkSel = linkLayer.selectAll<SVGLineElement, SimLink>('line')
    .data(links)
    .join('line')
    .attr('stroke', d => d.type === 'recommended' ? 'rgba(99,102,241,0.5)' : d.type === 'user_rated' ? 'rgba(13,148,136,0.4)' : 'rgba(255,255,255,0.08)')
    .attr('stroke-width', d => d.type === 'recommended' ? 1.5 : 1)

  // Node colors
  const nodeColor = (d: SimNode) => d.type === 'user' ? '#6366f1' : d.type === 'rec' ? '#0d9488' : d.type === 'rated' ? 'rgba(255,255,255,0.25)' : 'rgba(255,255,255,0.1)'
  const nodeR = (d: SimNode) => d.type === 'user' ? 10 : d.type === 'rec' ? 8 : 5.5

  const nodeSel = nodeLayer.selectAll<SVGCircleElement, SimNode>('circle')
    .data(nodes)
    .join('circle')
    .attr('r', d => nodeR(d))
    .attr('fill', d => nodeColor(d))
    .attr('stroke', d => d.type === 'user' ? '#a5b4fc' : d.type === 'rec' ? '#5eead4' : 'none')
    .attr('stroke-width', 1.5)
    .style('cursor', 'pointer')
    .on('mouseover', (event, d) => {
      const rect = container.getBoundingClientRect()
      const typeLabel = d.type === 'user' ? 'Selected user' : d.type === 'rec' ? 'Recommended' : d.type === 'rated' ? `Rated ${d.rating?.toFixed(1) ?? '?'}★` : 'Similar user'
      tip.style('opacity', 1)
        .html(`<strong>${d.label}</strong><br/><span style="color:var(--text-muted);font-size:0.75rem">${typeLabel}</span>`)
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 10}px`)
    })
    .on('mouseout', () => tip.style('opacity', 0))
    .call(d3.drag<SVGCircleElement, SimNode>()
      .on('start', (event, d) => { if (!event.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
      .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y })
      .on('end', (event, d) => { if (!event.active) sim.alphaTarget(0); d.fx = null; d.fy = null })
    )

  sim.on('tick', () => {
    linkSel
      .attr('x1', d => (d.source as unknown as SimNode).x!)
      .attr('y1', d => (d.source as unknown as SimNode).y!)
      .attr('x2', d => (d.target as unknown as SimNode).x!)
      .attr('y2', d => (d.target as unknown as SimNode).y!)
    nodeSel.attr('cx', d => d.x!).attr('cy', d => d.y!)
  })

  // Legend
  const leg = svg.append('g').attr('transform', `translate(10, ${H - 14})`)
  const legDefs = [
    { color: '#6366f1', label: 'you' },
    { color: 'rgba(255,255,255,0.3)', label: 'rated' },
    { color: '#0d9488', label: 'recommended' },
    { color: 'rgba(255,255,255,0.1)', label: 'similar users' },
  ]
  legDefs.forEach(({ color, label }, i) => {
    leg.append('circle').attr('cx', i * 100).attr('cy', 0).attr('r', 4).attr('fill', color)
    leg.append('text').attr('x', i * 100 + 10).attr('y', 4).attr('fill', 'var(--text-muted)').style('font-size', '9px').text(label)
  })
}
