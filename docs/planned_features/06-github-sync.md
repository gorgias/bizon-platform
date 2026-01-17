# GitHub Sync

**Priority:** P2
**Effort:** Medium (port from main platform)
**Status:** Planned

## Overview

GitOps workflow for pipeline management. Define pipelines as YAML files in a GitHub repository and sync them automatically via webhooks.

## Why This Matters

- **Version control** - Track pipeline changes over time
- **Code review** - PRs for pipeline changes
- **CI/CD native** - Fits into existing workflows
- **Disaster recovery** - Pipelines are code, easily restored
- **Team collaboration** - Standard git workflow

## User Experience

### 1. Connect Repository

```
Settings > GitHub Sync > Connect Repository
- Enter repository URL (github.com/org/repo)
- Authenticate via GitHub OAuth or PAT
- Select branch to sync (default: main)
- Configure sync directory (default: pipelines/)
```

### 2. Define Pipelines as YAML

```yaml
# pipelines/stripe-to-bigquery.yaml
name: stripe-to-bigquery
schedule: "0 2 * * *"
enabled: true

config:
  source:
    name: stripe
    stream: customers
    authentication:
      type: api_key
      params:
        token: ${STRIPE_API_KEY}  # From secrets

  destination:
    name: bigquery
    config:
      project_id: ${GCP_PROJECT}
      dataset: stripe_raw
      credentials_base64: ${GCP_CREDENTIALS}
```

### 3. Push & Sync

```bash
git add pipelines/stripe-to-bigquery.yaml
git commit -m "Add Stripe pipeline"
git push origin main
# Webhook triggers sync
# Pipeline created/updated in Bizon
```

### 4. Monitor Sync Status

```
Settings > GitHub Sync > History
- Last sync: 2 minutes ago
- Status: Success
- Changes: Created 1 pipeline, Updated 0, Deleted 0
```

## Architecture

```
┌─────────────┐     Webhook      ┌─────────────────────┐
│   GitHub    │────────────────▶│    Bizon API        │
│             │                  │                     │
│  pipelines/ │                  │  ┌───────────────┐  │
│  ├── a.yaml │◀────Pull────────│  │  Sync Service │  │
│  └── b.yaml │                  │  └───────────────┘  │
└─────────────┘                  │         │          │
                                 │         ▼          │
                                 │  ┌───────────────┐  │
                                 │  │   Database    │  │
                                 │  │  (Pipelines)  │  │
                                 │  └───────────────┘  │
                                 └─────────────────────┘
```

## Sync Logic

### Pull (GitHub → Bizon)

1. Receive webhook (push event)
2. Clone/pull repository
3. Parse YAML files in sync directory
4. Compare with existing pipelines:
   - New file → Create pipeline
   - Modified file → Update pipeline
   - Deleted file → Delete or disable pipeline
5. Record sync in history

### Push (Bizon → GitHub) [Optional]

1. User triggers "Export to GitHub"
2. Generate YAML from pipeline configs
3. Commit to repository
4. Push changes

## Data Model

```python
# models.py

class GitHubSyncConfig(Base):
    """GitHub sync configuration."""
    __tablename__ = "github_sync_config"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Repository info
    repo_url: Mapped[str] = mapped_column(String(500))
    branch: Mapped[str] = mapped_column(String(100), default="main")
    sync_directory: Mapped[str] = mapped_column(String(255), default="pipelines")

    # Authentication
    github_token_encrypted: Mapped[str] = mapped_column(Text)  # Encrypted PAT

    # Webhook
    webhook_secret: Mapped[str] = mapped_column(String(100))

    # Settings
    enabled: Mapped[bool] = mapped_column(default=True)
    auto_enable_new: Mapped[bool] = mapped_column(default=False)  # Auto-enable new pipelines
    delete_on_remove: Mapped[bool] = mapped_column(default=False)  # Delete or just disable

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(onupdate=datetime.utcnow)


class GitHubSyncLog(Base):
    """Sync operation history."""
    __tablename__ = "github_sync_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    config_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("github_sync_config.id"))

    # Git info
    commit_sha: Mapped[str] = mapped_column(String(40))
    commit_message: Mapped[str | None] = mapped_column(Text)
    commit_author: Mapped[str | None] = mapped_column(String(255))

    # Sync results
    status: Mapped[str] = mapped_column(String(20))  # success, failed, partial
    created_count: Mapped[int] = mapped_column(default=0)
    updated_count: Mapped[int] = mapped_column(default=0)
    deleted_count: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None] = mapped_column(Text)

    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column()


class GitHubSourceMapping(Base):
    """Mapping between GitHub files and pipelines."""
    __tablename__ = "github_source_mappings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    config_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("github_sync_config.id"))
    pipeline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pipelines.id"))

    # File info
    file_path: Mapped[str] = mapped_column(String(500))  # Relative to repo root
    file_sha: Mapped[str] = mapped_column(String(40))    # Last synced SHA

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(onupdate=datetime.utcnow)
```

