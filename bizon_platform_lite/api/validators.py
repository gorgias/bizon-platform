"""Security validation for pipeline configurations.

Validates:
- Transform Python code (AST analysis to prevent code injection)
- YAML injection patterns in config values (prevents !!python/object attacks)
"""

import ast
import re
from dataclasses import dataclass
from typing import Any

# Allowed import prefixes - bizon ecosystem and safe stdlib
ALLOWED_IMPORT_PREFIXES = (
    "bizon",
    "datetime",
    "json",
    "orjson",
    "re",
    "math",
    "decimal",
    "uuid",
    "hashlib",
    "base64",
    "urllib.parse",
    "collections",
    "itertools",
    "functools",
    "typing",
    "dataclasses",
    "enum",
    "copy",
    "operator",
    "string",
    "textwrap",
)

# Dangerous builtins that should be blocked
BLOCKED_BUILTINS = {
    # Code execution
    "eval",
    "exec",
    "compile",
    "__import__",
    # File/IO
    "open",
    "input",
    "print",
    # Introspection that could be abused
    "globals",
    "locals",
    "vars",
    "dir",
    "getattr",
    "setattr",
    "delattr",
    "hasattr",
    # Object manipulation
    "type",
    "object",
    "classmethod",
    "staticmethod",
    "property",
    # Memory/system
    "memoryview",
    "bytearray",
    "breakpoint",
    "help",
    "license",
    "credits",
    "copyright",
    "quit",
    "exit",
}

# Dangerous attribute access patterns
BLOCKED_ATTRIBUTES = {
    # Dunder methods that could escape sandbox
    "__class__",
    "__bases__",
    "__mro__",
    "__subclasses__",
    "__code__",
    "__globals__",
    "__builtins__",
    "__import__",
    "__loader__",
    "__spec__",
    # OS/system access
    "system",
    "popen",
    "spawn",
    "fork",
    "kill",
    "execv",
    "execve",
    "execvp",
    # File operations
    "read",
    "write",
    "readline",
    "readlines",
    "writelines",
    # Network
    "connect",
    "bind",
    "listen",
    "accept",
    "send",
    "recv",
    "sendall",
    "sendto",
    "recvfrom",
}

# Completely blocked modules (even if prefixed with allowed)
BLOCKED_MODULES = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "shutil",
    "pathlib",
    "io",
    "tempfile",
    "pickle",
    "marshal",
    "shelve",
    "dbm",
    "sqlite3",
    "ctypes",
    "multiprocessing",
    "threading",
    "asyncio",
    "concurrent",
    "signal",
    "resource",
    "sysconfig",
    "importlib",
    "builtins",
    "code",
    "codeop",
    "compileall",
    "dis",
    "inspect",
    "traceback",
    "gc",
    "weakref",
    "atexit",
    "fcntl",
    "pty",
    "tty",
    "termios",
    "grp",
    "pwd",
    "spwd",
    "crypt",
    "ssl",
    "http",
    "urllib.request",
    "urllib.error",
    "ftplib",
    "poplib",
    "imaplib",
    "smtplib",
    "telnetlib",
    "socketserver",
    "xmlrpc",
    "ipaddress",
}


@dataclass
class ValidationError:
    """A single validation error."""

    line: int
    column: int
    message: str


@dataclass
class ValidationResult:
    """Result of transform validation."""

    valid: bool
    errors: list[ValidationError]

    def __bool__(self) -> bool:
        return self.valid


