"use client"

import { useSession } from "next-auth/react"
import { useRouter, usePathname } from "next/navigation"
import { useEffect, useState } from "react"
import { AppShell } from "@/components/layout/AppShell"

interface ProtectedLayoutProps {
  children: React.ReactNode
  onToggleNotebook: () => void
}

export function ProtectedLayout({
  children,
  onToggleNotebook,
}: ProtectedLayoutProps) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const pathname = usePathname()
  const [mounted, setMounted] = useState(false)

  const isLoginPage = pathname === "/login"
  const isAuthRoute = pathname.startsWith("/api/auth")

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true)
  }, [])

  useEffect(() => {
    // Only check auth after component is mounted
    if (!mounted) return

    // If not authenticated and not on login page, redirect to login
    if (status === "unauthenticated" && !isLoginPage && !isAuthRoute) {
      router.replace("/login")
    }
  }, [status, pathname, isLoginPage, isAuthRoute, router, mounted])

  // Don't render anything until mounted to prevent hydration mismatch
  if (!mounted) {
    return null
  }

  // Show loading state while checking auth
  if (status === "loading") {
    return (
      <div className="flex items-center justify-center h-screen bg-base">
        <p className="text-muted">Checking authentication...</p>
      </div>
    )
  }

  // If on login page, show children without AppShell
  if (isLoginPage || isAuthRoute) {
    return <>{children}</>
  }

  // If authenticated, show AppShell with children
  if (status === "authenticated" && session) {
    return (
      <AppShell onToggleNotebook={onToggleNotebook}>
        {children}
      </AppShell>
    )
  }

  // If unauthenticated, show nothing (useEffect will redirect)
  if (status === "unauthenticated") {
    return (
      <div className="flex items-center justify-center h-screen bg-base">
        <p className="text-muted">Redirecting to login...</p>
      </div>
    )
  }

  return null
}
