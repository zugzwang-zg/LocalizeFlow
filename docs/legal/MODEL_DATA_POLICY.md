# Model data policy

Status: active project policy for development and release decisions

Last reviewed: 2026-08-15

## Default rule: no training use

LocalizeFlow does not authorize uploaded material, prompts, model inputs,
outputs, or human edits to be used to train or improve a third-party model.
Any model-backed deployment must select and configure a relay and model service
whose applicable terms, settings, and contract support that rule.

This is a product requirement, not a claim that an unidentified provider
already satisfies it. If the maintainer cannot verify the actual provider's
training use, human-review access, retention, regions, subprocessors, and
deletion route, the model-backed path must remain disabled for user data.

## Current repository state

- The public Web Demo does not call a model API.
- Local development calls are limited to synthetic test material.
- A local relay URL or credential does not identify the relay's legal entity,
  subprocessors, regions, or data terms.
- No hosted free trial is currently approved to accept uploads.

## Data minimization

When a model path is approved, send only confirmed facts required for the
selected SKU, market, and content type. Exclude original uploads, source files,
unknown values, unrelated SKUs, credentials, personal data, and full project
history. Persist operational metadata rather than raw prompt or response bodies
in logs by default.

## Change control

The maintainer must repeat the provider disclosure review before changing the
relay, model provider, model, API route, hosting/data region, retention setting,
training setting, or subprocessor chain. An undisclosed change pauses user-data
processing until the notice and consent flow are updated.
