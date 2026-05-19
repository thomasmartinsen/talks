---
name: adr-writer
description: Write an Architecture Decision Record (ADR) in MADR format from a description of a problem, options considered, and the decision made. Use this skill whenever anyone wants to document an architecture decision, capture a technical choice, write an ADR, record why something was built a certain way, or says things like "let's document this decision", "we need an ADR for this", or "I want to capture why we chose X over Y". Also useful when a team is debating options and wants to formalise the outcome.
---

# ADR Writer

A skill for capturing architecture decisions clearly and consistently using the [MADR (Markdown Architectural Decision Records)](https://adr.github.io/madr/) format.

ADRs serve as institutional memory. They tell future developers not just *what* was decided, but *why* — including the options that were considered and rejected.

---

## Output

A single Markdown file following MADR format, saved to `docs/decisions/NNNN-<title>.md` (or equivalent location in the project).

---

## Process

### Step 1 — Gather context

Ask the user for (or infer from context):

- **The decision title** — a short, verb-noun phrase (e.g. "Use MediatR for CQRS", "Store audit logs in separate database")
- **The context / problem** — what situation prompted this decision? What constraints apply?
- **The options considered** — at least two; three or more is ideal
- **The chosen option** — which option was selected and why
- **Consequences** — what does this decision make easier or harder going forward?

If the user hasn't thought through all options yet, help them brainstorm — ask what alternatives were discussed, even informally.

If you are running in a non-interactive context (e.g. a single-shot prompt with no follow-up possible), proceed directly: make reasonable inferences from the information provided, state your assumptions explicitly in the ADR draft (e.g. as a brief note at the start of the Context section), and skip the interactive review in Step 4.

### Step 2 — Write the ADR

Use the MADR template below. Fill in all sections. If information is missing for a section, use a sensible placeholder and flag it to the user. Omit the Links section if there are no relevant links to include.

- **Date**: Always fill in today's date in `YYYY-MM-DD` format. Never leave it as a placeholder and never rely on your training data for the current date — verify it by running `Get-Date -Format 'yyyy-MM-dd'` (Windows) or `date +%Y-%m-%d` (Linux/macOS) before writing the file.
- **Status**: Use `Accepted` when a decision has been confirmed. Use `Proposed` when the decision is still under discussion or has not been formally ratified — and add a note at the top of the Decision Outcome section such as: `> **Note:** This ADR is in *Proposed* status. No final decision has been made yet.`
- **Decision Drivers**: Always populate this section with at least two concrete drivers extracted from the user's context. These should be specific constraints or goals, not vague statements.

```markdown
# <Title>

## Status

Accepted <!-- or: Proposed | Deprecated | Superseded by [NNNN](NNNN-<title>.md) -->

## Date

YYYY-MM-DD

## Context and Problem Statement

<Describe the situation and the question that needed answering. 2–4 sentences. Focus on the forces at play, not the solution.>

## Decision Drivers

- <Driver 1 — e.g. "Must integrate with existing identity provider">
- <Driver 2 — e.g. "Team has no prior experience with X">
- <Driver 3>

## Considered Options

- Option A — <Name>
- Option B — <Name>
- Option C — <Name>

## Decision Outcome

**Chosen option: Option X — <Name>**

<Why this option was chosen. Reference the decision drivers. 2–4 sentences.>

### Positive Consequences

- <What this decision makes easier or better>

### Negative Consequences / Trade-offs

- <What this decision makes harder, or what you give up>

## Pros and Cons of the Options

### <Option A name>

<Brief description>

**Pros:**
- ...

**Cons:**
- ...

### <Option B name>

<Brief description>

**Pros:**
- ...

**Cons:**
- ...

### <Option C name> (if applicable)

<Brief description>

**Pros:**
- ...

**Cons:**
- ...

## Links

- [Related ADR](NNNN-<title>.md) <!-- optional -->
- [Reference documentation](https://...) <!-- optional -->
```

### Step 3 — Save the file

Determine the target path using the convention:

```
docs/decisions/NNNN-<kebab-case-title>.md
```

Where `NNNN` is the next sequential number in the `docs/decisions/` folder. If no ADRs exist yet (or the folder doesn't exist), use `0001`. If the folder doesn't exist, create it.

Save the ADR to **exactly one file** at the determined path — do not create additional files (e.g. `adr.md` or `draft.md`) alongside it. Then tell the user the filename you used.

### Step 4 — Review with the user

Present the draft. Ask if:
- The options are represented fairly
- Any decision drivers are missing
- The consequences section captures real trade-offs

Make edits and produce a final version.

---

## Tips

- Keep the Context section neutral — it should describe the problem, not argue for the chosen solution
- "Decision Drivers" are the criteria that matter most; good ADRs make these explicit so readers can evaluate whether the same decision would apply to their situation
- If a decision is being revisited, mark the old ADR as "Superseded by NNNN" rather than editing it
- The best time to write an ADR is immediately after the decision — memory fades fast
- Common ADR topics include: ORM choice, authentication approach, API style, caching strategy, logging infrastructure, deployment topology
