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
