# Phase 1d: Testing Sandbox

**Effort:** Medium
**Dependencies:** 01c-source-generation
**PR Size:** ~1 week

## Goal

Safely execute generated source code against real APIs without exposing secrets to the LLM or risking the host system. This is the "guarantee" in "connector done right every time."

## The Problem

```
Generated code could:
├── Have syntax errors
├── Have import errors
├── Have runtime errors
├── Make incorrect API calls
├── Leak secrets in logs/errors
└── Do malicious things (if compromised)

We need to:
├── Execute code safely
├── Test against real APIs
├── Capture detailed errors
├── Never expose secrets to LLM
└── Return sanitized results
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Testing Flow                                               │
│                                                             │
│  1. Generated code (from templates)                         │
│  2. Static validation (AST, imports)                        │
│  3. Sandbox execution (isolated)                            │
│  4. Real API call (with secrets)                            │
│  5. Sanitized results (to LLM/user)                         │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Sandbox                                                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Subprocess with:                                     │  │
│  │  - Fresh Python environment                           │  │
│  │  - Limited imports (allowlist)                        │  │
│  │  - Network access (for API calls)                     │  │
│  │  - Timeout (30s default)                              │  │
│  │  - Memory limit                                       │  │
│  │  - Secrets injected as env vars                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                         │                                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Results Sanitizer                                    │  │
│  │  - Redact secrets from output                         │  │
│  │  - Redact secrets from errors                         │  │
│  │  - Return structured result                           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Test Levels

| Level | What it Tests | Real API? | Secrets? |
|-------|---------------|-----------|----------|
| 1. Syntax | Code parses | No | No |
| 2. Imports | Modules load | No | No |
| 3. Instantiate | Class creates | No | No |
| 4. Connection | Auth works | Yes | Yes |
| 5. Fetch | Records retrieved | Yes | Yes |
| 6. Pagination | Multiple pages | Yes | Yes |

```python
class TestLevel(Enum):
    SYNTAX = 1
    IMPORTS = 2
    INSTANTIATE = 3
    CONNECTION = 4
    FETCH = 5
    PAGINATION = 6

class TestResult(BaseModel):
    level: TestLevel
    passed: bool
    error: str | None
    error_type: str | None  # "SyntaxError", "ConnectionError", etc.
    sample_records: list[dict] | None
    record_count: int | None
    duration_ms: int
```

## Implementation

### Static Validation (Levels 1-3)

```python
def validate_syntax(code: str) -> TestResult:
    """Level 1: Parse AST"""
    try:
        ast.parse(code)
        return TestResult(level=TestLevel.SYNTAX, passed=True)
    except SyntaxError as e:
        return TestResult(
            level=TestLevel.SYNTAX,
            passed=False,
            error=str(e),
            error_type="SyntaxError"
        )

def validate_imports(code: str) -> TestResult:
    """Level 2: Check imports against allowlist"""
    allowed = {
        "typing", "requests", "time", "json", "datetime",
        "bizon.source.config", "bizon.source.models", "bizon.source.source"
    }
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in allowed:
                    return TestResult(
                        level=TestLevel.IMPORTS,
                        passed=False,
                        error=f"Import not allowed: {alias.name}",
                        error_type="ImportError"
                    )
    return TestResult(level=TestLevel.IMPORTS, passed=True)

def validate_instantiate(code: str, config: dict) -> TestResult:
    """Level 3: Try to create instance (no API calls)"""
    # Run in subprocess to isolate
    result = run_in_sandbox(
        code=code,
        script="""
source_class = get_source_class()
config_class = source_class.get_config_class()
config = config_class(**CONFIG)
source = source_class(config=config)
print("OK")
""",
        env={"CONFIG": json.dumps(config)},
        timeout=5
    )
    return TestResult(
        level=TestLevel.INSTANTIATE,
        passed=result.exit_code == 0,
        error=result.stderr if result.exit_code != 0 else None
    )
