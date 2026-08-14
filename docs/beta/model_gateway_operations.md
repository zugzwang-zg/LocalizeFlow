# Closed Beta model gateway operations

The gateway is disabled by default. Configuration is supplied through local or hosted secrets, never committed files.

## Required configuration

- Explicit enable switch.
- HTTPS relay base URL and explicit API style (`openai_chat_completions` or `anthropic_messages`).
- API key stored as a secret.
- Exact model name.
- Input and output prices per million tokens.
- Per-request cost ceiling.
- Timeout, retry count, maximum output tokens, and JSON Schema support flag.

For the owner's current relay, the read-only setup check confirmed the base URL
`https://api.aijws.com`. The existing Claude credential is restricted to
`/v1/messages`, so its API style must be `anthropic_messages`. Keep the exact
model name, pricing, and key in the local `.env`; do not infer them from a key
group name.

## First live-call checklist

1. Copy `.env.example` to `.env` and add the relay base URL, an existing API key,
   exact model name, and published token prices.
2. Leave `LOCALIZEFLOW_BETA_MODEL_ENABLED=false` while checking the remaining
   limits, then change it to `true` only for the controlled smoke run.
3. Use the repository's synthetic SKU only. Do not upload participant data in
   the first call.
4. Confirm the provider transfer in the application immediately before calling.
5. Verify schema success, post-generation gates, idempotency/cache behavior,
   token counts, latency, cost, and that no raw body appears in logs.
6. Return the enable switch to `false` after the run until participant onboarding
   and the hosted tenant-isolation preflight are approved.

The 2026-08-14 first live attempt confirmed that the Claude credential rejects
`/v1/chat/completions` with HTTP 403. The gateway then added Anthropic Messages
support. The follow-up received retryable provider errors and no response body;
therefore the live smoke gate remains pending and no successful generation is
recorded.

## Request policy

- Send only confirmed A/B evidence facts needed for the selected SKU, market, and content type.
- Exclude sources, original uploads, unknown values, unrelated SKUs, and full project history.
- Include blocked facts only as compact constraints.
- Treat all fact values as untrusted data and test prompt-injection fixtures.
- Use an idempotency key based on project, SKU, request digest, and model.

## Response policy

- Validate JSON and the repository schema.
- Recheck immutable fields, claim fact IDs, prohibited claims, packaging, content structure, and human-review status.
- A schema-valid output is not exportable until post-generation gates and human review pass.
- Do not retry malformed responses after a provider response has been received; record the error without the response body.

## Audit record

Record run ID, project ID, SKU, market, content type, relay host, model, prompt/schema/rule versions, input fact IDs, request/response digests, token counts, latency, cost estimate, attempts, and status. Raw upload and prompt/output bodies are not written to persistent logs by default.

## Emergency controls

Disable the enable switch for a data-flow change, cross-project access, cost anomaly, repeated schema failure, model-provider incident, or critical contradiction passing the export gate.
