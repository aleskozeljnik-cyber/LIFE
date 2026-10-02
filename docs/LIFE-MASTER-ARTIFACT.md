# LIFE — MASTER PRODUCT & DEVELOPMENT ARTIFACT

**Version:** 1.0  
**Status:** Foundation / Owner Pilot  
**Last updated:** 2026-10-02  
**Owner:** Aleš Koželjnik  
**Repository:** `aleskozeljnik-cyber/LIFE`

---

# 0. NORTH STAR

## Product ambition

LIFE should become the intelligence layer for a person's digital life.

The long-term ambition is not to build another inbox, calendar, task manager, or chatbot.

The ambition is to build a product that can be used by a meaningful share of smartphone-using adults in Europe — with a long-term target of **10% of EU adults with smartphones**.

The product must therefore be designed from the beginning for:

- millions of users
- multiple identity/provider ecosystems
- strong privacy expectations
- multilingual Europe
- different levels of digital sophistication
- reliable synchronization
- explainable AI decisions
- user control and correction

## Product promise

> **Connect your digital life. LIFE tells you what matters.**

The user should not need to understand where information lives.

LIFE should connect the context and surface what matters now.

---

# 1. WHAT LIFE IS

LIFE is a **Personal Intelligence Layer**.

It sits above the user's existing digital tools:

- email
- calendar
- chat
- documents
- contacts
- tasks
- communication platforms

LIFE collects, understands, connects, prioritizes and helps the user act.

## Core loop

```
COLLECT
   ↓
NORMALIZE
   ↓
UNDERSTAND
   ↓
CONNECT
   ↓
DECIDE WHAT MATTERS
   ↓
ACT
   ↓
LEARN FROM USER
```

---

# 2. WHAT LIFE IS NOT

LIFE should NOT become:

- another inbox
- another calendar
- another task list
- another generic AI chat
- a dashboard full of widgets
- a notification aggregator
- a system that forces the user into one provider ecosystem

The source applications remain sources.

**LIFE is the intelligence layer above them.**

---

# 3. CORE USER EXPERIENCE

The primary question LIFE answers every day:

> **What actually matters to me now?**

Today should normally contain a small number of meaningful items.

Ideal output:

### 1. TALUM — prepare for tomorrow's meeting

Teams + Outlook + Calendar + document

**Next:** prepare the three missing numbers.

**Why:** Teams request + tomorrow's meeting + latest proposal.

---

### 2. Janez is waiting for your answer

Outlook + WhatsApp

**Next:** reply to Janez.

**Why:** unanswered request from yesterday.

---

### 3. Family appointment

Calendar + message

**Next:** confirm the appointment.

**Why:** deadline today.

---

The user should not see 47 raw records.

---

# 4. UNIVERSAL SOURCE LAYER

All integrations must feed the same provider-neutral architecture.

## Initial source roadmap

### P0 — existing / foundation

- Google Gmail
- Google Calendar

### P1 — immediate

- Microsoft Outlook Mail
- Microsoft Outlook Calendar
- Microsoft Teams

### P2

- Apple / iCloud
- OneDrive
- SharePoint
- Slack

### P3

- WhatsApp
- Viber
- mobile Messages / SMS

For WhatsApp, Viber and other restricted platforms, integration must use supported official mechanisms and must not depend on scraping or fragile unofficial APIs.

---

# 5. PROVIDER-NEUTRAL DATA MODEL

The current LIFE implementation is obligation-centric.

Current conceptual model:

```
source → obligation → life_item
```

This is not sufficient for the long-term product.

Target model:

```
SOURCE
  ↓
ITEM
  ↓
PERSON / ORGANIZATION
  ↓
PROJECT / TOPIC
  ↓
CONTEXT / RELATIONSHIP
  ↓
OBLIGATION / DECISION
  ↓
NEXT ACTION
  ↓
LIFE ITEM
```

## 5.1 Source

A connected account/provider.

