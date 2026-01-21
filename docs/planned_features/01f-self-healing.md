# Phase 1f: Self-Healing

**Effort:** High
**Dependencies:** 01e-secrets-management
**PR Size:** ~2 weeks

## Goal

When a pipeline fails at 3am, Bizon AI diagnoses the problem, fixes the code, tests the fix, and redeploys - all without human intervention (based on trust level).

## The Value Prop

```
Traditional:
  3:00 AM - Pipeline fails
  9:00 AM - Engineer sees alert
  10:00 AM - Engineer investigates
  11:00 AM - Engineer deploys fix
  = 8 hours of downtime

With Bizon AI:
  3:00 AM - Pipeline fails
  3:01 AM - AI diagnoses issue
  3:02 AM - AI generates fix
  3:03 AM - AI tests fix
  3:04 AM - AI deploys (or opens PR)
  3:05 AM - Pipeline recovers
  9:00 AM - Engineer sees "auto-recovered" status
  = 5 minutes of downtime
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Pipeline Runs                                              │
└─────────────────────────────────────────────────────────────┘
         │
         │ On failure
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Failure Monitor                                            │
│  - Watches for failed runs                                  │
│  - Filters: only healable failures                          │
│  - Rate limits: max N heals per pipeline per day            │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Diagnosis Agent                                            │
│  - Analyzes error logs                                      │
│  - Identifies root cause category                           │
│  - Determines if fixable                                    │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Fix Generator                                              │
│  - Reads current source code                                │
│  - Applies targeted fix based on diagnosis                  │
│  - Uses same templates as source generation                 │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Testing Sandbox                                            │
│  - Tests fix against real API                               │
│  - Must pass all test levels                                │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Deployment (based on trust level)                          │
│                                                             │
│  Level 1 (Suggest): Open PR, notify human                   │
│  Level 2 (Assist): Auto-deploy, notify human                │
│  Level 3 (Autonomous): Auto-deploy, log only                │
└─────────────────────────────────────────────────────────────┘
```

## Failure Categories

| Category | Example | Fixable? | Fix Strategy |
|----------|---------|----------|--------------|
| **Rate Limit** | 429 Too Many Requests | Yes | Add exponential backoff |
| **Auth Expired** | 401 token expired | Maybe | Refresh OAuth token |
| **Schema Change** | KeyError: 'user_id' | Yes | Update response parsing |
| **API Down** | Connection timeout | No | Wait and retry |
| **Bad Data** | ValidationError | Maybe | Add data cleaning |
| **Code Bug** | AttributeError | Yes | LLM fix |
| **Pagination** | Infinite loop | Yes | Fix pagination logic |

```python
class FailureCategory(Enum):
    RATE_LIMIT = "rate_limit"
    AUTH_EXPIRED = "auth_expired"
    SCHEMA_CHANGE = "schema_change"
    API_UNAVAILABLE = "api_unavailable"
    DATA_VALIDATION = "data_validation"
    CODE_ERROR = "code_error"
    PAGINATION_ERROR = "pagination_error"
    UNKNOWN = "unknown"

class Diagnosis(BaseModel):
    category: FailureCategory
    fixable: bool
    confidence: float  # 0-1
    details: str
    suggested_fix: str | None
```

## Diagnosis Agent

```python
async def diagnose_failure(
    error_logs: str,
    source_code: str,
    recent_successes: int
) -> Diagnosis:
    """
    Analyze failure and determine root cause.
    """
    # First, try rule-based detection (fast, reliable)
    diagnosis = rule_based_diagnosis(error_logs)
    if diagnosis.confidence > 0.9:
        return diagnosis

    # Fall back to LLM for complex cases
    prompt = f"""
    Analyze this pipeline failure and determine the root cause.

    Error logs:
    ```
    {error_logs[-5000:]}  # Truncate for context
    ```

    Source code:
    ```python
    {source_code}
    ```

    Recent history: {recent_successes} successful runs before this failure

    Respond with:
    1. Category: One of {[c.value for c in FailureCategory]}
    2. Fixable: true/false
    3. Confidence: 0-1
    4. Details: What went wrong
    5. Suggested fix: If fixable, what change to make
    """

    response = await llm.complete(prompt, response_format=Diagnosis)
    return response

def rule_based_diagnosis(error_logs: str) -> Diagnosis:
    """Fast pattern matching for common errors."""

    if "429" in error_logs or "rate limit" in error_logs.lower():
        return Diagnosis(
            category=FailureCategory.RATE_LIMIT,
            fixable=True,
            confidence=0.95,
            details="API rate limit exceeded",
            suggested_fix="Add exponential backoff to request logic"
        )

    if "401" in error_logs and "expired" in error_logs.lower():
        return Diagnosis(
            category=FailureCategory.AUTH_EXPIRED,
            fixable=True,
            confidence=0.90,
            details="Authentication token expired",
            suggested_fix="Refresh OAuth token before request"
        )

    if "KeyError" in error_logs or "key not found" in error_logs.lower():
        return Diagnosis(
            category=FailureCategory.SCHEMA_CHANGE,
            fixable=True,
            confidence=0.85,
            details="API response structure changed",
            suggested_fix="Update response parsing to handle new schema"
        )

    if "ConnectionError" in error_logs or "timeout" in error_logs.lower():
        return Diagnosis(
            category=FailureCategory.API_UNAVAILABLE,
            fixable=False,
            confidence=0.90,
            details="API is temporarily unavailable",
            suggested_fix=None  # Just wait and retry
        )

    return Diagnosis(
        category=FailureCategory.UNKNOWN,
        fixable=False,
        confidence=0.5,
        details="Could not determine failure cause",
        suggested_fix=None
    )
```

