"use client"

import { ChartStyle } from "@/lib/types"
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"

interface ChartBlockProps {
  data: Record<string, unknown>[]
  style?: ChartStyle
}

const COLORS = [
  "#6366f1",
  "#a855f7",
  "#ec4899",
  "#f43f5e",
  "#f97316",
  "#eab308",
]

export default function ChartBlock({ data, style }: ChartBlockProps) {
  if (!data || data.length === 0) {
    return <div className="text-muted text-sm">No chart data available.</div>
  }

  const chartStyle = style || ChartStyle.BAR
  const height = 280

  if (chartStyle === ChartStyle.LINE) {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
          <XAxis dataKey="name" stroke="#64748b" />
          <YAxis stroke="#64748b" />
          <Tooltip
            contentStyle={{ backgroundColor: "#111118", border: "1px solid #1e1e2e" }}
            labelStyle={{ color: "#e2e8f0" }}
          />
          <Legend />
          {Object.keys(data[0]).map((key) => (
            key !== "name" && (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke="#6366f1"
                strokeWidth={2}
                dot={false}
              />
            )
          ))}
        </LineChart>
      </ResponsiveContainer>
    )
  }

  if (chartStyle === ChartStyle.PIE) {
    const pieData = data.map((item) => ({
      name: String(item.name),
      value: Number(item.value) || 0,
    }))
    return (
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={pieData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) =>
              `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`
            }
            outerRadius={80}
            fill="#6366f1"
            dataKey="value"
          >
            {pieData.map((_, idx) => (
              <Cell key={`cell-${idx}`} fill={COLORS[idx % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
        <XAxis dataKey="name" stroke="#64748b" />
        <YAxis stroke="#64748b" />
        <Tooltip
          contentStyle={{ backgroundColor: "#111118", border: "1px solid #1e1e2e" }}
          labelStyle={{ color: "#e2e8f0" }}
        />
        <Legend />
        {Object.keys(data[0]).map((key) => (
          key !== "name" && (
            <Bar key={key} dataKey={key} fill="#6366f1" />
          )
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}