Examples:

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

## 5.2 Item

A normalized piece of information.

Types:

- message
- calendar_event
- document
- task
- contact
- conversation

Core fields should include:

- provider
- account_id
- external_id
- item_type
- title
- body/summary
- created_at
- updated_at
- participants
- source URL when available
- provider metadata
- sync metadata

## 5.3 Person

Canonical identity across sources.

Example:

```
Janez Novak
 ├── Gmail: janez.novak@...
 ├── Outlook: J. Novak
 ├── Teams: Janez
 └── WhatsApp: Janez
```

LIFE must eventually understand these as one person.

## 5.4 Project / Topic

A shared context.

Example:

```
TALUM
 ├── Gmail
 ├── Outlook
 ├── Teams
 ├── Calendar
 ├── Documents
 └── People
```

## 5.5 Relationship

Examples:

- same person
- same project
- same topic
- same conversation
- message related to event
- document referenced by message
- reply/follow-up
- person associated with project

## 5.6 Obligation

A potential responsibility.

Examples:

- reply
- prepare
- send
- approve
- sign
- pay
- attend
- decide
- follow up

Fields:

- action
- due_at
- status
- confidence
- evidence

## 5.7 Life Item

The final user-facing object.

Must contain:

- title
- concise summary
- next action
- priority
- due date
- evidence
- confidence
- related people
- related projects/topics

---

# 6. INTELLIGENCE LAYERS

## Layer 1 — COLLECT

Get information reliably.

Requirements:

- OAuth
- permissions
- pagination
- initial sync
- incremental sync
- deduplication
- retry
- sync health

## Layer 2 — UNDERSTAND

Determine:

- what happened
- who is involved
- what it is about
- whether action is required
- when it matters
- confidence

## Layer 3 — CONNECT

Connect:

- people
- conversations
- projects
- topics
- meetings
- documents
- obligations

This is the core differentiation.

## Layer 4 — DECIDE

Determine:

- what matters now
- what can wait
- what is noise
- what is already completed
- what is duplicate
- what requires user action

## Layer 5 — ACT

Suggest or eventually execute:

- reply
- prepare
- schedule
- create task
- follow up
- draft document
- send message

Initial rule:

> **LIFE suggests → user confirms → LIFE acts.**

No silent outbound actions.

## Layer 6 — LEARN

User corrections become durable signals.

Examples:

- "ignore these"
- "this person is important"
- "this project is high priority"
- "this is already handled"

The system must improve from corrections without losing transparency.

---

# 7. PEOPLE + PROJECTS ARE CORE

People and projects are not optional future features.

They are required for LIFE to become genuinely useful.

## People

LIFE should eventually answer:

> Who is this person across my digital life?

and:

> What do I currently owe this person?

## Projects

LIFE should eventually answer:

> What is happening with Talum?

without requiring the user to search:

- Gmail
- Outlook
- Teams
- Calendar
- SharePoint
- documents

---

# 8. PRIVACY PRINCIPLES

Privacy is part of the product architecture.

Rules:

1. Source-by-source consent.
2. Least-privilege permissions where possible.
3. Clear connected-source status.
4. User-controlled disconnect.
5. User-controlled export.
6. User-controlled deletion.
7. No silent outbound actions.
8. Evidence must be inspectable.
9. AI provider data-use policy must be compatible with processing user data.
10. Provider-specific permissions must be visible.
11. Sensitive data should not be retained unnecessarily.
12. Product telemetry must be separated from user content.

---

# 9. CONNECTOR CONTRACT

A connector is NOT production-ready merely because it can fetch messages.

Every connector should support, where technically possible:

- authorization
- initial sync
- incremental sync
- pagination
- deduplication
- normalized item mapping
- source metadata
- sync status
- error state
- reconnect
- disconnect
- export
- deletion
- permission reporting

Connector quality is measured by:

- reliability
- latency
- completeness
- duplicate rate
- failure recovery
- user trust

