# LocalizeFlow Public Demo Privacy Notice

Last updated: 2026-08-15

## Scope

This notice applies only to the repository's public deterministic Web Demo. The
Demo uses frozen fictional examples, runs in the visitor's browser, does not
call a model API, and does not provide a hosted account or production service.

The optional local Closed Beta code path is described separately below. A
future hosted free trial will require a deployment-specific privacy notice
before it is activated; the draft in `docs/legal/` is not an active policy.

## Public Demo data

The Demo does not automatically transmit product selections, generated
samples, edits, feedback, or usage events to the project maintainer. It does
not use third-party analytics, advertising cookies, or browser fingerprinting.

If local experience metrics are enabled, the Demo stores at most 100 events for
no more than 30 days in the visitor's browser `localStorage`. Each event may
contain an anonymous run identifier, event name, timestamp, elapsed time,
market, content type, and workflow step. It does not contain content bodies,
names, email addresses, IP addresses, or API credentials. Visitors can disable,
export, or delete these metrics in the Demo.

## Feedback and third-party links

Feedback leaves the browser only when a visitor deliberately opens and submits
a GitHub issue. The proposed issue body excludes edited content by default. A
separately downloaded local feedback file contains full edited content only
after an explicit opt-in; downloading it does not send it to the project.

GitHub and other external sites apply their own privacy terms when a visitor
follows a link. Do not put personal, confidential, customer, or production data
in the Demo, GitHub issue forms, or public repository discussions.

## Optional local Closed Beta mode

When explicitly enabled on a user's own computer, the local Closed Beta mode
can store test-account metadata and project content in an encrypted SQLite
database under `.private/`. The user controls that local installation and can
export or delete the local project from the application. Local records remain
until the user deletes them; this repository does not operate a remote backup
or receive those records by itself.

This local mechanism is not a privacy notice for a hosted service. Do not use
real personal, confidential, customer, or production data until the applicable
organization has approved a deployment-specific notice, retention schedule,
processor disclosure, request channel, and backup deletion process.

## Requests and contact

For browser metrics, use the Demo's export and clear controls. For a local
Closed Beta project, use the in-app export and deletion controls. Do not submit
private data in a public GitHub issue. Security reports should use the private
channel described in `SECURITY.md`.

No hosted privacy-request channel is active because no hosted trial is active.
A dedicated privacy contact and verified request workflow are release blockers
for any future hosted trial.

## Changes

Material changes to what the public Demo collects or transmits require this
notice and the in-product disclosure to be updated before the change is
released.
