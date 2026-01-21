# Phase 1e: Secrets Management

**Effort:** Medium
**Dependencies:** 01d-testing-sandbox
**PR Size:** ~1 week

## Goal

Handle API credentials securely so that:
1. LLM never sees actual secret values
2. Secrets are encrypted at rest
3. Secrets are injected at runtime only
4. Audit trail for secret access
5. Enterprise customers can use their own vaults

## The Problem

Many companies have strict security policies:

```
❌ "Our API keys cannot be sent to any third-party LLM"
❌ "Secrets must be stored in our Vault, not your database"
❌ "We need audit logs of who accessed which secret"
```

If we can't satisfy these, we lose enterprise deals.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  User provides credentials                                   │
│                                                             │
│  Option A: Bizon-managed (encrypted in our DB)              │
│  Option B: Reference only (stored in customer's Vault)      │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Secret Store Interface                                      │
│                                                             │
│  get_secret(tenant_id, secret_name) → value                 │
│  set_secret(tenant_id, secret_name, value)                  │
│  delete_secret(tenant_id, secret_name)                      │
│  list_secrets(tenant_id) → [name, name, ...]  (no values!)  │
└─────────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  Encrypted  │   │  HashiCorp  │   │  AWS        │
│  Postgres   │   │  Vault      │   │  Secrets    │
│  (default)  │   │             │   │  Manager    │
└─────────────┘   └─────────────┘   └─────────────┘
```

## Key Principle: LLM Never Sees Secrets

```
┌─────────────────────────────────────────────────────────────┐
│  What LLM Sees                                              │
│                                                             │
│  Config:                                                    │
│    api_key: ${SECRETS.stripe_api_key}                       │
│    base_url: https://api.stripe.com/v1                      │
│                                                             │
│  Generated code:                                            │
│    def get_authenticator(self):                             │
│        return BearerAuth(self.config.api_key)               │
│                                                             │
│  Test result:                                               │
│    ✓ Connection successful                                  │
│    ✓ Fetched 3 records                                      │
│    Error: "401 Unauthorized" (if failed)                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  What LLM NEVER Sees                                        │
│                                                             │
│  ✗ sk_live_4eC39HqLyjWDarjtT1zdp7dc                         │
│  ✗ Any actual secret value                                  │
│  ✗ Secrets in error messages                                │
└─────────────────────────────────────────────────────────────┘
```

## Data Model

```python
class SecretReference(BaseModel):
    """Reference to a secret, not the secret itself."""
    name: str  # e.g., "stripe_api_key"
    source: Literal["bizon", "vault", "aws", "env"]
    path: str | None  # For vault: "secret/data/stripe"
    version: int | None  # For versioned stores

class SourceConfig(BaseModel):
    """Config that can reference secrets."""
    name: str
    stream: str
    # Secrets are references, not values
    api_key: str | SecretReference
    base_url: str

# In code, secrets look like:
# ${SECRETS.stripe_api_key}
# At runtime, resolved to actual value
```

## Secret Collection Flow

```
User: "Create a connector for Stripe"

Agent: I'll need your Stripe API key to test the connector.

       How would you like to provide it?

       1. Enter now (stored encrypted in Bizon)
       2. Reference from HashiCorp Vault
       3. Reference from AWS Secrets Manager
       4. I'll set it as an environment variable

User: "Enter now"

Agent: [Shows secure input form - NOT in chat]

       ┌──────────────────────────────────────────────┐
       │  Stripe API Key                              │
       │  [••••••••••••••••••••••••••••••••]         │
       │                                              │
       │  This secret will be encrypted and stored    │
       │  securely. It will never be sent to AI.     │
       │                                              │
       │  [Save Secret]                               │
       └──────────────────────────────────────────────┘

       ✓ Secret saved as "stripe_api_key"

Agent: Testing connection...
       ✓ Connected successfully!
```

## Implementation

### Secret Store Interface

```python
from abc import ABC, abstractmethod

class SecretStore(ABC):
    """Interface for secret storage backends."""

    @abstractmethod
    async def get(self, tenant_id: str, name: str) -> str:
        """Get secret value. Raises if not found."""
        pass

    @abstractmethod
    async def set(self, tenant_id: str, name: str, value: str) -> None:
        """Store secret value."""
        pass

    @abstractmethod
    async def delete(self, tenant_id: str, name: str) -> None:
        """Delete secret."""
        pass

    @abstractmethod
    async def list(self, tenant_id: str) -> list[str]:
        """List secret names (not values!)."""
        pass
```

### Encrypted Postgres Store (Default)

```python
from cryptography.fernet import Fernet

class PostgresSecretStore(SecretStore):
    def __init__(self, encryption_key: str):
        self.fernet = Fernet(encryption_key.encode())

    async def get(self, tenant_id: str, name: str) -> str:
        row = await db.fetch_one(
            "SELECT encrypted_value FROM secrets WHERE tenant_id = $1 AND name = $2",
            tenant_id, name
        )
        if not row:
            raise SecretNotFoundError(name)

        # Log access
        await self._audit_log(tenant_id, name, "read")

        return self.fernet.decrypt(row.encrypted_value).decode()

    async def set(self, tenant_id: str, name: str, value: str) -> None:
        encrypted = self.fernet.encrypt(value.encode())
        await db.execute(
            """
            INSERT INTO secrets (tenant_id, name, encrypted_value, created_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (tenant_id, name)
            DO UPDATE SET encrypted_value = $3, updated_at = NOW()
            """,
            tenant_id, name, encrypted
        )
        await self._audit_log(tenant_id, name, "write")

    async def _audit_log(self, tenant_id: str, name: str, action: str):
        await db.execute(
            "INSERT INTO secret_audit_log (tenant_id, secret_name, action, timestamp) VALUES ($1, $2, $3, NOW())",
            tenant_id, name, action
        )
```

### HashiCorp Vault Store

```python
import hvac

class VaultSecretStore(SecretStore):
    def __init__(self, vault_url: str, vault_token: str):
        self.client = hvac.Client(url=vault_url, token=vault_token)

    async def get(self, tenant_id: str, name: str) -> str:
        # Path: secret/data/{tenant_id}/{name}
        path = f"secret/data/{tenant_id}/{name}"
        result = self.client.secrets.kv.v2.read_secret_version(path=path)
        return result["data"]["data"]["value"]

    async def set(self, tenant_id: str, name: str, value: str) -> None:
        path = f"secret/data/{tenant_id}/{name}"
        self.client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret={"value": value}
        )
