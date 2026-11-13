# Workspace and multi-repository coordination

<discovery>
A workspace can be one Git repo, a monorepo, or several independent repos. Detect repository boundaries via actual local Git root / worktree metadata, not folder names, glob matches, or assumed hierarchy. Capture for each: real path, role/technology (observed or UNKNOWN), applicable instructions, current branch/HEAD, staged/unstaged/untracked changes, read/write access, available test commands and CI. Do not assume adding a directory to a host also loads its project instructions. Confirm applied instructions explicitly.

Define separate sets:
- `VISIBLE`: actual directories available/readable in host;
- `RELEVANT`: roots needed to understand/task outcome (read-only allowed);
- `EDIT_APPROVED`: roots and paths with explicit authorized changes;
- `EXCLUDED`: not to touch, including unrelated repos.

If a required root is inaccessible, report missing evidence and ask to expose it or narrow scope. Don't fake analysis or demand workspace edits just because another repository is visible. No assumed global Git transactions.
</discovery>

<impact-analysis>
For every requested outcome: map `AC → repository changes → integration evidence`; trace contracts and dependencies. Typical four-repo project:
- FE: views, validation, HTTP client, generated API clients.
- BE: endpoints, business rules, DTOs, storage mappings.
- DB/Flyway: forward migrations, rollout compatibility, existing data/backfill and rollback plan.
- Terraform: infrastructure resources, IAM/network, state, plan/apply risks.
Only use labels supported by inspection. Relevance is not authorization to edit. A change might require FE+BE+Flyway but *not* Terraform.
</impact-analysis>

<planning>
- Keep one authoritative AC set, not four contradictory specs. Record root and exact source revision per implementation slice.
- Build a dependency graph: database expand → BE compatible release → FE consumption is one possible order, NOT a universal rule. Flag incompatible API/schema/infra assumptions and inter-release skew.
- Design backwards-compatible expand/contract where relevant. For Flyway, prefer new migrations rather than mutating already-applied versioned migrations, after checking actual environment. For Terraform, `plan` is evidence, never permission for `apply`; review impact/state/secrets, and require approval to run any destructive operation.
- Parallel delegate only independent read-only exploration or changes proven nonconflicting; workers may not write the same files/worktree concurrently. Respect per-root permission boundaries and context.
</planning>

<verification>
- Check each affected repository's own relevant tests/lint/static analysis on its actual snapshot.
- Check interface contract tests, migration-to-BE schema compatibility, FE-to-BE scenarios, infrastructure inputs/outputs and deployment sequence where relevant. `NOT RUN` if integration environment cannot be exercised.
- Reviewer verifies each diff and cross-root edges. `AI_PASS` for the *whole task* is blocked when an affected root or required integration evidence was omitted.
- End with one human review summary: affected vs examined-only roots, snapshot/branch per changed repo, AC→repo→test mapping, compatibility/release order, residual risk, separate PR/merge/deploy actions. Do not claim atomic commits/rollouts.
</verification>

<optional-workspace-profile>
The plugin does not require generated config. For recurring multi-repo sessions, `sdlc-setup` may propose one user-owned `.ai-sdlc/workspace.yaml` with `schemaVersion: 1`, repository aliases/paths and verified relationships. Treat it as an *index and preference*, not as authority for files, permissions, requirements, or deployment. Never auto-commit duplicates across repos or override host trust boundaries.
</optional-workspace-profile>
