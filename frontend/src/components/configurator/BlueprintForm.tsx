"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { useSession } from "next-auth/react"
import { Clock, Grid2X2, Scale, Table2 } from "lucide-react"
import { createApi, ApiError } from "@/lib/api"
import { ExtensivenesLevel, FormatPreference } from "@/lib/types"

export function BlueprintForm() {
  const router = useRouter()
  const { data: session } = useSession()
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  const [topic, setTopic] = useState("")
  const [extensiveness, setExtensiveness] = useState<ExtensivenesLevel>(
    ExtensivenesLevel.QUICK
  )
  const [formatPref, setFormatPref] = useState<FormatPreference>(
    FormatPreference.COMPARISON
  )
  const [phase, setPhase] = useState<"idle" | "running" | "error">("idle")
  const [progressMsg, setProgressMsg] = useState("")
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [])

  const startPolling = (jobId: string, token: string) => {
    if (intervalRef.current) clearInterval(intervalRef.current)
    const api = createApi(token)

    intervalRef.current = setInterval(async () => {
      try {
        const status = await api.getJobStatus(jobId)
        setProgressMsg(status.progress_message)

        if (status.status === "complete" && status.workspace_slug) {
          clearInterval(intervalRef.current!)
          intervalRef.current = null
          router.push(`/workspace/${status.workspace_slug}`)
        } else if (status.status === "failed") {
          clearInterval(intervalRef.current!)
          intervalRef.current = null
          setPhase("error")
          setErrorMsg(status.error ?? "Research failed")
        }
      } catch (e) {
        console.error("Polling error:", e)
        if (e instanceof ApiError && e.status === 401) {
          clearInterval(intervalRef.current!)
          intervalRef.current = null
          setPhase("error")
          setErrorMsg("Session expired. Please sign in again.")
        }
      }
    }, 2000)
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (topic.trim().length < 3) {
      setErrorMsg("Topic must be at least 3 characters")
      return
    }

    if (!session?.nexusToken) {
      setErrorMsg("Not authenticated")
      return
    }

    try {
      setErrorMsg(null)
      setPhase("running")
      setProgressMsg("Starting research...")

      const token = session.nexusToken
      const api = createApi(token)
      const result = await api.runResearch({
        topic: topic.trim(),
        extensiveness,
        format_preference: formatPref,
      })

      startPolling(result.job_id, token)
    } catch (error) {
      setPhase("error")
      setErrorMsg(
        error instanceof Error ? error.message : "Failed to start research"
      )
    }
  }

  const formatOptions = [
    { value: FormatPreference.TIMELINE, icon: Clock, label: "Timeline" },
    { value: FormatPreference.SWOT, icon: Grid2X2, label: "SWOT Analysis" },
    { value: FormatPreference.PROS_CONS, icon: Scale, label: "Pros & Cons" },
    {
      value: FormatPreference.COMPARISON,
      icon: Table2,
      label: "Comparison Matrix",
    },
  ]

  const isLoading = phase === "running"
  const isError = phase === "error"

  return (
    <div className="min-h-screen bg-base flex items-center justify-center p-4">
      <div className="w-full max-w-[560px] space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-accent">NEXUS</h1>
          <p className="text-muted text-lg">Research Blueprint</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Topic Input */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-primary">
              Research Topic
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => {
                setTopic(e.target.value)
                if (errorMsg && e.target.value.trim().length >= 3) {
                  setErrorMsg(null)
                }
              }}
              placeholder="e.g., Future of electric vehicles in Germany"
              disabled={isLoading}
              className="w-full px-4 py-3 bg-card border border-border rounded-lg text-primary placeholder-muted focus:outline-none focus:border-accent transition-colors disabled:opacity-50"
            />
            {errorMsg && (
              <p className="text-sm text-red-400">{errorMsg}</p>
            )}
          </div>

          {/* Extensiveness */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-primary">
              Research Depth
            </label>
            <div className="flex gap-3">
              {[
                { value: ExtensivenesLevel.QUICK, label: "Quick" },
                { value: ExtensivenesLevel.DEEP, label: "Deep Dive" },
              ].map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setExtensiveness(option.value)}
                  disabled={isLoading}
                  className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 ${
                    extensiveness === option.value
                      ? "bg-accent text-white"
                      : "bg-card border border-border text-primary hover:border-accent"
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Format Preference */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-primary">
              Output Format
            </label>
            <div className="grid grid-cols-2 gap-3">
              {formatOptions.map(({ value, icon: Icon, label }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setFormatPref(value)}
                  disabled={isLoading}
                  className={`p-3 rounded-lg border transition-colors disabled:opacity-50 ${
                    formatPref === value
                      ? "border-accent bg-accent/10"
                      : "border-border hover:border-accent"
                  }`}
                >
                  <Icon className="w-5 h-5 mx-auto mb-2 text-accent" />
                  <p className="text-xs font-medium text-primary">{label}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full px-6 py-3 bg-accent text-white rounded-lg font-semibold hover:bg-accent/90 disabled:opacity-50 transition-colors"
          >
            {isLoading ? "Researching..." : "Start Research"}
          </button>
        </form>

        {/* Progress */}
        {isLoading && (
          <div className="space-y-2 text-center">
            <div className="flex justify-center">
              <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
            </div>
            <p className="text-sm text-muted">{progressMsg}</p>
          </div>
        )}

        {/* Error Message */}
        {isError && errorMsg && (
          <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg">
            <p className="text-sm text-red-300">{errorMsg}</p>
            <button
              onClick={() => {
                setPhase("idle")
                setErrorMsg(null)
              }}
              className="mt-2 text-xs text-red-400 hover:text-red-300 underline"
            >
              Try again
            </button>
          </div>
        )}

        {/* Info Text */}
        <p className="text-center text-xs text-muted">
          Research typically takes 2-5 minutes depending on topic complexity
        </p>
      </div>
    </div>
  )
}
