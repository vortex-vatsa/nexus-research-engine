"use client"

import { SessionProvider } from "next-auth/react"
import { useState } from "react"
import { ProtectedLayout } from "./protected-layout"

interface LayoutClientProps {
  children: React.ReactNode
}

export function LayoutClient({ children }: LayoutClientProps) {
  const [showNotebook, setShowNotebook] = useState(false)

  return (
    <SessionProvider>
      <ProtectedLayout
        showNotebook={showNotebook}
        onToggleNotebook={() => setShowNotebook(!showNotebook)}
      >
        {children}
      </ProtectedLayout>
    </SessionProvider>
  )
}