---

# 10. CURRENT TECHNICAL FOUNDATION

## Stack

- Next.js frontend
- FastAPI backend
- Railway
- Supabase/Postgres
- GitHub
- OAuth
- provider adapters
- intelligence layer

## Current working sources

- Gmail
- Google Calendar

## Current intelligence

Already implemented:

- noise filtering
- actionability scoring
- calendar-vs-action distinction
- cross-source clustering
- evidence
- next-action generation
- user corrections foundation
- privacy gate
- live intelligence endpoint
- production deployment

## Current limitation

The current intelligence implementation still centers on:

```
obligation → life_item
```

The next architectural milestone is to introduce the provider-neutral context model.

---

# 11. ROADMAP

## PHASE 0 — FOUNDATION

Status: IN PROGRESS

- [x] Google OAuth
- [x] Gmail ingestion
- [x] Google Calendar ingestion
- [x] normalized sources
- [x] obligations
- [x] life_items
- [x] privacy gate
- [x] noise filtering
- [x] actionability
- [x] cross-source clustering foundation
- [x] evidence
- [x] corrections foundation
- [ ] provider-neutral Item model
- [ ] People model
- [ ] Project/Topic model
- [ ] relationship graph

---

# 12. PHASE 1 — OWNER PILOT

Target: Aleš

Sources:

- Gmail
- Google Calendar
- Outlook Mail
- Outlook Calendar
- Teams

## Pilot workflows

1. Email → meeting
2. Teams → meeting
3. Person across Gmail + Outlook + Teams
4. Project across email + calendar + Teams
5. Message → document
6. Explicit request → obligation
7. Completed item → suppressed
8. Marketing → suppressed
9. Same project across multiple sources → one context
10. User correction → future behavior

## Owner acceptance criteria

- maximum 3 meaningful Today actions
- every action has evidence
- cross-source links are understandable
- obvious noise is suppressed
- no silent data loss
- sync failures are visible
- corrections affect future output
- user can inspect source evidence
- disconnect works
- export works
- deletion works

---

# 13. PHASE 2 — 10 USER BETA

Only start after owner pilot acceptance.

## User selection

Use 10 users with deliberately different profiles:

- Google-heavy
- Microsoft-heavy
- mixed ecosystem
- entrepreneur
- manager
- employee
- high communication volume
- lower communication volume
- personal-heavy
- work-heavy

## Beta rules

- invitation only
- explicit consent
- source-by-source permissions
- clear privacy explanation
- real usage for at least 30 days
- weekly review of failure cases

## Metrics

### Product

- daily active use
- weekly retention
- repeat usage
- action acceptance rate
- action rejection rate

### Intelligence

- useful action rate
- false positives
- false negatives
- duplicate rate
- correction rate
- evidence click-through

### Infrastructure

- sync success
- sync latency
- error rate
- recovery time
- AI cost per active user

---

# 14. PHASE 3 — 100 USERS

Goals:

- identify common user patterns
- validate onboarding
- validate source combinations
- improve People resolution
- improve Project resolution
- improve ranking
- improve privacy UX
- determine pricing hypotheses

---

# 15. PHASE 4 — 1,000 USERS

Requirements:

- robust incremental sync
- automated onboarding
- support tooling
- observability
- cost controls
- model evaluation framework
- connector health dashboard
- privacy audit
- data deletion verification

---

# 16. PHASE 5 — SCALE

Target architecture must support:

- 10k
- 100k
- 1M+
- eventually multi-million users

Scaling principles:

- asynchronous ingestion
- queues
- incremental processing
- provider-specific rate limiting
- event-driven updates
- idempotent jobs
- cached derived intelligence
- background enrichment
- strict tenant isolation
- observability

---

# 17. UX PRINCIPLES

## Today

Today is not an inbox.

Today answers:

1. What matters?
2. Why?
3. What should I do?
4. What evidence supports it?

## Navigation

