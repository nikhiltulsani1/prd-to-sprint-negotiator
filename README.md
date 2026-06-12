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

# Sprint 2 — with context from last sprint
python main.py samples/sample_prd.txt --sprint 2 \
  --completed "User Authentication" \
  --blocked "Task Board" \
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

## Sample Output

```markdown
## Sprint 2 Backlog — TaskFlow

**Sprint Goal:** Deliver stable collaboration features with full
test coverage, focusing on Team Management and Notifications.

## Committed Scope (13 / 32 pts)
| Feature | Story Points | QA Requirements |
|---------|-------------|-----------------|
| Team Management | 8 | Role permission boundary tests, invitation expiry |
| Notifications | 5 | Email delivery failure handling, duplicate prevention |

## Excluded This Sprint
| Feature | Reason | Planned For |
|---------|--------|-------------|
| Task Board | QA-flagged: drag-and-drop conflict resolution undefined | Sprint 3 |
```

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