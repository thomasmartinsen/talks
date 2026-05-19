# Graph-Based Verification Guide

Reference for Phase 7: using the knowledge graph to verify that generated OpenSpec outputs actually cover the codebase. This phase is optional and only runs when `.openspec-bootstrap-tmp/graphify-out/graph.json` exists.

---

## Prerequisites

- `.openspec-bootstrap-tmp/graphify-out/graph.json` must exist (built in Phase 0.5)
- `.openspec-bootstrap-tmp/graphify-out/GRAPH_REPORT.md` should exist
- Generated specs in `openspec/specs/`
- Generated agents and instructions from Phases 4–5
- `$GRAPHIFY` variable set to `.openspec-bootstrap-venv/bin/graphify` (configured in Phase 0)

## Working Directory

All verification artifacts go in `.openspec-bootstrap-tmp/verification/`. This keeps intermediate query results out of context.

---

## Step 1: Spec Coverage Check

Verify that every god node and major community has representation in the generated specs.

### Query god nodes:

```bash
$GRAPHIFY query "list all god nodes with their community label" \
  --graph .openspec-bootstrap-tmp/graphify-out/graph.json --budget 800 \
  > .openspec-bootstrap-tmp/verification/god-nodes-list.txt
```

### Check coverage:

For each god node, determine if it's covered by a spec:

| God Node | Community | Covered By | Status |
|----------|-----------|-----------|--------|
| UserService | identity | `openspec/specs/identity/spec.md` | ✅ Covered |
| OrderProcessor | orders | `openspec/specs/orders/spec.md` | ✅ Covered |
| CacheManager | infra | *(none)* | ❌ Gap |

**Coverage formula:** `(covered god nodes / total god nodes) × 100%`

**Target:** ≥80% coverage. Below 80%, iterate on Phase 3 before presenting the output summary.

### For uncovered nodes, recommend:

```markdown
## Coverage Gaps

### CacheManager (infra community, degree 18)
- **Recommendation:** Add `openspec/specs/infrastructure/spec.md` covering caching behavior
- **Key relationships:** Connected to UserService, ProductCatalog, SessionStore
- **Rationale found:** "NOTE: 5min TTL chosen to balance freshness vs DB load" (src/cache/config.ts:12)
```

---

## Step 2: Agent Coverage Check

Verify that generated agent roles cover all major communities.

### Query communities:

```bash
$GRAPHIFY query "list all communities with node count and dominant type" \
  --graph .openspec-bootstrap-tmp/graphify-out/graph.json --budget 600 \
  > .openspec-bootstrap-tmp/verification/communities-list.txt
```

### Check coverage:

A community is "covered" if at least one generated agent role maps to its domain. Communities with <5 nodes can be ignored.

| Community | Nodes | Dominant Type | Agent Role | Status |
|-----------|-------|---------------|-----------|--------|
| identity | 42 | code (auth) | security-engineer, backend-developer | ✅ |
| orders | 38 | code (business) | backend-developer | ✅ |
| infra | 15 | code (database) | *(none specific)* | ⚠️ Consider database-expert |
| ci-cd | 8 | config | devops-engineer | ✅ |

### For uncovered communities:

Suggest adding the appropriate agent role from the catalog, or note that an existing agent should expand its scope.

---

## Step 3: Instruction Accuracy Check

Compare AST-extracted patterns against generated coding-standards instructions to catch contradictions.

### Query naming patterns:

```bash
$GRAPHIFY query "show function and class naming patterns across the codebase" \
  --graph .openspec-bootstrap-tmp/graphify-out/graph.json --budget 600 \
  > .openspec-bootstrap-tmp/verification/naming-patterns.txt
```

### Query error handling:

```bash
$GRAPHIFY query "show error handling patterns and custom error classes" \
  --graph .openspec-bootstrap-tmp/graphify-out/graph.json --budget 400 \
  > .openspec-bootstrap-tmp/verification/error-patterns.txt
```

### Check for contradictions:

Compare the graph's extracted patterns against the generated coding-standards instruction file. Flag:

- **Naming mismatches**: If the graph shows `snake_case` function names but the instruction says `camelCase`
- **Import pattern mismatches**: If the graph shows barrel exports are used but the instruction bans them
- **Error handling mismatches**: If the graph shows a `Result` pattern but the instruction documents `try/catch`

