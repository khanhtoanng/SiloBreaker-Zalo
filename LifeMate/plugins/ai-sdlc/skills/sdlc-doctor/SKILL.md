---
name: sdlc-doctor
description: Diagnose local AI SDLC plugin discovery, host compatibility, workspace scoping, legacy harness conflicts, migrations, and reviewer delegation in Claude Code, Cursor, or Codex.
argument-hint: "[claude|cursor|codex|all] [workspace roots]"
---

# SDLC Doctor — inspect first

<checks>
1. Identify current host, installed plugin identity, skill discovery and effective version. Report `VERIFIED / NOT VERIFIED / UNAVAILABLE` and how verified; do not equate a valid JSON file with runtime discovery.
2. Check workspace roots, actual permissions, trust/instruction loading, Git worktrees, unrelated local modifications and cross-root access.
3. Find old `.claude/skills/sdlc-work`, `.cursor/skills/sdlc-work`, `.agents/skills/sdlc-work` and legacy reviewer definitions; propose a diff-based manual retirement plan, never silently delete them.
4. Check whether a fresh independent reviewer can actually be invoked on an identifiable current snapshot. Non-editing prompt ≠ sandbox enforcement in Codex.
5. Detect conflicting host/path rules, missing files, invalid relative references, unsupported config keys and optional dependency assumptions.
6. If an optional workspace profile exists, check names and paths, schema and relationship hypotheses. Propose compatible corrections with an exact approval request before writing.
</checks>

<result>
Output a concise table: `Host | Plugin discovery | Roots | Reviewer | Issues | Next action`. Any migration/repair is a separate approved change. The installed plugin runtime is authoritative; project-owned rules remain project-owned.
</result>
