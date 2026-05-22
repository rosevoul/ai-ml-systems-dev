/**
 * architecture.ts
 * Animated SVG architecture diagram — the hero visual.
 *
 * Layout (viewBox 0 0 1100 520):
 *   User & Context        x≈60
 *   Two-Tower Retrieval   x≈220
 *   Transformer Re-ranking x≈440  (with 4 sub-nodes)
 *   RAG + KB              x≈440  (below transformer)
 *   Agentic Orchestration x≈700  (with 6 sub-nodes)
 *   Recommendations       x≈940
 *
 * Features:
 *   - Animated dashed flow paths along each edge
 *   - Hover to highlight a node + all its connections
 *   - Click any node to scroll to its page section
 */

const W = 1100
const H = 520
const ANIM_DUR = '3s'

interface Node {
  id: string
  label: string
  sub?: string[]
  x: number
  y: number
  w: number
  h: number
  section: string        // page section to scroll to on click
  color: 'accent' | 'teal' | 'muted'
}

interface Edge {
  from: string
  to: string
  curved?: boolean
  feedback?: boolean
}

// ── Node definitions ─────────────────────────────────────────────────────────
const NODES: Node[] = [
  {
    id: 'user', label: 'User & Context',
    sub: ['history', 'profile', 'preferences'],
    x: 30, y: 190, w: 140, h: 80,
    section: '#user-context', color: 'muted',
  },
  {
    id: 'two-tower', label: 'Two-Tower',
    sub: ['Retrieval'],
    x: 210, y: 190, w: 140, h: 80,
    section: '#retrieval', color: 'teal',
  },
  {
    id: 'reranking', label: 'Transformer',
    sub: ['MBAR', 'LiGR', 'Rank Transformer', 'Graph Transformer'],
    x: 400, y: 100, w: 160, h: 160,
    section: '#reranking', color: 'accent',
  },
  {
    id: 'rag', label: 'RAG + Knowledge Base',
    sub: ['Documents', 'Embeddings', 'Index'],
    x: 400, y: 310, w: 160, h: 80,
    section: '#rag', color: 'teal',
  },
  {
    id: 'agentic', label: 'Agentic Orchestration',
    sub: ['Planner', 'Retriever', 'Aligner', 'Summarizer', 'Ranker', 'Responder'],
    x: 618, y: 110, w: 180, h: 200,
    section: '#agentic', color: 'accent',
  },
  {
    id: 'output', label: 'Recommendations',
    sub: ['+ Explanations'],
    x: 862, y: 185, w: 150, h: 90,
    section: '#recommendations', color: 'teal',
  },
]

// ── Edge definitions ─────────────────────────────────────────────────────────
const EDGES: Edge[] = [
  { from: 'user',       to: 'two-tower'  },
  { from: 'two-tower',  to: 'reranking'  },
  { from: 'reranking',  to: 'agentic'    },
  { from: 'rag',        to: 'agentic',   curved: true },
  { from: 'agentic',    to: 'output'     },
  { from: 'agentic',    to: 'two-tower', feedback: true },
]

// ── Helpers ──────────────────────────────────────────────────────────────────
function cx(n: Node) { return n.x + n.w / 2 }
function cy(n: Node) { return n.y + n.h / 2 }
function rightX(n: Node) { return n.x + n.w }

function nodeById(id: string): Node {
  const n = NODES.find(nd => nd.id === id)
  if (!n) throw new Error(`Unknown node ${id}`)
  return n
}

// ── Color palettes ───────────────────────────────────────────────────────────
const COLORS = {
  accent: { fill: 'rgba(99,102,241,0.1)', stroke: 'rgba(99,102,241,0.5)', text: '#a5b4fc', sub: '#818cf8' },
  teal:   { fill: 'rgba(13,148,136,0.1)', stroke: 'rgba(13,148,136,0.4)', text: '#5eead4', sub: '#2dd4bf' },
  muted:  { fill: 'rgba(255,255,255,0.04)', stroke: 'rgba(255,255,255,0.1)', text: '#c4c4d4', sub: '#7070a0' },
} as const