Underlying sources remain accessible:

- Today
- Needs attention
- Inbox
- Calendar
- People
- Projects
- Documents

But the user should normally start with LIFE's interpretation.

---

# 18. PRODUCT DIFFERENTIATION

Potential long-term moat:

### 1. Context graph

LIFE knows relationships between:

- people
- projects
- messages
- events
- documents
- obligations

### 2. Personal memory

LIFE learns the user's preferences and corrections.

### 3. Cross-provider neutrality

LIFE is not tied to Google or Microsoft.

### 4. Evidence-first intelligence

Every meaningful conclusion can be inspected.

### 5. Action layer

Eventually LIFE moves from:

> "Here is what happened."

to:

> "Here is what you should do."

and eventually:

> "I prepared it. Confirm?"

---

# 19. RULES FOR DEVELOPMENT

From this point forward:

1. Do not add integrations without fitting them into the universal model.
2. Do not optimize UI before intelligence quality.
3. Do not confuse sync success with product success.
4. Do not add raw data to Today just because it exists.
5. Do not hide evidence.
6. Do not allow silent outbound actions.
7. Do not sacrifice privacy for convenience.
8. Every major product decision must be recorded in this artifact.
9. Every pilot failure becomes a test case.
10. The 10-user beta is a validation stage, not a vanity launch.

---

# 20. IMMEDIATE NEXT BUILD

## Milestone A — Context Core

Build:

1. provider-neutral Item abstraction
2. Person entity
3. Project/Topic entity
4. relationships between items/entities
5. evidence model
6. provider adapter interface
7. migration path from current obligations
8. tests for deduplication and cross-source linking

## Milestone B — Microsoft

Then add:

1. Outlook OAuth
2. Outlook Mail sync
3. Outlook Calendar sync
4. Teams integration
5. Microsoft identity normalization
6. cross-provider linking

## Milestone C — Owner Pilot

Run LIFE with Aleš's real:

- Gmail
- Google Calendar
- Outlook
- Teams

and evaluate daily.

Only after acceptance move to 10 users.

---

# 21. DECISION LOG

### 2026-10-02

**Decision:** LIFE is being developed as a Personal Intelligence Layer, not an inbox/task aggregator.

**Validation evidence:** Before Context Core work began, production logs show successful real-account flow on 2026-10-01: Google OAuth callbacks returned 303, followed by /auth/status 200, /health 200, Gmail/Calendar sync 200, and /life-items 200. Context Core deployment activity started only on 2026-10-02 at 06:13 UTC.

**Decision:** Long-term ambition is mass consumer adoption, with a strategic target of 10% of EU adults with smartphones.

**Decision:** Outlook + Teams move into the first major integration phase.

**Decision:** iCloud, Slack, WhatsApp and Viber are part of the long-term source strategy, subject to technical/API/privacy constraints.

**Decision:** The architecture must become provider-neutral before adding many connectors.

**Decision:** People and Projects are core intelligence entities.

**Decision:** Owner pilot comes before 10-user beta.

**Decision:** This artifact is the living source of truth and must be updated as major decisions are made.

---

# 22. CURRENT POSITION

### Product

**Direction:** CLEAR

### Architecture

**Foundation:** GOOD  
**Needs:** Context Core redesign

### Integrations

**Google:** WORKING  
**Microsoft:** NEXT  
**Teams:** NEXT  
**Apple/iCloud:** PLANNED  
**Slack:** PLANNED  
**WhatsApp:** PLANNED / API validation required  
**Viber:** PLANNED / API validation required

### Intelligence

**Basic:** WORKING  
**Cross-source:** FOUNDATION WORKING  
**People graph:** NOT YET  
**Project graph:** NOT YET  
**Persistent personal memory:** PARTIAL  
**Action layer:** FUTURE

### Pilot

**Owner:** NOT STARTED AS FORMAL PILOT  
**10 users:** NOT STARTED

---

