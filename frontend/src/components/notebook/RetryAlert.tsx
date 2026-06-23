"use client"

import { AlertCircle } from "lucide-react"

interface RetryAlertProps {
  messageId: string
  onRetry: (messageId: string) => void
  disabled?: boolean
}

export default function RetryAlert({
  messageId,
  onRetry,
  disabled = false,
}: RetryAlertProps) {
  return (
    <div className="bg-card border border-border rounded p-3 space-y-2">
      <div className="flex gap-2 items-start">
        <AlertCircle className="w-4 h-4 text-muted flex-shrink-0 mt-0.5" />
        <div className="flex-1 text-xs text-muted">
          This answer needs more data. Run a quick web search?
        </div>
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => onRetry(messageId)}
          disabled={disabled}
          className="flex-1 px-2 py-1.5 bg-accent text-base text-xs rounded hover:bg-accent/80 disabled:opacity-50 transition"
        >
          Search the web
        </button>
        <button
          className="flex-1 px-2 py-1.5 bg-base border border-border text-primary text-xs rounded hover:bg-card/80 transition"
        >
          Dismiss
        </button>
      </div>
    </div>
  )
}
