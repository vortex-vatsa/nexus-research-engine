"use client"

import { SessionProvider } from "next-auth/react"
import { useState } from "react"
import { ProtectedLayout } from "./protected-layout"
import NotebookContext from "@/lib/notebook-context"

interface LayoutClientProps {
  children: React.ReactNode
}

export function LayoutClient({ children }: LayoutClientProps) {
  const [showNotebook, setShowNotebook] = useState(false)

  return (
    <SessionProvider>
      <NotebookContext.Provider value={{ showNotebook, setShowNotebook }}>
        <ProtectedLayout onToggleNotebook={() => setShowNotebook(!showNotebook)}>
          {children}
        </ProtectedLayout>
      </NotebookContext.Provider>
    </SessionProvider>
  )
}
