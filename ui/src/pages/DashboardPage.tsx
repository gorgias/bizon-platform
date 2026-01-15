import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { GitBranch, Play, CheckCircle, XCircle, Clock, ArrowRight } from 'lucide-react'
import { Card, CardContent, PageLoader, Button } from '../components/ui'
import { statsApi } from '../api'

export function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: () => statsApi.get(),
  })

  if (isLoading) {
    return <PageLoader />
  }

  const statCards = [
    {
      label: 'Total Pipelines',
      value: stats?.total_pipelines ?? 0,
      icon: GitBranch,
      color: 'text-bizon-primary',
    },
    {
      label: 'Enabled',
      value: stats?.enabled_pipelines ?? 0,
      icon: Play,
      color: 'text-bizon-success',
    },
    {
      label: 'Total Runs',
      value: stats?.total_runs ?? 0,
      icon: Clock,
      color: 'text-bizon-textSecondary',
    },
    {
      label: 'Successful',
      value: stats?.successful_runs ?? 0,
      icon: CheckCircle,
      color: 'text-bizon-success',
    },
    {
      label: 'Failed',
      value: stats?.failed_runs ?? 0,
      icon: XCircle,
      color: 'text-bizon-danger',
    },
  ]

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-bizon-text">Dashboard</h1>
        <p className="text-bizon-textSecondary mt-1">
          Overview of your pipeline operations
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {statCards.map(({ label, value, icon: Icon, color }) => (
          <Card key={label}>
            <CardContent className="flex items-center gap-4">
              <div className={`p-3 rounded-lg bg-bizon-bg ${color}`}>
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold text-bizon-text">{value}</p>
                <p className="text-sm text-bizon-textSecondary">{label}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="flex gap-4">
        <Link to="/pipelines">
          <Button variant="secondary">
            <GitBranch className="h-4 w-4 mr-2" />
            View Pipelines
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </Link>
        <Link to="/pipelines/new">
          <Button>
            Create Pipeline
          </Button>
        </Link>
      </div>
    </div>
  )
}
