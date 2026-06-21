"use client"

import { useSession, signOut } from "next-auth/react"
import { MessageSquare, LogOut } from "lucide-react"
import { Sidebar } from "./Sidebar"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"

interface AppShellProps {
  children: React.ReactNode
  showNotebook?: boolean
  onToggleNotebook?: () => void
}

export function AppShell({
  children,
  showNotebook = false,
  onToggleNotebook,
}: AppShellProps) {
  const { data: session } = useSession()

  const userInitial = session?.user?.email?.[0].toUpperCase() || "U"

  return (
    <div className="flex h-screen bg-base overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-14 bg-surface border-b border-border flex items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-accent">NEXUS</h1>
            <p className="text-muted text-sm">Research Engine</p>
          </div>

          <div className="flex items-center gap-4">
            {onToggleNotebook && (
              <button
                onClick={onToggleNotebook}
                className="flex items-center gap-2 px-3 py-1.5 text-muted hover:text-primary transition-colors text-sm"
                title="Toggle research assistant"
              >
                <MessageSquare className="w-4 h-4" />
                <span className="hidden sm:inline">Research Assistant</span>
              </button>
            )}

            {session?.user && (
              <>
                <Avatar className="h-8 w-8">
                  <AvatarImage
                    src={session.user.image || undefined}
                    alt={session.user.name || "User"}
                  />
                  <AvatarFallback className="bg-accent text-white text-xs">
                    {userInitial}
                  </AvatarFallback>
                </Avatar>

                <button
                  onClick={() => signOut({ redirectTo: "/login" })}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-muted hover:text-primary transition-colors text-sm"
                  title="Sign out"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:inline">Sign out</span>
                </button>
              </>
            )}
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto bg-base">
          {children}
        </main>
      </div>
    </div>
  )
}
