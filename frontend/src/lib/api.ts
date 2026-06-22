import type {
  ResearchRequest,
  ResearchJobStatus,
  DashboardPayload,
  WorkspaceListItem,
  NotebookQuery,
  NotebookResponse,
} from "@/lib/types"

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message)
  }
}

async function request<T>(
  path: string,
  nexusToken: string,
  init?: RequestInit
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }
  if (nexusToken) {
    headers["Authorization"] = `Bearer ${nexusToken}`
  }

  const res = await fetch(`${BASE}${path}`, {
    headers,
    ...init,
  })

  if (!res.ok) throw new ApiError(res.status, await res.text())
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const createApi = (nexusToken: string) => ({
  runResearch: (body: ResearchRequest) =>
    request<{ job_id: string }>("/research/run", nexusToken, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getJobStatus: (jobId: string) =>
    request<ResearchJobStatus>(`/research/status/${jobId}`, nexusToken),

  listWorkspaces: () =>
    request<WorkspaceListItem[]>("/workspaces", nexusToken),

  getWorkspace: (slug: string) =>
    request<DashboardPayload>(`/workspaces/${slug}`, nexusToken),

  deleteWorkspace: (slug: string) =>
    request<void>(`/workspaces/${slug}`, nexusToken, { method: "DELETE" }),

  queryNotebook: (body: NotebookQuery) =>
    request<NotebookResponse>("/notebook/query", nexusToken, {
      method: "POST",
      body: JSON.stringify(body),
    }),
})
