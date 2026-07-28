"""Unit tests — input validators"""

import pytest
from app.utils.validators import validate_email, validate_password, validate_username


class TestEmailValidator:
    def test_valid_email(self):
        assert validate_email("user@example.com") is None

    def test_valid_email_subdomains(self):
        assert validate_email("user@mail.example.co.in") is None

    def test_empty_email(self):
        assert validate_email("") is not None

    def test_missing_at(self):
        assert validate_email("userexample.com") is not None

    def test_missing_domain(self):
        assert validate_email("user@") is not None

    def test_none_email(self):
        assert validate_email(None) is not None

    def test_whitespace_stripped(self):
        assert validate_email("  user@example.com  ") is None


class TestPasswordValidator:
    def test_strong_password(self):
        assert validate_password("StrongPass@1") is None

    def test_too_short(self):
        assert validate_password("Sh@1") is not None

    def test_no_uppercase(self):
        assert validate_password("weakpass@1") is not None

    def test_no_lowercase(self):
        assert validate_password("WEAKPASS@1") is not None

    def test_no_digit(self):
        assert validate_password("WeakPass@!") is not None

    def test_no_special_char(self):
        assert validate_password("WeakPass1A") is not None

    def test_too_long(self):
        assert validate_password("A" * 130 + "@1a") is not None

    def test_empty(self):
        assert validate_password("") is not None


class TestUsernameValidator:
    def test_valid_username(self):
        assert validate_username("john_doe") is None

    def test_valid_with_hyphen(self):
        assert validate_username("john-doe-99") is None

    def test_too_short(self):
        assert validate_username("ab") is not None

    def test_too_long(self):
        assert validate_username("a" * 51) is not None

    def test_special_chars(self):
        assert validate_username("john@doe") is not None

    def test_spaces(self):
        assert validate_username("john doe") is not None

    def test_empty(self):
        assert validate_username("") is not None
