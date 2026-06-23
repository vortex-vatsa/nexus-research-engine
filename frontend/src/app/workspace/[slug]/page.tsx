"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { createApi } from "@/lib/api"
import type { DashboardPayload } from "@/lib/types"
import DashboardCanvas from "@/components/dashboard/DashboardCanvas"
import NotebookPanel from "@/components/notebook/NotebookPanel"
import { useNotebook } from "@/lib/notebook-context"

interface WorkspacePageProps {
  params: { slug: string }
}

export default function WorkspacePage({ params }: WorkspacePageProps) {
  const { data: session } = useSession()
  const router = useRouter()
  const { showNotebook } = useNotebook()
  const [payload, setPayload] = useState<DashboardPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!session?.user?.email) return

    const token = (session as any).nexusToken || ""
    const api = createApi(token)

    const fetchWorkspace = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await api.getWorkspace(params.slug)
        setPayload(data)
      } catch (err) {
        setError("Workspace not found")
        console.error("Failed to load workspace:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchWorkspace()
  }, [session, params.slug])

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
        <div className="text-red-400">⚠️ {error || "Workspace not found"}</div>
        <button
          onClick={() => router.push("/")}
          className="px-3 py-1.5 text-sm rounded bg-accent text-base hover:bg-accent/80"
        >
          Back
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
      <DashboardCanvas payload={payload} />
      <NotebookPanel workspaceSlug={params.slug} isOpen={showNotebook} />
    </>
  )
}