```

### Sandbox Execution (Levels 4-6)

```python
def run_in_sandbox(
    code: str,
    script: str,
    env: dict,
    timeout: int = 30
) -> SandboxResult:
    """
    Execute code in isolated subprocess.
    Secrets passed via env vars, never in code.
    """
    # Write code to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        code_path = f.name

    # Write test script
    test_script = f"""
import sys
import json
import os
sys.path.insert(0, os.path.dirname("{code_path}"))

# Import the generated source
exec(open("{code_path}").read())

# Get config from env (secrets here)
CONFIG = json.loads(os.environ.get("CONFIG", "{{}}"))

def get_source_class():
    # Find the class that extends AbstractSource
    for name, obj in list(globals().items()):
        if isinstance(obj, type) and hasattr(obj, 'streams'):
            return obj
    raise ValueError("No source class found")

{script}
"""

    # Run with restricted environment
    result = subprocess.run(
        ["python", "-c", test_script],
        env={
            **os.environ,
            **env,  # Includes secrets
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=tempfile.gettempdir()
    )

    # Clean up
    os.unlink(code_path)

    return SandboxResult(
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=sanitize_output(result.stderr, env)  # Remove secrets!
    )

def sanitize_output(text: str, env: dict) -> str:
    """Remove any secret values from output."""
    for key, value in env.items():
        if key.startswith("SECRET_") or "KEY" in key or "TOKEN" in key:
            text = text.replace(value, "[REDACTED]")
    return text
```

### Connection Test (Level 4)

```python
def test_connection(
    code: str,
    config: dict,
    secrets: dict
) -> TestResult:
    """Level 4: Test check_connection() with real API"""
    result = run_in_sandbox(
        code=code,
        script="""
import json

source_class = get_source_class()
config_class = source_class.get_config_class()

# Merge config with secrets
full_config = {**CONFIG, **SECRETS}
config = config_class(**full_config)
source = source_class(config=config)

success, error = source.check_connection()
print(json.dumps({"success": success, "error": error}))
""",
        env={
            "CONFIG": json.dumps(config),
            "SECRETS": json.dumps(secrets),  # API keys etc.
        },
        timeout=30
    )

    if result.exit_code != 0:
        return TestResult(
            level=TestLevel.CONNECTION,
            passed=False,
            error=result.stderr,  # Already sanitized
            error_type="RuntimeError"
        )

    data = json.loads(result.stdout)
    return TestResult(
        level=TestLevel.CONNECTION,
        passed=data["success"],
        error=data["error"]
    )
```

### Fetch Test (Level 5)

```python
def test_fetch(
    code: str,
    config: dict,
    secrets: dict,
    stream: str
) -> TestResult:
    """Level 5: Fetch first page of records"""
    result = run_in_sandbox(
        code=code,
        script="""
import json

source_class = get_source_class()
config_class = source_class.get_config_class()

full_config = {**CONFIG, **SECRETS, "stream": STREAM}
config = config_class(**full_config)
source = source_class(config=config)

iteration = source.get()
print(json.dumps({
    "count": len(iteration.records),
    "has_more": iteration.next_pagination is not None,
    "sample": [r.data for r in iteration.records[:3]]
}))
""",
        env={
            "CONFIG": json.dumps(config),
            "SECRETS": json.dumps(secrets),
            "STREAM": stream,
        },
        timeout=60
    )

    if result.exit_code != 0:
        return TestResult(
            level=TestLevel.FETCH,
            passed=False,
            error=result.stderr,
            error_type="RuntimeError"
        )

    data = json.loads(result.stdout)
    return TestResult(
        level=TestLevel.FETCH,
        passed=data["count"] > 0,
        error=None if data["count"] > 0 else "No records fetched",
        sample_records=data["sample"],
        record_count=data["count"]
    )
```

## Error Diagnosis

When a test fails, the LLM needs to understand why WITHOUT seeing secrets:

```python
def diagnose_error(result: TestResult) -> DiagnosedError:
    """
    Analyze error and provide actionable diagnosis.
    """
    error = result.error or ""

    # Authentication errors
    if "401" in error or "Unauthorized" in error:
        return DiagnosedError(
            category="authentication",
            message="API returned 401 Unauthorized",
            suggestion="Check that credentials are correct and have required permissions"
        )

    if "403" in error or "Forbidden" in error:
        return DiagnosedError(
            category="authorization",
            message="API returned 403 Forbidden",
            suggestion="The credentials may lack permission for this endpoint"
        )

    # Rate limiting
    if "429" in error or "rate limit" in error.lower():
        return DiagnosedError(
            category="rate_limit",
            message="API rate limit exceeded",
            suggestion="Add retry logic with exponential backoff"
        )

    # Connection errors
    if "ConnectionError" in error or "timeout" in error.lower():
        return DiagnosedError(
            category="connection",
            message="Could not connect to API",
            suggestion="Check base_url is correct and API is reachable"
        )

    # Response parsing
    if "KeyError" in error or "JSONDecodeError" in error:
        return DiagnosedError(
            category="parsing",
            message="Could not parse API response",
            suggestion="Check response structure matches expected format"
        )

    return DiagnosedError(
        category="unknown",
        message=error[:500],  # Truncate for safety
        suggestion="Review the error message and adjust the code"
    )
```

## Full Test Flow

```python
async def test_source(
    code: str,
    config: dict,
    secrets: dict,
    stream: str
) -> FullTestResult:
    """
    Run all test levels, stop on first failure.
    Returns detailed results for each level.
    """
    results = []

    # Level 1: Syntax
    r = validate_syntax(code)
    results.append(r)
    if not r.passed:
        return FullTestResult(results=results, passed=False)

    # Level 2: Imports
    r = validate_imports(code)
    results.append(r)
    if not r.passed:
        return FullTestResult(results=results, passed=False)

    # Level 3: Instantiate
    r = validate_instantiate(code, config)
    results.append(r)
    if not r.passed:
        return FullTestResult(results=results, passed=False)

    # Level 4: Connection
    r = test_connection(code, config, secrets)
    results.append(r)
    if not r.passed:
        return FullTestResult(results=results, passed=False)

    # Level 5: Fetch
    r = test_fetch(code, config, secrets, stream)
    results.append(r)

    return FullTestResult(
        results=results,
        passed=r.passed,
        sample_records=r.sample_records
    )
```

## Tasks

- [ ] Implement SandboxResult and TestResult models
- [ ] Implement static validation (syntax, imports)
- [ ] Implement sandbox subprocess execution
- [ ] Implement secret sanitization
- [ ] Implement connection test
- [ ] Implement fetch test
- [ ] Implement pagination test (optional, stretch)
- [ ] Implement error diagnosis
- [ ] Add timeout and memory limits
- [ ] Add logging (sanitized)

## Testing

- [ ] Test with valid source code
- [ ] Test with syntax errors
- [ ] Test with bad imports
- [ ] Test with connection failure (bad credentials)
- [ ] Test with parsing failure (wrong response structure)
- [ ] Verify secrets never appear in output

## Success Criteria

- [ ] All test levels execute correctly
- [ ] Secrets are NEVER exposed in errors/logs
- [ ] Timeout prevents hanging
- [ ] Errors are actionable (LLM can fix)
- [ ] Sample records returned on success