// ── Edge path calculation ────────────────────────────────────────────────────
function edgePath(edge: Edge): string {
  const from = nodeById(edge.from)
  const to   = nodeById(edge.to)

  if (edge.feedback) {
    // agentic → two-tower: arc below the diagram as a feedback loop
    const x1 = cx(from)
    const y1 = from.y + from.h        // bottom of agentic
    const x2 = cx(to)
    const y2 = to.y + to.h            // bottom of two-tower
    const arcY = H - 28               // route just above the bottom edge
    return `M ${x1} ${y1} C ${x1} ${arcY}, ${x2} ${arcY}, ${x2} ${y2}`
  }

  const x1 = rightX(from)
  const y1 = cy(from)
  const x2 = to.x
  const y2 = cy(to)

  if (edge.curved) {
    // rag → agentic: curve up from below
    const mx = (x1 + x2) / 2
    return `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`
  }

  const mid = (x1 + x2) / 2
  return `M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`
}

// ── SVG builder ──────────────────────────────────────────────────────────────
function buildSVG(_container: HTMLElement): SVGSVGElement {
  const NS = 'http://www.w3.org/2000/svg'

  function el<K extends keyof SVGElementTagNameMap>(tag: K, attrs: Record<string, string | number> = {}): SVGElementTagNameMap[K] {
    const e = document.createElementNS(NS, tag)
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v))
    return e
  }

  const svg = el('svg', {
    viewBox: `0 0 ${W} ${H}`,
    preserveAspectRatio: 'xMidYMid meet',
    role: 'img',
    'aria-label': 'Architecture diagram: User Context → Two-Tower Retrieval → Transformer Re-ranking → Agentic Orchestration → Recommendations',
  })

  // ── Defs: arrowhead marker ─────────────────────────────────────────────
  const defs = el('defs')
  const marker = el('marker', { id: 'arrow', markerWidth: '8', markerHeight: '8', refX: '8', refY: '3', orient: 'auto' })
  const path = el('path', { d: 'M0,0 L0,6 L8,3 z', fill: 'rgba(99,102,241,0.5)' })
  marker.appendChild(path)
  defs.appendChild(marker)

  // Animated dot marker
  const dotMarker = el('marker', { id: 'dot', markerWidth: '6', markerHeight: '6', refX: '3', refY: '3', orient: 'auto' })
  const dotCircle = el('circle', { cx: '3', cy: '3', r: '2.5', fill: '#6366f1' })
  dotMarker.appendChild(dotCircle)
  defs.appendChild(dotMarker)

  svg.appendChild(defs)

  // ── Edge layer ─────────────────────────────────────────────────────────
  const edgeGroup = el('g')
  const animGroup = el('g')

  const pathEls: Map<string, SVGPathElement> = new Map()

  EDGES.forEach((edge, i) => {
    const d = edgePath(edge)
    const delay = i * 0.4

    // Static background path
    const bgPath = el('path', {
      d,
      fill: 'none',
      stroke: 'rgba(255,255,255,0.06)',
      'stroke-width': '1.5',
    })
    edgeGroup.appendChild(bgPath)

    // Animated flow path
    const isFeedback = edge.feedback === true
    const flowPath = el('path', {
      d,
      fill: 'none',
      stroke: isFeedback ? 'rgba(251,191,36,0.5)' : 'rgba(99,102,241,0.45)',
      'stroke-width': isFeedback ? '1' : '1.5',
      'stroke-dasharray': isFeedback ? '4 8' : '6 10',
      'marker-end': 'url(#arrow)',
    })
    const animateEl = document.createElementNS(NS, 'animate')
    animateEl.setAttribute('attributeName', 'stroke-dashoffset')
    animateEl.setAttribute('from', '200')
    animateEl.setAttribute('to', '0')
    animateEl.setAttribute('dur', ANIM_DUR)
    animateEl.setAttribute('begin', `${delay}s`)
    animateEl.setAttribute('repeatCount', 'indefinite')
    flowPath.appendChild(animateEl)
    animGroup.appendChild(flowPath)

    // Moving dot
    const movingPath = el('path', {
      d,
      fill: 'none',
      stroke: 'none',
      id: `edge-path-${i}`,
    })
    animGroup.appendChild(movingPath)

    const movingDot = el('circle', { r: '4', fill: '#6366f1', opacity: '0.8' })
    const animMotion = document.createElementNS(NS, 'animateMotion')
    animMotion.setAttribute('dur', ANIM_DUR)
    animMotion.setAttribute('begin', `${delay}s`)
    animMotion.setAttribute('repeatCount', 'indefinite')
    const mpath = document.createElementNS(NS, 'mpath')
    mpath.setAttributeNS('http://www.w3.org/1999/xlink', 'href', `#edge-path-${i}`)
    animMotion.appendChild(mpath)
    movingDot.appendChild(animMotion)
    animGroup.appendChild(movingDot)

    // Store flow path for hover
    const key = `${edge.from}-${edge.to}`
    pathEls.set(key, flowPath)
  })

  svg.appendChild(edgeGroup)
  svg.appendChild(animGroup)

  // ── Node layer ─────────────────────────────────────────────────────────
  const nodeGroup = el('g')

  NODES.forEach(node => {
    const c = COLORS[node.color]
    const g = el('g', { 'data-node': node.id, style: 'cursor:pointer' })

    // Background rect
    const rect = el('rect', {
      x: node.x, y: node.y, width: node.w, height: node.h,
      rx: '8',
      fill: c.fill,
      stroke: c.stroke,
      'stroke-width': '1',
    })
    g.appendChild(rect)

    // Label
    const labelY = node.sub && node.sub.length > 0
      ? node.y + 22
      : cy(node) + 5

    const labelEl = el('text', {
      x: cx(node), y: labelY,
      'text-anchor': 'middle',
      fill: c.text,
      'font-size': '11',
      'font-weight': '600',
      'font-family': 'Inter, system-ui, sans-serif',
      'letter-spacing': '0.02em',
    })
    labelEl.textContent = node.label
    g.appendChild(labelEl)

    // Sub-items
    if (node.sub) {
      node.sub.forEach((s, i) => {
        const subEl = el('text', {
          x: cx(node),
          y: node.y + 38 + i * 18,
          'text-anchor': 'middle',
          fill: c.sub,
          'font-size': '9.5',
          'font-family': 'Inter, system-ui, sans-serif',
        })
        subEl.textContent = s
        g.appendChild(subEl)
      })
    }

    // Hover interactions
    g.addEventListener('mouseenter', () => {
      rect.setAttribute('stroke-width', '1.5')
      rect.setAttribute('fill', c.fill.replace('0.1', '0.18').replace('0.04', '0.08'))
    })
    g.addEventListener('mouseleave', () => {
      rect.setAttribute('stroke-width', '1')
      rect.setAttribute('fill', c.fill)
    })

    // Click → scroll to section
    g.addEventListener('click', () => {
      const target = document.querySelector(node.section)
      target?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })

    nodeGroup.appendChild(g)
  })

  svg.appendChild(nodeGroup)

  // ── Subtle entrance animation via CSS ──────────────────────────────────
  svg.style.opacity = '0'
  svg.style.transition = 'opacity 600ms ease'
  requestAnimationFrame(() => {
    requestAnimationFrame(() => { svg.style.opacity = '1' })
  })

  return svg as unknown as SVGSVGElement
}

// ── Public mount function ─────────────────────────────────────────────────────
export function mountArchitecture(container: HTMLElement): void {
  const svg = buildSVG(container)
  container.appendChild(svg)
}
