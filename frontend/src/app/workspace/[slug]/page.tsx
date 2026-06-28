"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect, useState, use } from "react"
import { AlertCircle } from "lucide-react"
import { createApi } from "@/lib/api"
import type { DashboardPayload } from "@/lib/types"
import DashboardCanvas from "@/components/dashboard/DashboardCanvas"
import NotebookPanel from "@/components/notebook/NotebookPanel"
import { useNotebook } from "@/lib/notebook-context"

interface WorkspacePageProps {
  params: Promise<{ slug: string }>
}

export default function WorkspacePage({ params }: WorkspacePageProps) {
  const { slug } = use(params)
  const { data: session } = useSession()
  const router = useRouter()
  const { showNotebook } = useNotebook()
  const [payload, setPayload] = useState<DashboardPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!session?.user?.email) return

    const token = (session as { nexusToken?: string }).nexusToken || ""
    const api = createApi(token)

    const fetchWorkspace = async () => {
      try {
        const data = await api.getWorkspace(slug)
        setPayload(data)
        setError(null)
      } catch {
        setError("Workspace not found")
      } finally {
        setLoading(false)
      }
    }

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    fetchWorkspace()
  }, [session, slug])

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <div className="text-muted">Loading...</div>
      </div>
    )
  }

  if (error || !payload) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center gap-4">
        <AlertCircle className="w-12 h-12 text-red-500 opacity-80" />
        <div className="text-center space-y-2">
          <h2 className="text-lg font-semibold text-primary">Workspace not found</h2>
          <p className="text-sm text-muted">{error}</p>
        </div>
        <button
          onClick={() => router.push("/")}
          className="px-4 py-2 text-sm font-medium rounded bg-accent text-white hover:bg-accent/80 transition-colors"
        >
          Back to Home
        </button>
      </div>
    )
  }

  if (payload.topic_metadata.schema_version !== "1.0") {
    console.warn(
      `Schema mismatch: expected 1.0, got ${payload.topic_metadata.schema_version}`
    )
  }

  return (
    <>
      <div style={{ marginRight: showNotebook ? "320px" : "0", transition: "margin-right 0.3s ease-out" }}>
        <DashboardCanvas payload={payload} />
      </div>
      <NotebookPanel workspaceSlug={slug} isOpen={showNotebook} />
    </>
  )
}
