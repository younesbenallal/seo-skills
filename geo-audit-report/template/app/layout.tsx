import type { Metadata } from "next"
import { Geist } from "next/font/google"

import "@/app/globals.css"

const geist = Geist({
  subsets: ["latin"],
  display: "swap",
})

export const metadata: Metadata = {
  title: "Geo visibility audit",
  description: "Prospect-facing AI search visibility, citation, and local map audit.",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={geist.className}>
      <body>{children}</body>
    </html>
  )
}
