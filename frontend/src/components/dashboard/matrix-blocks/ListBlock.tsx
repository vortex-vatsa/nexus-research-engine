"use client"

interface ListBlockProps {
  rows: string[][]
}

export default function ListBlock({ rows }: ListBlockProps) {
  if (!rows || rows.length === 0) {
    return <div className="text-muted text-sm">No list data available.</div>
  }

  return (
    <div className="space-y-3">
      {rows.map((row, idx) => (
        <div key={idx} className="pb-3 border-b border-border last:border-0">
          <div className="font-medium text-primary text-sm mb-1">
            {row[0]}
          </div>
          {row[1] && (
            <div className="text-xs text-muted leading-relaxed">
              {row[1]}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
