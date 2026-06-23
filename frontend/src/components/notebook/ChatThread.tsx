"use client"

import { BookOpen } from "lucide-react"
import type { RetrievedChunk } from "@/lib/types"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  sources?: RetrievedChunk[]
  confidence?: number
  needsWebSearch?: boolean
}

interface ChatThreadProps {
  messages: Message[]
}

export default function ChatThread({ messages }: ChatThreadProps) {
  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center">
        <BookOpen className="w-8 h-8 text-muted mb-2" />
        <p className="text-sm text-muted">Ask a question about your research</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {messages.map((msg) => (
        <div key={msg.id}>
          {msg.role === "user" ? (
            <div className="flex justify-end">
              <div className="max-w-xs bg-accent text-base rounded-lg px-3 py-2 text-sm">
                {msg.content}
              </div>
            </div>
          ) : (
            <div className="flex justify-start">
              <div className="max-w-xs bg-card border border-border rounded-lg px-3 py-2 space-y-2">
                <p className="text-sm text-primary leading-relaxed">
                  {msg.content}
                </p>

                {msg.confidence !== undefined && (
                  <div className="text-xs text-muted mb-2">
                    <div className="font-semibold mb-1">Confidence</div>
                    <div className="w-full bg-base rounded h-1.5 overflow-hidden">
                      <div
                        className={`h-full transition-all ${
                          msg.confidence > 0.7
                            ? "bg-green-500"
                            : msg.confidence >= 0.3
                              ? "bg-yellow-500"
                              : "bg-red-500"
                        }`}
                        style={{ width: `${msg.confidence * 100}%` }}
                      />
                    </div>
                  </div>
                )}

                {msg.sources && msg.sources.length > 0 && (
                  <div className="text-xs text-muted pt-2 border-t border-border">
                    <div className="font-semibold mb-1">Sources ({msg.sources.length})</div>
                    {msg.sources.slice(0, 2).map((source, idx) => (
                      <a
                        key={idx}
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block truncate text-accent hover:underline"
                      >
                        {source.url.replace(/^https?:\/\//, "").substring(0, 20)}...
                      </a>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
