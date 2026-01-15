"""Reusable pipeline configurations for tests."""

# Valid configurations
VALID_DUMMY_CONFIG = {
    "name": "test-dummy-to-logger",
    "source": {
        "name": "dummy",
        "stream": "creatures",
        "authentication": {"type": "api_key", "params": {"token": "test_key"}},
    },
    "destination": {
        "name": "logger",
        "config": {"dummy": "dummy"},
    },
}

VALID_WITH_TRANSFORMS = {
    "name": "test-with-transforms",
    "source": {
        "name": "dummy",
        "stream": "creatures",
        "authentication": {"type": "api_key", "params": {"token": "test_key"}},
    },
    "destination": {
        "name": "logger",
        "config": {"dummy": "dummy"},
    },
    "transforms": [
        {
            "label": "uppercase_name",
            "python": "record['name'] = record.get('name', '').upper(); return record",
        },
    ],
}

# Invalid configurations
INVALID_MISSING_SOURCE = {
    "name": "test-missing-source",
    "destination": {
        "name": "logger",
        "config": {"dummy": "dummy"},
    },
}

INVALID_MISSING_DESTINATION = {
    "name": "test-missing-destination",
    "source": {
        "name": "dummy",
        "stream": "creatures",
        "authentication": {"type": "api_key", "params": {"token": "test_key"}},
    },
}

# Malicious transform configurations
MALICIOUS_TRANSFORM_IMPORT_OS = {
    "name": "malicious-import-os",
    "source": {
        "name": "dummy",
        "stream": "creatures",
        "authentication": {"type": "api_key", "params": {"token": "test_key"}},
    },
    "destination": {
        "name": "logger",
        "config": {"dummy": "dummy"},
    },
    "transforms": [
        {"label": "evil", "python": "import os; os.system('rm -rf /')"},
    ],
}

MALICIOUS_TRANSFORM_EVAL = {
    "name": "malicious-eval",
    "source": {
        "name": "dummy",
        "stream": "creatures",
        "authentication": {"type": "api_key", "params": {"token": "test_key"}},
    },
    "destination": {
        "name": "logger",
        "config": {"dummy": "dummy"},
    },
    "transforms": [
        {"label": "evil", "python": "eval('malicious_code')"},
    ],
}

# YAML injection configurations
YAML_INJECTION_PYTHON_OBJECT = {
    "name": "yaml-injection",
    "source": {
        "name": "!!python/object/apply:os.system",
        "stream": "creatures",
    },
    "destination": {
        "name": "logger",
        "config": {"dummy": "dummy"},
    },
}

# Saved connector sample configs
SAMPLE_SOURCE_CONFIG = {
    "name": "hubspot",
    "stream": "contacts",
    "authentication": {"type": "api_key", "params": {"token": "test_token"}},
}

SAMPLE_DESTINATION_CONFIG = {
    "project_id": "test-project",
    "dataset": "test_dataset",
    "credentials_base64": "dGVzdA==",
}
