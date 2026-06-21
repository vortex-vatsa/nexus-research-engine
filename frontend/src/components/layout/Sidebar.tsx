"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useSession } from "next-auth/react"
import { Trash2, Plus } from "lucide-react"
import { useWorkspaceStore } from "@/store/workspace"
import { createApi } from "@/lib/api"
import { formatDate } from "@/lib/utils"

export function Sidebar() {
  const router = useRouter()
  const { data: session } = useSession()
  const [isLoading, setIsLoading] = useState(true)
  const { workspaces, activeSlug, fetchWorkspaces, removeWorkspace } = useWorkspaceStore()

  useEffect(() => {
    if (session?.accessToken) {
      fetchWorkspaces(session.accessToken).finally(() => setIsLoading(false))
    }
  }, [session?.accessToken, fetchWorkspaces])

  const handleDelete = async (slug: string) => {
    if (!session?.accessToken) return
    try {
      const api = createApi(session.accessToken)
      await api.deleteWorkspace(slug)
      removeWorkspace(slug)
    } catch (error) {
      console.error("Failed to delete workspace:", error)
    }
  }

  return (
    <div className="w-60 bg-surface border-r border-border flex flex-col h-screen">
      <div className="p-4 border-b border-border">
        <button
          onClick={() => router.push("/")}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-accent text-white rounded-lg font-semibold hover:bg-accent/90 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Research
        </button>
      </div>

      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="p-4 text-center text-muted text-sm">Loading workspaces...</div>
        ) : workspaces.length === 0 ? (
          <div className="p-4 text-center text-muted text-sm">
            <p>No workspaces yet.</p>
            <p className="mt-2">Start your first research.</p>
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {workspaces.map((workspace) => (
              <div
                key={workspace.slug}
                className={`group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                  activeSlug === workspace.slug
                    ? "bg-accent/10"
                    : "hover:bg-card"
                }`}
              >
                <button
                  onClick={() => router.push(`/workspace/${workspace.slug}`)}
                  className="flex-1 text-left truncate"
                >
                  <p className="text-primary font-medium truncate text-sm max-w-xs">
                    {workspace.topic}
                  </p>
                  <p className="text-muted text-xs">
                    {formatDate(workspace.generated_at)}
                  </p>
                </button>
                <button
                  onClick={() => handleDelete(workspace.slug)}
                  className="opacity-0 group-hover:opacity-100 p-1.5 text-muted hover:text-red-400 transition-all"
                  title="Delete workspace"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
