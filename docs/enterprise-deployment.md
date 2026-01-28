# Enterprise Multi-Instance Deployment

This guide explains how to deploy multiple isolated Bizon instances for enterprise customers using a single-tenant architecture.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│              Single PostgreSQL Cluster                       │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐               │
│  │ db_acme   │  │ db_corp   │  │ db_xyz    │  ...          │
│  └───────────┘  └───────────┘  └───────────┘               │
└─────────────────────────────────────────────────────────────┘
        │                │                │
        ▼                ▼                ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ namespace:    │ │ namespace:    │ │ namespace:    │
│   acme        │ │   corp        │ │   xyz         │
│ ┌───────────┐ │ │ ┌───────────┐ │ │ ┌───────────┐ │
│ │ API       │ │ │ │ API       │ │ │ │ API       │ │
│ │ Worker    │ │ │ │ Worker    │ │ │ │ Worker    │ │
│ │ UI        │ │ │ │ UI        │ │ │ │ UI        │ │
│ └───────────┘ │ │ └───────────┘ │ │ └───────────┘ │
└───────────────┘ └───────────────┘ └───────────────┘
        │                │                │
        ▼                ▼                ▼
  acme.bizon.cloud  corp.bizon.cloud  xyz.bizon.cloud
```

**Key benefits:**
- **Data isolation**: Each customer has their own database
- **Resource isolation**: Kubernetes namespaces isolate workloads
- **Independent upgrades**: Roll out updates per customer
- **Single codebase**: Same application deployed N times
- **Single Postgres**: One cluster to monitor and maintain

## Prerequisites

- Kubernetes cluster (GKE, EKS, AKS, or self-hosted)
- Managed PostgreSQL (Cloud SQL, RDS, or similar)
- Helm 3.x
- DNS configured with wildcard or per-customer subdomains

## Provisioning a New Customer

### Step 1: Create the Database

Connect to your PostgreSQL cluster and create a new database:

```sql
-- Create database for customer
CREATE DATABASE bizon_acme;

-- Optionally create a dedicated user
CREATE USER bizon_acme WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE bizon_acme TO bizon_acme;
```

### Step 2: Deploy with Helm

```bash
# Create namespace
kubectl create namespace acme

# Deploy Bizon from GHCR
helm install bizon oci://ghcr.io/bizon-data/charts/bizon-platform-lite \
  --namespace acme \
  --set postgresql.enabled=false \
  --set externalDatabase.host="postgres-host" \
  --set externalDatabase.database="bizon_acme" \
  --set externalDatabase.username="bizon_acme" \
  --set externalDatabase.password="password" \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host="acme.bizon.cloud" \
  --set security.encryptionKey="customer-specific-encryption-key" \
  --set security.adminPassword="customer-specific-password" \
  --set config.instanceName="Acme Bizon"
```

Alternatively, use a local chart:

```bash
helm install bizon ./helm/bizon-platform-lite \
  --namespace acme \
  -f values-acme.yaml
```

### Step 3: Run Migrations

```bash
kubectl exec -n acme deployment/bizon-api -- alembic upgrade head
```

### Step 4: Verify Deployment

```bash
# Check pods are running
kubectl get pods -n acme

# Test the API
curl -u admin:password https://acme.bizon.cloud/api/health
```

## Terraform/Pulumi Automation

For automated provisioning, use Infrastructure as Code:

### Terraform Example

```hcl
variable "tenant" {
  description = "Customer tenant identifier"
  type        = string
}

# Create database
resource "postgresql_database" "tenant" {
  name = "bizon_${var.tenant}"
}

# Create Kubernetes namespace
resource "kubernetes_namespace" "tenant" {
  metadata {
    name = var.tenant
  }
}

