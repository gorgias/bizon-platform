"""Tests for git sync webhook functionality."""

import hashlib
import hmac
import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from bizon_platform.api.routes.custom_sources import (
    _verify_github_signature,
    _verify_gitlab_signature,
)


class TestVerifyGitHubSignature:
    """Tests for GitHub signature verification."""

    def test_valid_signature(self):
        """Test that valid GitHub signature is accepted."""
        secret = "my-webhook-secret"
        payload = b'{"ref": "refs/heads/main"}'

        # Compute the expected signature
        expected = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
        signature = f"sha256={expected}"

        assert _verify_github_signature(payload, signature, secret) is True

    def test_invalid_signature(self):
        """Test that invalid GitHub signature is rejected."""
        secret = "my-webhook-secret"
        payload = b'{"ref": "refs/heads/main"}'
        signature = "sha256=invalid_signature_here"

        assert _verify_github_signature(payload, signature, secret) is False

    def test_missing_signature(self):
        """Test that missing signature is rejected."""
        payload = b'{"ref": "refs/heads/main"}'

        assert _verify_github_signature(payload, None, "secret") is False

    def test_wrong_prefix(self):
        """Test that wrong signature prefix is rejected."""
        payload = b'{"ref": "refs/heads/main"}'
        signature = "sha1=some_signature"

        assert _verify_github_signature(payload, signature, "secret") is False

    def test_tampered_payload(self):
        """Test that tampered payload fails verification."""
        secret = "my-webhook-secret"
        original_payload = b'{"ref": "refs/heads/main"}'
        tampered_payload = b'{"ref": "refs/heads/malicious"}'

        # Compute signature with original payload
        expected = hmac.new(
            secret.encode("utf-8"),
            original_payload,
            hashlib.sha256,
        ).hexdigest()
        signature = f"sha256={expected}"

        # Verify with tampered payload should fail
        assert _verify_github_signature(tampered_payload, signature, secret) is False


class TestVerifyGitLabSignature:
    """Tests for GitLab token verification."""

    def test_valid_token(self):
        """Test that valid GitLab token is accepted."""
        secret = "my-webhook-secret"
        payload = b'{"ref": "refs/heads/main"}'

        assert _verify_gitlab_signature(payload, secret, secret) is True

    def test_invalid_token(self):
        """Test that invalid GitLab token is rejected."""
        secret = "my-webhook-secret"
        payload = b'{"ref": "refs/heads/main"}'

        assert _verify_gitlab_signature(payload, "wrong-token", secret) is False

    def test_missing_token(self):
        """Test that missing token is rejected."""
        payload = b'{"ref": "refs/heads/main"}'

        assert _verify_gitlab_signature(payload, None, "secret") is False


