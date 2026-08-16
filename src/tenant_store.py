"""Encrypted, tenant-scoped local store for Closed Beta lifecycle testing."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Iterator

from cryptography.fernet import Fernet, InvalidToken

EMAIL_PATTERN = re.compile(r"^[^@\s]{1,128}@[^@\s]{1,190}$")
PROJECT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class TenantStoreError(RuntimeError):
    """Base error for local tenant storage."""


class TenantAuthenticationError(TenantStoreError):
    """Raised for a generic authentication failure."""


class TenantAccessError(TenantStoreError):
    """Raised without revealing whether another tenant's resource exists."""


@dataclass(frozen=True)
class TenantStoreSettings:
    enabled: bool = False
    database_path: Path = Path(".private/localizeflow_tenants.sqlite3")
    master_key: str = ""
    session_ttl_minutes: int = 30

    @classmethod
    def from_env(cls, *, project_root: Path | None = None) -> TenantStoreSettings:
        raw_path = Path(
            os.getenv(
                "LOCALIZEFLOW_TENANT_DATABASE_PATH",
                ".private/localizeflow_tenants.sqlite3",
            )
        )
        if project_root is not None and not raw_path.is_absolute():
            raw_path = project_root / raw_path
        return cls(
            enabled=os.getenv("LOCALIZEFLOW_TENANT_STORE_ENABLED", "false").lower()
            == "true",
            database_path=raw_path,
            master_key=os.getenv("LOCALIZEFLOW_TENANT_MASTER_KEY", ""),
            session_ttl_minutes=int(
                os.getenv("LOCALIZEFLOW_TENANT_SESSION_TTL_MINUTES", "30")
            ),
        )

    def validate(self) -> None:
        if not 5 <= self.session_ttl_minutes <= 120:
            raise TenantStoreError("Session lifetime must be between 5 and 120 minutes.")
        if self.enabled:
            try:
                Fernet(self.master_key.encode("ascii"))
            except (ValueError, TypeError) as error:
                raise TenantStoreError("Tenant master key must be a valid Fernet key.") from error


@dataclass(frozen=True)
class TenantSession:
    token: str
    account_id: str
    expires_at: str


