"use client"

interface ExecutiveBriefProps {
  summary: string
  extensiveness: string
  formatPreference: string
}

export default function ExecutiveBrief({
  summary,
  extensiveness,
  formatPreference,
}: ExecutiveBriefProps) {
  const paragraphs = summary.split("\n\n").filter((p) => p.trim())

  return (
    <div className="border-l-4 border-accent rounded p-4 bg-card h-fit sticky top-6">
      <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-4">
        Executive Brief
      </h3>
      <div className="space-y-3 mb-4">
        {paragraphs.map((para, idx) => (
          <p key={idx} className="text-sm text-primary leading-relaxed">
            {para}
          </p>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        <span className="px-2 py-1 bg-accent/10 text-accent text-xs rounded">
          {extensiveness}
        </span>
        <span className="px-2 py-1 bg-accent/10 text-accent text-xs rounded capitalize">
          {formatPreference.replace(/_/g, " ")}
        </span>
      </div>
    </div>
  )
}
