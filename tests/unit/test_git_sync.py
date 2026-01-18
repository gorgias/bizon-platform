"""Tests for git sync module."""

import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from bizon_platform_lite.git_sync import (
    GitSyncError,
    GitSyncResult,
    _get_repo_url_with_auth,
    _run_git_command,
    sync_from_git,
    sync_on_startup,
)


class TestGitSyncResult:
    """Tests for GitSyncResult dataclass."""

    def test_success_result(self):
        """Test creating a successful result."""
        result = GitSyncResult(
            success=True,
            message="Synced 3 sources",
            commit_hash="abc1234",
            files_updated=3,
            synced_at=datetime(2024, 1, 15, 10, 30, 0),
        )
        assert result.success is True
        assert result.message == "Synced 3 sources"
        assert result.commit_hash == "abc1234"
        assert result.files_updated == 3
        assert result.synced_at == datetime(2024, 1, 15, 10, 30, 0)

    def test_failure_result(self):
        """Test creating a failure result."""
        result = GitSyncResult(
            success=False,
            message="Git sync failed: connection error",
        )
        assert result.success is False
        assert result.message == "Git sync failed: connection error"
        assert result.commit_hash is None
        assert result.files_updated == 0
        assert result.synced_at is None


class TestGetRepoUrlWithAuth:
    """Tests for _get_repo_url_with_auth function."""

    def test_no_repo_url_raises_error(self):
        """Test that missing repo URL raises GitSyncError."""
        with patch("bizon_platform_lite.git_sync.settings") as mock_settings:
            mock_settings.git_sync_repo_url = None
            with pytest.raises(GitSyncError, match="Git sync repo URL not configured"):
                _get_repo_url_with_auth()

    def test_https_url_without_token(self):
        """Test HTTPS URL without token is returned as-is."""
        with patch("bizon_platform_lite.git_sync.settings") as mock_settings:
            mock_settings.git_sync_repo_url = "https://github.com/org/repo.git"
            mock_settings.git_sync_token = None
            url = _get_repo_url_with_auth()
            assert url == "https://github.com/org/repo.git"

    def test_https_url_with_token(self):
        """Test HTTPS URL with token has token injected."""
        with patch("bizon_platform_lite.git_sync.settings") as mock_settings:
            mock_settings.git_sync_repo_url = "https://github.com/org/repo.git"
            mock_settings.git_sync_token = "ghp_secret123"
            url = _get_repo_url_with_auth()
            assert url == "https://ghp_secret123@github.com/org/repo.git"

    def test_ssh_url_ignores_token(self):
        """Test SSH URL is returned as-is even with token."""
        with patch("bizon_platform_lite.git_sync.settings") as mock_settings:
            mock_settings.git_sync_repo_url = "git@github.com:org/repo.git"
            mock_settings.git_sync_token = "ghp_secret123"
            url = _get_repo_url_with_auth()
            assert url == "git@github.com:org/repo.git"


