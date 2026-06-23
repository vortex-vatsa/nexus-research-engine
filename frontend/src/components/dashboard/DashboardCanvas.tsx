"use client"

import type { DashboardPayload } from "@/lib/types"
import { formatDate } from "@/lib/utils"
import ExecutiveBrief from "./ExecutiveBrief"
import DataMatrix from "./DataMatrix"
import DocumentLibrary from "./DocumentLibrary"

interface DashboardCanvasProps {
  payload: DashboardPayload
}

export default function DashboardCanvas({ payload }: DashboardCanvasProps) {
  const { topic_metadata, executive_summary, matrix_data, document_library } =
    payload

  return (
    <div className="w-full h-full flex flex-col bg-base p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-primary mb-2">
          {topic_metadata.topic}
        </h1>
        <div className="flex items-center gap-3 text-sm text-muted">
          <span>{formatDate(topic_metadata.generated_at)}</span>
          <span className="px-2 py-1 bg-card rounded text-xs font-mono">
            v{topic_metadata.schema_version}
          </span>
        </div>
      </div>

      {/* Three-column grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1 overflow-auto">
        {/* Left: Executive Brief (25%) */}
        <div className="lg:col-span-1">
          <ExecutiveBrief
            summary={executive_summary}
            extensiveness={topic_metadata.extensiveness}
            formatPreference={topic_metadata.format_preference}
          />
        </div>

        {/* Center: Data Matrix (50%) */}
        <div className="lg:col-span-2 overflow-auto">
          <DataMatrix components={matrix_data} />
        </div>

        {/* Right: Document Library (25%) */}
        <div className="lg:col-span-1">
          <DocumentLibrary sources={document_library} />
        </div>
      </div>
    </div>
  )
}
