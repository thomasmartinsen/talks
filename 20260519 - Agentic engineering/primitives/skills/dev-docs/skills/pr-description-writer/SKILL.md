---
name: pr-description-writer
description: Generate a professional, well-structured pull request description from a git diff, a list of commits, or a plain-language description of what changed. Use this skill whenever anyone wants to write a PR description, needs help describing their changes, wants a pull request summary, or says things like "write my PR description", "help me describe these changes", "what should I put in the PR body", or "make my PR client-readable". Also use it when a PR description is missing, thin, or only contains a ticket number.
---

# PR Description Writer

A skill for writing pull request descriptions that communicate _why_ and _what_ — not just a list of commits.

Good PR descriptions speed up review and make the git history useful to future developers.

---

## When to use this skill

- You've finished a feature and need a PR description before requesting review
- A PR has a weak or missing description and needs improving
- The PR is stakeholder-facing and needs a professional, non-jargon tone
- You want to make sure breaking changes and testing evidence are clearly captured

---

## Input the user can provide

Accept any of the following (or a combination):

- A `git diff` or `git log --oneline` output
- A list of files changed
- A ticket/issue number or title
- A plain-language description of what changed and why
- A raw, rough draft they want polished

If the user provides nothing, ask for a brief description of the change.

---

## Process

### Step 1 — Understand the change

From the input, identify:

- **What changed** — code, config, infrastructure, tests, docs
- **Why it changed** — feature, bug fix, refactor, performance improvement, dependency update, security patch
- **Scope** — which layers / services / components are affected
- **Breaking changes** — anything that changes existing behaviour, API contracts, or DB schema

If the input is ambiguous, ask one clarifying question before drafting.

### Step 2 — Draft the PR description

Use this structure:

```markdown
## Summary

<1–3 sentences. What does this PR do and why? Write for a reader who hasn't seen the code.>

## Changes

<Bullet list of the main changes. Group by area if there are many. Use plain language — avoid implementation details that don't help a reviewer understand intent.>

- **<Area>:** <What changed and why>
- **<Area>:** <What changed and why>

## Testing

<How was this tested? Be specific. "I tested it" is not enough.>

- [ ] Unit tests added/updated ← check off items confirmed by the input; leave [ ] for items that should happen but aren't confirmed yet
- [ ] Integration tests pass
- [ ] Manual testing: <describe scenario(s) tested>

## Breaking Changes

<If none, write "None." If yes, describe what breaks and how consumers should adapt. DB schema migrations (column renames, table drops, default changes) always belong here in addition to any mention in Changes — they are breaking changes even when migrations run automatically.>

## Screenshots / Output

<Only include this section if the change has a visible effect you can illustrate — API response samples, log output, UI changes. Omit it entirely if there is nothing to show here.>

## Related

<If you have no information to put here, omit this section entirely — do not add placeholder bullets or write "not provided". Only include bullets where you have actual information.>

- Ticket: <link or reference>
- ADR: <link if an architecture decision underpins this>
- Dependencies: <other PRs that should merge first>
```

### Step 3 — Adjust tone

Determine whether the PR is internal or stakeholder-facing:

- If the user explicitly says "stakeholder-facing", "client-readable", "non-technical", or similar — apply stakeholder tone immediately without asking.
- If it's not explicit, infer from context (e.g. the description mentions business outcomes, external consumers, or a change log).
- Otherwise, default to internal tone.

**Internal PR** — technical detail is fine; reviewer is a team member.

**Stakeholder-facing PR** — Use the extended structure below instead of the standard template:

```markdown
## Summary

<The very first sentence must state the business value: "This change saves X", "Users can now Y", "The service no longer fails when Z." Put cost savings, capability gains, and solved problems in sentence one — not in What's Changing. Follow with 1–2 sentences on scope and any required reader action. Keep it to 2–3 sentences total.>

## What's Changing

<High-level bullet list. Avoid implementation detail. Focus on what the change means for the reader, not how it was built.>

## Breaking Changes

<If none, write "None." For breaking changes, use a table:>

| Change | Impact            | Required action     |
| ------ | ----------------- | ------------------- |
| <what> | <who is affected> | <what they must do> |

<Follow with a clear migration window statement if one exists.>

## Migration Guide

<Numbered steps consumers must follow to adapt. Be concrete — include field names, endpoint paths, and code patterns where helpful.>

1. <Step one>
2. <Step two>

## Why This Change?

<Optional but valuable for stakeholder PRs. Briefly explain the business or technical rationale. Helps stakeholders understand it wasn't arbitrary.>

## Timeline

<If there's a deadline or migration window, make it prominent here.>

| Milestone             | Date    |
| --------------------- | ------- |
| Change available      | Today   |
| Old behaviour removed | +N days |
```

For stakeholder-facing PRs, also:

- Replace acronyms and internal tool names with plain descriptions
- Move raw technical detail (stack traces, config snippets) to collapsible `<details>` blocks

### Step 4 — Flag assumptions

Present the draft, then add a short note at the end listing any sections where you made assumptions due to missing information — for example, if no ticket number was given, if testing approach was inferred rather than stated, or if breaking-change impact wasn't specified. This gives the user clear prompts to fill in rather than leaving them to spot gaps themselves.

Example:

> **To complete this description:** Add a ticket link in Related · Confirm whether integration tests have run · Verify the breaking changes section if there are DB migrations not mentioned.

---

## Tips

- The best PR description also works as a change log entry — write it with that dual purpose in mind
- For large PRs (>500 lines changed), suggest splitting and note the reason in the description
- If there are DB migrations in the PR, always mention them under Breaking Changes or in a dedicated Migration Notes section
- Always flag dependency version bumps, schema changes, or config changes — these need careful reviewer attention
- Keep the Summary to 3 sentences max — reviewers skim
