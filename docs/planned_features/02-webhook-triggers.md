# Webhook Triggers

**Priority:** P0
**Effort:** Low (~2 hours)
**Status:** Planned

## Overview

Enable pipelines to be triggered via HTTP POST requests, allowing event-driven architectures and CI/CD integration.

## Why This Matters

- **Event-driven pipelines** - Trigger on external events, not just cron
- **CI/CD integration** - Run pipelines as part of deployment workflows
- **Real-time sync** - Trigger immediately when source data changes
- **Flexibility** - Combine with cron for hybrid scheduling

## Use Cases

### 1. CI/CD Pipeline Sync
```yaml
# .github/workflows/deploy.yml
- name: Sync data after deploy
  run: |
    curl -X POST https://bizon.example.com/api/pipelines/$PIPELINE_ID/webhook \
      -H "X-Webhook-Secret: ${{ secrets.BIZON_WEBHOOK_SECRET }}"
```

### 2. Event-Driven from Stripe
```javascript
// Stripe webhook handler
app.post('/stripe-webhook', async (req, res) => {
  if (req.body.type === 'customer.created') {
    await fetch(`${BIZON_URL}/api/pipelines/${PIPELINE_ID}/webhook`, {
      method: 'POST',
      headers: { 'X-Webhook-Secret': WEBHOOK_SECRET }
    });
  }
});
```

### 3. Scheduled + On-Demand
```
Pipeline: stripe-to-bigquery
- Cron: Daily at 2am (full sync)
- Webhook: On new customer (incremental)
```

## API Design

### Trigger Endpoint

```
POST /api/pipelines/{pipeline_id}/webhook
```

**Headers:**
| Header | Required | Description |
|--------|----------|-------------|
| `X-Webhook-Secret` | Yes | Pipeline-specific secret |
| `Content-Type` | No | `application/json` if sending payload |

**Request Body (optional):**
```json
{
  "metadata": {
    "source": "github-actions",
    "commit": "abc123",
    "triggered_by": "deploy"
  }
}
```

**Response:**
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Pipeline run triggered successfully"
}
```

**Status Codes:**
| Code | Description |
|------|-------------|
| 202 | Run created successfully |
| 401 | Invalid or missing webhook secret |
| 404 | Pipeline not found |
| 409 | Pipeline already has a pending/running run |
| 423 | Pipeline is disabled |

### Webhook Secret Management

```
POST   /api/pipelines/{id}/webhook-secret     # Generate new secret
DELETE /api/pipelines/{id}/webhook-secret     # Revoke secret
```

**Generate Response:**
```json
{
  "secret": "whsec_abc123xyz...",
  "created_at": "2024-01-15T10:30:00Z",
  "note": "This secret will only be shown once"
}
```

## Implementation

### Database Changes

Add columns to `pipelines` table:

```python
# models.py
class Pipeline(Base):
    # ... existing fields ...
    webhook_secret_hash: Mapped[str | None] = mapped_column(String(128))
    webhook_enabled: Mapped[bool] = mapped_column(default=False)
```

Migration:
```python
# migrations/versions/xxx_add_webhook_support.py
def upgrade():
    op.add_column('pipelines', sa.Column('webhook_secret_hash', sa.String(128)))
    op.add_column('pipelines', sa.Column('webhook_enabled', sa.Boolean(), default=False))
```

### Route Implementation

```python
# routes/pipelines.py
import secrets
import hashlib

