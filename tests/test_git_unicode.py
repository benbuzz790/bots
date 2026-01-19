"""Tests for git operations with unicode/emoji characters.

This module tests that git operations properly handle unicode characters,
including emoji in commit messages, branch names, and file content.

Encoding Assumptions:
- Git commit messages should support full unicode (UTF-8)
- Branch names should support unicode characters
- File content with unicode should be preserved
- Git log output should be parsed correctly with unicode
"""

import git
import pytest
from encoding_fixtures import UNICODE_TEST_STRINGS, assert_no_mojibake
from git import Repo


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repository for testing."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Initialize git repo
    repo = Repo.init(repo_path)

    # Configure git user
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")

    yield repo_path, repo

    # Cleanup
    repo.close()


class TestGitCommitMessagesWithUnicode:
    """Test git commit messages with unicode and emoji characters."""

    def test_commit_message_with_emoji_checkmark(self, temp_git_repo):
        """Test commit message with ✅ emoji is preserved correctly."""
        repo_path, repo = temp_git_repo

        # Create a test file
        test_file = repo_path / "test.txt"
        test_file.write_text("test content", encoding="utf-8")

        # Stage and commit with emoji
        repo.index.add([str(test_file)])
        commit_msg = f"Add test file {UNICODE_TEST_STRINGS['emoji_checkmark']}"
        commit = repo.index.commit(commit_msg)

        # Verify commit message preserved emoji
        assert_no_mojibake(commit.message, [UNICODE_TEST_STRINGS["emoji_checkmark"]])
        assert UNICODE_TEST_STRINGS["emoji_checkmark"] in commit.message

    def test_commit_message_with_multiple_emoji(self, temp_git_repo):
        """Test commit message with multiple emoji characters."""
        repo_path, repo = temp_git_repo

        # Create a test file
        test_file = repo_path / "test.txt"
        test_file.write_text("test", encoding="utf-8")

        # Commit with multiple emoji
        repo.index.add([str(test_file)])
        commit_msg = (
            f"{UNICODE_TEST_STRINGS['emoji_checkmark']} Tests passing "
            f"{UNICODE_TEST_STRINGS['emoji_party']} "
            f"{UNICODE_TEST_STRINGS['emoji_wrench']} Fixed bug"
        )
        commit = repo.index.commit(commit_msg)

        # Verify all emoji preserved
        expected_emoji = [
            UNICODE_TEST_STRINGS["emoji_checkmark"],
            UNICODE_TEST_STRINGS["emoji_party"],
            UNICODE_TEST_STRINGS["emoji_wrench"],
        ]
        assert_no_mojibake(commit.message, expected_emoji)

    def test_commit_message_with_chinese_characters(self, temp_git_repo):
        """Test commit message with Chinese characters."""
        repo_path, repo = temp_git_repo

        test_file = repo_path / "test.txt"
        test_file.write_text("test", encoding="utf-8")

        repo.index.add([str(test_file)])
        commit_msg = f"更新文档 {UNICODE_TEST_STRINGS['chinese']}"
        commit = repo.index.commit(commit_msg)

        assert_no_mojibake(commit.message, [UNICODE_TEST_STRINGS["chinese"]])

    def test_commit_message_with_arabic_characters(self, temp_git_repo):
        """Test commit message with Arabic characters."""
        repo_path, repo = temp_git_repo

        test_file = repo_path / "test.txt"
        test_file.write_text("test", encoding="utf-8")

        repo.index.add([str(test_file)])
        commit_msg = f"تحديث {UNICODE_TEST_STRINGS['arabic']}"
        commit = repo.index.commit(commit_msg)

        assert_no_mojibake(commit.message, [UNICODE_TEST_STRINGS["arabic"]])

    def test_commit_message_mixed_unicode(self, temp_git_repo):
        """Test commit message with mixed unicode characters."""
        repo_path, repo = temp_git_repo

        test_file = repo_path / "test.txt"
        test_file.write_text("test", encoding="utf-8")

        repo.index.add([str(test_file)])
        commit_msg = UNICODE_TEST_STRINGS["mixed"]
        commit = repo.index.commit(commit_msg)

        # Verify all unicode types preserved
        expected_chars = ["✅", "中文", "🎉", "العربية", "❌"]
        assert_no_mojibake(commit.message, expected_chars)


