import { create } from "zustand"
import type { WorkspaceListItem } from "@/lib/types"
import { createApi } from "@/lib/api"

interface WorkspaceStore {
  activeSlug: string | null
  workspaces: WorkspaceListItem[]
  isLoading: boolean
  error: string | null
  setActiveSlug: (slug: string | null) => void
  fetchWorkspaces: (token: string) => Promise<void>
  removeWorkspace: (slug: string) => void
}

export const useWorkspaceStore = create<WorkspaceStore>((set) => ({
  activeSlug: null,
  workspaces: [],
  isLoading: false,
  error: null,

  setActiveSlug: (slug) => set({ activeSlug: slug }),

  fetchWorkspaces: async (token) => {
    set({ isLoading: true, error: null })
    try {
      const workspaces = await createApi(token).listWorkspaces()
      set({ workspaces, isLoading: false })
    } catch (e) {
      set({ error: String(e), isLoading: false })
    }
  },

  removeWorkspace: (slug) =>
    set((state) => ({
      workspaces: state.workspaces.filter((w) => w.slug !== slug),
    })),
}))