```

### AWS Secrets Manager Store

```python
import boto3

class AWSSecretsStore(SecretStore):
    def __init__(self, region: str):
        self.client = boto3.client("secretsmanager", region_name=region)

    async def get(self, tenant_id: str, name: str) -> str:
        secret_id = f"bizon/{tenant_id}/{name}"
        response = self.client.get_secret_value(SecretId=secret_id)
        return response["SecretString"]

    async def set(self, tenant_id: str, name: str, value: str) -> None:
        secret_id = f"bizon/{tenant_id}/{name}"
        try:
            self.client.create_secret(
                Name=secret_id,
                SecretString=value
            )
        except self.client.exceptions.ResourceExistsException:
            self.client.update_secret(
                SecretId=secret_id,
                SecretString=value
            )
```

### Secret Resolution at Runtime

```python
class SecretResolver:
    """Resolves secret references to actual values at runtime."""

    def __init__(self, store: SecretStore, tenant_id: str):
        self.store = store
        self.tenant_id = tenant_id

    async def resolve_config(self, config: dict) -> dict:
        """
        Replace ${SECRETS.xxx} references with actual values.
        """
        resolved = {}
        for key, value in config.items():
            if isinstance(value, str) and value.startswith("${SECRETS."):
                secret_name = value[10:-1]  # Extract name from ${SECRETS.xxx}
                resolved[key] = await self.store.get(self.tenant_id, secret_name)
            elif isinstance(value, dict):
                resolved[key] = await self.resolve_config(value)
            else:
                resolved[key] = value
        return resolved
```

### Integration with Testing Sandbox

```python
async def test_source_with_secrets(
    code: str,
    config: dict,
    secret_refs: list[str],
    tenant_id: str,
    store: SecretStore
) -> TestResult:
    """
    Test source code with secrets resolved at the last moment.
    Secrets are passed to sandbox via env vars, never in code.
    """
    # Resolve secrets
    secrets = {}
    for ref in secret_refs:
        secrets[ref] = await store.get(tenant_id, ref)

    # Run test (sandbox sanitizes output)
    return await test_source(
        code=code,
        config=config,
        secrets=secrets,  # Injected as env vars
        stream=config["stream"]
    )
```

## UI: Secure Secret Input

Secrets are NEVER entered in chat. Always use dedicated secure form:

```typescript
// SecretInputModal.tsx
export function SecretInputModal({ secretName, onSave, onCancel }) {
  const [value, setValue] = useState("");

  const handleSave = async () => {
    await api.saveSecret(secretName, value);
    // Clear from memory immediately
    setValue("");
    onSave();
  };

  return (
    <Modal>
      <h3>Enter Secret: {secretName}</h3>
      <input
        type="password"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        autoComplete="off"
      />
      <p className="text-muted">
        This secret is encrypted and stored securely.
        It is never sent to AI models.
      </p>
      <Button onClick={handleSave}>Save Secret</Button>
      <Button variant="ghost" onClick={onCancel}>Cancel</Button>
    </Modal>
  );
}
```

## Configuration

```python
# settings.py
class SecretsConfig(BaseModel):
    store: Literal["postgres", "vault", "aws"] = "postgres"

    # Postgres (default)
    encryption_key: str  # Must be 32-byte Fernet key

    # HashiCorp Vault
    vault_url: str | None = None
    vault_token: str | None = None

    # AWS Secrets Manager
    aws_region: str | None = None
```

## Database Schema

```sql
-- Secrets table (for postgres store)
CREATE TABLE secrets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    encrypted_value BYTEA NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(tenant_id, name)
);

-- Audit log
CREATE TABLE secret_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    secret_name VARCHAR(255) NOT NULL,
    action VARCHAR(50) NOT NULL,  -- read, write, delete
    actor_id UUID,  -- user who accessed
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_secret_audit_tenant ON secret_audit_log(tenant_id, timestamp);
```

## Tasks

- [ ] Define SecretStore interface
- [ ] Implement PostgresSecretStore with encryption
- [ ] Add secrets table migration
- [ ] Add audit log table migration
- [ ] Implement SecretResolver
- [ ] Create secret input API endpoint
- [ ] Create SecretInputModal component
- [ ] Integrate with testing sandbox
- [ ] Implement VaultSecretStore (optional)
- [ ] Implement AWSSecretsStore (optional)

## Testing

- [ ] Test secret encryption/decryption roundtrip
- [ ] Test audit logging
- [ ] Test secret resolution in configs
- [ ] Verify secrets never appear in logs
- [ ] Verify secrets never sent to LLM
- [ ] Test with bad encryption key (should fail gracefully)

## Success Criteria

- [ ] LLM never sees secret values
- [ ] Secrets encrypted at rest
- [ ] Secrets sanitized from all output
- [ ] Audit trail for all access
- [ ] Enterprise customers can use Vault
- [ ] UI provides secure input method