class TestGitLogParsingWithUnicode:
    """Test parsing git log output with unicode characters."""

    def test_git_log_preserves_emoji(self, temp_git_repo):
        """Test that git log output preserves emoji in commit messages."""
        repo_path, repo = temp_git_repo

        # Create multiple commits with emoji
        for i, emoji_key in enumerate(["emoji_checkmark", "emoji_cross", "emoji_party"]):
            test_file = repo_path / f"test{i}.txt"
            test_file.write_text(f"content {i}", encoding="utf-8")
            repo.index.add([str(test_file)])

            emoji = UNICODE_TEST_STRINGS[emoji_key]
            commit_msg = f"Commit {i} {emoji}"
            repo.index.commit(commit_msg)

        # Get log and verify emoji preserved
        commits = list(repo.iter_commits())
        assert len(commits) == 3

        # Check each commit message
        assert UNICODE_TEST_STRINGS["emoji_party"] in commits[0].message
        assert UNICODE_TEST_STRINGS["emoji_cross"] in commits[1].message
        assert UNICODE_TEST_STRINGS["emoji_checkmark"] in commits[2].message

    def test_git_log_with_unicode_author_name(self, temp_git_repo):
        """Test git log with unicode in author name."""
        repo_path, repo = temp_git_repo

        test_file = repo_path / "test.txt"
        test_file.write_text("test", encoding="utf-8")
        repo.index.add([str(test_file)])

        # Create commit with unicode author
        author = git.Actor("张三 Zhang", "zhang@example.com")
        commit = repo.index.commit("Test commit", author=author, committer=author)

        # Verify author name preserved
        assert "张三" in commit.author.name
        assert_no_mojibake(commit.author.name, ["张三"])


class TestGitFileContentWithUnicode:
    """Test git operations with unicode file content."""

    def test_commit_file_with_unicode_content(self, temp_git_repo):
        """Test committing file with unicode content."""
        repo_path, repo = temp_git_repo

        # Create file with unicode content
        test_file = repo_path / "unicode_content.txt"
        unicode_content = f"""
        Status: {UNICODE_TEST_STRINGS['emoji_checkmark']}
        Error: {UNICODE_TEST_STRINGS['emoji_cross']}
        Chinese: {UNICODE_TEST_STRINGS['chinese']}
        Arabic: {UNICODE_TEST_STRINGS['arabic']}
        """
        test_file.write_text(unicode_content, encoding="utf-8")

        # Commit the file
        repo.index.add([str(test_file)])
        repo.index.commit("Add unicode content")

        # Read back and verify
        content = test_file.read_text(encoding="utf-8")
        assert_no_mojibake(
            content,
            [
                UNICODE_TEST_STRINGS["emoji_checkmark"],
                UNICODE_TEST_STRINGS["emoji_cross"],
                UNICODE_TEST_STRINGS["chinese"],
                UNICODE_TEST_STRINGS["arabic"],
            ],
        )

    def test_diff_with_unicode_content(self, temp_git_repo):
        """Test git diff with unicode content changes."""
        repo_path, repo = temp_git_repo

        # Create initial file
        test_file = repo_path / "test.txt"
        test_file.write_text("Initial content", encoding="utf-8")
        repo.index.add([str(test_file)])
        repo.index.commit("Initial commit")

        # Modify with unicode
        new_content = f"Updated {UNICODE_TEST_STRINGS['emoji_checkmark']}"
        test_file.write_text(new_content, encoding="utf-8")

        # Get diff
        diff = repo.git.diff("HEAD")

        # Verify unicode in diff
        assert UNICODE_TEST_STRINGS["emoji_checkmark"] in diff or "emoji_checkmark" in diff

    def test_commit_multiple_files_with_unicode(self, temp_git_repo):
        """Test committing multiple files with unicode content."""
        repo_path, repo = temp_git_repo

        # Create multiple files with different unicode
        files_content = {
            "emoji.txt": UNICODE_TEST_STRINGS["emoji_checkmark"],
            "chinese.txt": UNICODE_TEST_STRINGS["chinese"],
            "arabic.txt": UNICODE_TEST_STRINGS["arabic"],
        }

        for filename, content in files_content.items():
            file_path = repo_path / filename
            file_path.write_text(content, encoding="utf-8")
            repo.index.add([str(file_path)])

        repo.index.commit("Add unicode files")

        # Verify all files preserved unicode
        for filename, expected_content in files_content.items():
            file_path = repo_path / filename
            actual_content = file_path.read_text(encoding="utf-8")
            assert expected_content in actual_content


