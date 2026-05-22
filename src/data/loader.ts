import type {
  RecommendationsData,
  EmbeddingsData,
  PipelineTraceData,
  ModelIntrinsicsData,
} from './types'

const BASE = import.meta.env.BASE_URL + 'assets/data/'
const cache = new Map<string, unknown>()

async function fetchJSON<T>(filename: string): Promise<T> {
  if (cache.has(filename)) return cache.get(filename) as T
  const res = await fetch(BASE + filename)
  if (!res.ok) throw new Error(`Failed to load ${filename}: ${res.status}`)
  const data = await res.json() as T
  cache.set(filename, data)
  return data
}

export interface AllData {
  recs: RecommendationsData
  embeddings: EmbeddingsData
  trace: PipelineTraceData
  intrinsics: ModelIntrinsicsData
}

export async function loadAll(): Promise<AllData> {
  const [recs, embeddings, trace, intrinsics] = await Promise.all([
    fetchJSON<RecommendationsData>('recommendations.json'),
    fetchJSON<EmbeddingsData>('embeddings_2d.json'),
    fetchJSON<PipelineTraceData>('pipeline_trace.json'),
    fetchJSON<ModelIntrinsicsData>('model_intrinsics.json'),
  ])
  return { recs, embeddings, trace, intrinsics }
}

export function getUserIds(data: AllData): string[] {
  return Object.keys(data.recs.users)
}

export function pickRandomUser(data: AllData, exclude?: string): string {
  const ids = getUserIds(data).filter(id => id !== exclude)
  return ids[Math.floor(Math.random() * ids.length)]
}