## Fix Generator

```python
async def generate_fix(
    source_code: str,
    diagnosis: Diagnosis
) -> str:
    """
    Generate fixed source code based on diagnosis.
    """
    if diagnosis.category == FailureCategory.RATE_LIMIT:
        return apply_rate_limit_fix(source_code)

    if diagnosis.category == FailureCategory.AUTH_EXPIRED:
        return apply_auth_refresh_fix(source_code)

    # For complex fixes, use LLM
    prompt = f"""
    Fix this source code based on the diagnosis.

    Current code:
    ```python
    {source_code}
    ```

    Diagnosis: {diagnosis.category.value}
    Details: {diagnosis.details}
    Suggested fix: {diagnosis.suggested_fix}

    Return the COMPLETE fixed source code.
    Only change what's necessary to fix the issue.
    Preserve all existing functionality.
    """

    fixed_code = await llm.complete(prompt)
    return fixed_code

def apply_rate_limit_fix(code: str) -> str:
    """Apply battle-tested rate limit fix."""
    # Insert retry logic into _request method
    rate_limit_code = '''
        # Handle rate limiting with exponential backoff
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            time.sleep(min(retry_after, 300))  # Max 5 min wait
            continue
    '''
    # Insert into existing _request method
    return insert_into_request_method(code, rate_limit_code)
```

## Healing Flow

```python
async def heal_pipeline(
    pipeline_id: str,
    run_id: str,
    trust_level: TrustLevel
) -> HealingResult:
    """
    Attempt to heal a failed pipeline run.
    """
    # 1. Get failure details
    run = await get_run(run_id)
    pipeline = await get_pipeline(pipeline_id)
    source_code = await get_source_code(pipeline.source)

    # 2. Diagnose
    diagnosis = await diagnose_failure(
        error_logs=run.error_logs,
        source_code=source_code,
        recent_successes=await count_recent_successes(pipeline_id)
    )

    if not diagnosis.fixable:
        return HealingResult(
            success=False,
            action="skipped",
            reason=f"Not fixable: {diagnosis.details}"
        )

    # 3. Generate fix
    fixed_code = await generate_fix(source_code, diagnosis)

    # 4. Validate fix
    test_result = await test_source(
        code=fixed_code,
        config=pipeline.source_config,
        secrets=await get_secrets(pipeline),
        stream=pipeline.stream
    )

    if not test_result.passed:
        return HealingResult(
            success=False,
            action="fix_failed",
            reason=f"Fix didn't work: {test_result.error}"
        )

    # 5. Deploy based on trust level
    if trust_level == TrustLevel.SUGGEST:
        pr_url = await create_pr(
            pipeline=pipeline,
            old_code=source_code,
            new_code=fixed_code,
            diagnosis=diagnosis
        )
        await notify_user(
            title=f"Fix ready for {pipeline.name}",
            message=f"Bizon AI fixed a {diagnosis.category.value} issue. Review PR: {pr_url}",
            priority="normal"
        )
        return HealingResult(
            success=True,
            action="pr_created",
            pr_url=pr_url
        )

    elif trust_level == TrustLevel.ASSIST:
        await deploy_fix(pipeline, fixed_code)
        await trigger_run(pipeline_id)
        await notify_user(
            title=f"Auto-fixed: {pipeline.name}",
            message=f"Bizon AI fixed a {diagnosis.category.value} issue and redeployed.",
            priority="low"
        )
        return HealingResult(
            success=True,
            action="auto_deployed"
        )

    elif trust_level == TrustLevel.AUTONOMOUS:
        await deploy_fix(pipeline, fixed_code)
        await trigger_run(pipeline_id)
        # No notification, just log
        await log_healing(pipeline_id, diagnosis, "auto_deployed")
        return HealingResult(
            success=True,
            action="auto_deployed"
        )
```

