// ── Core data shapes matching JSON output from faye-recsys-models ────────────

export interface HistoryItem {
  movieId: number
  title: string
  genres: string[]
  rating: number
  timestamp: number
}

export interface RecScores {
  two_tower: number
  mbar: number
  ligr: number
  rank_transformer: number
  graph_transformer: number
  xgboost_final: number
}

export interface RagDoc {
  movieId?: number
  snippet: string
  source: string
  score?: number
}

export interface Recommendation {
  movieId: number
  title: string
  year: number | null
  genres: string[]
  scores: RecScores
  explanation: string
  factors: string[]
  rag_docs: RagDoc[]
}

export interface UserRec {
  history: HistoryItem[]
  recommendations: Recommendation[]
}

export interface RecommendationsData {
  users: Record<string, UserRec>
}

// ── Embeddings 2D ─────────────────────────────────────────────────────────────

export interface UserPoint {
  id: number
  x: number
  y: number
}

export interface MoviePoint {
  id: number
  title: string
  genres: string[]
  x: number
  y: number
}

export interface EmbeddingsData {
  users: UserPoint[]
  movies: MoviePoint[]
}

// ── Pipeline trace ────────────────────────────────────────────────────────────

export interface TraceStep {
  agent: string
  input: string
  output: string
  data_used: string
  latency_ms: number
}

export interface PipelineTraceData {
  [userId: string]: { steps: TraceStep[] }
}

// ── Model intrinsics ──────────────────────────────────────────────────────────

export interface MbarIntrinsic {
  history_titles: string[]
  rec_titles: string[]
  weights: number[][]
}

export interface LigrCandidate {
  movieId: number
  title: string
  relevance_score: number
  diversity_gain: number
  genres: string[]
  is_new_genre_for_user: boolean
}

export interface LigrIntrinsic {
  candidates: LigrCandidate[]
  user_history_genres: string[]
  greedy_genre_coverage: number
  ligr_genre_coverage: number
}

export interface RtCandidate {
  movieId: number
  title: string
  two_tower_rank: number
  rank_transformer_rank: number
  two_tower_score: number
  rank_transformer_score: number
}

export interface GraphNode {
  id: number | string
  title?: string
  rating?: number
  shared_users?: number
  bridge_movies?: string[]
  shared_movies?: number[]
}

export interface GraphEdge {
  source: string
  target: string
  weight: number
  type: 'user_rated' | 'neighbor_rated' | 'recommended'
}

export interface GraphIntrinsic {
  user_node: { id: number }
  rated_movies: GraphNode[]
  recommended_movies: GraphNode[]
  neighbor_users: GraphNode[]
  edges: GraphEdge[]
}

export interface CandidateFunnel {
  pool: number
  two_tower: number
  reranked: number
  final: number
}

export interface ModelIntrinsic {
  mbar: MbarIntrinsic
  ligr: LigrIntrinsic
  rank_transformer: { candidates: RtCandidate[] }
  graph_transformer: GraphIntrinsic
  candidate_funnel: CandidateFunnel
  feature_contributions: Record<string, number>
}

export interface ModelIntrinsicsData {
  [userId: string]: ModelIntrinsic
}

// ── App state ─────────────────────────────────────────────────────────────────

export type ModelKey = 'two_tower' | 'mbar' | 'ligr' | 'rank_transformer' | 'graph_transformer'

export interface AppState {
  selectedUserId: string
  activeModel: ModelKey
  recs: RecommendationsData
  embeddings: EmbeddingsData
  trace: PipelineTraceData
  intrinsics: ModelIntrinsicsData
}
