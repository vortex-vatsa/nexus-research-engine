export enum ComponentType {
  TABLE = "table",
  CHART = "chart",
  LIST = "list",
}

export enum ChartStyle {
  BAR = "bar",
  LINE = "line",
  PIE = "pie",
}

export enum ExtensivenesLevel {
  QUICK = "quick",
  DEEP = "deep",
}

export enum FormatPreference {
  TIMELINE = "timeline",
  SWOT = "swot",
  PROS_CONS = "pros_cons",
  COMPARISON = "comparison",
}

export enum JobStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETE = "complete",
  FAILED = "failed",
}

export interface TopicMetadata {
  topic: string
  extensiveness: string
  format_preference: string
  generated_at: string
  schema_version: string
}

export interface MatrixComponent {
  section_title: string
  component_type: ComponentType
  headers?: string[]
  rows?: string[][]
  chart_style?: ChartStyle
  data?: Record<string, unknown>[]
  description?: string
}

export interface DownloadedImage {
  alt: string
  local_url: string
}

export interface DocumentSource {
  id: string
  title: string
  url: string
  local_path: string
  snippet: string
  downloaded_images: DownloadedImage[]
}

export interface DashboardPayload {
  topic_metadata: TopicMetadata
  executive_summary: string
  matrix_data: MatrixComponent[]
  document_library: DocumentSource[]
}

export interface ResearchRequest {
  topic: string
  extensiveness: ExtensivenesLevel
  format_preference: FormatPreference
}

export interface ResearchJobStatus {
  job_id: string
  status: JobStatus
  progress_message: string
  workspace_slug?: string
  error?: string
  created_at: string
  updated_at: string
}

export interface NotebookQuery {
  workspace_slug: string
  question: string
}

export interface RetrievedChunk {
  content: string
  source_id: string
  url: string
  chunk_index: number
  distance: number
}

export interface NotebookResponse {
  answer: string
  sources: RetrievedChunk[]
  confidence_score: number
  needs_web_search: boolean
}

export interface WorkspaceListItem {
  slug: string
  topic: string
  generated_at: string
}