# 23. DEFINITION OF SUCCESS

LIFE succeeds when a user can connect their digital life and stop asking:

> "Where did I get that information?"

and instead ask:

> **"What do I need to do?"**

LIFE should answer that question with context, evidence and the smallest useful next step.


---

# 24. PROGRESS UPDATE — CONTEXT CORE

### 2026-10-02

**Milestone started:** Context Core

Implemented in Supabase:
- `context_items` — provider-neutral normalized source items
- `people` — canonical people identity layer
- `projects` — project/topic layer
- `context_relationships` — relationships between items, people and projects
- `context_evidence` — provenance/evidence bridge to context, obligations and LIFE items

Implemented in backend:
- `backend/app/context.py`
- `NormalizedItem`
- `PersonRef`
- `ProjectRef`
- `ProviderAdapter` connector contract
- provider-neutral email/name normalization
- stable provider + external-id item identity key

Tests added:
- normalization tests
- provider-neutral duplicate identity test

Migration:
- `supabase/migrations/20261002080000_add_context_core.sql`

Important architecture rule:
- Context Core is additive and backward-compatible.
- Existing `obligation → life_item` flow remains intact while the new context graph is introduced.
- No Microsoft connector is added until the normalized context contract is established.

### Current Context Core status
- [x] Item abstraction
- [x] Person entity schema
- [x] Project/Topic entity schema
- [x] Relationship schema
- [x] Evidence schema
- [x] Provider adapter contract
- [x] Basic normalization tests
- [ ] Persist Gmail/Calendar items into `context_items`
- [ ] Resolve People from real source participants
- [ ] Resolve Projects/Topics from real items
- [ ] Build cross-source relationship engine
- [ ] Migrate existing obligations to reference context evidence
- [ ] Add Outlook adapter
- [ ] Add Teams adapter

### Security note
Context Core is RLS-enabled and has now been explicitly locked down at the Data API boundary:
- anon and authenticated have no table privileges on the five Context Core tables
- explicit deny-all RLS policies exist for anon and authenticated
- the current LIFE backend continues to use a server-side Postgres connection
- this is intentionally deny-by-default until LIFE's custom session identity is mapped to a database authorization identity suitable for per-user RLS
- the next auth/data-boundary milestone must replace deny-all with tested per-user policies before any browser/Data API access is introduced

This is not treated as a deferred hardening task anymore.

### Next immediate build
**Context ingestion bridge:** take existing Gmail/Calendar normalized records and persist them as `context_items`, then derive People and Project/Topic candidates from those items without changing Today behavior.


### Context ingestion bridge — completed

- [x] Gmail sync writes normalized `context_items`
- [x] Calendar sync writes normalized `context_items`
- [x] Context items link back to existing `sources`
- [x] Existing obligations remain the decision/action layer
- [x] Existing known obligations are backfilled into Context Core on subsequent sync

The next implementation step is now the **Context Resolution Engine**:
1. extract people from Gmail/Calendar participants
2. canonicalize identities
3. generate Project/Topic candidates
4. create relationships between source items
5. attach evidence to obligations/LIFE items
6. test cross-source linking before Outlook is introduced


### 2026-10-02 — production validation and security correction

**Production validation before Context Core:** confirmed in Railway HTTP logs that the real production account successfully completed Google OAuth and then loaded the Today data path before Context Core was introduced. Representative sequence on 2026-10-01:
- /auth/google/callback → 303
- /health → 200
- /auth/status → 200
- /sources/calendar/sync → 200
- /sources/gmail/sync → 200
- /life-items → 200

This is the evidence baseline for the architecture work. The exact historical Railway variable-edit event for DATABASE_URL is not retained in the repository history, so the artifact records the stronger observable fact: the production process was successfully connecting to the database and serving authenticated real-account data after the correction.

