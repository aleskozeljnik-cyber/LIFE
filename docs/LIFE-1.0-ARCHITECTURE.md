# LIFE 1.0 Architecture

## 1. Product definition

LIFE is a personal intelligence layer over the user's digital life.

It collects information from multiple providers, normalizes it, resolves people/topics/projects across sources, identifies meaningful obligations and decisions, and presents a small set of actions with evidence.

The user should experience one LIFE, not a collection of integrations.

## 2. Provider-neutral model

### Source
A connected provider/account:
- google_gmail
- google_calendar
- microsoft_outlook_mail
- microsoft_outlook_calendar
- microsoft_teams
- apple_icloud
- slack
- whatsapp
- viber
- documents

### Item
A normalized piece of information:
- message
- calendar_event
- task
- document
- contact
- conversation

Required fields:
- provider
- external_id
- account_id
- item_type
- title
- body/summary
- created_at
- updated_at
- participants
- source_url when available
- raw metadata reference

### Entity
Canonical person/company/project/topic identity resolved across providers.

### Context
A relationship between items/entities:
- same person
- same project/topic
- same conversation
- same event
- reply/follow-up
- document referenced by message
- message related to calendar event

### Obligation
A normalized potential responsibility:
- requested_action
- due_at
- status
- confidence
- evidence

### Life item
The final user-facing decision/action object:
- title
- concise summary
- next_action
- priority
- due_at
- evidence
- confidence
- related people/projects

## 3. Intelligence pipeline

COLLECT
-> NORMALIZE
-> DEDUPLICATE
-> RESOLVE PEOPLE
-> RESOLVE TOPICS/PROJECTS
-> CONNECT CONTEXT
-> DETECT OBLIGATIONS
-> DECIDE WHAT MATTERS
-> GENERATE NEXT ACTION
-> PRESENT WITH EVIDENCE

## 4. Connector contract

Every provider adapter must support, where the provider allows it:
- OAuth/authorization
- initial sync
- incremental sync
- pagination
- deduplication
- source metadata
- disconnect
- deletion/export
- sync health
- permission scope reporting

A connector is not considered production-ready merely because messages can be fetched.

## 5. Product priorities

### P0
- Google Gmail
- Google Calendar
- provider-neutral model
- evidence/provenance
- corrections
- privacy gate

### P1
- Microsoft Outlook Mail
- Microsoft Outlook Calendar
- Microsoft Teams
- People resolution
- cross-source project/topic linking

### P2
- iCloud bridge
- OneDrive / SharePoint
- Slack

### P3
- WhatsApp
- Viber
- mobile Messages/SMS

WhatsApp/Viber integration must be based on supported official mechanisms and must not rely on scraping or fragile unofficial access.

## 6. Owner pilot

The first production test is Aleš's real environment.

Test workflows:
1. Email -> meeting
2. Teams message -> meeting
3. Message -> document
4. Person across Gmail/Outlook/Teams
5. Project across mail/calendar/chat/document
6. Explicit request -> action
7. Completed item -> suppressed
8. Marketing/noise -> suppressed
9. User correction -> future behavior
10. Disconnect/export/delete

Acceptance:
- maximum 3 meaningful Today actions
- each action has evidence
- cross-source links are understandable
- obvious noise is suppressed
- no silent data loss
- sync failures are visible
- user can inspect and correct LIFE

## 7. Ten-user beta

Only after owner pilot acceptance:
- 10 invited users
- source-by-source consent
- telemetry limited to product quality metrics
- weekly false-positive/false-negative review
- measure:
  - sync success
  - sync latency
  - useful-action rate
  - false-positive rate
  - correction rate
  - evidence click-through
  - retention / repeated use

## 8. UX rule

Today is not an inbox.

Today answers:
1. What matters now?
2. Why?
3. What should I do?
4. What evidence supports it?

Everything else remains accessible underneath the intelligence layer.