## API Endpoints

```
# Configuration
GET    /api/github-sync/config           # Get sync config
POST   /api/github-sync/config           # Create/update sync config
DELETE /api/github-sync/config           # Remove sync config

# Manual operations
POST   /api/github-sync/pull             # Trigger manual pull
POST   /api/github-sync/push             # Trigger push to GitHub

# History
GET    /api/github-sync/history          # Get sync history
GET    /api/github-sync/history/{id}     # Get specific sync details

# Webhook
POST   /api/github-sync/webhook          # GitHub webhook endpoint

# Mappings
GET    /api/github-sync/mappings         # List file-pipeline mappings
```

## Sync Service

```python
# github_sync/service.py
import tempfile
import git
import yaml
from pathlib import Path

class GitHubSyncService:
    def __init__(self, config: GitHubSyncConfig, db: AsyncSession):
        self.config = config
        self.db = db

    async def pull(self, commit_sha: str | None = None) -> GitHubSyncLog:
        """Pull changes from GitHub and sync pipelines."""
        log = GitHubSyncLog(config_id=self.config.id, status="running")
        self.db.add(log)
        await self.db.commit()

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Clone repository
                repo = git.Repo.clone_from(
                    self._get_auth_url(),
                    tmpdir,
                    branch=self.config.branch,
                    depth=1,
                )

                log.commit_sha = repo.head.commit.hexsha
                log.commit_message = repo.head.commit.message
                log.commit_author = str(repo.head.commit.author)

                # Parse YAML files
                sync_dir = Path(tmpdir) / self.config.sync_directory
                if not sync_dir.exists():
                    raise ValueError(f"Sync directory not found: {self.config.sync_directory}")

                # Get current mappings
                existing_mappings = await self._get_existing_mappings()

                # Process each YAML file
                processed_files = set()
                for yaml_file in sync_dir.glob("*.yaml"):
                    file_path = str(yaml_file.relative_to(tmpdir))
                    processed_files.add(file_path)

                    with open(yaml_file) as f:
                        pipeline_def = yaml.safe_load(f)

                    await self._sync_pipeline(file_path, pipeline_def, log)

                # Handle deleted files
                for mapping in existing_mappings:
                    if mapping.file_path not in processed_files:
                        await self._handle_deleted(mapping, log)

                log.status = "success"

        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)

        finally:
            log.finished_at = datetime.utcnow()
            await self.db.commit()

        return log

    async def _sync_pipeline(self, file_path: str, definition: dict, log: GitHubSyncLog):
        """Create or update pipeline from definition."""
        # Check if mapping exists
        mapping = await self.db.execute(
            select(GitHubSourceMapping)
            .where(GitHubSourceMapping.config_id == self.config.id)
            .where(GitHubSourceMapping.file_path == file_path)
        )
        mapping = mapping.scalar_one_or_none()

        # Extract pipeline data
        pipeline_data = {
            "name": definition["name"],
            "config": definition["config"],
            "schedule": definition.get("schedule"),
            "enabled": definition.get("enabled", self.config.auto_enable_new),
        }

        # Resolve secrets/variables
        pipeline_data["config"] = self._resolve_variables(pipeline_data["config"])

        if mapping:
            # Update existing pipeline
            pipeline = await self.db.get(Pipeline, mapping.pipeline_id)
            for key, value in pipeline_data.items():
                setattr(pipeline, key, value)
            log.updated_count += 1
        else:
            # Create new pipeline
            pipeline = Pipeline(**pipeline_data)
            self.db.add(pipeline)
            await self.db.flush()

            # Create mapping
            mapping = GitHubSourceMapping(
                config_id=self.config.id,
                pipeline_id=pipeline.id,
                file_path=file_path,
                file_sha=log.commit_sha,
            )
            self.db.add(mapping)
            log.created_count += 1

    def _resolve_variables(self, config: dict) -> dict:
        """Resolve ${VAR_NAME} placeholders from environment."""
        import os
        import re

        def replace_vars(obj):
            if isinstance(obj, str):
                # Replace ${VAR_NAME} with env value
                pattern = r'\$\{([A-Z_][A-Z0-9_]*)\}'
                return re.sub(pattern, lambda m: os.environ.get(m.group(1), m.group(0)), obj)
            elif isinstance(obj, dict):
                return {k: replace_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_vars(item) for item in obj]
            return obj

        return replace_vars(config)
```

