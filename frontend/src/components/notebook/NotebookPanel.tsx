"use client"

import { useState, useRef, useEffect } from "react"
import { useSession } from "next-auth/react"
import { createApi } from "@/lib/api"
import type { NotebookQuery, RetrievedChunk } from "@/lib/types"
import ChatThread from "./ChatThread"
import QueryInput from "./QueryInput"
import RetryAlert from "./RetryAlert"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  sources?: RetrievedChunk[]
  confidence?: number
  needsWebSearch?: boolean
}

interface NotebookPanelProps {
  workspaceSlug: string
  isOpen: boolean
}

export default function NotebookPanel({
  workspaceSlug,
  isOpen,
}: NotebookPanelProps) {
  const { data: session } = useSession()
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  const scroll = () => {
    endRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scroll()
  }, [messages])

  const handleSubmit = async (question: string) => {
    if (!question.trim() || !session) return

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question,
    }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)

    try {
      const token = (session as { nexusToken?: string }).nexusToken || ""
      const api = createApi(token)

      const response = await api.queryNotebook({
        workspace_slug: workspaceSlug,
        question,
      } as NotebookQuery)

      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        confidence: response.confidence_score,
        needsWebSearch: response.needs_web_search,
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch {
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: "Failed to get an answer. Please try again.",
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  const handleRetry = async (messageId: string) => {
    const msg = messages.find((m) => m.id === messageId)
    if (!msg) return

    setLoading(true)
    try {
      const token = (session as { nexusToken?: string }).nexusToken || ""
      const api = createApi(token)

      const response = await api.queryNotebook({
        workspace_slug: workspaceSlug,
        question: msg.content,
      } as NotebookQuery)

      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId
            ? {
                ...m,
                content: response.answer,
                sources: response.sources,
                confidence: response.confidence_score,
                needsWebSearch: response.needs_web_search,
              }
            : m
        )
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        position: "fixed",
        right: 0,
        top: "56px",
        height: "calc(100vh - 56px)",
        width: "320px",
        backgroundColor: "#111118",
        borderLeft: "1px solid #1e1e2e",
        display: "flex",
        flexDirection: "column",
        zIndex: 9999,
        transform: isOpen ? "translateX(0)" : "translateX(100%)",
        transition: "transform 0.3s ease-out",
        boxShadow: "-2px 0 10px rgba(0,0,0,0.3)"
      }}
    >
      {/* Header */}
      <div className="p-4 border-b border-border">
        <h2 className="text-sm font-semibold text-primary">
          Research Assistant
        </h2>
      </div>

      {/* Chat thread */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <ChatThread messages={messages} />
        <div ref={endRef} />
      </div>

      {/* Retry alerts */}
      <div className="px-4 space-y-2">
        {messages
          .filter((m) => m.needsWebSearch && m.role === "assistant")
          .map((m) => (
            <RetryAlert
              key={m.id}
              messageId={m.id}
              onRetry={handleRetry}
              disabled={loading}
            />
          ))}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-border bg-card/50">
        <QueryInput onSubmit={handleSubmit} disabled={loading} />
      </div>
    </div>
  )
}