## Failure Monitor

```python
class FailureMonitor:
    """
    Watches for pipeline failures and triggers healing.
    """
    def __init__(self):
        self.healing_limits = {}  # pipeline_id -> count today

    async def on_run_failed(self, run: Run):
        """Called when a pipeline run fails."""
        pipeline_id = run.pipeline_id

        # Rate limit healing attempts
        if self.healing_limits.get(pipeline_id, 0) >= 3:
            await log("Max healing attempts reached", pipeline_id=pipeline_id)
            return

        # Check if pipeline has healing enabled
        pipeline = await get_pipeline(pipeline_id)
        if not pipeline.auto_heal:
            return

        # Check if this is a healable failure type
        if run.error_type in ["manual_cancel", "timeout"]:
            return

        # Attempt healing
        result = await heal_pipeline(
            pipeline_id=pipeline_id,
            run_id=run.id,
            trust_level=pipeline.trust_level
        )

        self.healing_limits[pipeline_id] = self.healing_limits.get(pipeline_id, 0) + 1

        if result.success:
            await log("Pipeline healed", pipeline_id=pipeline_id, action=result.action)
```

## Git Integration (for PRs)

```python
async def create_pr(
    pipeline: Pipeline,
    old_code: str,
    new_code: str,
    diagnosis: Diagnosis
) -> str:
    """Create a PR with the fix."""

    # Create branch
    branch_name = f"bizon-ai/fix-{pipeline.name}-{int(time.time())}"
    await git_create_branch(branch_name)

    # Commit fix
    source_path = pipeline.source_file_path
    await git_write_file(source_path, new_code)
    await git_commit(
        message=f"fix({pipeline.name}): {diagnosis.category.value}\n\n{diagnosis.details}",
        author="Bizon AI <ai@bizon.dev>"
    )

    # Create PR
    pr = await git_create_pr(
        title=f"[Bizon AI] Fix {pipeline.name}: {diagnosis.category.value}",
        body=f"""
## Automated Fix

Bizon AI detected and fixed an issue with the `{pipeline.name}` pipeline.

### Diagnosis
- **Category:** {diagnosis.category.value}
- **Details:** {diagnosis.details}
- **Confidence:** {diagnosis.confidence:.0%}

### Changes
```diff
{generate_diff(old_code, new_code)}
```

### Verification
- [x] Fix tested against real API
- [x] Sample records fetched successfully

---
*This PR was automatically generated by Bizon AI.*
""",
        head=branch_name,
        base="main"
    )

    return pr.url
```

## Configuration

```yaml
# bizon.yaml
ai:
  trust_level: 2  # 1=suggest, 2=assist, 3=autonomous

  healing:
    enabled: true
    max_attempts_per_day: 3
    notify_on_fix: true

    # What can be auto-fixed
    auto_fix:
      rate_limit: true
      auth_expired: true
      schema_change: true
      code_error: false  # Require human review

    # What requires human approval
    require_approval:
      - delete_pipeline
      - change_destination
      - modify_schedule
```

## Tasks

- [ ] Implement Diagnosis model and FailureCategory enum
- [ ] Implement rule-based diagnosis
- [ ] Implement LLM diagnosis fallback
- [ ] Implement fix generator for each category
- [ ] Implement FailureMonitor service
- [ ] Implement healing flow
- [ ] Implement Git PR creation
- [ ] Implement notifications (email, Slack)
- [ ] Add healing configuration to bizon.yaml
- [ ] Add healing dashboard UI

## Testing

- [ ] Test diagnosis of rate limit error
- [ ] Test diagnosis of auth expired error
- [ ] Test diagnosis of schema change error
- [ ] Test fix generation and deployment
- [ ] Test PR creation flow
- [ ] Test rate limiting of healing attempts
- [ ] Test trust level enforcement

## Success Criteria

- [ ] >80% of healable failures auto-recovered
- [ ] False positive rate <5% (bad fixes)
- [ ] Healing completes in <5 minutes
- [ ] Notifications delivered reliably
- [ ] PRs are reviewable and mergeable