**Security correction:** Context Core Data API access was explicitly locked down immediately after review. anon and authenticated privileges were revoked and explicit deny-all RLS policies were added for all five Context Core tables. Per-user RLS will be enabled as part of the identity/data-boundary work before any direct browser access.


## 2026-10-02 — Context Core ingestion/identity progress

### Implemented
- Context Core tables exist in production and remain deny-by-default for Supabase Data API roles.
- Gmail and Google Calendar sync persist provider-neutral `context_items`.
- Context item persistence now returns the canonical item UUID for downstream relationships.
- Gmail participants are normalized into canonical `people` records using normalized email/name.
- Calendar attendees are normalized into the same `people` model.
- Self identity is excluded from participant relationships.
- Explicit project markers are supported in titles: `[Project: NAME]` and `Project: NAME`.
- Explicit project hints are normalized into `projects`.
- Item → person and item → project relationships are persisted idempotently.
- Added automated test for explicit project hint extraction.

### Important limitation
Project inference is intentionally conservative at this stage. LIFE does **not** yet infer arbitrary projects from free-form email/calendar text. That will be a separate intelligence step after real owner-pilot data is populated and inspected.

### Next verification
1. Confirm latest backend deployment is SUCCESS.
2. Run real Gmail + Calendar sync on the owner account.
3. Verify counts and representative rows in `context_items`, `people`, `projects`, and `context_relationships`.
4. Inspect whether person resolution is correctly merging the same person across items.
5. Only then implement broader project/topic resolution and cross-source linking.


## 2026-10-02 — Context Core RLS guardrail correction

- Verified the original 10 Context Core deny policies were `PERMISSIVE`.
- Replaced all 10 with `AS RESTRICTIVE` policies for `anon` and `authenticated` across all five Context Core tables.
- Verified `pg_policies.permissive = RESTRICTIVE` for all 10 policies after migration.
- The change is recorded as a new migration: `20261002090000_make_context_core_deny_policies_restrictive.sql`.
- Existing migration history was restored rather than rewritten.
- Supabase security advisor still reports pre-existing RLS/no-policy findings on legacy tables and two SECURITY DEFINER execution warnings; these are separate from the Context Core correction and are not silently changed here.


## 2026-10-02 — Context Core identity-resolution validation

Real owner production data was inspected after the Gmail + Calendar sync:
- 50 context_items (47 Gmail messages + 3 Calendar events)
- 47 canonical people
- 102 participant relationships
- 0 projects, because no real item contained an explicit project marker

**Identity resolution is demonstrably deduplicating across multiple items.** Example:
- Canonical person: `Ziga B` / `ziga.brodnik@gmail.com`
- Same `people.id`: `b85f86e2-57b9-4ad8-80f7-febb6a96e52b`
- Linked to 7 distinct context items: 1 Calendar event and 6 Gmail messages.

**Cross-source identity resolution is also verified.** The same canonical `people.id` is used when a person appears as a Calendar attendee and in Gmail. The production data contains multiple such cases. The clearest example is `Ziga B / ziga.brodnik@gmail.com`: the same person row is linked to the Calendar event `VABILO 7. REDNA SEJA UO RKGV` and Gmail messages including `DOPIS PREDSEDNIKA ČLANOM UO - NUJNO!`.

This is evidence of actual identity merging, not merely repeated insertion into separate source-specific person rows.

**Project observation (not a task):** the current explicit-tag-only mechanism will likely produce zero projects in normal real-world use because users rarely write standardized `[Project: NAME]` / `Project: NAME` markers. This is recorded as an observation for a later product/architecture decision; it is intentionally **not** a current implementation task.


## 2026-10-02 — Context Resolution Engine real-data validation

A one-off production sync was executed for the owner account using the current Gmail + Calendar pipeline. The temporary startup hook was reverted immediately after the sync and the normal backend deployment was verified successful.

Observed production state after sync:
- 56 context_items total
- 53 Gmail messages
- 3 Calendar events
- 51 canonical people
- 108 context_relationships
- 0 projects/topics created by the conservative cross-source title-token resolver

