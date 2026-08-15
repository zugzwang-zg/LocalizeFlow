# Local tenant isolation and encrypted storage

This document describes the D2 local reference implementation. It is not a
hosted identity system and does not authorize collection of real user data.

## Security model

The Closed Beta UI remains closed unless the encrypted tenant store is enabled.
A user must create or authenticate a local account before upload, generation,
project export, or deletion controls are shown.

- Passwords are hashed with `hashlib.scrypt` using a unique 16-byte salt.
- Login responses do not disclose whether an email address exists.
- Sessions use 256-bit random bearer tokens, stored in memory only as SHA-256
  token digests, and expire after 30 minutes by default.
- Account email, project name, imported facts, model output, and review payloads
  are encrypted with Fernet before being written to SQLite.
- Email lookup uses HMAC-SHA256 derived from the encryption key; plaintext email
  is not used as a database index.
- Every project query includes the authenticated `account_id` and `project_id`.
  Missing and cross-tenant resources return the same access-denied response.
- Audit events contain action, outcome, opaque account/project IDs, and time.
  They never contain uploaded facts, output bodies, email, or project names.

SQLite retains opaque account and project identifiers plus timestamps in
plaintext metadata. Project IDs must not contain a brand name, email, SKU, or
other sensitive value.

## Data lifecycle

An authenticated account can:

1. create multiple isolated projects;
2. export one project as decrypted JSON;
3. export the account and all owned projects;
4. permanently delete a project;
5. permanently delete the account and all projects after password re-entry.

Primary-store deletion is immediate. A content-free audit event remains after
project or account deletion. The local implementation does not create backups;
therefore local deletion is irreversible and local recovery is unavailable.

A hosted Beta must define encrypted backups before launch. The provisional
policy is daily backups, a tested restore procedure, and removal of deleted
tenant content from backups within seven calendar days. This is a policy target,
not a capability of the current repository.

## Key and transport boundaries

The Fernet key is loaded from `.env`, which is ignored by Git. Rotating the key
without decrypting and re-encrypting existing records makes the database
unreadable. A hosted version must use a managed KMS/secret manager, separate keys
per environment, documented rotation, and restricted operator access.

Fernet protects selected fields at rest; it does not encrypt network traffic.
The local Streamlit app is bound to localhost for development. A hosted version
must terminate HTTPS at a trusted edge, enforce secure cookies/session handling,
and test HSTS and proxy-header configuration before accepting real data.

## Production blockers

- no email verification, invitation allowlist, MFA, password reset, or login
  brute-force protection;
- in-memory sessions are not shared across instances and are revoked on restart;
- no managed database row-level security or multi-instance authorization test;
- no external KMS, automated rotation, encrypted backup, or restore rehearsal;
- no hosted HTTPS and secure-cookie evidence;
- no privacy request workflow or legal retention approval.

The automated suite proves local cross-tenant read, write, export, and delete
denial. It does not prove the security of a future hosting platform.