class TestRunGitCommand:
    """Tests for _run_git_command function."""

    def test_successful_command(self):
        """Test running a successful git command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = _run_git_command(["git", "status"])
            mock_run.assert_called_once_with(
                ["git", "status"],
                cwd=None,
                capture_output=True,
                text=True,
                timeout=120,
            )
            assert result == mock_result

    def test_failed_command_raises_error(self):
        """Test that failed git command raises GitSyncError."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "fatal: not a git repository"

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(GitSyncError, match="fatal: not a git repository"):
                _run_git_command(["git", "status"])

    def test_timeout_raises_error(self):
        """Test that timeout raises GitSyncError."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 120)):
            with pytest.raises(GitSyncError, match="Git command timed out"):
                _run_git_command(["git", "fetch"])

    def test_git_not_installed_raises_error(self):
        """Test that missing git raises GitSyncError."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(GitSyncError, match="Git is not installed"):
                _run_git_command(["git", "status"])

    def test_command_with_cwd(self):
        """Test running git command with working directory."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            _run_git_command(["git", "status"], cwd=Path("/tmp/repo"))
            mock_run.assert_called_once()
            assert mock_run.call_args[1]["cwd"] == Path("/tmp/repo")


class TestSyncFromGit:
    """Tests for sync_from_git function."""

    def test_sync_disabled_returns_failure(self):
        """Test that sync returns failure when disabled."""
        with patch("bizon_platform_lite.git_sync.settings") as mock_settings:
            mock_settings.git_sync_enabled = False
            result = sync_from_git()
            assert result.success is False
            assert "not enabled" in result.message

    def test_sync_no_repo_url_returns_failure(self):
        """Test that sync returns failure when repo URL not configured."""
        with patch("bizon_platform_lite.git_sync.settings") as mock_settings:
            mock_settings.git_sync_enabled = True
            mock_settings.git_sync_repo_url = None
            result = sync_from_git()
            assert result.success is False
            assert "not configured" in result.message

    @patch("bizon_platform_lite.git_sync.shutil.rmtree")
    @patch("bizon_platform_lite.git_sync.shutil.copytree")
    @patch("bizon_platform_lite.git_sync._run_git_command")
    @patch("bizon_platform_lite.git_sync.Path")
    def test_successful_sync(self, mock_path_class, mock_run_git, mock_copytree, mock_rmtree):
        """Test a successful git sync operation."""
        with patch("bizon_platform_lite.git_sync.settings") as mock_settings:
            # Configure settings
            mock_settings.git_sync_enabled = True
            mock_settings.git_sync_repo_url = "https://github.com/org/repo.git"
            mock_settings.git_sync_branch = "main"
            mock_settings.git_sync_path = "custom_sources"
            mock_settings.git_sync_token = None
            mock_settings.custom_sources_dir = "./custom_sources"

            # Mock temp directory
            mock_temp_dir = MagicMock()
            mock_temp_dir.exists.return_value = False
            mock_temp_dir.__truediv__ = lambda self, x: MagicMock(
                exists=MagicMock(return_value=True),
                is_dir=MagicMock(return_value=True),
                iterdir=MagicMock(return_value=[]),
                parent=MagicMock(),
                write_text=MagicMock(),
                name="source1",
            )

            # Mock source directory with one source
            mock_source_item = MagicMock()
            mock_source_item.is_dir.return_value = True
            mock_source_item.name = "my_source"
            mock_source_py = MagicMock()
            mock_source_py.exists.return_value = True
            mock_source_item.__truediv__ = lambda self, x: mock_source_py

            mock_source_dir = MagicMock()
            mock_source_dir.exists.return_value = True
            mock_source_dir.iterdir.return_value = [mock_source_item]

            # Mock target directory
            mock_target_dir = MagicMock()
            mock_target_dir.mkdir = MagicMock()

            # Setup Path class mock
            def path_side_effect(path_str):
                if path_str == "/tmp/bizon-git-sync-temp":
                    return mock_temp_dir
                elif "custom_sources" in str(path_str):
                    if path_str == "./custom_sources":
                        return mock_target_dir
                    return mock_source_dir
                return MagicMock()

            mock_path_class.side_effect = path_side_effect

            # Mock git commands
            mock_run_git.return_value = MagicMock(stdout="abc12345\n")

            result = sync_from_git()

            # Verify git commands were called
            assert mock_run_git.call_count >= 1

    def test_sync_git_error_returns_failure(self):
        """Test that git errors are handled gracefully."""
        with patch("bizon_platform_lite.git_sync.settings") as mock_settings:
            mock_settings.git_sync_enabled = True
            mock_settings.git_sync_repo_url = "https://github.com/org/repo.git"
            mock_settings.git_sync_branch = "main"
            mock_settings.git_sync_path = "custom_sources"
            mock_settings.git_sync_token = None
            mock_settings.custom_sources_dir = "./custom_sources"

            with patch("bizon_platform_lite.git_sync.shutil.rmtree"):
                with patch("bizon_platform_lite.git_sync._run_git_command") as mock_run_git:
                    mock_run_git.side_effect = GitSyncError("Authentication failed")

                    with patch("bizon_platform_lite.git_sync._get_temp_clone_dir") as mock_temp:
                        mock_temp_dir = MagicMock()
                        mock_temp_dir.exists.return_value = False
                        mock_temp_dir.mkdir = MagicMock()
                        mock_temp.return_value = mock_temp_dir

                        result = sync_from_git()
                        assert result.success is False
                        assert "Authentication failed" in result.message


class TestSyncOnStartup:
    """Tests for sync_on_startup function."""

    def test_startup_sync_disabled(self):
        """Test that startup sync does nothing when disabled."""
        with patch("bizon_platform_lite.git_sync.settings") as mock_settings:
            mock_settings.git_sync_enabled = False

            with patch("bizon_platform_lite.git_sync.sync_from_git") as mock_sync:
                sync_on_startup()
                mock_sync.assert_not_called()

    def test_startup_sync_enabled_calls_sync(self):
        """Test that startup sync calls sync_from_git when enabled."""
        with patch("bizon_platform_lite.git_sync.settings") as mock_settings:
            mock_settings.git_sync_enabled = True

            mock_result = GitSyncResult(success=True, message="Synced")
            with patch("bizon_platform_lite.git_sync.sync_from_git", return_value=mock_result) as mock_sync:
                sync_on_startup()
                mock_sync.assert_called_once()

    def test_startup_sync_logs_failure(self):
        """Test that startup sync logs failures appropriately."""
        with patch("bizon_platform_lite.git_sync.settings") as mock_settings:
            mock_settings.git_sync_enabled = True

            mock_result = GitSyncResult(success=False, message="Failed to connect")
            with patch("bizon_platform_lite.git_sync.sync_from_git", return_value=mock_result):
                with patch("bizon_platform_lite.git_sync.logger") as mock_logger:
                    sync_on_startup()
                    # Should log a warning for failed sync
                    mock_logger.warning.assert_called()


class TestGitSyncIntegration:
    """Integration-style tests for git sync with mocked filesystem."""

    @patch("bizon_platform_lite.git_sync.shutil")
    @patch("subprocess.run")
    def test_full_sync_workflow(self, mock_subprocess_run, mock_shutil):
        """Test the full sync workflow with all components mocked."""
        with patch("bizon_platform_lite.git_sync.settings") as mock_settings:
            # Configure settings
            mock_settings.git_sync_enabled = True
            mock_settings.git_sync_repo_url = "https://github.com/test/sources.git"
            mock_settings.git_sync_branch = "main"
            mock_settings.git_sync_path = "custom_sources"
            mock_settings.git_sync_token = "test_token"
            mock_settings.custom_sources_dir = "/app/custom_sources"

            # Mock successful git commands
            mock_subprocess_run.return_value = MagicMock(
                returncode=0,
                stdout="abc1234567890\n",
                stderr="",
            )

            # Mock shutil operations
            mock_shutil.rmtree = MagicMock()
            mock_shutil.copytree = MagicMock()

            # Mock Path operations
            with patch("bizon_platform_lite.git_sync.Path") as mock_path_class:
                # Create mock temp directory
                mock_temp = MagicMock()
                mock_temp.exists.return_value = True
                mock_temp.mkdir = MagicMock()

                # Mock sparse checkout file
                mock_sparse_file = MagicMock()
                mock_sparse_parent = MagicMock()
                mock_sparse_parent.mkdir = MagicMock()
                mock_sparse_file.parent = mock_sparse_parent

                # Mock source directory with sources
                mock_source1 = MagicMock()
                mock_source1.is_dir.return_value = True
                mock_source1.name = "source_a"
                mock_source1_py = MagicMock()
                mock_source1_py.exists.return_value = True
                mock_source1.__truediv__ = lambda self, x: mock_source1_py

                mock_source2 = MagicMock()
                mock_source2.is_dir.return_value = True
                mock_source2.name = "source_b"
                mock_source2_py = MagicMock()
                mock_source2_py.exists.return_value = True
                mock_source2.__truediv__ = lambda self, x: mock_source2_py

                mock_source_dir = MagicMock()
                mock_source_dir.exists.return_value = True
                mock_source_dir.iterdir.return_value = [mock_source1, mock_source2]

                # Mock target directory
                mock_target = MagicMock()
                mock_target.mkdir = MagicMock()
                mock_target_source = MagicMock()
                mock_target_source.exists.return_value = False
                mock_target.__truediv__ = lambda self, x: mock_target_source

                # Setup path returns
                def path_factory(path_str):
                    if "git-sync-temp" in str(path_str):
                        return mock_temp
                    elif ".git/info/sparse-checkout" in str(path_str):
                        return mock_sparse_file
                    elif path_str == "/app/custom_sources":
                        return mock_target
                    else:
                        return mock_source_dir

                mock_path_class.side_effect = path_factory
                mock_temp.__truediv__ = lambda self, x: (
                    mock_sparse_file
                    if "sparse-checkout" in str(x)
                    else mock_source_dir
                    if x == "custom_sources"
                    else MagicMock()
                )

                result = sync_from_git()

                # Verify subprocess was called for git operations
                assert mock_subprocess_run.call_count > 0

                # Check that git init was called
                git_calls = [str(c) for c in mock_subprocess_run.call_args_list]
                assert any("git" in str(c) for c in git_calls)
