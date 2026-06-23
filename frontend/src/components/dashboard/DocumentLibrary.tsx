"use client"

import { getDomain } from "@/lib/utils"
import type { DocumentSource } from "@/lib/types"
import { ExternalLink } from "lucide-react"

interface DocumentLibraryProps {
  sources: DocumentSource[]
}

export default function DocumentLibrary({ sources }: DocumentLibraryProps) {
  if (!sources || sources.length === 0) {
    return (
      <div className="border border-border rounded p-4 bg-card h-fit sticky top-6">
        <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-4">
          Source Library
        </h3>
        <div className="text-muted text-sm">No sources saved.</div>
      </div>
    )
  }

  return (
    <div className="border border-border rounded p-4 bg-card h-fit sticky top-6">
      <div className="flex items-center gap-2 mb-4">
        <h3 className="text-xs font-semibold text-muted uppercase tracking-wide">
          Source Library
        </h3>
        <span className="px-2 py-1 bg-accent/10 text-accent text-xs rounded">
          {sources.length}
        </span>
      </div>

      <div className="space-y-3 max-h-[calc(100vh-180px)] overflow-y-auto pr-2">
        {sources.map((source) => (
          <a
            key={source.id}
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block p-3 rounded bg-base border border-border/50 hover:border-accent/50 transition text-left"
          >
            <div className="flex items-start gap-2 mb-1">
              <div className="flex-1 min-w-0">
                <h4 className="text-xs font-medium text-primary truncate">
                  {source.title}
                </h4>
              </div>
              <ExternalLink className="w-3 h-3 text-muted flex-shrink-0 mt-0.5" />
            </div>
            <div className="text-xs text-accent mb-2">
              {getDomain(source.url)}
            </div>
            <p className="text-xs text-muted line-clamp-3">
              {source.snippet}
            </p>
          </a>
        ))}
      </div>
    </div>
  )
}