## Webhook Handler

```python
# routes/github_sync.py
import hmac
import hashlib

@router.post("/github-sync/webhook")
async def handle_webhook(
    request: Request,
    x_hub_signature_256: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub webhook events."""
    body = await request.body()

    # Verify signature
    config = await db.execute(select(GitHubSyncConfig).where(GitHubSyncConfig.enabled == True))
    config = config.scalar_one_or_none()

    if not config:
        raise HTTPException(404, "GitHub sync not configured")

    expected_sig = "sha256=" + hmac.new(
        config.webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(x_hub_signature_256, expected_sig):
        raise HTTPException(401, "Invalid signature")

    # Parse event
    event = await request.json()
    event_type = request.headers.get("X-GitHub-Event")

    if event_type == "push":
        # Only sync if changes are in sync directory
        ref = event.get("ref", "")
        if ref != f"refs/heads/{config.branch}":
            return {"message": "Ignored (different branch)"}

        # Check if any changed files are in sync directory
        commits = event.get("commits", [])
        relevant_changes = False
        for commit in commits:
            for file in commit.get("added", []) + commit.get("modified", []) + commit.get("removed", []):
                if file.startswith(config.sync_directory):
                    relevant_changes = True
                    break

        if not relevant_changes:
            return {"message": "Ignored (no changes in sync directory)"}

        # Trigger sync
        service = GitHubSyncService(config, db)
        log = await service.pull(commit_sha=event["after"])

        return {
            "message": "Sync completed",
            "log_id": str(log.id),
            "status": log.status,
            "created": log.created_count,
            "updated": log.updated_count,
            "deleted": log.deleted_count,
        }

    return {"message": f"Ignored event type: {event_type}"}
```

## Security Considerations

1. **Token storage** - GitHub tokens encrypted at rest
2. **Webhook verification** - HMAC signature validation
3. **Secret resolution** - Variables from environment, not stored in repo
4. **Repository access** - Minimal permissions (read-only for sync)
5. **Audit trail** - All sync operations logged

## UI Components

### Sync Configuration

```tsx
function GitHubSyncSettings() {
  const { data: config } = useQuery('github-sync-config', fetchSyncConfig);

  return (
    <Card>
      <h2>GitHub Sync</h2>

      {config ? (
        <>
          <div className="mb-4">
            <p>Repository: {config.repo_url}</p>
            <p>Branch: {config.branch}</p>
            <p>Directory: {config.sync_directory}</p>
            <StatusChip status={config.enabled ? 'active' : 'disabled'} />
          </div>

          <Button onClick={triggerManualSync}>Sync Now</Button>
          <Button variant="danger" onClick={disconnectRepo}>Disconnect</Button>
        </>
      ) : (
        <GitHubConnectForm onConnect={refetch} />
      )}
    </Card>
  );
}
```

### Sync History

```tsx
function SyncHistory() {
  const { data: history } = useQuery('github-sync-history', fetchSyncHistory);

  return (
    <Table>
      <thead>
        <tr>
          <th>Time</th>
          <th>Commit</th>
          <th>Status</th>
          <th>Changes</th>
        </tr>
      </thead>
      <tbody>
        {history?.map(log => (
          <tr key={log.id}>
            <td>{formatDate(log.started_at)}</td>
            <td>
              <code>{log.commit_sha?.slice(0, 7)}</code>
              <span>{log.commit_message?.slice(0, 50)}</span>
            </td>
            <td><StatusChip status={log.status} /></td>
            <td>+{log.created_count} ~{log.updated_count} -{log.deleted_count}</td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
```

## Future Enhancements

- **Branch environments** - Sync different branches to different environments
- **PR previews** - Test pipeline changes in PRs before merging
- **Conflict resolution** - Handle manual edits vs. synced pipelines
- **Multi-repo** - Sync from multiple repositories
- **GitLab/Bitbucket** - Support other git providers
