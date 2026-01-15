import { NavLink } from 'react-router-dom'
import { LayoutDashboard, GitBranch, Database, Plug } from 'lucide-react'
import { cn } from '../../lib/utils'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/pipelines', icon: GitBranch, label: 'Pipelines' },
  { to: '/connectors', icon: Plug, label: 'Connectors' },
  { to: '/saved', icon: Database, label: 'Saved' },
]

export function MainNav() {
  return (
    <nav className="flex items-center gap-1">
      {navItems.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              isActive
                ? 'bg-bizon-primary/10 text-bizon-primary'
                : 'text-bizon-textSecondary hover:text-bizon-text hover:bg-bizon-surface'
            )
          }
        >
          <Icon className="h-4 w-4" />
          {label}
        </NavLink>
      ))}
    </nav>
  )
}
