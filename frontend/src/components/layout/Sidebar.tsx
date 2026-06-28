"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useSession } from "next-auth/react"
import { Trash2, Plus, BookOpen } from "lucide-react"
import { useWorkspaceStore } from "@/store/workspace"
import { createApi } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import { useToast } from "@/hooks/useToast"

export function Sidebar() {
  const router = useRouter()
  const { data: session } = useSession()
  const [isLoading, setIsLoading] = useState(true)
  const { workspaces, activeSlug, fetchWorkspaces, removeWorkspace } = useWorkspaceStore()
  const { success, error: showError } = useToast()

  useEffect(() => {
    if (session?.nexusToken) {
      fetchWorkspaces(session.nexusToken).finally(() => setIsLoading(false))
    }
  }, [session?.nexusToken, fetchWorkspaces])

  const handleDelete = async (slug: string) => {
    if (!session?.nexusToken) return
    try {
      const api = createApi(session.nexusToken)
      await api.deleteWorkspace(slug)
      removeWorkspace(slug)
      success("Workspace deleted.")
    } catch (error) {
      console.error("Failed to delete workspace:", error)
      showError("Failed to delete workspace")
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
          <div className="flex flex-col items-center justify-center p-4 pt-12 text-center">
            <BookOpen className="w-8 h-8 text-muted mb-3 opacity-50" />
            <p className="text-muted text-sm">No workspaces yet.</p>
            <p className="text-muted text-xs mt-1">Start your first research.</p>
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
