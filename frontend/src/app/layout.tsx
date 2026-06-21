import type { Metadata } from "next"
import "./globals.css"
import { LayoutClient } from "./layout-client"

export const metadata: Metadata = {
  title: "NEXUS — Autonomous Research Engine",
  description: "NEXUS is an autonomous research engine that replaces AI chat boxes with a structured visual business dashboard.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="h-full bg-base">
      <body className="h-full m-0 p-0 bg-base">
        <LayoutClient>{children}</LayoutClient>
      </body>
    </html>
  )
}
