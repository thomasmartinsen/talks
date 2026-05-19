---
name: skill-creator
description: Create new GitHub Copilot CLI skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy. Use this skill whenever anyone mentions creating, building, writing, editing, improving, or testing a Copilot CLI skill, even if they just say something like "make a skill for X" or "help me improve my skill."
---

# Skill Creator (GitHub Copilot CLI)

A skill for creating new GitHub Copilot CLI skills and iteratively improving them.

At a high level, the process of creating a skill goes like this:

- Decide what you want the skill to do and roughly how it should do it
- Write a draft of the skill
- Create a few test prompts and run Copilot-with-access-to-the-skill on them
- Help the user evaluate the results both qualitatively and quantitatively
  - While the runs happen in the background, draft some quantitative evals if there aren't any. Explain them to the user.
  - Use the `eval-viewer/generate_review.py` script to show the user the results, and also let them look at the quantitative metrics
- Rewrite the skill based on feedback from the user's evaluation of the results
- Repeat until you're satisfied
- Expand the test set and try again at larger scale

Your job is to figure out where the user is in this process and jump in to help them progress. Maybe they say "I want to make a skill for X" — you can help narrow down what they mean, write a draft, write the test cases, figure out how they want to evaluate, run all the prompts, and repeat. Or maybe they already have a draft — in that case go straight to the eval/iterate part of the loop.

Be flexible. If the user says "I don't need evals, just help me write it", do that.

After the skill is done, you can also run the description optimizer to help the skill trigger reliably.

---

## Communicating with the user

Skill creator users span a wide range — from experienced developers to first-timers. Pay attention to context cues:

- "evaluation" and "benchmark" are OK in most cases
- For technical terms like "JSON" or "assertion", check that the user knows what they mean before using them without explanation

Briefly explain terms when in doubt.

---

## Creating a skill

### Capture Intent

Start by understanding the user's intent. The current conversation might already contain a workflow the user wants to capture. Extract answers from the conversation history first — the tools used, the sequence of steps, corrections the user made, input/output formats observed. Confirm with the user before proceeding.

1. What should this skill enable Copilot to do?
2. When should this skill trigger? (what user phrases/contexts)
3. What's the expected output format?
4. Should we set up test cases? Skills with objectively verifiable outputs (file transforms, data extraction, code generation) benefit from test cases. Skills with subjective outputs (writing style, design quality) often don't need them.

### Interview and Research

Ask about edge cases, input/output formats, example files, success criteria, and dependencies. Wait to write test prompts until you've got this part ironed out.

### Write the SKILL.md

Based on the user interview, fill in these components:

- **name**: Skill identifier
- **description**: When to trigger, what it does. This is the primary triggering mechanism — include both what the skill does AND specific contexts for when to use it. All "when to use" info goes here, not in the body. Make descriptions a little "pushy" to combat undertriggering. Example: instead of "How to build a dashboard", write "How to build a dashboard. Use this skill whenever the user mentions dashboards, data visualization, or wants to display any kind of data, even if they don't explicitly ask for a 'dashboard'."
- **compatibility**: Required tools, dependencies (optional, rarely needed)
- **the rest of the skill :)**

### Skill Writing Guide

#### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic/repetitive tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons, fonts)
```

#### Progressive Disclosure

Skills use a three-level loading system:

1. **Metadata** (name + description) - Always in context (~100 words)
2. **SKILL.md body** - In context whenever skill triggers (<500 lines ideal)
3. **Bundled resources** - As needed (unlimited, scripts can execute without loading)

**Key patterns:**

- Keep SKILL.md under 500 lines; add an additional layer of hierarchy with clear pointers if approaching this limit
- Reference files clearly from SKILL.md with guidance on when to read them
- For large reference files (>300 lines), include a table of contents

**Domain organization**: When a skill supports multiple domains/frameworks, organize by variant:

```
cloud-deploy/
├── SKILL.md (workflow + selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

Copilot reads only the relevant reference file.

#### Principle of Lack of Surprise

Skills must not contain malware, exploit code, or any content that could compromise system security. Don't create misleading skills or skills designed to facilitate unauthorized access, data exfiltration, or other malicious activities.

#### Writing Patterns

Prefer the imperative form in instructions.

**Defining output formats:**

```markdown
## Report structure

ALWAYS use this exact template:

# [Title]

## Executive summary

## Key findings

## Recommendations
```

**Examples pattern:**

```markdown
## Commit message format

**Example 1:**
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

### Writing Style

Explain to the model _why_ things are important rather than using heavy-handed MUSTs. Use theory of mind and try to make the skill general. Write a draft, then look at it with fresh eyes and improve it.

### Test Cases

After writing the skill draft, come up with 2-3 realistic test prompts. Share them with the user: "Here are a few test cases I'd like to try. Do these look right, or do you want to add more?" Then run them.

Save test cases to `evals/evals.json`. Don't write assertions yet — just the prompts. You'll draft assertions while the runs are in progress.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

See `references/schemas.md` for the full schema (including the `assertions` field, which you'll add later).

---

## Running and evaluating test cases

This section is one continuous sequence — don't stop partway through.

Put results in `<skill-name>-workspace\` as a sibling to the skill directory. Within the workspace, organize by iteration (`iteration-1\`, `iteration-2\`, etc.) and within that, each test case gets a directory named **`eval-N\`** (e.g. `eval-1\`, `eval-2\`) — the aggregation script discovers directories by this `eval-N` prefix. Use `eval_name` inside `eval_metadata.json` for the human-readable name. Don't create all of this upfront — just create directories as you go.

### Step 1: Spawn all runs (with-skill AND baseline) in the same turn

For each test case, spawn two agents — one with the skill, one without. Use the `runSubagent` tool with `agentName: "Explore"` (or the default agent if Explore is unavailable) to execute each run. The `runSubagent` tool is synchronous, so launch all runs for eval-1 (with + without) before moving to eval-2, batching pairs where possible.

> **Note:** The `task` tool with `mode: "background"` is not available in all environments. Use `runSubagent` instead. This means runs are sequential rather than truly parallel — spawn both the with-skill and without-skill run for the same eval case in the same turn by calling `runSubagent` twice back-to-back descriptions, then move to the next eval.

**With-skill run prompt template:**

```
You are executing a GitHub Copilot CLI skill evaluation.

Skill to follow: Read and follow the skill at <path-to-skill>\SKILL.md
Task: <eval prompt>
Input files: <eval files if any, or "none">

Execute the task following the skill's instructions as closely as possible.
Save all outputs to: <workspace>\iteration-<N>\<eval-name>\with_skill\outputs\
Save a transcript of your steps to: <workspace>\iteration-<N>\<eval-name>\with_skill\outputs\transcript.md
Save execution metrics to: <workspace>\iteration-<N>\<eval-name>\with_skill\outputs\metrics.json
  Metrics format: {"tool_calls": {"Read": N, ...}, "total_tool_calls": N, "total_steps": N, "files_created": [...], "errors_encountered": N, "output_chars": N}
```

**Baseline run prompt template:**

- **Creating a new skill**: same prompt, no skill path, save to `without_skill\outputs\`.
- **Improving an existing skill**: snapshot the old skill first (copy to `<workspace>\skill-snapshot\`), then point the baseline agent at the snapshot. Save to `old_skill\outputs\`.

Write an `eval_metadata.json` for each test case (assertions can be empty for now). The directory is named `eval-N` but use `eval_name` for a human-readable description:

```json
{
  "eval_id": 1,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "assertions": []
}
```

### Step 2: While runs are in progress, draft assertions

Don't just wait — draft quantitative assertions for each test case and explain them to the user. If assertions already exist in `evals/evals.json`, review and explain them.

Good assertions are objectively verifiable and have descriptive names. Subjective skills are better evaluated qualitatively.

Update the `eval_metadata.json` files and `evals/evals.json` with the assertions once drafted. Also explain to the user what they'll see in the viewer.

### Step 3: As runs complete, note timing

You will be automatically notified when background agents complete. When each agent completes, note the start/end times and capture timing information. Save to `timing.json` in the run directory:

```json
{
  "total_duration_seconds": 45.0,
  "executor_start": "2026-01-15T10:30:00Z",
  "executor_end": "2026-01-15T10:30:45Z",
  "executor_duration_seconds": 45.0
}
```

### Step 4: Grade, aggregate, and launch the viewer

Once all runs are done:

1. **Grade each run** — spawn a grader agent (using `runSubagent`) that reads `agents/grader.md` and evaluates each assertion against the outputs. Save results to `grading.json` at the exact path `<eval-N>\<config>\run-1\grading.json` — the aggregation script looks for grading files at `run-1/grading.json` inside each config directory. The grading.json expectations array must use the fields `text`, `passed`, and `evidence` — the viewer depends on these exact field names.

   Grader prompt template:

   ```
   Read agents/grader.md at <skill-creator-copilot-path>\agents\grader.md and follow its instructions.

   Expectations: <list of assertion strings>
   Transcript path: <eval-N>\<config>\outputs\transcript.md
   Outputs dir: <eval-N>\<config>\outputs\

   Save grading results to: <eval-N>\<config>\run-1\grading.json
   ```

2. **Aggregate into benchmark** — run from the skill-creator-copilot directory:

   ```powershell
   python -m scripts.aggregate_benchmark <workspace>\iteration-N --skill-name <name>
   ```

   This produces `benchmark.json` and `benchmark.md`. If generating benchmark.json manually, see `references/schemas.md` for the exact schema.
   Put each with_skill version before its baseline counterpart.

3. **Do an analyst pass** — read the benchmark data and surface patterns the aggregate stats might hide. See `agents/analyzer.md` (the "Analyzing Benchmark Results" section) for what to look for.

4. **Launch the viewer** with both qualitative outputs and quantitative data:

   ```powershell
   $viewer = Start-Process -FilePath "python" `
     -ArgumentList "<skill-creator-copilot-path>\eval-viewer\generate_review.py <workspace>\iteration-N --skill-name 'my-skill' --benchmark <workspace>\iteration-N\benchmark.json" `
     -PassThru -NoNewWindow
   ```

   For iteration 2+, also pass `--previous-workspace <workspace>\iteration-<N-1>`.

   If there is no display or the environment is headless, use `--static <output_path>` to write a standalone HTML file instead of starting a server. The user can open this file directly.

5. **Tell the user** something like: "I've opened the results in your browser. There are two tabs — 'Outputs' lets you click through each test case and leave feedback, 'Benchmark' shows the quantitative comparison. When you're done, come back here and let me know."

### What the user sees in the viewer

The "Outputs" tab shows one test case at a time:

- **Prompt**: the task that was given
- **Output**: the files the skill produced, rendered inline where possible
- **Previous Output** (iteration 2+): collapsed section showing last iteration's output
- **Formal Grades** (if grading was run): collapsed section showing assertion pass/fail
- **Feedback**: a textbox that auto-saves as they type
- **Previous Feedback** (iteration 2+): their comments from last time

The "Benchmark" tab shows the stats summary: pass rates, timing, and token usage for each configuration.

Navigation is via prev/next buttons or arrow keys. When done, they click "Submit All Reviews" which saves all feedback to `feedback.json`.

### Step 5: Read the feedback

When the user tells you they're done, read `feedback.json`:

```json
{
  "reviews": [
    {
      "run_id": "eval-0-with_skill",
      "feedback": "the chart is missing axis labels",
      "timestamp": "..."
    },
    { "run_id": "eval-1-with_skill", "feedback": "", "timestamp": "..." }
  ],
  "status": "complete"
}
```

Empty feedback means the user thought it was fine. Focus improvements on where the user had specific complaints.

Stop the viewer when done:

```powershell
Stop-Process -Id $viewer.Id
```

---

## Improving the skill

This is the heart of the loop. You've run the test cases, the user has reviewed the results, and now you need to make the skill better.

### How to think about improvements

1. **Generalize from the feedback.** You're creating skills that could be used millions of times across many different prompts. Avoid fiddly overfitty changes — if there's a stubborn issue, try branching out and using different metaphors or different patterns of working.

2. **Keep the prompt lean.** Remove things that aren't pulling their weight. Read the transcripts (not just the final outputs) — if the skill is making the model waste time on unproductive steps, remove those parts.

3. **Explain the why.** Explain the reasoning behind everything you're asking the model to do. If you find yourself writing ALWAYS or NEVER in all caps, that's a yellow flag — try to reframe and explain the reasoning so that the model understands why it matters.

4. **Look for repeated work across test cases.** If all test runs independently wrote similar helper scripts or took the same multi-step approach, that's a strong signal the skill should bundle that script. Write it once, put it in `scripts/`, and tell the skill to use it.

### The iteration loop

After improving the skill:

1. Apply your improvements to the skill
2. Rerun all test cases into a new `iteration-<N+1>\` directory, including baseline runs
3. Launch the reviewer with `--previous-workspace` pointing at the previous iteration
4. Wait for the user to review and tell you they're done
5. Read the new feedback, improve again, repeat

Keep going until:

- The user says they're happy
- The feedback is all empty (everything looks good)
- You're not making meaningful progress

---

## Advanced: Blind comparison

For situations where you want a more rigorous comparison between two versions of a skill (e.g., the user asks "is the new version actually better?"), there's a blind comparison system. Read `agents/comparator.md` and `agents/analyzer.md` for the details. The basic idea: give two outputs to an independent agent without telling it which is which, and let it judge quality. Then analyze why the winner won.

Use the `runSubagent` tool for the comparator and analyzer agents.

This is optional and most users won't need it. The human review loop is usually sufficient.

---

## Description Optimization

The description field in SKILL.md frontmatter is the primary mechanism that determines whether Copilot invokes a skill. After creating or improving a skill, offer to optimize the description for better triggering accuracy.

### Step 1: Generate trigger eval queries

Create 20 eval queries — a mix of should-trigger and should-not-trigger. Save as JSON:

```json
[
  { "query": "the user prompt", "should_trigger": true },
  { "query": "another prompt", "should_trigger": false }
]
```

The queries must be realistic and specific — include file paths, personal context, column names, company names, a bit of backstory. Use a mix of lengths and some casual/abbreviated phrasing. Focus on edge cases rather than making them clear-cut.

Bad: `"Format this data"`, `"Extract text from PDF"`, `"Create a chart"`

Good: `"ok so my boss just sent me this xlsx file (its in my downloads, called something like 'Q4 sales final FINAL v2.xlsx') and she wants me to add a column that shows the profit margin as a percentage. The revenue is in column C and costs are in column D i think"`

For the **should-trigger** queries (8-10), cover different phrasings of the same intent — formal, casual, implicit. Include cases where the user doesn't explicitly name the skill but clearly needs it.

For the **should-not-trigger** queries (8-10), focus on near-misses — queries that share keywords but actually need something different. Avoid obviously irrelevant negatives.

### Step 2: Review with user

Present the eval set to the user for review using the HTML template:

1. Read the template from `assets/eval_review.html`
2. Replace the placeholders:
   - `__EVAL_DATA_PLACEHOLDER__` → the JSON array of eval items
   - `__SKILL_NAME_PLACEHOLDER__` → the skill's name
   - `__SKILL_DESCRIPTION_PLACEHOLDER__` → the skill's current description
3. Write to a temp file and open it:
   ```powershell
   $tempFile = "$env:TEMP\eval_review_<skill-name>.html"
   # (write the file)
   Start-Process $tempFile
   ```
4. The user edits queries, toggles should-trigger, adds/removes entries, then clicks "Export Eval Set"
5. The file downloads to `~/Downloads/eval_set.json` — check Downloads for the most recent version

### Step 3: Optimize the description inline

Since the GitHub Copilot CLI doesn't have access to `claude -p` for running the description optimization loop as a subprocess, perform it inline:

1. **Evaluate the current description**: For each eval query, assess whether a Copilot instance reading only the skill name + description would decide to invoke the skill. Score it pass/fail and note your reasoning.

2. **Identify failures**:
   - False negatives (should-trigger queries that the description doesn't clearly cover)
   - False positives (should-not-trigger queries that the description might accidentally match)

3. **Propose an improved description**: Rewrite the description to fix the failures. Focus on:
   - Adding keywords/contexts that should trigger the skill
   - Being more specific to avoid false positives
   - Including both what the skill does AND when to use it

4. **Re-evaluate**: Check the improved description against all eval queries again.

5. **Repeat** up to 5 times, keeping the best-scoring version.

6. **Apply the result**: Update the skill's SKILL.md frontmatter with the best description. Show the user before/after and report the scores.

### How skill triggering works

Skills appear in Copilot's `available_skills` list with their name + description, and Copilot decides whether to consult a skill based on that description. Copilot only consults skills for tasks it can't easily handle on its own — simple one-step queries may not trigger a skill even if the description matches perfectly. Complex, multi-step, or specialized queries reliably trigger skills when the description matches.

This means eval queries should be substantive enough that Copilot would actually benefit from consulting a skill.

---

## Packaging

Package the skill using:

```powershell
python -m scripts.package_skill <path\to\skill-folder>
```

This produces a `.skill` file the user can install. Tell the user the path to the resulting `.skill` file.

---

## GitHub Copilot CLI-Specific Notes

- **Sub-agents**: Use the `runSubagent` tool to spawn agents that execute test cases or grade outputs. This tool is synchronous — it blocks until the agent completes and returns the result. To parallelise, call `runSubagent` multiple times in the same tool-call batch (the skill-executor agent handles them concurrently). The `task` tool with `mode: "background"` is not available in this environment.
- **Todo tracking**: Use the `manage_todo_list` tool to track eval steps across the session. The `sql` tool is not available in this environment.
- **PowerShell**: All shell commands use PowerShell. Use `Start-Process` instead of `open`/`xdg-open`, `$env:TEMP` for temp files, and Windows-style paths with backslashes.
- **Process management**: Use `$proc = Start-Process ... -PassThru` to get a handle on background processes, and `Stop-Process -Id $proc.Id` to kill them.
- **No `claude -p`**: Description optimization runs inline (see above) rather than via subprocess.
- **Updating an existing skill**:
  - **Preserve the original name.** Note the skill's directory name and `name` frontmatter field — use them unchanged.
  - **Copy to a writeable location before editing** if the installed skill path may be read-only. Copy to a temp directory, edit there, and package from the copy.

---

## Reference files

The agents/ directory contains instructions for specialized sub-agents. Read them when you need to spawn the relevant agent.

- `agents/grader.md` — How to evaluate assertions against outputs
- `agents/comparator.md` — How to do blind A/B comparison between two outputs
- `agents/analyzer.md` — How to analyze why one version beat another

The references/ directory has additional documentation:

- `references/schemas.md` — JSON structures for evals.json, grading.json, etc.

---

Repeating the core loop for emphasis:

- Figure out what the skill is about
- Draft or edit the skill
- Run Copilot-with-access-to-the-skill on test prompts (via the `task` tool)
- With the user, evaluate the outputs:
  - Create benchmark.json and run `eval-viewer/generate_review.py` to help the user review them
  - Run quantitative evals
- Repeat until you and the user are satisfied
- Package the final skill and return it to the user

Use the `sql` tool's `todos` table to track your steps so you don't lose track.

Good luck!
