# Observability Dashboard

**Priority:** P1
**Effort:** Medium
**Status:** Planned

## Overview

Production-grade monitoring and alerting for pipeline health. Track run history, success rates, data volumes, and get notified when things go wrong.

## Why This Matters

- **Production readiness** - Can't run in prod without monitoring
- **Debugging** - Quickly identify and diagnose failures
- **Capacity planning** - Understand data volumes and trends
- **SLAs** - Track and report on pipeline reliability

## Features

### 1. Dashboard Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Pipeline Health                          │
├─────────────────────────────────────────────────────────────┤
│  Active Pipelines: 12    Runs Today: 47    Success: 95.7%  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Run History (Last 7 Days)                           │  │
│  │  ████████████████████░░██████████████████████████    │  │
│  │  Mon  Tue  Wed  Thu  Fri  Sat  Sun                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Recent Failures:                                           │
│  • stripe-to-bigquery - 2h ago - "Authentication failed"   │
│  • hubspot-sync - 5h ago - "Rate limit exceeded"           │
└─────────────────────────────────────────────────────────────┘
```

### 2. Pipeline Metrics

Per-pipeline statistics:
- Total runs
- Success/failure rate
- Average duration
- Records processed
- Data volume (bytes)
- Last run status
- Next scheduled run

### 3. Run History

Filterable run history:
- By pipeline
- By status (success/failed/cancelled)
- By trigger type (schedule/manual/webhook)
- By date range

### 4. Alerting

Notify on:
- Pipeline failure
- Pipeline stuck (running too long)
- Consecutive failures
- No data returned
- Schedule missed

Channels:
- Slack
- Email
- Webhook (custom integrations)
- PagerDuty (future)

## Data Model

### New Tables

```python
# models.py

class PipelineMetrics(Base):
    """Aggregated metrics per pipeline."""
    __tablename__ = "pipeline_metrics"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    pipeline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pipelines.id"))
    date: Mapped[date] = mapped_column()  # Aggregation date

    # Run counts
    total_runs: Mapped[int] = mapped_column(default=0)
    successful_runs: Mapped[int] = mapped_column(default=0)
    failed_runs: Mapped[int] = mapped_column(default=0)

    # Duration stats (seconds)
    total_duration: Mapped[int] = mapped_column(default=0)
    min_duration: Mapped[int | None] = mapped_column()
    max_duration: Mapped[int | None] = mapped_column()

    # Data stats
    total_records: Mapped[int] = mapped_column(default=0)
    total_bytes: Mapped[int] = mapped_column(default=0)

    __table_args__ = (
        UniqueConstraint("pipeline_id", "date"),
    )


class AlertConfig(Base):
    """Alert configuration."""
    __tablename__ = "alert_configs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(default=True)

    # What to alert on
    alert_on_failure: Mapped[bool] = mapped_column(default=True)
    alert_on_consecutive_failures: Mapped[int | None] = mapped_column()  # Alert after N failures
    alert_on_duration_exceeded: Mapped[int | None] = mapped_column()  # Seconds
    alert_on_no_data: Mapped[bool] = mapped_column(default=False)

    # Where to send
    channel_type: Mapped[str] = mapped_column(String(50))  # slack, email, webhook
    channel_config: Mapped[dict] = mapped_column(EncryptedJSON)  # webhook_url, email, etc.

    # Scope
    pipeline_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pipelines.id"))  # Null = all pipelines

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class AlertHistory(Base):
    """Sent alert history."""
    __tablename__ = "alert_history"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    alert_config_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("alert_configs.id"))
    pipeline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pipelines.id"))
    run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pipeline_runs.id"))

    alert_type: Mapped[str] = mapped_column(String(50))  # failure, duration, no_data
    message: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    delivery_status: Mapped[str] = mapped_column(String(20))  # sent, failed
```

### Extend PipelineRun

```python
class PipelineRun(Base):
    # ... existing fields ...

    # Add metrics
    records_processed: Mapped[int | None] = mapped_column()
    bytes_processed: Mapped[int | None] = mapped_column()