class TestGitSyncWebhookEndpoint:
    """Tests for the webhook endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client with mocked settings."""
        from bizon_platform.api.app import app

        return TestClient(app)

    @pytest.fixture
    def webhook_secret(self):
        """Webhook secret for tests."""
        return "test-webhook-secret-12345"

    def _compute_github_signature(self, payload: bytes, secret: str) -> str:
        """Compute GitHub webhook signature."""
        signature = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"

    def test_webhook_not_configured(self, client):
        """Test webhook returns error when secret not configured."""
        with patch("bizon_platform.api.routes.custom_sources.settings") as mock_settings:
            mock_settings.git_sync_webhook_secret = None
            mock_settings.git_sync_enabled = True

            response = client.post(
                "/api/custom-sources/git-sync/webhook",
                json={"ref": "refs/heads/main"},
                headers={"X-Hub-Signature-256": "sha256=test"},
            )

            assert response.status_code == 400
            assert "not configured" in response.json()["detail"]

    def test_webhook_git_sync_disabled(self, client, webhook_secret):
        """Test webhook returns error when git sync is disabled."""
        with patch("bizon_platform.api.routes.custom_sources.settings") as mock_settings:
            mock_settings.git_sync_webhook_secret = webhook_secret
            mock_settings.git_sync_enabled = False

            payload = json.dumps({"ref": "refs/heads/main"}).encode()
            signature = self._compute_github_signature(payload, webhook_secret)

            response = client.post(
                "/api/custom-sources/git-sync/webhook",
                content=payload,
                headers={
                    "X-Hub-Signature-256": signature,
                    "X-GitHub-Event": "push",
                    "Content-Type": "application/json",
                },
            )

            assert response.status_code == 400
            assert "not enabled" in response.json()["detail"]

    def test_webhook_invalid_github_signature(self, client, webhook_secret):
        """Test webhook rejects invalid GitHub signature."""
        with patch("bizon_platform.api.routes.custom_sources.settings") as mock_settings:
            mock_settings.git_sync_webhook_secret = webhook_secret
            mock_settings.git_sync_enabled = True

            response = client.post(
                "/api/custom-sources/git-sync/webhook",
                json={"ref": "refs/heads/main"},
                headers={
                    "X-Hub-Signature-256": "sha256=invalid",
                    "X-GitHub-Event": "push",
                },
            )

            assert response.status_code == 401
            assert "Invalid signature" in response.json()["detail"]

    def test_webhook_invalid_gitlab_token(self, client, webhook_secret):
        """Test webhook rejects invalid GitLab token."""
        with patch("bizon_platform.api.routes.custom_sources.settings") as mock_settings:
            mock_settings.git_sync_webhook_secret = webhook_secret
            mock_settings.git_sync_enabled = True

            response = client.post(
                "/api/custom-sources/git-sync/webhook",
                json={"ref": "refs/heads/main"},
                headers={
                    "X-Gitlab-Token": "wrong-token",
                    "X-Gitlab-Event": "Push Hook",
                },
            )

            assert response.status_code == 401
            assert "Invalid token" in response.json()["detail"]

    def test_webhook_unknown_source(self, client, webhook_secret):
        """Test webhook rejects requests without GitHub/GitLab headers."""
        with patch("bizon_platform.api.routes.custom_sources.settings") as mock_settings:
            mock_settings.git_sync_webhook_secret = webhook_secret
            mock_settings.git_sync_enabled = True

            response = client.post(
                "/api/custom-sources/git-sync/webhook",
                json={"ref": "refs/heads/main"},
            )

            assert response.status_code == 400
            assert "Unknown webhook source" in response.json()["detail"]

    def test_webhook_skips_wrong_branch(self, client, webhook_secret):
        """Test webhook skips pushes to non-configured branches."""
        with patch("bizon_platform.api.routes.custom_sources.settings") as mock_settings:
            mock_settings.git_sync_webhook_secret = webhook_secret
            mock_settings.git_sync_enabled = True
            mock_settings.git_sync_branch = "main"

            payload = json.dumps({"ref": "refs/heads/develop"}).encode()
            signature = self._compute_github_signature(payload, webhook_secret)

            response = client.post(
                "/api/custom-sources/git-sync/webhook",
                content=payload,
                headers={
                    "X-Hub-Signature-256": signature,
                    "X-GitHub-Event": "push",
                    "Content-Type": "application/json",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "skipped"
            assert "develop" in data["message"]
            assert "main" in data["message"]

    def test_webhook_triggers_sync_github(self, client, webhook_secret):
        """Test webhook triggers sync for correct branch (GitHub)."""
        with patch("bizon_platform.api.routes.custom_sources.settings") as mock_settings:
            mock_settings.git_sync_webhook_secret = webhook_secret
            mock_settings.git_sync_enabled = True
            mock_settings.git_sync_branch = "main"

            payload = json.dumps({"ref": "refs/heads/main"}).encode()
            signature = self._compute_github_signature(payload, webhook_secret)

            with patch("bizon_platform.api.routes.custom_sources._run_sync_background"):
                response = client.post(
                    "/api/custom-sources/git-sync/webhook",
                    content=payload,
                    headers={
                        "X-Hub-Signature-256": signature,
                        "X-GitHub-Event": "push",
                        "Content-Type": "application/json",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "sync_triggered"
                assert "main" in data["message"]

    def test_webhook_triggers_sync_gitlab(self, client, webhook_secret):
        """Test webhook triggers sync for correct branch (GitLab)."""
        with patch("bizon_platform.api.routes.custom_sources.settings") as mock_settings:
            mock_settings.git_sync_webhook_secret = webhook_secret
            mock_settings.git_sync_enabled = True
            mock_settings.git_sync_branch = "main"

            payload = json.dumps({"ref": "refs/heads/main"}).encode()

            with patch("bizon_platform.api.routes.custom_sources._run_sync_background"):
                response = client.post(
                    "/api/custom-sources/git-sync/webhook",
                    content=payload,
                    headers={
                        "X-Gitlab-Token": webhook_secret,
                        "X-Gitlab-Event": "Push Hook",
                        "Content-Type": "application/json",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "sync_triggered"

    def test_webhook_invalid_json(self, client, webhook_secret):
        """Test webhook handles invalid JSON payload."""
        with patch("bizon_platform.api.routes.custom_sources.settings") as mock_settings:
            mock_settings.git_sync_webhook_secret = webhook_secret
            mock_settings.git_sync_enabled = True

            payload = b"not valid json"
            signature = self._compute_github_signature(payload, webhook_secret)

            response = client.post(
                "/api/custom-sources/git-sync/webhook",
                content=payload,
                headers={
                    "X-Hub-Signature-256": signature,
                    "X-GitHub-Event": "push",
                    "Content-Type": "application/json",
                },
            )

            assert response.status_code == 400
            assert "Invalid JSON" in response.json()["detail"]


class TestGitSyncStatusWebhookConfigured:
    """Tests for webhook_configured field in status endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from bizon_platform.api.app import app

        return TestClient(app)

    def test_status_shows_webhook_not_configured(self, client):
        """Test status shows webhook_configured=false when not set."""
        with patch("bizon_platform.api.routes.custom_sources.settings") as mock_settings:
            mock_settings.git_sync_enabled = True
            mock_settings.git_sync_repo_url = "https://github.com/org/repo.git"
            mock_settings.git_sync_branch = "main"
            mock_settings.git_sync_path = "custom_sources"
            mock_settings.git_sync_webhook_secret = None

            response = client.get("/api/custom-sources/git-sync/status")

            assert response.status_code == 200
            data = response.json()
            assert data["webhook_configured"] is False

    def test_status_shows_webhook_configured(self, client):
        """Test status shows webhook_configured=true when set."""
        with patch("bizon_platform.api.routes.custom_sources.settings") as mock_settings:
            mock_settings.git_sync_enabled = True
            mock_settings.git_sync_repo_url = "https://github.com/org/repo.git"
            mock_settings.git_sync_branch = "main"
            mock_settings.git_sync_path = "custom_sources"
            mock_settings.git_sync_webhook_secret = "my-secret"

            response = client.get("/api/custom-sources/git-sync/status")

            assert response.status_code == 200
            data = response.json()
            assert data["webhook_configured"] is True
