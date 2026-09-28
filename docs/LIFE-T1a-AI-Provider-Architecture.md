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

Cloudflare Workers AI is the default privacy-safe free/dev provider for T1a real-data testing. The selected model is `@cf/zai-org/glm-4.7-flash`. Gemini remains available for development/synthetic data, but real user data is blocked until the Gemini Paid Tier has been independently verified.

OpenRouter is available as an optional development provider using `openrouter/free`. Its free model pool is dynamic and its real-data privacy status must be independently verified before use.

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
## Real-data privacy gate

LIFE exposes ai_data_usage from GET /health and permits real Google source reads only when both conditions are true:

- an AI provider is configured;
- ai_data_usage == not_used_for_training.

The gate runs before the Google access token is used for Gmail or Calendar reads. Unsafe or unverified providers return HTTP 503 and do not start source synchronization.

Current policy:

| Provider | Real-data policy |
|---|---|
| Cloudflare Workers AI | allowed on documented no-training policy when configured |
| Anthropic commercial API | allowed when commercial API privacy status is verified |
| Gemini Free | blocked |
| Gemini Paid | allowed only after Paid Tier verification |
| OpenRouter | blocked until provider/model data handling is verified |
| Unknown | blocked |

Cloudflare states that Workers AI Customer Content is not used to train AI models or improve Cloudflare/third-party services without explicit consent. Workers AI currently has a Free plan allocation of 10,000 Neurons/day. JSON mode is supported by a defined subset of models; the selected GLM model is used with strict JSON prompting and LIFE validation, with local fallback on invalid output.

## Sources

- Cloudflare Workers AI data usage: https://developers.cloudflare.com/workers-ai/platform/data-usage/
- Cloudflare Workers AI pricing/free allocation: https://developers.cloudflare.com/workers-ai/platform/pricing/
- Cloudflare Workers AI JSON mode: https://developers.cloudflare.com/workers-ai/features/json-mode/
- Google Gemini pricing/data use: https://ai.google.dev/gemini-api/docs/pricing
- Anthropic commercial data training policy: https://privacy.anthropic.com/en/articles/7996868-is-my-data-used-for-model-training
## Logging and telemetry privacy

Usage telemetry is metadata-only. `usage_logs.metadata` and any future Sentry/error-tracking payload may contain only technical identifiers and measurements, for example:

```text
user/session-independent IDs
obligation_id
source_id
provider
status_code
sync status
message/event counts
prefilter_filtered
```

Never log or send to telemetry:
- raw Gmail/calendar subject
- message body
- sender
- extracted free-text content
- OAuth access/refresh tokens
- AI prompts or provider responses

The implementation uses an allow-list when writing sync telemetry so nested provider results cannot accidentally introduce message content later.

## Cheap pre-filter telemetry

For every Gmail sync, LIFE records the number of messages rejected by the deterministic pre-filter as `prefilter_filtered`. This value is a count only and is stored in `usage_logs.metadata`.

The metric is intentionally kept separate from AI extraction outcomes so T1a/T1b analysis can distinguish:
- messages rejected before AI;
- messages sent to AI;
- obligations extracted;
- messages skipped because they were already processed.

The pre-filter remains recall-first. The metric is required because a false negative at the filter stage is otherwise indistinguishable from a false negative from the model.

## Acceptance criteria for telemetry

Given a real Gmail sync:
- the sync may write usage telemetry only with allow-listed technical fields;
- no message subject/body/sender appears in usage metadata;
- `prefilter_filtered` is present as a numeric count;
- an extraction error must not include source content in error payloads.

Given a later addition of Sentry or another error tracker:
- event payloads follow the same metadata-only rule;
- source content may be attached only after explicit redaction and separate privacy review.