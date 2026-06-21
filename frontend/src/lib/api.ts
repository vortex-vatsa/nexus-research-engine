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
  token?: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...init,
  })

  if (!res.ok) throw new ApiError(res.status, await res.text())
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const createApi = (token: string) => ({
  runResearch: (body: ResearchRequest) =>
    request<{ job_id: string }>("/research/run", token, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getJobStatus: (jobId: string) =>
    request<ResearchJobStatus>(`/research/status/${jobId}`, token),

  listWorkspaces: () =>
    request<WorkspaceListItem[]>("/workspaces", token),

  getWorkspace: (slug: string) =>
    request<DashboardPayload>(`/workspaces/${slug}`, token),

  deleteWorkspace: (slug: string) =>
    request<void>(`/workspaces/${slug}`, token, { method: "DELETE" }),

  queryNotebook: (body: NotebookQuery) =>
    request<NotebookResponse>("/notebook/query", token, {
      method: "POST",
      body: JSON.stringify(body),
    }),
})