class EncryptedTenantStore:
    """SQLite metadata with encrypted tenant content and server-side authorization."""

    def __init__(
        self,
        settings: TenantStoreSettings,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        settings.validate()
        if not settings.enabled:
            raise TenantStoreError("Tenant store is disabled.")
        self.settings = settings
        self.clock = clock or (lambda: datetime.now(UTC))
        self._fernet = Fernet(settings.master_key.encode("ascii"))
        self._lookup_key = hashlib.sha256(
            base64.urlsafe_b64decode(settings.master_key.encode("ascii"))
            + b"localizeflow-tenant-lookup-v1"
        ).digest()
        self._sessions: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        settings.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def _now(self) -> datetime:
        moment = self.clock()
        return moment if moment.tzinfo else moment.replace(tzinfo=UTC)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.settings.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    account_id TEXT PRIMARY KEY,
                    email_lookup TEXT NOT NULL UNIQUE,
                    email_encrypted BLOB NOT NULL,
                    password_salt BLOB NOT NULL,
                    password_hash BLOB NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS projects (
                    account_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    name_encrypted BLOB NOT NULL,
                    payload_encrypted BLOB,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (account_id, project_id),
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    account_id TEXT,
                    project_id TEXT,
                    action TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    occurred_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_audit_account_time
                    ON audit_events(account_id, occurred_at);
                """
            )

    def _encrypt_json(self, value: Any) -> bytes:
        return self._fernet.encrypt(
            json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )

    def _decrypt_json(self, value: bytes) -> Any:
        try:
            return json.loads(self._fernet.decrypt(value).decode("utf-8"))
        except (InvalidToken, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise TenantStoreError("Encrypted tenant data could not be decrypted.") from error

    def _email_lookup(self, email: str) -> str:
        return hmac.new(
            self._lookup_key, email.casefold().strip().encode("utf-8"), hashlib.sha256
        ).hexdigest()

    @staticmethod
    def _normalize_email(email: str) -> str:
        normalized = email.casefold().strip()
        if not EMAIL_PATTERN.fullmatch(normalized) or len(normalized) > 320:
            raise TenantStoreError("Email address is invalid.")
        return normalized

    @staticmethod
    def _password_hash(password: str, salt: bytes) -> bytes:
        return hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32
        )

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < 12 or len(password) > 200:
            raise TenantStoreError("Password must contain 12 to 200 characters.")

    def _audit(
        self,
        connection: sqlite3.Connection,
        *,
        account_id: str | None,
        project_id: str | None,
        action: str,
        outcome: str,
    ) -> None:
        connection.execute(
            "INSERT INTO audit_events VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), account_id, project_id, action, outcome, self._now().isoformat()),
        )

    def create_account(self, *, email: str, password: str) -> str:
        normalized = self._normalize_email(email)
        self._validate_password(password)
        account_id = str(uuid.uuid4())
        salt = secrets.token_bytes(16)
        with self._lock, self._connect() as connection:
            try:
                connection.execute(
                    "INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        account_id,
                        self._email_lookup(normalized),
                        self._encrypt_json(normalized),
                        salt,
                        self._password_hash(password, salt),
                        self._now().isoformat(),
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise TenantStoreError("Account cannot be created.") from error
            self._audit(
                connection,
                account_id=account_id,
                project_id=None,
                action="account_create",
                outcome="success",
            )
        return account_id

    def authenticate(self, *, email: str, password: str) -> TenantSession:
        try:
            normalized = self._normalize_email(email)
        except TenantStoreError as error:
            raise TenantAuthenticationError("Invalid credentials.") from error
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT account_id, password_salt, password_hash FROM accounts "
                "WHERE email_lookup = ?",
                (self._email_lookup(normalized),),
            ).fetchone()
            candidate = self._password_hash(password, row["password_salt"]) if row else b""
            if row is None or not hmac.compare_digest(candidate, row["password_hash"]):
                self._audit(
                    connection,
                    account_id=None,
                    project_id=None,
                    action="login",
                    outcome="denied",
                )
                raise TenantAuthenticationError("Invalid credentials.")
            token = secrets.token_urlsafe(32)
            expires = self._now() + timedelta(minutes=self.settings.session_ttl_minutes)
            self._sessions[hashlib.sha256(token.encode()).hexdigest()] = {
                "account_id": row["account_id"],
                "expires_at": expires,
            }
            self._audit(
                connection,
                account_id=row["account_id"],
                project_id=None,
                action="login",
                outcome="success",
            )
            return TenantSession(token, row["account_id"], expires.isoformat())

    def _require_session(self, token: str) -> str:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with self._lock:
            session = self._sessions.get(token_hash)
            if session is None or session["expires_at"] <= self._now():
                self._sessions.pop(token_hash, None)
                raise TenantAuthenticationError("Session is invalid or expired.")
            return str(session["account_id"])

    def logout(self, token: str) -> None:
        with self._lock:
            self._sessions.pop(hashlib.sha256(token.encode()).hexdigest(), None)

    def create_project(self, token: str, *, project_id: str, name: str) -> None:
        account_id = self._require_session(token)
        if not PROJECT_PATTERN.fullmatch(project_id) or not name.strip() or len(name) > 120:
            raise TenantStoreError("Project ID or name is invalid.")
        now = self._now().isoformat()
        with self._lock, self._connect() as connection:
            try:
                connection.execute(
                    "INSERT INTO projects VALUES (?, ?, ?, NULL, ?, ?)",
                    (account_id, project_id, self._encrypt_json(name.strip()), now, now),
                )
            except sqlite3.IntegrityError as error:
                raise TenantStoreError("Project cannot be created.") from error
            self._audit(
                connection,
                account_id=account_id,
                project_id=project_id,
                action="project_create",
                outcome="success",
            )

    def list_projects(self, token: str) -> list[dict[str, Any]]:
        account_id = self._require_session(token)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT project_id, name_encrypted, created_at, updated_at FROM projects "
                "WHERE account_id = ? ORDER BY created_at",
                (account_id,),
            ).fetchall()
        return [
            {
                "project_id": row["project_id"],
                "name": self._decrypt_json(row["name_encrypted"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def _project_row(
        self, connection: sqlite3.Connection, account_id: str, project_id: str
    ) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM projects WHERE account_id = ? AND project_id = ?",
            (account_id, project_id),
        ).fetchone()
        if row is None:
            self._audit(
                connection,
                account_id=account_id,
                project_id=project_id,
                action="project_access",
                outcome="denied",
            )
            connection.commit()
            raise TenantAccessError("Project access denied.")
        return row

    def save_project(self, token: str, *, project_id: str, payload: dict[str, Any]) -> None:
        account_id = self._require_session(token)
        encrypted = self._encrypt_json(payload)
        with self._lock, self._connect() as connection:
            self._project_row(connection, account_id, project_id)
            connection.execute(
                "UPDATE projects SET payload_encrypted = ?, updated_at = ? "
                "WHERE account_id = ? AND project_id = ?",
                (encrypted, self._now().isoformat(), account_id, project_id),
            )
            self._audit(
                connection,
                account_id=account_id,
                project_id=project_id,
                action="project_write",
                outcome="success",
            )

    def load_project(self, token: str, *, project_id: str) -> dict[str, Any] | None:
        account_id = self._require_session(token)
        with self._connect() as connection:
            row = self._project_row(connection, account_id, project_id)
        return self._decrypt_json(row["payload_encrypted"]) if row["payload_encrypted"] else None

    def export_project(self, token: str, *, project_id: str) -> dict[str, Any]:
        account_id = self._require_session(token)
        with self._connect() as connection:
            row = self._project_row(connection, account_id, project_id)
            self._audit(
                connection,
                account_id=account_id,
                project_id=project_id,
                action="project_export",
                outcome="success",
            )
        return {
            "project_id": project_id,
            "name": self._decrypt_json(row["name_encrypted"]),
            "payload": (
                self._decrypt_json(row["payload_encrypted"])
                if row["payload_encrypted"]
                else None
            ),
            "exported_at": self._now().isoformat(),
        }

    def delete_project(self, token: str, *, project_id: str) -> dict[str, str]:
        account_id = self._require_session(token)
        deleted_at = self._now().isoformat()
        with self._lock, self._connect() as connection:
            self._project_row(connection, account_id, project_id)
            connection.execute(
                "DELETE FROM projects WHERE account_id = ? AND project_id = ?",
                (account_id, project_id),
            )
            self._audit(
                connection,
                account_id=account_id,
                project_id=project_id,
                action="project_delete",
                outcome="success",
            )
        return {"project_id": project_id, "deleted_at": deleted_at, "status": "deleted"}

    def export_account(self, token: str) -> dict[str, Any]:
        account_id = self._require_session(token)
        with self._connect() as connection:
            account = connection.execute(
                "SELECT email_encrypted, created_at FROM accounts WHERE account_id = ?",
                (account_id,),
            ).fetchone()
            if account is None:
                raise TenantAuthenticationError("Account is unavailable.")
        return {
            "account_id": account_id,
            "email": self._decrypt_json(account["email_encrypted"]),
            "created_at": account["created_at"],
            "projects": [
                self.export_project(token, project_id=item["project_id"])
                for item in self.list_projects(token)
            ],
            "exported_at": self._now().isoformat(),
        }

    def delete_account(self, token: str, *, password: str) -> dict[str, str]:
        account_id = self._require_session(token)
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT password_salt, password_hash FROM accounts WHERE account_id = ?",
                (account_id,),
            ).fetchone()
            if row is None or not hmac.compare_digest(
                self._password_hash(password, row["password_salt"]), row["password_hash"]
            ):
                raise TenantAuthenticationError("Invalid credentials.")
            connection.execute("DELETE FROM accounts WHERE account_id = ?", (account_id,))
            self._audit(
                connection,
                account_id=account_id,
                project_id=None,
                action="account_delete",
                outcome="success",
            )
        with self._lock:
            for token_hash, session in list(self._sessions.items()):
                if session["account_id"] == account_id:
                    self._sessions.pop(token_hash, None)
        return {
            "account_id": account_id,
            "deleted_at": self._now().isoformat(),
            "status": "deleted",
        }

    def audit_events(self, token: str) -> list[dict[str, Any]]:
        account_id = self._require_session(token)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT project_id, action, outcome, occurred_at FROM audit_events "
                "WHERE account_id = ? ORDER BY occurred_at",
                (account_id,),
            ).fetchall()
        return [dict(row) for row in rows]
