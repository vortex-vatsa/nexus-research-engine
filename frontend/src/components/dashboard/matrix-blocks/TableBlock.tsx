"use client"

interface TableBlockProps {
  headers: string[]
  rows: string[][]
}

export default function TableBlock({ headers, rows }: TableBlockProps) {
  if (!headers.length || !rows.length) {
    return <div className="text-muted text-sm">No data available.</div>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-border">
            {headers.map((h, i) => (
              <th
                key={i}
                className="px-3 py-2 text-left text-xs font-semibold text-muted bg-card/50"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIdx) => (
            <tr
              key={rowIdx}
              className={rowIdx % 2 === 0 ? "bg-base/50" : "bg-base"}
            >
              {row.map((cell, cellIdx) => (
                <td key={cellIdx} className="px-3 py-2 text-primary">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
