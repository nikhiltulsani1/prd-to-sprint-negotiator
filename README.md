# PRD-to-Sprint Negotiator

Five agents read your PRD and argue about it. You get a sprint backlog.

## Problem

Sprint planning meetings are painful in a specific way. The PM wants 
everything in the sprint. The engineer thinks half of it is underestimated. 
The QA person finds three features with no acceptance criteria ten minutes 
before the meeting ends. Then everyone compromises badly under time pressure 
and commits to a sprint that slips by Wednesday.

The root problem is that three different perspectives — product, engineering, 
and quality — need to be reconciled against a fixed capacity. That reconciliation 
takes time, domain knowledge, and someone willing to say no to things.

This agent does that reconciliation automatically.

## Solution

Five specialised agents run in sequence, each adding a layer of analysis:

- **Product Agent** — reads the PRD, extracts features, user stories, acceptance criteria, and priorities
- **Engineer Agent** — estimates story points (fibonacci), flags technical risks, identifies missing requirements
- **QA Agent** — reviews each feature for test coverage gaps, edge cases, and missing AC (runs in parallel per feature)
- **Negotiator Agent** — reconciles all three inputs against sprint capacity and velocity, includes or excludes with explicit reasoning
- **Output Agent** — formats the negotiated plan as a markdown sprint backlog ready to paste into Jira or GitHub Projects

```bash
# Sprint 1
python main.py samples/sample_prd.txt --sprint 1

# Sprint 2 — with context from last sprint (story points)
python main.py samples/sample_prd.txt --sprint 2 \
  --completed "User Authentication" \
  --blocked "Task Board" \
  --velocity 32

# Sprint 2 — backwards compatible ratio format also works
python main.py samples/sample_prd.txt --sprint 2 \
  --completed "User Authentication" \
  --velocity 0.8
```

## How It Works

```
PRD file
   │
   ▼
Product Agent → features, user stories, priorities
   │
   ▼
Engineer Agent → story points, risks, missing requirements
   │
   ▼
QA Agent (parallel) → test cases, edge cases, risk levels, flags
   │
   ▼
Negotiator Agent → sprint plan within capacity, with reasoning
   │
   ▼
Output Agent → sprint_N_backlog.md
```

Each agent only sees what it needs. The Negotiator gets all three
inputs and makes the final call on what fits in the sprint.

## Sprint Context

The --sprint, --completed, --blocked, and --velocity flags make
this reusable every sprint — not just a one-shot document generator.

| Flag | What it does |
|------|-------------|
| --sprint N | Sprint number — affects what gets filtered and how output is labelled |
| --completed "X, Y" | Stories finished last sprint — filtered out automatically |
| --blocked "X" | Stories that slipped — re-prioritised by Negotiator |
| --velocity 0.8 | Last sprint's completion rate — scales effective capacity |

Sprint 2 with velocity 0.8 means the Negotiator works with 32 points
instead of 40. It adjusts scope automatically.

## Web UI

A Streamlit interface is included for teams who prefer a browser-based workflow.

```bash
streamlit run app.py
```

Upload your PRD (TXT, MD, PDF, or DOCX), configure sprint context,
and click **Run the Room**. Watch each specialist's reasoning appear
live as agents complete. Results appear in three tabs:
Sprint Backlog, MCP Export, and Summary.

## MCP Export

Every run generates a sprint_{N}_mcp_payload.json alongside the backlog.
The payload is structured as tool calls compatible with:

- **Jira MCP** — creates epic, stories, subtasks, and QA tasks directly
- **Azure DevOps MCP** — same structure, ADO-compatible
- **Linear MCP** — issues and sub-issues ready to import

Each story includes implementation subtasks from the Engineer Agent
and QA tasks from the QA Agent — typically 40–50 QA tasks per sprint.
No copy-paste. One file. Direct import.

## Why Not Just Ask Claude or GPT?

A single model playing all five roles simultaneously has no one to argue with.
It agrees with itself. Features never get cut with real reasoning.
Capacity gets ignored. QA flags get glossed over.

The difference shows up in three specific places:

**Capacity enforcement.** Ask GPT-4o to plan a sprint and it will recommend
committing 49 points to a 40-point sprint. The Negotiator hard-caps at capacity
and explains every cut — 72.5% utilisation by default, adjustable by velocity.

**QA specificity.** A single prompt produces "test the login page."
The QA Agent produces "Verify POST /api/signup with duplicate email returns 409"
and "JWT token replay attacks — attempt reuse of old tokens after logout."
The difference is 9 years of QA domain knowledge encoded into the prompt.

**Traceability.** Every inclusion and exclusion has explicit reasoning
in the negotiation notes. Not a black box — a documented decision log.

## Sample Output

A realistic excerpt from sprint_1_backlog.md — generated from the TaskFlow sample PRD.

---

**Sprint Goal:** Implement core user authentication, task board, and team
management features with a focus on quality and security.

**Committed Scope (29 / 40 pts — 72.5% capacity)**

| Feature | Points | Priority | QA Risk |
|---------|--------|----------|---------|
| User Authentication | 8 | High | High |
| Task Board | 13 | High | High |
| Team Management | 8 | High | Medium |

**Excluded This Sprint**

| Feature | Reason | Planned For |
|---------|--------|-------------|
| Notifications | Medium priority, high QA risk, capacity constraint | Sprint 2 |
| Reporting | Low priority, deferred to maintain focus | Sprint 2 |