class TransformValidator(ast.NodeVisitor):
    """AST visitor that checks for dangerous patterns in transform code."""

    def __init__(self) -> None:
        self.errors: list[ValidationError] = []

    def add_error(self, node: ast.AST, message: str) -> None:
        """Add a validation error at the given node's location."""
        self.errors.append(
            ValidationError(
                line=getattr(node, "lineno", 0),
                column=getattr(node, "col_offset", 0),
                message=message,
            )
        )

    def visit_Import(self, node: ast.Import) -> None:
        """Check import statements."""
        for alias in node.names:
            module = alias.name
            if module in BLOCKED_MODULES or any(module.startswith(f"{blocked}.") for blocked in BLOCKED_MODULES):
                self.add_error(node, f"Import of '{module}' is not allowed")
            elif not any(module == allowed or module.startswith(f"{allowed}.") for allowed in ALLOWED_IMPORT_PREFIXES):
                self.add_error(
                    node,
                    f"Import of '{module}' is not allowed. Allowed: {', '.join(ALLOWED_IMPORT_PREFIXES)}",
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check from...import statements."""
        module = node.module or ""
        if module in BLOCKED_MODULES or any(module.startswith(f"{blocked}.") for blocked in BLOCKED_MODULES):
            self.add_error(node, f"Import from '{module}' is not allowed")
        elif not any(module == allowed or module.startswith(f"{allowed}.") for allowed in ALLOWED_IMPORT_PREFIXES):
            self.add_error(
                node,
                f"Import from '{module}' is not allowed. Allowed: {', '.join(ALLOWED_IMPORT_PREFIXES)}",
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Check function calls for dangerous builtins."""
        # Check direct builtin calls: eval(), exec(), etc.
        if isinstance(node.func, ast.Name):
            if node.func.id in BLOCKED_BUILTINS:
                self.add_error(node, f"Call to '{node.func.id}()' is not allowed")

        # Check method calls on names: os.system(), etc.
        elif isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            if attr in BLOCKED_ATTRIBUTES:
                self.add_error(node, f"Call to '.{attr}()' is not allowed")

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Check attribute access for dangerous patterns."""
        if node.attr in BLOCKED_ATTRIBUTES:
            self.add_error(node, f"Access to '.{node.attr}' is not allowed")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Check for dangerous name references."""
        # Block direct references to dangerous builtins
        if node.id in BLOCKED_BUILTINS and isinstance(node.ctx, ast.Load):
            self.add_error(node, f"Reference to '{node.id}' is not allowed")
        self.generic_visit(node)


def validate_transform_code(code: str) -> ValidationResult:
    """Validate Python transform code for security.

    Args:
        code: Python code string to validate

    Returns:
        ValidationResult with valid=True if code passes all checks,
        or valid=False with list of errors
    """
    # Handle empty code
    if not code or not code.strip():
        return ValidationResult(valid=True, errors=[])

    # Try to parse the code
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return ValidationResult(
            valid=False,
            errors=[
                ValidationError(
                    line=e.lineno or 0,
                    column=e.offset or 0,
                    message=f"Syntax error: {e.msg}",
                )
            ],
        )

    # Run the validator
    validator = TransformValidator()
    validator.visit(tree)

    return ValidationResult(
        valid=len(validator.errors) == 0,
        errors=validator.errors,
    )


def validate_transforms(transforms: list[dict] | None) -> ValidationResult:
    """Validate all transforms in a pipeline config.

    Args:
        transforms: List of transform dicts with 'label' and 'python' keys

    Returns:
        ValidationResult aggregating all transform validation results
    """
    if not transforms:
        return ValidationResult(valid=True, errors=[])

    all_errors: list[ValidationError] = []

    for i, transform in enumerate(transforms):
        if not isinstance(transform, dict):
            all_errors.append(
                ValidationError(
                    line=0,
                    column=0,
                    message=f"Transform {i + 1}: must be a dictionary",
                )
            )
            continue

        label = transform.get("label", f"Transform {i + 1}")
        code = transform.get("python", "")

        if not isinstance(code, str):
            all_errors.append(
                ValidationError(
                    line=0,
                    column=0,
                    message=f"{label}: 'python' field must be a string",
                )
            )
            continue

        result = validate_transform_code(code)
        for error in result.errors:
            all_errors.append(
                ValidationError(
                    line=error.line,
                    column=error.column,
                    message=f"{label} (line {error.line}): {error.message}",
                )
            )

    return ValidationResult(
        valid=len(all_errors) == 0,
        errors=all_errors,
    )


# YAML injection patterns - these could exploit unsafe YAML parsers
YAML_INJECTION_PATTERNS = [
    # Python object instantiation
    re.compile(r"!!python/", re.IGNORECASE),
    # Ruby object instantiation
    re.compile(r"!!ruby/", re.IGNORECASE),
    # Generic tag-based attacks
    re.compile(r"!!\w+/object", re.IGNORECASE),
    re.compile(r"!!\w+/apply", re.IGNORECASE),
    re.compile(r"!!\w+/module", re.IGNORECASE),
    # Perl attacks
    re.compile(r"!!perl/", re.IGNORECASE),
    # Java attacks
    re.compile(r"!!java/", re.IGNORECASE),
    # Generic code execution patterns
    re.compile(r"!!binary\s", re.IGNORECASE),
]


def check_yaml_injection(value: Any, path: str = "") -> list[ValidationError]:
    """Recursively check for YAML injection patterns in config values.

    Args:
        value: Any config value (string, dict, list, etc.)
        path: Current path in the config (for error messages)

    Returns:
        List of validation errors for detected injection patterns
    """
    errors: list[ValidationError] = []

    if isinstance(value, str):
        for pattern in YAML_INJECTION_PATTERNS:
            if pattern.search(value):
                errors.append(
                    ValidationError(
                        line=0,
                        column=0,
                        message=f"YAML injection detected at '{path}': pattern '{pattern.pattern}' is not allowed",
                    )
                )
    elif isinstance(value, dict):
        for key, val in value.items():
            key_path = f"{path}.{key}" if path else key
            # Check keys too - they could contain injection
            if isinstance(key, str):
                for pattern in YAML_INJECTION_PATTERNS:
                    if pattern.search(key):
                        errors.append(
                            ValidationError(
                                line=0,
                                column=0,
                                message=f"YAML injection detected in key '{key_path}'",
                            )
                        )
            errors.extend(check_yaml_injection(val, key_path))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            item_path = f"{path}[{i}]"
            errors.extend(check_yaml_injection(item, item_path))

    return errors


def validate_config_security(config: dict[str, Any]) -> ValidationResult:
    """Validate entire pipeline config for security issues.

    Checks for:
    - YAML injection patterns in all string values
    - Transform code security (via validate_transforms)

    Args:
        config: Pipeline configuration dict

    Returns:
        ValidationResult with all security errors
    """
    all_errors: list[ValidationError] = []

    # Check for YAML injection in all values
    yaml_errors = check_yaml_injection(config)
    all_errors.extend(yaml_errors)

    # Check transform code security
    transforms = config.get("transforms")
    if transforms:
        transform_result = validate_transforms(transforms)
        all_errors.extend(transform_result.errors)

    return ValidationResult(
        valid=len(all_errors) == 0,
        errors=all_errors,
    )