The identity layer continues to demonstrate real cross-source resolution. Earlier validation found 12 people linked from both Calendar and Gmail, including Ziga B / ziga.brodnik@gmail.com with one Calendar event and six Gmail messages linked to the same canonical person row.

The topic candidate experiment exposed an important limitation: requiring literal title-token overlap across two providers is too conservative for real personal data. The current Calendar titles were "Neven rd", "VABILO 7. REDNA SEJA UO RKGV", and "sestanek - Gašper Škarja"; the Gmail corpus did not provide sufficient literal cross-provider title-token overlap, so the resolver correctly produced zero candidates rather than inventing a topic.

Decision:
- Keep the conservative resolver as a safety baseline.
- Do not add Outlook yet.
- Next Context Resolution step should combine stronger deterministic evidence: shared canonical people, temporal proximity, participant overlap, reply/thread relationships, and distinctive multi-word terms.
- Topic/project creation must remain explainable and evidence-backed; no speculative AI-generated projects.


## 2026-10-02 — Context Resolution v2.1 implementation and validation findings

Implemented:
- Strong Calendar anchor extraction for distinctive uppercase tokens such as `RKGV`.
- Cross-source topic candidate resolution using shared canonical people between Gmail and Calendar.
- When Gmail timestamps are available, a 14-day temporal proximity constraint is applied.
- When Gmail timestamps are unavailable, only a strong Calendar anchor plus shared canonical person is allowed; generic Calendar titles are not promoted to topics.
- Gmail occurrence time now prefers Gmail `internalDate` and falls back to the RFC `Date` header.
- Added automated coverage for shared-person + Calendar-anchor resolution.

Validation finding:
- Production data currently contains 53 Gmail context items and 3 Calendar items, but Gmail `occurred_at` remains NULL after the attempted production sync. The pipeline therefore cannot yet use Gmail time proximity as evidence.
- The Railway-connected execution path used for one-off sync validation did not produce a database change, so no real topic/project creation is claimed from v2.1 yet.
- A temporary validation endpoint was attempted but caused an isolated syntax error in the temporary endpoint code; it was immediately removed.
- Production was restored to the normal backend startup and the cleanup deployment is SUCCESS.

Decision:
- Do not seed or fabricate topics directly in the database to make the test pass.
- Keep the v2.1 resolver in code but require real execution evidence before declaring topic resolution successful.
- Next validation should invoke the authenticated sync path using the real owner session or a dedicated secure internal execution mechanism, then verify a concrete topic such as RKGV and its linked Gmail/Calendar evidence.
- Do not add Outlook until this owner-pilot Context Resolution path is verified end-to-end.


## 2026-10-02 — Gmail timestamp fix deployed; awaiting real sync validation

Investigation clarified that the previous 0/53 occurred_at result was produced by a real sync that ran before the timestamp fix was deployed. The current backend now has explicit Gmail timestamp extraction:
- prefer Gmail internalDate
- fallback to RFC Date header
- isolated helper gmail_occurred_at_from_payload(...)
- automated tests cover both paths

Deployment:
- commit 267a340ce799a649cbe747b925e27d56305abd79 — explicit/testable timestamp extraction
- commit 27820cf14eb5fae4aea8f6f3afc6ff67c230210c — timestamp tests
- Railway deployment bb0f0c4e-8c7f-4df5-9caa-fd3a201b3d4b — SUCCESS

The fix is not yet considered production-validated. The next validation must use the real authenticated owner sync after deployment and verify that Gmail occurred_at is populated in production. No topic/project validation is claimed before that evidence exists.

### T1b follow-up — sync latency

Record for later, not current scope:
- recent Gmail sync requests observed at approximately 23–69 seconds
- one request ended with HTTP 499 after the browser/client closed the request
- target before T1b: validate real sync latency against the MVP requirement of <2 minutes and investigate client cancellation behavior if it recurs