# Deploy Bizon via Helm from GHCR
resource "helm_release" "bizon" {
  name       = "bizon"
  namespace  = kubernetes_namespace.tenant.metadata[0].name
  repository = "oci://ghcr.io/bizon-data/charts"
  chart      = "bizon-platform-lite"

  set {
    name  = "postgresql.enabled"
    value = "false"
  }

  set {
    name  = "externalDatabase.host"
    value = var.postgres_host
  }

  set {
    name  = "externalDatabase.database"
    value = postgresql_database.tenant.name
  }

  set {
    name  = "ingress.enabled"
    value = "true"
  }

  set {
    name  = "ingress.hosts[0].host"
    value = "${var.tenant}.bizon.cloud"
  }

  set_sensitive {
    name  = "security.encryptionKey"
    value = random_password.encryption_key.result
  }

  set_sensitive {
    name  = "security.adminPassword"
    value = random_password.admin_password.result
  }
}

resource "random_password" "encryption_key" {
  length  = 44
  special = false
}

resource "random_password" "admin_password" {
  length  = 32
  special = true
}
```

### Provisioning a Customer

```bash
terraform apply -var="tenant=acme"
```

## Configuration Reference

### Per-Instance Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/db` |
| `ENCRYPTION_KEY` | Fernet key for config encryption | Generate with `make key` |
| `ADMIN_PASSWORD` | Basic auth password | Strong random password |
| `INSTANCE_NAME` | Display name in UI | "Acme Corp" |
| `INSTANCE_DESCRIPTION` | Description shown in API docs | "Acme's data platform" |
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins | `["https://acme.bizon.cloud"]` |

### Shared Configuration

These typically stay the same across all instances:

| Variable | Description | Recommendation |
|----------|-------------|----------------|
| `STORAGE_LOCAL_PATH` | Pipeline output storage | Use PVC per namespace |
| `CUSTOM_SOURCES_DIR` | Custom source code | Mount via ConfigMap/PVC |
| `EXECUTION_BACKEND` | Pipeline execution method | `subprocess` or `docker` |

## Monitoring

### Single Postgres Monitoring

Monitor the Postgres cluster as one unit:

```sql
-- Per-database statistics
SELECT
  datname,
  numbackends AS active_connections,
  xact_commit AS transactions,
  blks_hit AS cache_hits,
  blks_read AS disk_reads,
  pg_database_size(datname) AS size_bytes
FROM pg_stat_database
WHERE datname LIKE 'bizon_%';
```

### Kubernetes Monitoring

Standard Kubernetes monitoring applies:
- Prometheus/Grafana for metrics
- Per-namespace resource quotas
- Pod resource limits

### Suggested Alerts

- Database connection pool exhaustion
- High CPU/memory per namespace
- Failed pipeline runs (per customer)
- API error rates

## Backup and Recovery

### Database Backups

Use your managed Postgres backup features, or:

```bash
# Backup specific customer
pg_dump -h postgres-host -U postgres bizon_acme > backup_acme.sql

# Restore
psql -h postgres-host -U postgres bizon_acme < backup_acme.sql
```

### Customer Data Migration

To move a customer to a different cluster:

1. Take database backup
2. Delete old deployment
3. Restore to new Postgres
4. Deploy to new cluster

## Scaling

### Horizontal Scaling

Scale workers per customer based on pipeline load:

```bash
kubectl scale deployment bizon-worker -n acme --replicas=3
```

### Resource Limits

Set appropriate limits per customer:

```yaml
# values.yaml
resources:
  api:
    limits:
      cpu: "1"
      memory: "1Gi"
  worker:
    limits:
      cpu: "2"
      memory: "4Gi"
```

## Security Considerations

1. **Database isolation**: Each customer has their own database
2. **Network policies**: Restrict cross-namespace communication
3. **Secrets management**: Use Kubernetes Secrets or external secret managers
4. **Encryption keys**: Unique per customer
5. **Auth**: Each instance has its own `ADMIN_PASSWORD`

## Troubleshooting

### Common Issues

**Database connection errors**
```bash
kubectl logs -n acme deployment/bizon-api | grep -i database
```

**Migration failures**
```bash
kubectl exec -n acme deployment/bizon-api -- alembic current
kubectl exec -n acme deployment/bizon-api -- alembic upgrade head
```

**Worker not processing jobs**
```bash
kubectl logs -n acme deployment/bizon-worker -f
```