**Negotiation Notes**
- Included all High priority features — User Auth, Task Board, Team Management — totalling 29 points
- 72.5% capacity utilisation meets the 70-80% target range
- Notifications excluded despite medium priority due to combined QA flags and capacity pressure
- All included features have explicitly defined acceptance criteria — no features blocked on missing AC

**QA Checklist (excerpt — full checklist has 40+ items)**

User Authentication:
- [ ] POST /signup with valid email and password returns 201 and creates user record
- [ ] POST /signup with already registered email returns 409 with specific error message
- [ ] POST /login with valid credentials returns 200 and properly formatted JWT
- [ ] POST /login with invalid password returns 401 Unauthorized
- [ ] Edge: Use expired JWT to access protected endpoint — verify 401 response
- [ ] Edge: JWT token replay attack — reuse token after logout — verify rejection

Task Board:
- [ ] POST /tasks with valid fields returns 201 and task appears in To Do column
- [ ] PATCH /tasks/{id}/move — drag to In Progress — verify backend state change
- [ ] Edge: Concurrent edit of same task by two users — verify conflict handling
- [ ] Edge: Drag and drop failure due to network latency — task must not enter inconsistent state

**MCP Payload Summary**
- 3 stories · 29 story points · 18 implementation subtasks · 46 QA tasks
- Export: sprint_1_mcp_payload.json — ready for Jira MCP, Azure DevOps MCP, Linear MCP

---

> Full output includes Executive Summary, Implementation Guidance,
> Risk Register, and complete QA Checklist with edge cases per feature.

## How to Run

```bash
git clone https://github.com/nikhiltulsani1/prd-to-sprint-negotiator.git
cd prd-to-sprint-negotiator
python -m venv .venv

# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Fill in your Azure AI Foundry credentials
```

Run with the sample PRD:

```bash
python main.py samples/sample_prd.txt --sprint 1
```

The sprint backlog is saved to sprint_1_backlog.md.

## What I Learned

The negotiator prompt needed three iterations to get right. The first
version was so cautious it committed 5 points out of 40 capacity —
technically correct but useless in practice. The fix was explicit rules:
target 70-80% capacity, only exclude features with zero acceptance criteria,
always explain every cut. After that it started making decisions that
actually resembled a real sprint planning session.

Parallel QA agent calls were an obvious win once I thought about it.
Running 5 feature reviews sequentially took 45 seconds because each
waits for the previous one. They don't depend on each other at all,
so ThreadPoolExecutor with max_workers=3 dropped that to 18 seconds.
Same pattern as the README/ARCHITECTURE/TESTPLAN parallel generation
in Project Kickstart Agent.

The QA agent produces genuinely useful test cases because the prompt
forces specificity — "Verify signup POST /api/signup with valid email
returns 201" instead of "test the login". That specificity comes from
9 years of writing test cases and knowing what vague ones actually cost you.

## What's Next

- **Persistent memory** — agent tracks sprint history automatically, no manual --completed flag
- **Direct Jira/Linear integration** — push backlog directly via MCP, no JSON export step
- **Velocity learning** — estimates improve as the agent sees your team's actual delivery data
- **Standards file** — upload team engineering standards, agent enforces them in every sprint
- **Stakeholder summary** — non-technical plain English export for PMs and leadership

## AI Tools Used

- Azure AI Foundry (gpt-4.1-mini) — all 5 agent calls
- GitHub Copilot (VS Code) — primary coding assistant
- Claude Code — architecture decisions and scaffolding

## Tech Stack

| Tool | Purpose |
|------|---------|
| Azure AI Foundry (gpt-4.1-mini) | All agent inference |
| requests | Foundry client (plain requests to avoid SDK api-version issues) |
| click | CLI interface |
| rich | Terminal output and panels |
| ThreadPoolExecutor | Parallel QA feature reviews |
| python-dotenv | Environment config |
| pytest | Test suite |

## Demo

▶️ [Watch the demo](#) — link updated after recording

> Runs in ~40 seconds end-to-end. Generates sprint backlog,
> QA checklist with 40–50 specific test cases, and MCP payload
> for direct Jira/ADO/Linear import.

## Reliability & Safety

- **Graceful degradation** — agent calls go to Azure AI Foundry first, then fall back to GitHub Models, then to defaults if both are unavailable. A single service outage doesn't break the pipeline.
- **No black-box decisions** — every feature the Negotiator includes or excludes comes with explicit written reasoning in the negotiation notes. A PM can see exactly why something was deferred.
- **Capacity is hard-enforced** — a programmatic safety net guarantees committed points never exceed effective sprint capacity, even if the model returns an inconsistent estimate. Story points are clamped to valid fibonacci values and totals are recalculated rather than trusted.
- **Independent failure isolation** — QA reviews run in parallel; if one feature's review fails, the others still complete rather than crashing the whole run.
- **Full pipeline test** covers all five agents end-to-end, asserting capacity limits hold and required output sections are present.

## Built By

**Nikhil Tulsani**
- Microsoft Learn Username: NikhilTulsani-1371
- GitHub: [@nikhiltulsani1](https://github.com/nikhiltulsani1)
- Hackathon: Microsoft Agents League 2026
- Hackathon Registered Mail : Nikhil.tulsani1@gmail.com
