"use client"

import { useState } from "react"
import { ArrowRight } from "lucide-react"

interface QueryInputProps {
  onSubmit: (question: string) => void
  disabled?: boolean
}

export default function QueryInput({
  onSubmit,
  disabled = false,
}: QueryInputProps) {
  const [input, setInput] = useState("")

  const handleSubmit = () => {
    if (input.trim()) {
      onSubmit(input)
      setInput("")
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="flex gap-2">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a question..."
        disabled={disabled}
        className="flex-1 bg-base border border-border rounded px-3 py-2 text-sm text-primary placeholder-muted focus:outline-none focus:border-accent disabled:opacity-50 resize-none"
        rows={3}
      />
      <button
        onClick={handleSubmit}
        disabled={disabled || !input.trim()}
        className="p-2 bg-accent text-base rounded hover:bg-accent/80 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  )
}