### Example contradiction report:

```markdown
## Instruction Contradictions

### Naming Convention
- **Instruction says:** "Functions use camelCase"
- **Graph shows:** 73% of functions use camelCase, 27% use snake_case (in Python modules)
- **Resolution:** Split convention by language — camelCase for TypeScript, snake_case for Python

### Error Handling
- **Instruction says:** "Use custom AppError class extending Error"
- **Graph shows:** AppError exists but 40% of catch blocks use raw Error
- **Resolution:** Instruction is aspirational (correct direction) — no change needed, but note inconsistency
```

---

## Step 4: Cross-Cutting Verification

Verify that surprising connections and bridge nodes are documented.

### Query bridge nodes:

```bash
$GRAPHIFY query "show nodes that appear in multiple communities" \
  --graph .openspec-bootstrap-tmp/graphify-out/graph.json --budget 500 \
  > .openspec-bootstrap-tmp/verification/bridge-nodes.txt
```

### Query surprising connections:

```bash
$GRAPHIFY path "<god-node-A>" "<god-node-B>" \
  --graph .openspec-bootstrap-tmp/graphify-out/graph.json \
  > .openspec-bootstrap-tmp/verification/path-A-to-B.txt
```

Use `$GRAPHIFY path` between god nodes in different communities to surface hidden dependency paths. Each surprising connection should be documented in either:
- A spec (as a cross-cutting requirement)
- An architecture instruction (as a dependency rule)
- An agent boundary definition (as a coordination point)

### Undocumented connections:

```markdown
## Undocumented Cross-Cutting Connections

### OrderProcessor → AuthMiddleware
- **Path:** OrderProcessor → validateOrder → checkPermission → AuthMiddleware
- **Impact:** Orders service depends on auth internals, not just the public API
- **Recommendation:** Document in architecture instruction as a dependency boundary violation, or add to specs/shared/auth-integration.md

### PaymentWebhook → InventoryService
- **Path:** PaymentWebhook → onPaymentSuccess → updateInventory → InventoryService
- **Impact:** Payment events trigger inventory updates — not visible from module structure
- **Recommendation:** Document as an event-driven integration in specs/orders/spec.md
```

---

## Verification Report Format

Combine all findings into `.openspec-bootstrap-tmp/verification-report.md`:

```markdown
# OpenSpec Bootstrap Verification Report

Generated on [date] using graphify knowledge graph.

## Summary

| Metric | Score | Target |
|--------|-------|--------|
| God node spec coverage | 85% (17/20) | ≥80% |
| Community agent coverage | 90% (9/10) | ≥80% |
| Instruction contradictions | 2 found | 0 ideal |
| Undocumented cross-cutting connections | 3 found | 0 ideal |

## Overall: ✅ PASS (coverage above threshold)

## Spec Coverage Gaps
[List from Step 1]

## Agent Coverage Gaps
[List from Step 2]

## Instruction Contradictions
[List from Step 3]

## Undocumented Connections
[List from Step 4]

## Recommendations
1. Add `openspec/specs/infrastructure/spec.md` to cover caching community (3 god nodes uncovered)
2. Consider adding `database-expert` agent — infra community has 15 nodes with no dedicated agent
3. Split naming convention instruction by language (TypeScript vs Python modules)
4. Document OrderProcessor → AuthMiddleware dependency in architecture instruction
```

---

## Iteration Guidance

If the verification report shows coverage below 80%:

1. Focus on **god nodes first** — they represent the highest-connectivity concepts and covering them provides the most value
2. Use `$GRAPHIFY explain <node-name>` to get a plain-language explanation of uncovered nodes before writing specs
3. Check `.openspec-bootstrap-tmp/graphify-out/wiki/` (if available) for pre-written community articles that can accelerate spec writing
4. Re-run verification after filling gaps to confirm improvement

If contradictions are found:
1. Check whether the contradiction is aspirational (the instruction describes the desired state, not current) — if so, keep the instruction but add a note
2. If the contradiction is factual (the instruction is wrong about current patterns), fix the instruction
3. When in doubt, favor what the AST actually shows over what config files suggest
