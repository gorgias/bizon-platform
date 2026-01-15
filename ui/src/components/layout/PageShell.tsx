import type { ReactNode } from 'react'
import { MainNav } from './MainNav'

interface PageShellProps {
  children: ReactNode
}

export function PageShell({ children }: PageShellProps) {
  return (
    <div className="min-h-screen bg-bizon-bg">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-bizon-border bg-bizon-bg/95 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-8">
              <a href="/" className="flex items-center gap-2">
                <img src="/logo.png" alt="Bizon" className="h-8 w-8" />
                <span className="font-semibold text-bizon-text">Bizon</span>
              </a>
              <MainNav />
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  )
}