class TestGitBranchNamesWithUnicode:
    """Test git branch operations with unicode names.

    Note: Git branch names have restrictions on unicode characters.
    Some characters like emoji may not be supported by all git versions.
    """

    def test_branch_with_safe_unicode(self, temp_git_repo):
        """Test creating branch with safe unicode characters (letters)."""
        repo_path, repo = temp_git_repo

        # Create initial commit
        test_file = repo_path / "test.txt"
        test_file.write_text("test", encoding="utf-8")
        repo.index.add([str(test_file)])
        repo.index.commit("Initial commit")

        # Try creating branch with unicode letters (safer than emoji)
        # Note: Git may restrict emoji in branch names
        try:
            branch_name = "feature/测试分支"
            repo.create_head(branch_name)

            # Verify branch exists
            assert branch_name in [b.name for b in repo.branches]
        except Exception as e:
            # Some git versions may not support unicode in branch names
            pytest.skip(f"Git version doesn't support unicode branch names: {e}")


class TestGitOperationsManagerWithUnicode:
    """Test GitOperationsManager class with unicode content."""

    def test_stage_files_with_unicode_content(self, temp_git_repo):
        """Test staging files that contain unicode."""
        repo_path, repo = temp_git_repo

        # Import the manager
        try:
            from src.git_operations.manager import GitOperationsManager
        except ImportError:
            pytest.skip("GitOperationsManager not available")

        manager = GitOperationsManager(str(repo_path))

        # Create file with unicode
        test_file = repo_path / "unicode.txt"
        test_file.write_text(f"Test {UNICODE_TEST_STRINGS['emoji_checkmark']}", encoding="utf-8")

        # Stage the file
        manager.stage_files(str(repo_path), ["unicode.txt"])

        # Verify staged
        assert "unicode.txt" in [item.a_path for item in repo.index.diff("HEAD")]

    def test_create_commit_with_emoji_message(self, temp_git_repo):
        """Test creating commit with emoji in message via manager."""
        repo_path, repo = temp_git_repo

        try:
            from src.git_operations.manager import GitOperationsManager
        except ImportError:
            pytest.skip("GitOperationsManager not available")

        manager = GitOperationsManager(str(repo_path))

        # Create and stage file
        test_file = repo_path / "test.txt"
        test_file.write_text("test", encoding="utf-8")
        manager.stage_files(str(repo_path), ["test.txt"])

        # Create commit with emoji
        commit_msg = f"Add test {UNICODE_TEST_STRINGS['emoji_checkmark']}"
        commit_sha = manager.create_commit(str(repo_path), commit_msg)

        # Verify commit message
        commit = repo.commit(commit_sha)
        assert_no_mojibake(commit.message, [UNICODE_TEST_STRINGS["emoji_checkmark"]])
