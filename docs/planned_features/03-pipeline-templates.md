# Pipeline Templates

**Priority:** P1
**Effort:** Low
**Status:** Planned

## Overview

Pre-built pipeline configurations for common data integration use cases. Users can browse, select, and customize templates to quickly create pipelines.

## Why This Matters

- **Instant value** - Get started in minutes, not hours
- **Best practices** - Templates encode recommended configurations
- **Discovery** - Users learn what's possible
- **Marketing** - "Stripe to BigQuery in 2 clicks"

## Template Categories

### E-commerce
- `shopify-to-bigquery` - Orders, customers, products
- `shopify-to-snowflake` - Full Shopify sync
- `stripe-to-bigquery` - Payments, customers, subscriptions
- `stripe-to-postgres` - Lightweight payment sync

### CRM & Marketing
- `hubspot-to-bigquery` - Contacts, deals, companies
- `hubspot-to-snowflake` - Full HubSpot sync
- `salesforce-to-bigquery` - Leads, opportunities, accounts
- `mailchimp-to-bigquery` - Campaigns, subscribers

### Product & Analytics
- `mixpanel-to-bigquery` - Events export
- `amplitude-to-snowflake` - User analytics
- `segment-to-bigquery` - Event stream

### Engineering
- `github-to-bigquery` - Issues, PRs, commits
- `jira-to-bigquery` - Issues, sprints, projects
- `pagerduty-to-bigquery` - Incidents, on-call

### Finance
- `quickbooks-to-bigquery` - Invoices, payments
- `xero-to-snowflake` - Full accounting sync

## Template Structure

```yaml
# templates/stripe-to-bigquery.yaml
name: Stripe to BigQuery
description: Sync Stripe customers, charges, and subscriptions to BigQuery
category: e-commerce
tags:
  - stripe
  - bigquery
  - payments

# Variables that users must provide
variables:
  - name: stripe_api_key
    label: Stripe API Key
    type: secret
    description: Your Stripe secret key (sk_live_xxx or sk_test_xxx)
    required: true

  - name: bigquery_project
    label: BigQuery Project ID
    type: string
    required: true

  - name: bigquery_dataset
    label: BigQuery Dataset
    type: string
    default: stripe_raw

  - name: bigquery_credentials
    label: BigQuery Service Account JSON
    type: secret
    description: Base64-encoded service account credentials
    required: true

# Available streams from this source
streams:
  - name: customers
    description: Stripe customer records
    default: true
  - name: charges
    description: Payment charges
    default: true
  - name: subscriptions
    description: Recurring subscriptions
    default: false
  - name: invoices
    description: Invoice records
    default: false

# The actual pipeline config (with variable placeholders)
config:
  source:
    name: stripe
    stream: "{{ stream }}"
    authentication:
      type: api_key
      params:
        token: "{{ stripe_api_key }}"

  destination:
    name: bigquery
    config:
      project_id: "{{ bigquery_project }}"
      dataset: "{{ bigquery_dataset }}"
      credentials_base64: "{{ bigquery_credentials }}"
      buffer_size: 50
      buffer_flush_timeout: 300

# Recommended schedule
default_schedule: "0 2 * * *"  # Daily at 2am
```

## User Experience

### 1. Browse Templates
```
GET /api/templates
GET /api/templates?category=e-commerce
GET /api/templates?search=stripe
```

### 2. View Template Details
```
GET /api/templates/stripe-to-bigquery
```

Shows:
- Description
- Required variables
- Available streams
- Default schedule

### 3. Create Pipeline from Template
```
POST /api/templates/stripe-to-bigquery/create
{
  "name": "My Stripe Pipeline",
  "variables": {
    "stripe_api_key": "sk_live_xxx",
    "bigquery_project": "my-project",
    "bigquery_dataset": "stripe_data",
    "bigquery_credentials": "eyJhbGc..."
  },
  "streams": ["customers", "charges"],
  "schedule": "0 */6 * * *"
}
```

Creates multiple pipelines (one per stream) with the provided configuration.

## Implementation

### Template Storage

Store templates as YAML files in the repository:

```
bizon-platform/
└── templates/
    ├── index.yaml           # Template index/metadata
    ├── stripe-to-bigquery.yaml
    ├── shopify-to-bigquery.yaml
    ├── hubspot-to-bigquery.yaml
    └── ...
```

### API Routes

