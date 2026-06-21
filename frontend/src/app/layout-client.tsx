"use client"

import { SessionProvider } from "next-auth/react"
import { useState } from "react"
import { AppShell } from "@/components/layout/AppShell"

interface LayoutClientProps {
  children: React.ReactNode
}

export function LayoutClient({ children }: LayoutClientProps) {
  const [showNotebook, setShowNotebook] = useState(false)

  return (
    <SessionProvider>
      <AppShell
        showNotebook={showNotebook}
        onToggleNotebook={() => setShowNotebook(!showNotebook)}
      >
        {children}
      </AppShell>
    </SessionProvider>
  )
}
