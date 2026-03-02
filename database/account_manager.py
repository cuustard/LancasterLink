"""Simple secure account management using SQLite and bcrypt.

This module provides functions to create and interact with a minimal
user table that stores only an email and a hashed password. Passwords
are hashed with bcrypt using automatic salting, and all SQL queries are
parameterised to avoid injection attacks.

Features covered:

* Email validation and normalization
* Password strength checking with clear error messages
* Database initialization with SQLite
* User registration and login with bcrypt hashing

The module depends only on the Python standard library and the external
package ``bcrypt``.

Usage example::

    from database import account_manager

    account_manager.init_db()
    success, msg = account_manager.register_user("user@example.com", "S3cure!Pass")
    print(success, msg)

"""

import re
import sqlite3
from typing import Tuple

import bcrypt  # make sure bcrypt is installed in your environment


# file-level constant for the database path; change if you want a different
# location or name.  Using a sqlite file in the workspace for demonstration.
DB_PATH = "users.db"


def init_db(db_path: str = DB_PATH) -> None:
    """Create the SQLite file and users table if they don't already exist.

    The table has two columns:

    * ``email`` - TEXT PRIMARY KEY; normalized lowercase addresses are stored.
    * ``password`` - TEXT; bcrypt hashes are stored as UTF-8 strings.
    """

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


# regular expression for a reasonably strict but not overly complex email
# pattern.  It ensures one '@', a domain with at least one dot, and only
# allowed characters in the local part.
_EMAIL_REGEX = re.compile(
    r"^(?P<local>[A-Za-z0-9._%+-]+)@(?P<domain>[A-Za-z0-9.-]+\.[A-Za-z]{2,})$"
)


def validate_email(email: str) -> Tuple[bool, str]:
    """Check that ``email`` adheres to a simple valid format.

    Trims whitespace and converts to lowercase before testing.  Returns a
    pair ``(is_valid, message)`` where ``message`` is empty on success or
    contains a human-readable diagnosis of why the email was rejected.
    """

    if not isinstance(email, str):
        return False, "Email must be a string"

    normalized = email.strip().lower()
    if not normalized:
        return False, "Email cannot be empty"

    match = _EMAIL_REGEX.match(normalized)
    if not match:
        return False, "Email is not in a valid format (e.g. user@example.com)"

    # additional checks could go here (forbidden characters, etc.)
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """Verify that ``password`` meets defined strength requirements.

    Returns ``(True, "")`` on success; on failure the message explains the
    first rule that was violated.
    """

    if not isinstance(password, str):
        return False, "Password must be a string"

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\\\[\]~`'\\-_=+;/]+", password):
        return False, "Password must contain at least one special character"

    # could add additional checks here (e.g., common password blacklist)
    return True, ""


def _normalize_email(email: str) -> str:
    """Helper that trims and lowercases the address for storage/lookup."""
    return email.strip().lower()


def register_user(email: str, password: str, db_path: str = DB_PATH) -> Tuple[bool, str]:
    """Attempt to register a new user.

    Validates the email and password, hashes the password with bcrypt, and
    inserts a new row into the ``users`` table.  If the email already
    exists the function returns ``(False, "Email already registered")``.

    Any other database error is propagated as a generic failure message
    to avoid leaking internal details.
    """

    ok, msg = validate_email(email)
    if not ok:
        return False, msg

    ok, msg = validate_password(password)
    if not ok:
        return False, msg

    normalized = _normalize_email(email)

    # hash the password; bcrypt.gensalt() automatically generates a random
    # salt and embeds it in the resulting hash string.
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (normalized, hashed),
        )
        conn.commit()
        return True, "User registered successfully"
    except sqlite3.IntegrityError:
        # typically triggered by primary key (email) collision
        return False, "Email already registered"
    except Exception:
        return False, "An error occurred while registering the user"
    finally:
        conn.close()


def login_user(email: str, password: str, db_path: str = DB_PATH) -> Tuple[bool, str]:
    """Verify login credentials.

    Normalizes the email, retrieves the stored hash, and uses ``bcrypt`` to
    check the supplied password.  The return tuple indicates success and
    provides an explanatory message.
    """

    normalized = _normalize_email(email)
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE email = ?", (normalized,))
        row = cursor.fetchone()
        if row is None:
            return False, "Invalid email or password"

        stored_hash = row[0].encode("utf-8")
        if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            return True, "Login successful"
        else:
            return False, "Invalid email or password"
    finally:
        conn.close()


# if this module is run as a script, provide a very simple interactive demo
if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("You can now call register_user/login_user from another script.")
