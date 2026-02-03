"""Tests for security validators."""

import pytest

from bizon_platform.api.routes.pipelines import validate_bizon_config
from tests.fixtures.configs import (
    MALICIOUS_TRANSFORM_EVAL,
    MALICIOUS_TRANSFORM_IMPORT_OS,
    VALID_DUMMY_CONFIG,
    VALID_WITH_TRANSFORMS,
    YAML_INJECTION_PYTHON_OBJECT,
)


class TestValidateBizonConfig:
    """Tests for validate_bizon_config function."""

    def test_valid_config_passes(self):
        """Valid config should pass validation."""
        # Should not raise
        validate_bizon_config(VALID_DUMMY_CONFIG)

    def test_valid_config_with_transforms_passes(self):
        """Valid config with safe transforms should pass."""
        # Should not raise
        validate_bizon_config(VALID_WITH_TRANSFORMS)

    def test_malicious_import_os_rejected(self):
        """Config with import os transform should be rejected."""
        with pytest.raises(ValueError) as exc_info:
            validate_bizon_config(MALICIOUS_TRANSFORM_IMPORT_OS)
        assert "Security validation failed" in str(exc_info.value)

    def test_malicious_eval_rejected(self):
        """Config with eval() in transform should be rejected."""
        with pytest.raises(ValueError) as exc_info:
            validate_bizon_config(MALICIOUS_TRANSFORM_EVAL)
        assert "Security validation failed" in str(exc_info.value)

    def test_yaml_injection_rejected(self):
        """Config with YAML injection patterns should be rejected."""
        with pytest.raises(ValueError) as exc_info:
            validate_bizon_config(YAML_INJECTION_PYTHON_OBJECT)
        assert "Security validation failed" in str(exc_info.value)

    def test_missing_source_rejected(self):
        """Config without source should be rejected."""
        config = {
            "name": "test",
            "destination": {"name": "logger", "config": {}},
        }
        with pytest.raises(ValueError):
            validate_bizon_config(config)

    def test_missing_destination_rejected(self):
        """Config without destination should be rejected."""
        config = {
            "name": "test",
            "source": {"name": "dummy", "stream": "test"},
        }
        with pytest.raises(ValueError):
            validate_bizon_config(config)

    def test_blocked_imports_in_transforms(self):
        """Various blocked imports should be rejected."""
        blocked_imports = [
            "subprocess",
            "socket",
            "shutil",
            "pathlib",
            "sys",
            "__builtins__",
        ]

        for module in blocked_imports:
            config = {
                **VALID_DUMMY_CONFIG,
                "transforms": [
                    {"label": "evil", "python": f"import {module}; return record"}
                ],
            }
            with pytest.raises(ValueError) as exc_info:
                validate_bizon_config(config)
            assert "Security validation failed" in str(exc_info.value)

    def test_blocked_builtins_in_transforms(self):
        """Blocked builtin functions should be rejected."""
        blocked_builtins = ["exec", "eval", "compile", "__import__", "open"]

        for builtin in blocked_builtins:
            config = {
                **VALID_DUMMY_CONFIG,
                "transforms": [
                    {"label": "evil", "python": f"{builtin}('test'); return record"}
                ],
            }
            with pytest.raises(ValueError) as exc_info:
                validate_bizon_config(config)
            assert "Security validation failed" in str(exc_info.value)
