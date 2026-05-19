---
name: estimation-helper
description: Break down a feature or user story into tasks and produce a structured estimate with story points, risks, and assumptions. Use this skill whenever anyone asks for an estimate, wants to size a feature, needs to break down a user story, is planning a sprint, or says things like "how long will this take", "how many points is this", "help me estimate", or "let's size this up". Even if the request is vague, jump in and start decomposing.
---

# Estimation Helper

A skill for developers who need to produce structured, defensible estimates quickly — whether for sprint planning, roadmap discussions, or change requests.

---

## When to use this skill

- A feature or user story needs story points before sprint planning
- A stakeholder asks "how long will this take?" and you need a written answer
- A change request needs a quick impact assessment
- You want a structured breakdown to review with the team before committing

---

## What you produce

1. **Task breakdown** — the feature decomposed into concrete, estimable subtasks
2. **Story point estimates** — per task and total, using the Fibonacci scale (1, 2, 3, 5, 8, 13, 21)
3. **Risks** — things that could make this take longer
4. **Assumptions** — things that must be true for the estimate to hold
5. **Out of scope** — things explicitly excluded to prevent scope creep

---

## Process

### Step 1 — Understand the request

If any of the following are genuinely missing and would materially change the estimate, ask before proceeding. If the user's message already supplies enough context, skip to Step 2 immediately — don't ask questions that were already answered.

- The feature or user story to estimate (if not already given)
- Tech stack and context (default to a standard layered architecture if not specified)
- Team velocity or preferred scale (default to Fibonacci 1–13 per task)
- Who the output is for: internal dev team, sprint planning, or client-facing document

If the user says "just estimate it" with minimal context, make reasonable assumptions, state them clearly in the **Context** line and **Assumptions** section, and proceed. Never stall indefinitely waiting for information.

### Step 2 — Decompose into tasks

Break the feature into concrete subtasks. Think in terms of:

- Backend: domain model changes, application layer (commands/queries/handlers), infrastructure (DB schema, migrations, external integrations), API endpoints
- Frontend: components, state, API integration (if applicable)
- Cross-cutting: unit tests, integration tests, documentation updates, deployment/config changes

Group tasks by layer or area. Use plain language — avoid acronyms stakeholders won't know.

### Step 3 — Assign estimates

For each task, assign a Fibonacci story point estimate and include a one-sentence rationale.

| Points | Meaning                                    |
| ------ | ------------------------------------------ |
| 1      | Trivial — 1–2 hours, no unknowns           |
| 2      | Small — half a day, well-understood        |
| 3      | Small-medium — about a day                 |
| 5      | Medium — 2–3 days, some complexity         |
| 8      | Large — up to a week, significant unknowns |
| 13     | Very large — consider splitting            |
| 21     | Epic — must be broken down further         |

If a task scores 13 or higher, flag it and suggest splitting it.

Once all tasks are scored, sum the total:

- **Total ≤ 20 points** — standard single estimate, proceed to Step 4.
- **Total > 20 points** — flag the feature as large. Add a **Phased Delivery** section to the output that breaks the work into 2–3 sprint-sized milestones (e.g. "Phase 1: core backend + API", "Phase 2: frontend integration", "Phase 3: edge cases, tests, polish"). Offer to produce a separate sub-estimate for each phase if the user wants more detail.

### Step 4 — Surface risks and assumptions

**Risks** are conditions that could increase the estimate:

- Unclear requirements
- Third-party or legacy integrations
- Missing environments or access
- Concurrent work by other teams

**Assumptions** are things that must hold for the estimate to be valid:

- Requirements are stable
- Dev environment is ready
- Dependencies (APIs, data, design) are available

### Step 5 — Produce the estimate document

Format the output as a Markdown document the user can copy into a ticket, Confluence page, or email.

Use this structure:

```markdown
## Estimate: <Feature Name>

**Date:** <today's date>
**Estimated by:** <name or team — use "GitHub Copilot" when Copilot produces the estimate>
**Context:** <one sentence covering what is included, any assumed tech stack, and intended audience>

---

### Task Breakdown

| # | Task | Area | Points | Notes |
|---|------|------|--------|-------|
| 1 | ... | Backend | 3 | one-sentence rationale |
| 2 | ... | Tests | 2 | ... |

...

**Total: X points** (~Y days at team velocity of Z pts/day, if known)

---
```

When total > 20 points, insert a **Phased Delivery** section immediately after the Total line and before Risks:

```markdown
### Phased Delivery

**Phase 1 — <name>** (~X pts): <tasks covered>
**Phase 2 — <name>** (~X pts): <tasks covered>
**Phase 3 — <name>** (~X pts): <tasks covered>

---
```

Then close the document with:

```markdown
### Risks

- ...
- ...

### Assumptions

- ...
- ...

### Out of Scope

- ...
- ...
```

**Important:** Place assumptions only in the dedicated **Assumptions** section — do not duplicate them above the task table. Any context you assumed (e.g. tech stack, team size, scope) belongs in the **Context** line of the header.

---

## Tips

- If the feature is large (total > 20 pts), always include the **Phased Delivery** section — it turns the estimate into an actionable plan stakeholders can act on immediately
- If the user gives a velocity (e.g. "we do 30 points a sprint"), translate the estimate into calendar time and sprint fractions in the **Total** line
- If no velocity is given, add a point-to-day guide as a footnote: `1 pt ≈ 0.5 day, 3 pts ≈ 1 day, 5 pts ≈ 2–3 days, 8 pts ≈ 1 week`
- For stakeholder-facing output, replace point values with day ranges (1 pt ≈ 0.5 day, 3 pts ≈ 1 day, 5 pts ≈ 2–3 days)
- Always list at least two risks and two assumptions — estimates with none are untrustworthy
