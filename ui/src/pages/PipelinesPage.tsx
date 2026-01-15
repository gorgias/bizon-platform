import { Link } from 'react-router-dom'
import { Plus, Play, MoreVertical, Copy, Trash2, ChevronDown, ChevronRight, Layers, GitBranch, X, Search } from 'lucide-react'
import { format } from 'date-fns'
import { Button, Card, StatusChip, PageLoader, EmptyState, TagChip } from '../components/ui'
import {
  usePipelines,
  useTriggerRun,
  useDeletePipeline,
  useDuplicatePipeline,
  useSyncOtherStreams,
  useTags,
} from '../hooks'
import { useState, useMemo } from 'react'
import type { Pipeline } from '../api'

type GroupBy = 'none' | 'source' | 'destination' | 'status' | 'tag'

function groupPipelines(pipelines: Pipeline[], groupBy: GroupBy): Map<string, Pipeline[]> {
  const groups = new Map<string, Pipeline[]>()

  if (groupBy === 'none') {
    groups.set('all', pipelines)
    return groups
  }

  for (const pipeline of pipelines) {
    if (groupBy === 'tag') {
      // For tag grouping, a pipeline can appear in multiple groups
      const tags = pipeline.tags?.length ? pipeline.tags : ['Untagged']
      for (const tag of tags) {
        if (!groups.has(tag)) {
          groups.set(tag, [])
        }
        groups.get(tag)!.push(pipeline)
      }
    } else {
      let key: string
      if (groupBy === 'source') {
        key = pipeline.config.source.name
      } else if (groupBy === 'destination') {
        key = pipeline.config.destination.name
      } else {
        key = pipeline.enabled ? 'Enabled' : 'Disabled'
      }

      if (!groups.has(key)) {
        groups.set(key, [])
      }
      groups.get(key)!.push(pipeline)
    }
  }

  // Sort groups: for status put Enabled first, otherwise alphabetically
  if (groupBy === 'status') {
    const sorted = new Map<string, Pipeline[]>()
    if (groups.has('Enabled')) sorted.set('Enabled', groups.get('Enabled')!)
    if (groups.has('Disabled')) sorted.set('Disabled', groups.get('Disabled')!)
    return sorted
  }

  // For tag grouping, put Untagged at the end
  if (groupBy === 'tag') {
    const sorted = new Map([...groups.entries()].sort((a, b) => {
      if (a[0] === 'Untagged') return 1
      if (b[0] === 'Untagged') return -1
      return a[0].localeCompare(b[0])
    }))
    return sorted
  }

  return new Map([...groups.entries()].sort((a, b) => a[0].localeCompare(b[0])))
}

type StatusFilter = 'all' | 'enabled' | 'disabled'

interface Filters {
  search: string
  status: StatusFilter
  source: string
  destination: string
  tags: string[]
}

