import type { Metadata } from "next"

import "@/app/globals.css"

export const metadata: Metadata = {
  title: "GEO Audit Dashboard",
  description: "Static-first dashboard for Bright Data GEO audits.",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
