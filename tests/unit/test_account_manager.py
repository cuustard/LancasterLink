import os
import tempfile

import pytest

from database import account_manager


@pytest.fixture
def temp_db_path(tmp_path):
    # create a temporary database file for each test
    return str(tmp_path / "test_users.db")


def test_email_validation():
    ok, msg = account_manager.validate_email("user@example.com")
    assert ok
    assert msg == ""

    ok, msg = account_manager.validate_email("bad-email")
    assert not ok
    assert "valid format" in msg

    ok, msg = account_manager.validate_email(" ")
    assert not ok
    assert "cannot be empty" in msg


def test_password_validation():
    ok, msg = account_manager.validate_password("Short1!")
    assert not ok
    assert "at least 8" in msg

    ok, msg = account_manager.validate_password("alllowercase1!")
    assert not ok
    assert "uppercase" in msg

    ok, msg = account_manager.validate_password("ALLUPPERCASE1!")
    assert not ok
    assert "lowercase" in msg

    ok, msg = account_manager.validate_password("NoNumber!")
    assert not ok
    assert "one number" in msg

    ok, msg = account_manager.validate_password("NoSpecial1")
    assert not ok
    assert "special character" in msg

    ok, msg = account_manager.validate_password("Good1!Pass")
    assert ok


def test_register_and_login(temp_db_path):
    account_manager.init_db(temp_db_path)
    # register succeeds
    success, msg = account_manager.register_user("New@Example.com ", "Good1!Pass", db_path=temp_db_path)
    assert success
    assert "registered" in msg

    # duplicate register fails gracefully
    success, msg = account_manager.register_user("new@example.com", "Good1!Pass", db_path=temp_db_path)
    assert not success
    assert "already registered" in msg

    # login with wrong password
    success, msg = account_manager.login_user("new@example.com", "badpass", db_path=temp_db_path)
    assert not success
    assert "Invalid" in msg

    # login with correct password
    success, msg = account_manager.login_user("  NEW@example.COM", "Good1!Pass", db_path=temp_db_path)
    assert success
    assert "successful" in msg
