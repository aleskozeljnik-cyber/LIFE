# LIFE — T1a AI Provider Architecture

## Decision

LIFE extraction is provider-switchable. The extraction pipeline calls one internal adapter and never depends directly on a vendor SDK.

```text
LIFE extraction
   |
   v
backend/app/ai.py
   |
   +--> gemini      -> gemini-3.1-flash-lite
   +--> openrouter  -> openrouter/free
   +--> anthropic   -> claude-sonnet-4-5
   |
   +--> unavailable/error -> local rules fallback
```

## Environment

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.1-flash-lite
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openrouter/free
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-5
AI_TIMEOUT_SECONDS=20
```

## Switching to Claude

Only environment configuration changes:

```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-sonnet-4-5
```

No frontend, database, correction, sync, or Today UI changes are required.

## Temporary free AI

Gemini is the default temporary/dev provider. The selected model is `gemini-3.1-flash-lite`.

OpenRouter is available as an optional development provider using `openrouter/free`. Its free model pool is dynamic.

Free providers are intended for development/testing. Before processing sensitive real pilot mail, confirm that the selected provider's data handling is acceptable.

## Candidate pre-filter

Before an email reaches an external model, LIFE applies a cheap deterministic action-marker filter. Calendar events bypass this filter. The filter is intentionally broad and can be improved later; it is not the source of truth.

## Output contract

Every AI provider must produce the same logical fields:

```text
title
summary
due_at
amount
currency
sender
category
priority
classification_reason
confidence
model
```

`classification_reason` is mandatory and human-readable.

## Failure behavior

- Missing provider key: local rule-based fallback.
- Provider timeout/error: local rule-based fallback.
- Invalid model JSON: local rule-based fallback.
- Explicit `null`: no obligation.
- No automatic cross-provider failover for the same email.

## Telemetry

`confidence_logs.model` stores the actual provider model used. This enables later quality and cost comparison without changing the obligation schema.

## External references checked 28 Sep 2026

- Google Gemini pricing: https://ai.google.dev/gemini-api/docs/pricing
- Gemini 3.1 Flash-Lite: https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite
- Gemini structured output: https://ai.google.dev/gemini-api/docs/structured-output
- OpenRouter free models: https://openrouter.ai/collections/free-models
- OpenRouter free router: https://openrouter.ai/openrouter/free