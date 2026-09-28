# LIFE T1a — Dodatek 2: Logging, telemetry in monitoring predfiltra

## 1. Privacy contract za loge

`usage_logs.metadata` in vsak prihodnji error-tracking payload (Sentry ipd.) sme vsebovati samo tehnične oznake, ID-je in agregirane metrike.

Dovoljeno:
- obligation_id
- source_id
- provider/model
- status/status_code
- sync state
- message/event counts
- prefilter_filtered
- messages_sent_to_ai
- execution duration in druge tehnične metrike

Prepovedano:
- Gmail subject
- Gmail body
- sender/recipient
- Calendar title/description
- AI prompt
- AI response
- OAuth access/refresh token
- exception payload, ki vsebuje source content

Sync telemetry mora uporabljati allow-list in nikoli neposredno zapisati celotnega provider result objekta.

## 2. Spremljanje cheap pre-filterja

Predfilter je recall-first in lahko naredi false negative. Med T1a/T1b mora LIFE za vsakega uporabnika meriti:

```text
messages_found
messages_skipped
prefilter_filtered
messages_sent_to_ai
obligations_created
```

`prefilter_filtered` je število Gmail sporočil, ki so bila izločena pred AI klicem. `messages_sent_to_ai` je število novih sporočil, ki jih je prefilter spustil do AI.

Telemetrija vsebuje samo številke; ne vsebuje vsebine sporočil.

## 3. Definition of Done

- sync telemetry je allow-listed;
- v `usage_logs.metadata` ni source content;
- `prefilter_filtered` je zabeležen na sync;
- `messages_sent_to_ai` je zabeležen ali enolično izračunljiv;
- provider/model identiteta ostane na voljo za analizo kakovosti;
- prihodnji Sentry/error-tracking event mora uporabljati isti privacy contract;
- realni pilotni podatki se ne smejo pojaviti v observability payloadih.