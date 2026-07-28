"""Unit tests — security utilities"""

import pytest
from app.core.security import (
    safe_filename, generate_token, validate_file_extension,
    validate_numeric_range, sanitize_input,
)


class TestSafeFilename:
    def test_returns_string(self):
        result = safe_filename("test_data.csv")
        assert isinstance(result, str)

    def test_contains_original_name(self):
        result = safe_filename("mydata.csv")
        assert "mydata.csv" in result

    def test_empty_filename_uses_default(self):
        result = safe_filename("")
        assert result  # non-empty

    def test_path_traversal_prevented(self):
        result = safe_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result

    def test_uniqueness(self):
        r1 = safe_filename("data.csv")
        r2 = safe_filename("data.csv")
        assert r1 != r2  # random suffix ensures uniqueness


class TestGenerateToken:
    def test_returns_string(self):
        assert isinstance(generate_token(), str)

    def test_min_length(self):
        token = generate_token(48)
        assert len(token) >= 60  # base64 of 48 bytes ≈ 64 chars

    def test_uniqueness(self):
        tokens = {generate_token() for _ in range(100)}
        assert len(tokens) == 100


class TestValidateFileExtension:
    def test_allowed_csv(self):
        assert validate_file_extension("data.csv", {"csv", "xlsx"}) is True

    def test_allowed_xlsx(self):
        assert validate_file_extension("data.xlsx", {"csv", "xlsx"}) is True

    def test_disallowed_exe(self):
        assert validate_file_extension("evil.exe", {"csv", "xlsx"}) is False

    def test_no_extension(self):
        assert validate_file_extension("noextfile", {"csv"}) is False

    def test_case_insensitive(self):
        assert validate_file_extension("DATA.CSV", {"csv"}) is True


class TestValidateNumericRange:
    def test_within_range(self):
        assert validate_numeric_range(50.0, 0, 100) is True

    def test_on_boundary_low(self):
        assert validate_numeric_range(0.0, 0, 100) is True

    def test_on_boundary_high(self):
        assert validate_numeric_range(100.0, 0, 100) is True

    def test_below_range(self):
        assert validate_numeric_range(-1.0, 0, 100) is False

    def test_above_range(self):
        assert validate_numeric_range(101.0, 0, 100) is False

    def test_none_value(self):
        assert validate_numeric_range(None, 0, 100) is False

    def test_string_number(self):
        assert validate_numeric_range("50", 0, 100) is True


class TestSanitizeInput:
    def test_strips_whitespace(self):
        assert sanitize_input("  hello  ") == "hello"

    def test_removes_script_tag_chars(self):
        result = sanitize_input("<script>alert('xss')</script>")
        assert "<" not in result
        assert ">" not in result

    def test_max_length(self):
        long_str = "a" * 2000
        result = sanitize_input(long_str, max_length=100)
        assert len(result) == 100

    def test_none_returns_empty(self):
        assert sanitize_input(None) == ""

    def test_normal_string_unchanged(self):
        result = sanitize_input("Delhi 2024")
        assert "Delhi 2024" == result