@router.post("/{pipeline_id}/webhook", status_code=202)
async def trigger_webhook(
    pipeline_id: uuid.UUID,
    x_webhook_secret: str = Header(...),
    payload: dict | None = None,
    db: AsyncSession = Depends(get_db),
):
    # Get pipeline
    pipeline = await db.get(Pipeline, pipeline_id)
    if not pipeline:
        raise HTTPException(404, "Pipeline not found")

    # Verify webhook is enabled
    if not pipeline.webhook_enabled or not pipeline.webhook_secret_hash:
        raise HTTPException(401, "Webhook not configured for this pipeline")

    # Verify secret (constant-time comparison)
    provided_hash = hashlib.sha256(x_webhook_secret.encode()).hexdigest()
    if not secrets.compare_digest(provided_hash, pipeline.webhook_secret_hash):
        raise HTTPException(401, "Invalid webhook secret")

    # Check pipeline is enabled
    if not pipeline.enabled:
        raise HTTPException(423, "Pipeline is disabled")

    # Check for existing pending/running run
    existing = await db.execute(
        select(PipelineRun)
        .where(PipelineRun.pipeline_id == pipeline_id)
        .where(PipelineRun.status.in_(["pending", "running"]))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Pipeline already has a pending or running run")

    # Create run
    run = PipelineRun(
        pipeline_id=pipeline_id,
        status="pending",
        triggered_by="webhook",
        metadata=payload.get("metadata") if payload else None,
    )
    db.add(run)
    await db.commit()

    return {"run_id": str(run.id), "status": "pending"}


@router.post("/{pipeline_id}/webhook-secret")
async def generate_webhook_secret(
    pipeline_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    pipeline = await db.get(Pipeline, pipeline_id)
    if not pipeline:
        raise HTTPException(404, "Pipeline not found")

    # Generate secret
    secret = f"whsec_{secrets.token_urlsafe(32)}"
    secret_hash = hashlib.sha256(secret.encode()).hexdigest()

    # Update pipeline
    pipeline.webhook_secret_hash = secret_hash
    pipeline.webhook_enabled = True
    await db.commit()

    return {
        "secret": secret,
        "created_at": datetime.utcnow().isoformat(),
        "note": "This secret will only be shown once. Store it securely.",
    }


@router.delete("/{pipeline_id}/webhook-secret")
async def revoke_webhook_secret(
    pipeline_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    pipeline = await db.get(Pipeline, pipeline_id)
    if not pipeline:
        raise HTTPException(404, "Pipeline not found")

    pipeline.webhook_secret_hash = None
    pipeline.webhook_enabled = False
    await db.commit()

    return {"message": "Webhook secret revoked"}
```

### Schema Updates

```python
# schemas.py
class PipelineResponse(BaseModel):
    # ... existing fields ...
    webhook_enabled: bool = False

class WebhookSecretResponse(BaseModel):
    secret: str
    created_at: datetime
    note: str

class WebhookTriggerResponse(BaseModel):
    run_id: str
    status: str
    message: str = "Pipeline run triggered successfully"
```

## UI Changes

Add webhook configuration to pipeline detail page:

```tsx
// PipelineWebhook.tsx
function PipelineWebhook({ pipeline }) {
  const [secret, setSecret] = useState<string | null>(null);

  const generateSecret = async () => {
    const res = await api.post(`/pipelines/${pipeline.id}/webhook-secret`);
    setSecret(res.data.secret);
  };

  return (
    <div>
      <h3>Webhook Trigger</h3>
      {pipeline.webhook_enabled ? (
        <>
          <p>Webhook URL:</p>
          <code>{`${API_URL}/api/pipelines/${pipeline.id}/webhook`}</code>

          {secret && (
            <Alert>
              <p>Your webhook secret (shown once):</p>
              <code>{secret}</code>
            </Alert>
          )}

          <Button onClick={revokeSecret} variant="danger">
            Revoke Secret
          </Button>
        </>
      ) : (
        <Button onClick={generateSecret}>
          Enable Webhook
        </Button>
      )}
    </div>
  );
}
```

## Security Considerations

1. **Secret storage** - Only store hashed secrets, never plaintext
2. **Constant-time comparison** - Prevent timing attacks
3. **Rate limiting** - Prevent webhook abuse (optional)
4. **IP allowlisting** - Optional restriction to known IPs
5. **Payload validation** - Sanitize any metadata in payload

## Testing

```python
# tests/api/test_webhooks.py
class TestWebhookTrigger:
    async def test_trigger_with_valid_secret(self, client, pipeline_with_webhook):
        response = await client.post(
            f"/api/pipelines/{pipeline_with_webhook.id}/webhook",
            headers={"X-Webhook-Secret": "whsec_test123"},
        )
        assert response.status_code == 202
        assert "run_id" in response.json()

    async def test_trigger_with_invalid_secret(self, client, pipeline_with_webhook):
        response = await client.post(
            f"/api/pipelines/{pipeline_with_webhook.id}/webhook",
            headers={"X-Webhook-Secret": "wrong_secret"},
        )
        assert response.status_code == 401

    async def test_trigger_disabled_pipeline(self, client, disabled_pipeline):
        response = await client.post(
            f"/api/pipelines/{disabled_pipeline.id}/webhook",
            headers={"X-Webhook-Secret": "whsec_test123"},
        )
        assert response.status_code == 423
```

## Documentation Updates

Add to README:
```markdown
## Webhook Triggers

Trigger pipelines via HTTP POST:

```bash
# Generate webhook secret
curl -X POST https://bizon/api/pipelines/{id}/webhook-secret

# Trigger pipeline
curl -X POST https://bizon/api/pipelines/{id}/webhook \
  -H "X-Webhook-Secret: whsec_xxx"
```
```

## Future Enhancements

- **Payload templating** - Pass webhook payload data into pipeline config
- **Retry configuration** - Automatic retries on failure
- **Webhook logs** - Track all incoming webhook calls
- **Multiple secrets** - Allow multiple valid secrets per pipeline
- **Signature verification** - HMAC signatures like Stripe/GitHub webhooks
