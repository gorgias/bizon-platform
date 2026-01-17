# Connector Marketplace

**Priority:** P3
**Effort:** High
**Status:** Future

## Overview

Community-contributed connectors with discovery, ratings, and one-click installation. Build an ecosystem around Bizon similar to Airbyte's connector catalog.

## Why This Matters

- **Network effects** - More connectors → more users → more connectors
- **Community growth** - Contributors become advocates
- **Long tail coverage** - Community covers niche data sources
- **Reduced maintenance** - Community maintains their connectors

## Vision

```
┌─────────────────────────────────────────────────────────────┐
│                   Connector Marketplace                     │
├─────────────────────────────────────────────────────────────┤
│  Search: [stripe____________] [Sources ▼] [Search]         │
│                                                             │
│  Featured Connectors                                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ Stripe  │ │ HubSpot │ │ Shopify │ │ Notion  │          │
│  │ ★★★★★   │ │ ★★★★☆   │ │ ★★★★★   │ │ ★★★★☆   │          │
│  │ 2.1k    │ │ 1.8k    │ │ 1.5k    │ │ 980     │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
│                                                             │
│  Recently Added                                             │
│  • Linear (by @johndoe) - Project management               │
│  • Airtable (by @jane) - No-code database                  │
│  • Plaid (by @finance_dev) - Financial data                │
└─────────────────────────────────────────────────────────────┘
```

## Connector Specification

### Package Structure

```
my-connector/
├── connector.yaml          # Manifest
├── source.py              # Implementation
├── requirements.txt       # Dependencies
├── README.md             # Documentation
├── icon.svg              # Display icon
└── tests/
    └── test_source.py
```

### Manifest (connector.yaml)

```yaml
# Connector metadata
name: linear
version: 1.2.0
display_name: Linear
description: Sync issues, projects, and teams from Linear
category: project-management
author:
  name: John Doe
  email: john@example.com
  github: johndoe

# Supported streams
streams:
  - name: issues
    description: Linear issues with full details
    incremental: true
  - name: projects
    description: Projects and their metadata
    incremental: false
  - name: teams
    description: Team information
    incremental: false
  - name: users
    description: Workspace users
    incremental: false

# Authentication options
authentication:
  - type: api_key
    label: API Key
    fields:
      - name: api_key
        type: secret
        required: true
        description: Your Linear API key

# Configuration options
config:
  - name: workspace_id
    type: string
    required: false
    description: Filter to specific workspace (optional)

# Requirements
python_version: ">=3.10"
dependencies:
  - httpx>=0.24.0
  - pydantic>=2.0.0

# Compatibility
bizon_version: ">=0.1.0"

# Links
repository: https://github.com/johndoe/bizon-connector-linear
documentation: https://johndoe.github.io/bizon-connector-linear
```

## Registry Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Connector Registry                       │
│                    (registry.bizon.dev)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Catalog    │  │   Packages   │  │   Reviews    │     │
│  │   (metadata) │  │   (storage)  │  │   & Ratings  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ API
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Bizon Instance                           │
│                                                             │
│  bizon connector search "linear"                           │
│  bizon connector install linear                            │
│  bizon connector update linear                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## API Design

### Registry API

```
# Search & Discovery
GET  /api/v1/connectors
     ?search=stripe
     &category=e-commerce
     &type=source
     &sort=downloads|rating|updated

GET  /api/v1/connectors/{name}
GET  /api/v1/connectors/{name}/versions
GET  /api/v1/connectors/{name}/versions/{version}
GET  /api/v1/connectors/{name}/reviews

# Package Download
GET  /api/v1/connectors/{name}/download
GET  /api/v1/connectors/{name}/versions/{version}/download

# Publishing (authenticated)
POST /api/v1/connectors
PUT  /api/v1/connectors/{name}/versions/{version}

# Reviews (authenticated)
POST /api/v1/connectors/{name}/reviews
```

### Instance API

```
# Installed connectors
GET    /api/connectors/installed
POST   /api/connectors/install
DELETE /api/connectors/{name}

# Updates
GET    /api/connectors/updates
POST   /api/connectors/{name}/update
```

## Installation Flow

### CLI

