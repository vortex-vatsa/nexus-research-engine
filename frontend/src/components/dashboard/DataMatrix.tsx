"use client"

import { ComponentType, type MatrixComponent } from "@/lib/types"
import TableBlock from "./matrix-blocks/TableBlock"
import ChartBlock from "./matrix-blocks/ChartBlock"
import ListBlock from "./matrix-blocks/ListBlock"
import { BarChart3 } from "lucide-react"
import React from "react"

interface DataMatrixProps {
  components: MatrixComponent[]
}

class ChartErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return <div className="text-muted p-4 text-sm">Chart failed to render.</div>
    }
    return this.props.children
  }
}

export default function DataMatrix({ components }: DataMatrixProps) {
  if (!components || components.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <BarChart3 className="w-8 h-8 text-muted mb-3 opacity-50" />
        <p className="text-muted text-sm">No structured data generated.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h3 className="text-xs font-semibold text-muted uppercase tracking-wide">
        Data Matrix
      </h3>
      {components.map((component, idx) => (
        <ChartErrorBoundary key={idx}>
          <div className="border border-border rounded bg-card p-4">
            <h4 className="text-sm font-semibold text-primary mb-4">
              {component.section_title}
            </h4>
            {component.component_type === ComponentType.TABLE && (
              <TableBlock
                headers={component.headers || []}
                rows={component.rows || []}
              />
            )}
            {component.component_type === ComponentType.CHART && (
              <ChartBlock
                data={component.data || []}
                style={component.chart_style}
              />
            )}
            {component.component_type === ComponentType.LIST && (
              <ListBlock rows={component.rows || []} />
            )}
            {component.description && (
              <p className="text-xs text-muted mt-3 pt-3 border-t border-border">
                {component.description}
              </p>
            )}
          </div>
        </ChartErrorBoundary>
      ))}
    </div>
  )
}
