from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography.fernet import Fernet

from src.tenant_store import (
    EncryptedTenantStore,
    TenantAccessError,
    TenantAuthenticationError,
    TenantStoreSettings,
)


class TenantStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = [datetime(2026, 8, 15, 9, 0, tzinfo=UTC)]
        self.database = Path(self.temp.name) / "tenants.sqlite3"
        self.store = EncryptedTenantStore(
            TenantStoreSettings(
                enabled=True,
                database_path=self.database,
                master_key=Fernet.generate_key().decode("ascii"),
                session_ttl_minutes=30,
            ),
            clock=lambda: self.now[0],
        )

    def account(self, email: str, password: str = "correct horse battery") -> str:
        self.store.create_account(email=email, password=password)
        return self.store.authenticate(email=email, password=password).token

    def test_account_login_and_generic_invalid_credentials(self) -> None:
        self.store.create_account(
            email="Owner@Example.invalid", password="correct horse battery"
        )
        session = self.store.authenticate(
            email="owner@example.invalid", password="correct horse battery"
        )
        self.assertTrue(session.token)
        with self.assertRaisesRegex(TenantAuthenticationError, "Invalid credentials"):
            self.store.authenticate(
                email="owner@example.invalid", password="wrong password value"
            )
        with self.assertRaisesRegex(TenantAuthenticationError, "Invalid credentials"):
            self.store.authenticate(
                email="missing@example.invalid", password="wrong password value"
            )

    def test_cross_tenant_read_write_export_and_delete_are_denied(self) -> None:
        owner = self.account("owner@example.invalid")
        other = self.account("other@example.invalid")
        self.store.create_project(owner, project_id="owner-project", name="Secret brand")
        self.store.save_project(
            owner,
            project_id="owner-project",
            payload={"facts": [{"value": "confidential formula"}]},
        )
        operations = (
            lambda: self.store.load_project(other, project_id="owner-project"),
            lambda: self.store.save_project(
                other, project_id="owner-project", payload={"overwrite": True}
            ),
            lambda: self.store.export_project(other, project_id="owner-project"),
            lambda: self.store.delete_project(other, project_id="owner-project"),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaisesRegex(
                TenantAccessError, "Project access denied"
            ):
                operation()
        self.assertEqual(
            self.store.load_project(owner, project_id="owner-project")["facts"][0]["value"],
            "confidential formula",
        )
        denied_events = [
            event
            for event in self.store.audit_events(other)
            if event["action"] == "project_access" and event["outcome"] == "denied"
        ]
        self.assertEqual(len(denied_events), 4)
        self.assertNotIn("confidential formula", repr(denied_events))

    def test_tenants_may_reuse_project_ids_without_collision(self) -> None:
        first = self.account("first@example.invalid")
        second = self.account("second@example.invalid")
        self.store.create_project(first, project_id="project-001", name="First")
        self.store.create_project(second, project_id="project-001", name="Second")
        self.store.save_project(first, project_id="project-001", payload={"owner": "first"})
        self.store.save_project(second, project_id="project-001", payload={"owner": "second"})
        self.assertEqual(
            self.store.load_project(first, project_id="project-001"), {"owner": "first"}
        )
        self.assertEqual(
            self.store.load_project(second, project_id="project-001"), {"owner": "second"}
        )

    def test_email_project_name_and_payload_are_encrypted_at_rest(self) -> None:
        token = self.account("private-owner@example.invalid")
        self.store.create_project(token, project_id="opaque-001", name="Confidential Brand")
        self.store.save_project(
            token,
            project_id="opaque-001",
            payload={"secret": "unreleased formula and launch copy"},
        )
        database_bytes = self.database.read_bytes()
        for plaintext in (
            b"private-owner@example.invalid",
            b"Confidential Brand",
            b"unreleased formula and launch copy",
        ):
            self.assertNotIn(plaintext, database_bytes)

    def test_project_and_account_exports_are_tenant_scoped(self) -> None:
        token = self.account("export@example.invalid")
        self.store.create_project(token, project_id="project-001", name="Export project")
        self.store.save_project(token, project_id="project-001", payload={"facts": [1, 2]})
        project = self.store.export_project(token, project_id="project-001")
        account = self.store.export_account(token)
        self.assertEqual(project["payload"], {"facts": [1, 2]})
        self.assertEqual(account["email"], "export@example.invalid")
        self.assertEqual([item["project_id"] for item in account["projects"]], ["project-001"])

    def test_project_delete_removes_content_and_retains_body_free_audit(self) -> None:
        token = self.account("delete-project@example.invalid")
        self.store.create_project(token, project_id="project-001", name="Delete me")
        self.store.save_project(
            token, project_id="project-001", payload={"secret": "must disappear"}
        )
        result = self.store.delete_project(token, project_id="project-001")
        self.assertEqual(result["status"], "deleted")
        with self.assertRaises(TenantAccessError):
            self.store.load_project(token, project_id="project-001")
        audit_text = repr(self.store.audit_events(token))
        self.assertIn("project_delete", audit_text)
        self.assertNotIn("must disappear", audit_text)

    def test_account_delete_cascades_projects_and_revokes_sessions(self) -> None:
        password = "correct horse battery"
        token = self.account("delete-account@example.invalid", password)
        self.store.create_project(token, project_id="project-001", name="Delete account")
        result = self.store.delete_account(token, password=password)
        self.assertEqual(result["status"], "deleted")
        with self.assertRaises(TenantAuthenticationError):
            self.store.list_projects(token)
        connection = sqlite3.connect(self.database)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM accounts").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0], 0)
            delete_audit = connection.execute(
                "SELECT action, outcome FROM audit_events WHERE action='account_delete'"
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual(delete_audit, ("account_delete", "success"))

    def test_expired_session_cannot_access_projects(self) -> None:
        token = self.account("expiry@example.invalid")
        self.now[0] += timedelta(minutes=31)
        with self.assertRaisesRegex(TenantAuthenticationError, "expired"):
            self.store.list_projects(token)


if __name__ == "__main__":
    unittest.main()