## 2026-10-02 — Owner-pilot Context Resolution v2.1 production validation

- Normal authenticated LIFE open now triggers Gmail + Calendar sync automatically for an already-connected Google account; no manual "Sync now" action is required.
- Production validation after frontend lifecycle fix:
  - Calendar sync: HTTP 200
  - Gmail sync: HTTP 200
  - Gmail sync duration: ~94.7s
  - Calendar sync duration: ~15.7s
- Real production Context Core after successful sync:
  - context_items: 59
  - Gmail: 56
  - Calendar: 3
  - Gmail with occurred_at: 41/56
  - Calendar with occurred_at: 3/3
  - people: 54
  - context_relationships: 115
- This confirms the explicit Gmail timestamp extraction is working in production for the majority of newly processed Gmail messages. Remaining Gmail rows without occurred_at require provider-payload/path investigation; do not assume they are current or validly timestampable.
- Cross-source topic validation produced a real candidate:
  - RKGV
  - linked to the Calendar event "VABILO 7. REDNA SEJA UO RKGV"
- The first resolver run also produced false-positive topic candidates "REDNA" and "SEJA" from generic uppercase governance words. These were identified as false positives, removed from derived production data, and the resolver stopword set was strengthened.
- Do not accept generic uppercase words as topics merely because they are uppercase. Topic candidates must remain distinctive and explainable.
- Do not add Outlook yet. First complete owner-pilot validation of People → Topics/Projects → Evidence → Life Item/briefing on real data.
- No synthetic topic/project data is to be seeded to make validation pass.


## 2026-10-02 — Context Evidence Layer implemented

### Production change
- Context Core evidence is now persisted for real provider-normalized items.
- Project relationships now also create explicit project-link evidence.
- Life Items now persist source evidence linking the generated Life Item back to the underlying obligation and provider context item.
- Existing production data was backfilled from existing context/relationship/life-item records only; no synthetic topic, project, obligation, or evidence content was created.

### Production validation
- Backend evidence deployment: `f94a002c-c4f1-4c0b-9086-4ac93d0a32f6` — SUCCESS.
- `context_evidence` now contains 59 real `context_source` records, 1 `project_link` record and 2 `life_item_source` records.
- Current real topic/project state remains: RKGV only; REDNA and SEJA remain removed.

### Quality gate / next correction
- An older Life Item snapshot still contains a false cross-source grouping around `ŠTEVILKA RAČUN 14001` and the RKGV calendar event. This is treated as a clustering-quality defect, not accepted as product behavior.
- Next build: strengthen cross-source clustering so provider linkage requires meaningful shared context (canonical person, project/topic evidence, or distinctive temporal/context overlap) rather than weak token coincidence.
- After that correction, re-run the owner-pilot path end-to-end: People → Topic/Project → Evidence → Life Item → next action.
- Outlook remains deferred until this owner-pilot Context Resolution path is reliable.


## 2026-10-02 — Cross-source clustering hardening v2

- Backend commit `4a8af134abf386f09f1d93f76d8edeedac3458fb` deployed successfully.
- Cross-source Life Item clustering now requires real contextual evidence: shared canonical person, shared project, or sufficiently strong multi-token content overlap. Weak single-token coincidence no longer creates a cross-provider cluster.
- Production context/source linkage was repaired for existing records; 59 owner-pilot context items now have source linkage where a corresponding source exists.
- Evidence layer after backfill: 59 `context_source`, 20 `life_item_source`, 1 `project_link` records.
- One previously generated cross-source Life Item remains stale in the persisted table until authenticated `GET /life-items` rebuilds the owner-pilot view; it is not accepted as valid product behavior.
- Next validation gate: refresh/open LIFE with the owner session, confirm the stale invoice/RKGV cluster disappears, and confirm the real RKGV topic remains connected through People → Topic → Evidence → Life Item.
- Outlook remains deferred until this owner-pilot chain passes production validation.
