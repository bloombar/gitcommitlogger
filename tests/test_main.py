import json
import os
import re
from datetime import datetime, timezone

import pytest

from gitcommitlogger.__main__ import fix_date, get_commit_data, get_commit_ids, get_exclusions

TESTS_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.join(os.path.dirname(TESTS_DIR), "src", "gitcommitlogger")


class TestFixDate:
    def test_returns_mm_dd_yyyy_hh_mm_format(self):
        result = fix_date("1677887316")
        assert re.fullmatch(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}", result)

    def test_unix_timestamp_converts_to_eastern_time(self):
        import pytz
        ts = 1677887316
        expected = (
            datetime.utcfromtimestamp(ts)
            .replace(tzinfo=pytz.utc)
            .astimezone(pytz.timezone("America/New_York"))
            .strftime("%m/%d/%Y %H:%M")
        )
        assert fix_date(str(ts)) == expected

    def test_iso_format_accepted(self):
        result = fix_date("2023-03-03T21:48:36+00:00")
        assert re.fullmatch(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}", result)

    def test_unix_and_iso_yield_same_result_for_same_moment(self):
        ts = 1677887316
        iso = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        assert fix_date(str(ts)) == fix_date(iso)


class TestGetCommitData:

    @pytest.fixture
    def commit1_data(self):
        with open(os.path.join(TESTS_DIR, "test_commit1.txt")) as f:
            return get_commit_data(f.read().strip())

    @pytest.fixture
    def commit2_data(self):
        with open(os.path.join(TESTS_DIR, "test_commit2.txt")) as f:
            return get_commit_data(f.read().strip())

    @pytest.fixture
    def commit3_data(self):
        with open(os.path.join(TESTS_DIR, "test_commit3.txt")) as f:
            return get_commit_data(f.read().strip())

    @pytest.fixture
    def commit4_data(self):
        """Non-merge commit with paragraph-style multi-line message (Subject + blank + Body)."""
        with open(os.path.join(TESTS_DIR, "test_commit4.txt")) as f:
            return get_commit_data(f.read().strip())

    @pytest.fixture
    def commit5_data(self):
        """Non-merge commit with consecutive-line multi-line message (no blank line separator)."""
        with open(os.path.join(TESTS_DIR, "test_commit5.txt")) as f:
            return get_commit_data(f.read().strip())

    # --- simple commit (test_commit1) ---

    def test_simple_id(self, commit1_data):
        assert commit1_data["id"] == "e32032cb2c89e6a33f0b6ff56667422c5229a518"

    def test_simple_author_name(self, commit1_data):
        assert commit1_data["author_name"] == "Bishnu Dev"

    def test_simple_author_email(self, commit1_data):
        assert commit1_data["author_email"] == "61447680+bordernone@users.noreply.github.com"

    def test_simple_message(self, commit1_data):
        assert commit1_data["message"] == "added login, updated navbar"

    def test_simple_files(self, commit1_data):
        assert commit1_data["files"] == "2"

    def test_simple_additions(self, commit1_data):
        assert commit1_data["additions"] == "120"

    def test_simple_deletions(self, commit1_data):
        assert commit1_data["deletions"] == "22"

    def test_simple_date_format(self, commit1_data):
        assert re.fullmatch(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}", commit1_data["date"])

    # --- merge commit with multi-line message (test_commit2) ---

    def test_merge_multiline_id(self, commit2_data):
        assert commit2_data["id"] == "42df000869022d1b784f04a9aa6cacf69a5093c8"

    def test_merge_multiline_author_name(self, commit2_data):
        assert commit2_data["author_name"] == "Yewon Song"

    def test_merge_multiline_author_email(self, commit2_data):
        assert commit2_data["author_email"] == "98556497+sywu430@users.noreply.github.com"

    def test_merge_multiline_message_is_first_line(self, commit2_data):
        assert commit2_data["message"].startswith(
            "Merge pull request #24 from agiledev-students-spring-2023"
        )

    def test_merge_multiline_message_excludes_later_lines(self, commit2_data):
        assert "Added login screen" not in commit2_data["message"]
        assert "Foo bar baz" not in commit2_data["message"]

    def test_merge_multiline_files(self, commit2_data):
        assert commit2_data["files"] == "2"

    def test_merge_multiline_additions(self, commit2_data):
        assert commit2_data["additions"] == "120"

    def test_merge_multiline_deletions(self, commit2_data):
        assert commit2_data["deletions"] == "22"

    # --- merge commit with single-line message (test_commit3) ---

    def test_merge_singleline_id(self, commit3_data):
        assert commit3_data["id"] == "42df000869022d1b784f04a9aa6cacf69a5093c8"

    def test_merge_singleline_message(self, commit3_data):
        assert commit3_data["message"].startswith(
            "Merge pull request #24 from agiledev-students-spring-2023"
        )

    def test_merge_singleline_files(self, commit3_data):
        assert commit3_data["files"] == "2"

    def test_merge_singleline_additions(self, commit3_data):
        assert commit3_data["additions"] == "120"

    def test_merge_singleline_deletions(self, commit3_data):
        assert commit3_data["deletions"] == "22"

    # --- non-merge commit with paragraph-style multi-line message (test_commit4) ---

    def test_paragraph_multiline_id(self, commit4_data):
        assert commit4_data["id"] == "7a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b"

    def test_paragraph_multiline_author_name(self, commit4_data):
        assert commit4_data["author_name"] == "Alice Dev"

    def test_paragraph_multiline_author_email(self, commit4_data):
        assert commit4_data["author_email"] == "alice@example.com"

    def test_paragraph_multiline_message_is_subject_line(self, commit4_data):
        assert commit4_data["message"] == "Add user authentication feature"

    def test_paragraph_multiline_message_excludes_body(self, commit4_data):
        assert "JWT" not in commit4_data["message"]
        assert "bcrypt" not in commit4_data["message"]

    def test_paragraph_multiline_files(self, commit4_data):
        assert commit4_data["files"] == "5"

    def test_paragraph_multiline_additions(self, commit4_data):
        assert commit4_data["additions"] == "120"

    def test_paragraph_multiline_deletions(self, commit4_data):
        assert commit4_data["deletions"] == "8"

    def test_paragraph_multiline_date_format(self, commit4_data):
        assert re.fullmatch(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}", commit4_data["date"])

    # --- non-merge commit with consecutive-line multi-line message (test_commit5) ---

    def test_consecutive_multiline_id(self, commit5_data):
        assert commit5_data["id"] == "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b"

    def test_consecutive_multiline_author_name(self, commit5_data):
        assert commit5_data["author_name"] == "Bob Dev"

    def test_consecutive_multiline_author_email(self, commit5_data):
        assert commit5_data["author_email"] == "bob@example.com"

    def test_consecutive_multiline_message_is_first_line(self, commit5_data):
        assert commit5_data["message"] == "Fix null pointer exception in UserService"

    def test_consecutive_multiline_message_excludes_second_line(self, commit5_data):
        assert "Occurs when" not in commit5_data["message"]

    def test_consecutive_multiline_files(self, commit5_data):
        assert commit5_data["files"] == "2"

    def test_consecutive_multiline_additions(self, commit5_data):
        assert commit5_data["additions"] == "15"

    def test_consecutive_multiline_deletions(self, commit5_data):
        assert commit5_data["deletions"] == "3"

    def test_consecutive_multiline_date_format(self, commit5_data):
        assert re.fullmatch(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}", commit5_data["date"])

    # --- edge cases ---

    def test_empty_input_returns_empty_dict(self):
        assert get_commit_data("") == {}

    def test_malformed_input_returns_empty_dict(self):
        assert get_commit_data("not a git commit") == {}


