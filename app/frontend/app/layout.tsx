import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Industrial Troubleshooting Copilot',
  description: 'AI-powered industrial troubleshooting assistant. Upload manuals, ask questions, get cited answers with recommended actions.',
  keywords: ['industrial', 'troubleshooting', 'copilot', 'AI', 'maintenance', 'automation'],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#0a0a0b" />
      </head>
      <body>{children}</body>
    </html>
  )
}