export function PipelinesPage() {
  const { data: pipelines, isLoading } = usePipelines()
  const { data: allTags } = useTags()
  const triggerRun = useTriggerRun()
  const deletePipeline = useDeletePipeline()
  const duplicatePipeline = useDuplicatePipeline()
  const syncOtherStreams = useSyncOtherStreams()
  const [openMenu, setOpenMenu] = useState<string | null>(null)
  const [groupBy, setGroupBy] = useState<GroupBy>('none')
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set())
  const [filters, setFilters] = useState<Filters>({
    search: '',
    status: 'all',
    source: '',
    destination: '',
    tags: [],
  })

  // Extract unique sources and destinations for filter dropdowns
  const { sources, destinations } = useMemo(() => {
    if (!pipelines) return { sources: [], destinations: [] }
    const sourceSet = new Set(pipelines.map((p) => p.config.source.name))
    const destSet = new Set(pipelines.map((p) => p.config.destination.name))
    return {
      sources: Array.from(sourceSet).sort(),
      destinations: Array.from(destSet).sort(),
    }
  }, [pipelines])

  // Apply filters
  const filteredPipelines = useMemo(() => {
    if (!pipelines) return []
    return pipelines.filter((p) => {
      // Search filter
      if (filters.search) {
        const search = filters.search.toLowerCase()
        const matchesName = p.name.toLowerCase().includes(search)
        const matchesSource = p.config.source.name.toLowerCase().includes(search)
        const matchesDest = p.config.destination.name.toLowerCase().includes(search)
        if (!matchesName && !matchesSource && !matchesDest) return false
      }
      // Status filter
      if (filters.status === 'enabled' && !p.enabled) return false
      if (filters.status === 'disabled' && p.enabled) return false
      // Source filter
      if (filters.source && p.config.source.name !== filters.source) return false
      // Destination filter
      if (filters.destination && p.config.destination.name !== filters.destination) return false
      // Tag filter
      if (filters.tags.length > 0) {
        if (!p.tags || !filters.tags.some((t) => p.tags!.includes(t))) return false
      }
      return true
    })
  }, [pipelines, filters])

  const hasActiveFilters =
    filters.search !== '' ||
    filters.status !== 'all' ||
    filters.source !== '' ||
    filters.destination !== '' ||
    filters.tags.length > 0

  const clearFilters = () => {
    setFilters({ search: '', status: 'all', source: '', destination: '', tags: [] })
  }

  const toggleTagFilter = (tag: string) => {
    setFilters((prev) => ({
      ...prev,
      tags: prev.tags.includes(tag)
        ? prev.tags.filter((t) => t !== tag)
        : [...prev.tags, tag],
    }))
  }

  const groupedPipelines = useMemo(() => {
    return groupPipelines(filteredPipelines, groupBy)
  }, [filteredPipelines, groupBy])

  const toggleGroup = (group: string) => {
    setCollapsedGroups((prev) => {
      const next = new Set(prev)
      if (next.has(group)) {
        next.delete(group)
      } else {
        next.add(group)
      }
      return next
    })
  }

  if (isLoading) {
    return <PageLoader />
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-bizon-text">Pipelines</h1>
          <p className="text-bizon-textSecondary mt-1">
            Manage your data pipelines
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Group By Selector */}
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-bizon-muted" />
            <select
              value={groupBy}
              onChange={(e) => {
                setGroupBy(e.target.value as GroupBy)
                setCollapsedGroups(new Set())
              }}
              className="px-3 py-2 bg-bizon-surface border border-bizon-border rounded-lg text-sm text-bizon-text focus:outline-none focus:ring-2 focus:ring-bizon-primary"
            >
              <option value="none">No grouping</option>
              <option value="source">Group by Source</option>
              <option value="destination">Group by Destination</option>
              <option value="status">Group by Status</option>
              <option value="tag">Group by Tag</option>
            </select>
          </div>
          <Link to="/pipelines/new">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Pipeline
            </Button>
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-bizon-muted" />
          <input
            type="text"
            placeholder="Search pipelines..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="pl-9 pr-3 py-1.5 w-48 bg-bizon-surface border border-bizon-border rounded-lg text-sm text-bizon-text placeholder:text-bizon-muted focus:outline-none focus:ring-2 focus:ring-bizon-primary"
          />
        </div>

        <span className="text-bizon-border">|</span>

        {/* Status Filter */}
        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value as StatusFilter })}
          className="px-3 py-1.5 bg-bizon-surface border border-bizon-border rounded-lg text-sm text-bizon-text focus:outline-none focus:ring-2 focus:ring-bizon-primary"
        >
          <option value="all">All Status</option>
          <option value="enabled">Enabled</option>
          <option value="disabled">Disabled</option>
        </select>

        {/* Source Filter */}
        <select
          value={filters.source}
          onChange={(e) => setFilters({ ...filters, source: e.target.value })}
          className="px-3 py-1.5 bg-bizon-surface border border-bizon-border rounded-lg text-sm text-bizon-text focus:outline-none focus:ring-2 focus:ring-bizon-primary"
        >
          <option value="">All Sources</option>
          {sources.map((source) => (
            <option key={source} value={source}>
              {source}
            </option>
          ))}
        </select>

        {/* Destination Filter */}
        <select
          value={filters.destination}
          onChange={(e) => setFilters({ ...filters, destination: e.target.value })}
          className="px-3 py-1.5 bg-bizon-surface border border-bizon-border rounded-lg text-sm text-bizon-text focus:outline-none focus:ring-2 focus:ring-bizon-primary"
        >
          <option value="">All Destinations</option>
          {destinations.map((dest) => (
            <option key={dest} value={dest}>
              {dest}
            </option>
          ))}
        </select>

        {/* Tag Filter */}
        {allTags && allTags.length > 0 && (
          <select
            value={filters.tags.length === 1 ? filters.tags[0] : ''}
            onChange={(e) => {
              const value = e.target.value
              setFilters({ ...filters, tags: value ? [value] : [] })
            }}
            className="px-3 py-1.5 bg-bizon-surface border border-bizon-border rounded-lg text-sm text-bizon-text focus:outline-none focus:ring-2 focus:ring-bizon-primary"
          >
            <option value="">All Tags</option>
            {allTags.map((tag) => (
              <option key={tag} value={tag}>
                {tag}
              </option>
            ))}
          </select>
        )}

        {/* Clear Filters */}
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="text-xs text-bizon-muted hover:text-bizon-text flex items-center gap-1 ml-2"
          >
            <X className="h-3 w-3" />
            Clear filters
          </button>
        )}

        {/* Results count */}
        {hasActiveFilters && (
          <span className="text-xs text-bizon-muted ml-auto">
            {filteredPipelines.length} of {pipelines?.length} pipelines
          </span>
        )}
      </div>

      {pipelines?.length === 0 ? (
        <Card>
          <EmptyState
            title="No pipelines yet"
            description="Create your first pipeline to start moving data"
            action={
              <Link to="/pipelines/new">
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Pipeline
                </Button>
              </Link>
            }
          />
        </Card>
      ) : filteredPipelines.length === 0 ? (
        <Card>
          <EmptyState
            title="No matching pipelines"
            description="No pipelines match the current filters"
            action={
              <Button variant="secondary" onClick={clearFilters}>
                Clear filters
              </Button>
            }
          />
        </Card>
      ) : (
        <div className="space-y-4">
          {Array.from(groupedPipelines.entries()).map(([group, groupPipelines]) => (
            <div key={group}>
              {/* Group Header */}
              {groupBy !== 'none' && (
                <button
                  onClick={() => toggleGroup(group)}
                  className="w-full flex items-center gap-2 mb-2 px-2 py-1 text-left hover:bg-bizon-surface/50 rounded-lg transition-colors"
                >
                  {collapsedGroups.has(group) ? (
                    <ChevronRight className="h-4 w-4 text-bizon-muted" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-bizon-muted" />
                  )}
                  <span className="font-medium text-bizon-text">{group}</span>
                  <span className="text-sm text-bizon-muted">
                    ({groupPipelines.length})
                  </span>
                </button>
              )}

              {/* Group Content */}
              {!collapsedGroups.has(group) && (
                <div className={`space-y-3 ${groupBy !== 'none' ? 'ml-6' : ''}`}>
                  {groupPipelines.map((pipeline) => (
                    <Card key={pipeline.id} className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <Link
                            to={`/pipelines/${pipeline.id}`}
                            className="font-medium text-bizon-text hover:text-bizon-primary"
                          >
                            {pipeline.name}
                          </Link>
                          <StatusChip status={pipeline.enabled ? 'enabled' : 'disabled'} />
                          {pipeline.schedule && (
                            <span className="text-xs text-bizon-muted font-mono">
                              {pipeline.schedule}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="text-xs text-bizon-muted">
                            {format(new Date(pipeline.created_at), 'MMM d, yyyy')}
                          </span>

                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => triggerRun.mutate({ id: pipeline.id })}
                            disabled={triggerRun.isPending}
                          >
                            <Play className="h-4 w-4" />
                          </Button>

                          <div className="relative">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() =>
                                setOpenMenu(openMenu === pipeline.id ? null : pipeline.id)
                              }
                            >
                              <MoreVertical className="h-4 w-4" />
                            </Button>

                            {openMenu === pipeline.id && (
                              <div className="absolute right-0 mt-1 w-48 bg-bizon-surface border border-bizon-border rounded-lg shadow-lg z-10">
                                <button
                                  className="w-full px-4 py-2 text-left text-sm text-bizon-text hover:bg-bizon-bg flex items-center gap-2"
                                  onClick={() => {
                                    duplicatePipeline.mutate(pipeline.id)
                                    setOpenMenu(null)
                                  }}
                                >
                                  <Copy className="h-4 w-4" />
                                  Duplicate
                                </button>
                                <button
                                  className="w-full px-4 py-2 text-left text-sm text-bizon-text hover:bg-bizon-bg flex items-center gap-2"
                                  onClick={() => {
                                    syncOtherStreams.mutate(pipeline.id)
                                    setOpenMenu(null)
                                  }}
                                >
                                  <GitBranch className="h-4 w-4" />
                                  Sync other streams
                                </button>
                                <button
                                  className="w-full px-4 py-2 text-left text-sm text-bizon-danger hover:bg-bizon-bg flex items-center gap-2"
                                  onClick={() => {
                                    if (confirm('Delete this pipeline?')) {
                                      deletePipeline.mutate(pipeline.id)
                                    }
                                    setOpenMenu(null)
                                  }}
                                >
                                  <Trash2 className="h-4 w-4" />
                                  Delete
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="mt-2 flex items-center gap-3">
                        <span className="text-sm text-bizon-muted">
                          <span className="font-mono">{pipeline.config.source.name}</span>
                          <span className="mx-2">→</span>
                          <span className="font-mono">{pipeline.config.destination.name}</span>
                        </span>
                        {pipeline.tags && pipeline.tags.length > 0 && (
                          <div className="flex items-center gap-1">
                            {pipeline.tags.map((tag) => (
                              <TagChip key={tag} tag={tag} size="sm" />
                            ))}
                          </div>
                        )}
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