class TestGetCommitIds:

    def test_extracts_ids_from_valid_json(self, tmp_path):
        commits = [{"id": "abc123"}, {"id": "def456"}, {"id": "789xyz"}]
        f = tmp_path / "commits.json"
        f.write_text(json.dumps(commits))
        assert get_commit_ids(str(f)) == ["abc123", "def456", "789xyz"]

    def test_skips_entries_without_id_field(self, tmp_path):
        commits = [{"id": "abc123"}, {"sha": "no_id_here"}, {"id": "def456"}]
        f = tmp_path / "commits.json"
        f.write_text(json.dumps(commits))
        assert get_commit_ids(str(f)) == ["abc123", "def456"]

    def test_empty_array_returns_empty_list(self, tmp_path):
        f = tmp_path / "commits.json"
        f.write_text("[]")
        assert get_commit_ids(str(f)) == []

    def test_example_commits_file(self):
        path = os.path.join(SRC_DIR, "example_commits.json")
        ids = get_commit_ids(path)
        assert len(ids) == 1
        assert ids[0] == "8a126457bbd3a3e390058b6053bf700d404d6501"


class TestGetExclusions:

    def test_returns_list_of_strings(self):
        path = os.path.join(SRC_DIR, ".logsignore")
        result = get_exclusions(path)
        assert isinstance(result, list)
        assert all(isinstance(item, str) for item in result)

    def test_logsignore_contains_known_patterns(self):
        path = os.path.join(SRC_DIR, ".logsignore")
        result = get_exclusions(path)
        assert any("lock" in p.lower() for p in result)

    def test_empty_file_returns_empty_list(self, tmp_path):
        f = tmp_path / ".logsignore"
        f.write_text("")
        assert get_exclusions(str(f)) == []

    def test_single_pattern_returned(self, tmp_path):
        f = tmp_path / ".logsignore"
        f.write_text("*.jpg\n")
        assert "*.jpg" in get_exclusions(str(f))

    def test_multiple_patterns_all_returned(self, tmp_path):
        f = tmp_path / ".logsignore"
        f.write_text("*.jpg\n*.png\n*.gif\n")
        result = get_exclusions(str(f))
        assert "*.jpg" in result
        assert "*.png" in result
        assert "*.gif" in result