```python
# routes/templates.py
from pathlib import Path
import yaml

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

@router.get("/templates")
async def list_templates(
    category: str | None = None,
    search: str | None = None,
):
    """List available pipeline templates."""
    templates = []
    for path in TEMPLATES_DIR.glob("*.yaml"):
        if path.name == "index.yaml":
            continue
        with open(path) as f:
            template = yaml.safe_load(f)
            # Filter by category/search
            if category and template.get("category") != category:
                continue
            if search and search.lower() not in template["name"].lower():
                continue
            templates.append({
                "id": path.stem,
                "name": template["name"],
                "description": template["description"],
                "category": template.get("category"),
                "tags": template.get("tags", []),
            })
    return templates


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """Get template details."""
    path = TEMPLATES_DIR / f"{template_id}.yaml"
    if not path.exists():
        raise HTTPException(404, "Template not found")

    with open(path) as f:
        template = yaml.safe_load(f)

    # Don't expose the raw config, just metadata
    return {
        "id": template_id,
        "name": template["name"],
        "description": template["description"],
        "category": template.get("category"),
        "tags": template.get("tags", []),
        "variables": template["variables"],
        "streams": template["streams"],
        "default_schedule": template.get("default_schedule"),
    }


@router.post("/templates/{template_id}/create")
async def create_from_template(
    template_id: str,
    request: TemplateCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create pipeline(s) from template."""
    path = TEMPLATES_DIR / f"{template_id}.yaml"
    if not path.exists():
        raise HTTPException(404, "Template not found")

    with open(path) as f:
        template = yaml.safe_load(f)

    # Validate required variables
    for var in template["variables"]:
        if var["required"] and var["name"] not in request.variables:
            raise HTTPException(400, f"Missing required variable: {var['name']}")

    # Create pipeline for each selected stream
    pipelines = []
    for stream in request.streams:
        config = render_template(template["config"], {
            **request.variables,
            "stream": stream,
        })

        pipeline = Pipeline(
            name=f"{request.name} - {stream}",
            config=config,
            schedule=request.schedule or template.get("default_schedule"),
            enabled=False,  # Start disabled
        )
        db.add(pipeline)
        pipelines.append(pipeline)

    await db.commit()

    return {
        "pipelines": [
            {"id": str(p.id), "name": p.name}
            for p in pipelines
        ]
    }
```

### UI Components

```tsx
// TemplateGallery.tsx
function TemplateGallery() {
  const { data: templates } = useQuery('templates', fetchTemplates);

  return (
    <div className="grid grid-cols-3 gap-4">
      {templates?.map(template => (
        <TemplateCard
          key={template.id}
          template={template}
          onClick={() => navigate(`/templates/${template.id}`)}
        />
      ))}
    </div>
  );
}

// TemplateCard.tsx
function TemplateCard({ template }) {
  return (
    <Card>
      <h3>{template.name}</h3>
      <p>{template.description}</p>
      <div className="flex gap-2">
        {template.tags.map(tag => (
          <Badge key={tag}>{tag}</Badge>
        ))}
      </div>
    </Card>
  );
}

// TemplateWizard.tsx
function TemplateWizard({ templateId }) {
  const { data: template } = useQuery(['template', templateId], () =>
    fetchTemplate(templateId)
  );

  const [variables, setVariables] = useState({});
  const [streams, setStreams] = useState([]);

  return (
    <form onSubmit={handleCreate}>
      <h2>Create from {template?.name}</h2>

      {/* Variable inputs */}
      {template?.variables.map(v => (
        <FormField
          key={v.name}
          label={v.label}
          type={v.type === 'secret' ? 'password' : 'text'}
          required={v.required}
          value={variables[v.name] || ''}
          onChange={e => setVariables({...variables, [v.name]: e.target.value})}
        />
      ))}

      {/* Stream selection */}
      <h3>Select Streams</h3>
      {template?.streams.map(s => (
        <Checkbox
          key={s.name}
          label={s.name}
          description={s.description}
          defaultChecked={s.default}
          onChange={checked => /* update streams */}
        />
      ))}

      <Button type="submit">Create Pipelines</Button>
    </form>
  );
}
```

## Template Validation

Before publishing, templates are validated:

```python
def validate_template(template: dict) -> list[str]:
    errors = []

    # Required fields
    for field in ["name", "description", "variables", "streams", "config"]:
        if field not in template:
            errors.append(f"Missing required field: {field}")

    # Variable validation
    for var in template.get("variables", []):
        if "name" not in var:
            errors.append("Variable missing 'name'")
        if "type" not in var:
            errors.append(f"Variable {var.get('name')} missing 'type'")

    # Stream validation
    for stream in template.get("streams", []):
        if "name" not in stream:
            errors.append("Stream missing 'name'")

    # Config has required placeholders
    config_str = str(template.get("config", {}))
    if "{{ stream }}" not in config_str:
        errors.append("Config must include {{ stream }} placeholder")

    return errors
```

## Contributing Templates

Users can contribute templates via PR:

1. Create `templates/your-template.yaml`
2. Follow the template schema
3. Test locally with the validator
4. Submit PR with description of use case

## Future Enhancements

- **Template versioning** - Track template changes over time
- **Community ratings** - Upvote/downvote templates
- **Usage analytics** - Most popular templates
- **Custom templates** - Users save their own templates
- **Template composition** - Combine multiple templates