```

## API Endpoints

### Dashboard Stats

```
GET /api/stats/dashboard
```

Response:
```json
{
  "active_pipelines": 12,
  "runs_today": 47,
  "success_rate_today": 0.957,
  "runs_this_week": 312,
  "success_rate_week": 0.962,
  "recent_failures": [
    {
      "pipeline_id": "...",
      "pipeline_name": "stripe-to-bigquery",
      "run_id": "...",
      "error": "Authentication failed",
      "failed_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Pipeline Metrics

```
GET /api/pipelines/{id}/metrics?days=30
```

Response:
```json
{
  "pipeline_id": "...",
  "pipeline_name": "stripe-to-bigquery",
  "period": {
    "start": "2023-12-16",
    "end": "2024-01-15"
  },
  "summary": {
    "total_runs": 30,
    "successful_runs": 28,
    "failed_runs": 2,
    "success_rate": 0.933,
    "avg_duration_seconds": 145,
    "total_records": 15420,
    "total_bytes": 2457600
  },
  "daily": [
    {
      "date": "2024-01-15",
      "runs": 1,
      "success": 1,
      "failed": 0,
      "duration": 142,
      "records": 512
    }
  ]
}
```

### Run History

```
GET /api/runs?pipeline_id=xxx&status=failed&from=2024-01-01&limit=50
```

### Alerts

```
GET    /api/alerts                    # List alert configs
POST   /api/alerts                    # Create alert config
GET    /api/alerts/{id}               # Get alert config
PUT    /api/alerts/{id}               # Update alert config
DELETE /api/alerts/{id}               # Delete alert config
GET    /api/alerts/{id}/history       # Get alert history
POST   /api/alerts/{id}/test          # Send test alert
```

## Alert Channels

### Slack

```python
async def send_slack_alert(config: dict, message: str, pipeline: Pipeline, run: PipelineRun):
    webhook_url = config["webhook_url"]

    payload = {
        "text": f"Pipeline Alert: {pipeline.name}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Pipeline Failed*\n{message}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Pipeline:*\n{pipeline.name}"},
                    {"type": "mrkdwn", "text": f"*Status:*\n{run.status}"},
                    {"type": "mrkdwn", "text": f"*Error:*\n{run.error or 'N/A'}"},
                    {"type": "mrkdwn", "text": f"*Time:*\n{run.finished_at}"},
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Logs"},
                        "url": f"{FRONTEND_URL}/pipelines/{pipeline.id}/runs/{run.id}"
                    }
                ]
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=payload)
```

### Email

```python
async def send_email_alert(config: dict, message: str, pipeline: Pipeline, run: PipelineRun):
    # Use configured SMTP or email service
    await send_email(
        to=config["email"],
        subject=f"[Bizon] Pipeline Failed: {pipeline.name}",
        body=f"""
Pipeline: {pipeline.name}
Status: {run.status}
Error: {run.error}
Time: {run.finished_at}

View logs: {FRONTEND_URL}/pipelines/{pipeline.id}/runs/{run.id}
        """
    )
```

### Webhook

```python
async def send_webhook_alert(config: dict, message: str, pipeline: Pipeline, run: PipelineRun):
    payload = {
        "event": "pipeline.failed",
        "pipeline": {
            "id": str(pipeline.id),
            "name": pipeline.name,
        },
        "run": {
            "id": str(run.id),
            "status": run.status,
            "error": run.error,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        },
        "message": message,
    }

    async with httpx.AsyncClient() as client:
        await client.post(
            config["url"],
            json=payload,
            headers={"X-Bizon-Signature": sign_payload(payload, config.get("secret"))}
        )
```

## UI Components

### Dashboard Page

```tsx
function DashboardPage() {
  const { data: stats } = useQuery('dashboard-stats', fetchDashboardStats);

  return (
    <div>
      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard title="Active Pipelines" value={stats?.active_pipelines} />
        <StatCard title="Runs Today" value={stats?.runs_today} />
        <StatCard title="Success Rate" value={`${(stats?.success_rate_today * 100).toFixed(1)}%`} />
        <StatCard title="Failures" value={stats?.runs_today - Math.round(stats?.runs_today * stats?.success_rate_today)} variant="danger" />
      </div>

      {/* Run history chart */}
      <Card className="mb-8">
        <h3>Run History (Last 7 Days)</h3>
        <RunHistoryChart data={stats?.daily_runs} />
      </Card>

      {/* Recent failures */}
      <Card>
        <h3>Recent Failures</h3>
        <FailureList failures={stats?.recent_failures} />
      </Card>
    </div>
  );
}
```

### Pipeline Metrics View

```tsx
function PipelineMetrics({ pipelineId }) {
  const { data: metrics } = useQuery(
    ['pipeline-metrics', pipelineId],
    () => fetchPipelineMetrics(pipelineId)
  );

  return (
    <div>
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard title="Total Runs" value={metrics?.summary.total_runs} />
        <StatCard title="Success Rate" value={`${(metrics?.summary.success_rate * 100).toFixed(1)}%`} />
        <StatCard title="Avg Duration" value={formatDuration(metrics?.summary.avg_duration_seconds)} />
        <StatCard title="Records Processed" value={formatNumber(metrics?.summary.total_records)} />
      </div>

      <Card>
        <h3>Daily Metrics</h3>
        <MetricsChart data={metrics?.daily} />
      </Card>
    </div>
  );
}
```

## Background Jobs

### Metrics Aggregation

Run hourly to aggregate run metrics:

```python
# scheduler/jobs.py
async def aggregate_metrics():
    """Aggregate pipeline run metrics for the previous day."""
    yesterday = date.today() - timedelta(days=1)

    async with get_db_session() as db:
        # Get all runs from yesterday
        runs = await db.execute(
            select(PipelineRun)
            .where(func.date(PipelineRun.created_at) == yesterday)
        )

        # Group by pipeline
        pipeline_runs = defaultdict(list)
        for run in runs.scalars():
            pipeline_runs[run.pipeline_id].append(run)

        # Create/update metrics
        for pipeline_id, runs in pipeline_runs.items():
            metrics = PipelineMetrics(
                pipeline_id=pipeline_id,
                date=yesterday,
                total_runs=len(runs),
                successful_runs=sum(1 for r in runs if r.status == "success"),
                failed_runs=sum(1 for r in runs if r.status == "failed"),
                total_duration=sum((r.finished_at - r.started_at).seconds for r in runs if r.finished_at),
                total_records=sum(r.records_processed or 0 for r in runs),
                total_bytes=sum(r.bytes_processed or 0 for r in runs),
            )
            await db.merge(metrics)

        await db.commit()
```

### Alert Checker

Run after each pipeline run:

```python
async def check_alerts(run: PipelineRun):
    """Check if any alerts should be triggered for this run."""
    async with get_db_session() as db:
        # Get applicable alert configs
        configs = await db.execute(
            select(AlertConfig)
            .where(AlertConfig.enabled == True)
            .where(
                (AlertConfig.pipeline_id == run.pipeline_id) |
                (AlertConfig.pipeline_id == None)
            )
        )

        pipeline = await db.get(Pipeline, run.pipeline_id)

        for config in configs.scalars():
            should_alert = False
            message = ""

            # Check failure
            if config.alert_on_failure and run.status == "failed":
                should_alert = True
                message = f"Pipeline failed: {run.error}"

            # Check consecutive failures
            if config.alert_on_consecutive_failures:
                recent_runs = await get_recent_runs(db, run.pipeline_id, config.alert_on_consecutive_failures)
                if all(r.status == "failed" for r in recent_runs):
                    should_alert = True
                    message = f"Pipeline has failed {len(recent_runs)} consecutive times"

            # Check duration exceeded
            if config.alert_on_duration_exceeded and run.finished_at and run.started_at:
                duration = (run.finished_at - run.started_at).seconds
                if duration > config.alert_on_duration_exceeded:
                    should_alert = True
                    message = f"Pipeline took {duration}s (threshold: {config.alert_on_duration_exceeded}s)"

            if should_alert:
                await send_alert(config, message, pipeline, run)
```

## Future Enhancements

- **Custom metrics** - User-defined metrics from transform code
- **Anomaly detection** - Alert on unusual patterns
- **SLA tracking** - Define and track SLAs
- **Cost tracking** - Estimate cloud costs per pipeline
- **Grafana integration** - Export metrics to Grafana
- **Log aggregation** - Centralized log search