```bash
# Search for connectors
bizon connector search linear
# Results:
# NAME    VERSION  DOWNLOADS  RATING  DESCRIPTION
# linear  1.2.0    2,150      4.8     Sync from Linear

# Install connector
bizon connector install linear
# Installing linear@1.2.0...
# Downloading package...
# Installing dependencies...
# Done! Run 'bizon connector test linear' to verify.

# Test connector
bizon connector test linear --stream issues
# Testing connection... OK
# Fetching sample records... 5 records fetched

# Update connector
bizon connector update linear
# Updating linear 1.2.0 → 1.3.0...
# Done!

# List installed
bizon connector list
# NAME    VERSION  STREAMS
# linear  1.3.0    issues, projects, teams, users
```

### UI

```tsx
function ConnectorMarketplace() {
  const { data: connectors } = useQuery('marketplace', fetchMarketplace);

  return (
    <div>
      <SearchBar onSearch={setSearch} />
      <CategoryFilter categories={categories} />

      <div className="grid grid-cols-3 gap-4">
        {connectors?.map(connector => (
          <ConnectorCard
            key={connector.name}
            connector={connector}
            onInstall={() => installConnector(connector.name)}
          />
        ))}
      </div>
    </div>
  );
}

function ConnectorCard({ connector, onInstall }) {
  return (
    <Card>
      <img src={connector.icon_url} />
      <h3>{connector.display_name}</h3>
      <p>{connector.description}</p>

      <div className="flex items-center gap-2">
        <Stars rating={connector.rating} />
        <span>{connector.downloads} downloads</span>
      </div>

      <Button onClick={onInstall}>Install</Button>
    </Card>
  );
}
```

## Security Model

### Connector Verification

1. **Automated scanning**
   - Dependency vulnerability check
   - Code analysis for dangerous patterns
   - License compliance

2. **Manual review** (for verified badge)
   - Code review by maintainers
   - Security audit
   - Quality assessment

3. **Trust levels**
   - Unverified: Community contributed
   - Verified: Passed automated + manual review
   - Official: Maintained by Bizon team

### Runtime Isolation

```python
# Connector runs in isolated environment
class ConnectorSandbox:
    def __init__(self, connector_path: Path):
        self.path = connector_path
        self.venv = self._create_venv()

    def _create_venv(self):
        """Create isolated virtualenv for connector."""
        venv_path = self.path / ".venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)])
        return venv_path

    def install_dependencies(self):
        """Install connector dependencies in isolation."""
        pip = self.venv / "bin" / "pip"
        requirements = self.path / "requirements.txt"
        subprocess.run([str(pip), "install", "-r", str(requirements)])

    def run(self, config: dict) -> SourceIteration:
        """Execute connector in subprocess."""
        python = self.venv / "bin" / "python"
        result = subprocess.run(
            [str(python), str(self.path / "source.py")],
            input=json.dumps(config),
            capture_output=True,
            timeout=300,
        )
        return SourceIteration.model_validate_json(result.stdout)
```

## Publishing Flow

### Submit Connector

1. Create connector following spec
2. Run local validation: `bizon connector validate ./my-connector`
3. Create account on registry
4. Publish: `bizon connector publish ./my-connector`
5. Automated tests run
6. Connector available (unverified)

### Get Verified

1. Request verification via registry
2. Automated security scan
3. Manual code review
4. If approved, gets verified badge
5. Featured in marketplace

## Monetization Options

### For Registry Operator (Bizon)

- **Premium connectors** - Enterprise data sources
- **Priority support** - Fast issue resolution
- **Custom development** - Build connectors for customers

### For Connector Authors

- **Sponsored connectors** - Companies pay for maintenance
- **Donations** - Community support
- **Consulting** - Implementation help

## Implementation Phases

### Phase 1: Local Registry

- File-based connector storage
- CLI commands for install/update
- No rating/reviews

### Phase 2: Central Registry

- Hosted registry at registry.bizon.dev
- Package upload/download
- Basic search and discovery

### Phase 3: Community Features

- User accounts
- Ratings and reviews
- Download statistics
- Verified badges

### Phase 4: Ecosystem

- Automated testing CI
- Security scanning
- Monetization features
- Partner program

## Success Metrics

- Number of published connectors
- Monthly active installs
- Connector coverage vs Airbyte
- Community contributor count
- Time to first connector publish

## Challenges

1. **Quality control** - Maintaining connector quality at scale
2. **Breaking changes** - Handling bizon-core API changes
3. **Security** - Ensuring connector code is safe
4. **Maintenance** - Keeping connectors up-to-date
5. **Discovery** - Helping users find the right connector

## Inspiration

- **Airbyte Connector Catalog** - 400+ connectors
- **npm Registry** - Package discovery and versioning
- **VS Code Marketplace** - Quality tiers and reviews
- **Terraform Registry** - Provider ecosystem
