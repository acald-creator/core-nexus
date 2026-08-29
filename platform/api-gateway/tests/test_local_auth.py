"""Tests for local login allowlist."""
from __future__ import annotations

from src.routes.auth import _check_local_credentials, _local_users_map


def test_local_users_map_parses():
    assert _local_users_map("alice:secret,bob:other") == {
        "alice": "secret",
        "bob": "other",
    }
    assert _local_users_map("") == {}
    assert _local_users_map(None) == {}


def test_lab_default_accepts_any_nonempty():
    assert _check_local_credentials("anyone", "goes", None) is True
    assert _check_local_credentials("", "x", None) is False
    assert _check_local_credentials("x", "", None) is False


def test_allowlist_enforced():
    users = "analyst:changeme,admin:s3cret"
    assert _check_local_credentials("analyst", "changeme", users) is True
    assert _check_local_credentials("analyst", "wrong", users) is False
    assert _check_local_credentials("nobody", "changeme", users) is False
