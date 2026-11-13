---
name: sdlc-setup
description: Inspect and optionally configure AI SDLC for a local single-repo or multi-repo workspace (Claude Code, Cursor, Codex). Use for first-time setup, roots discovery, or repository integration—not for product implementation.
argument-hint: "<inspect|configure> [workspace roots] [claude|cursor|codex|all]"
---

# SDLC Setup — optional, non-destructive

<rules>
- The SDLC workflow is shipped in the installed plugin. NEVER copy the whole runtime or roles into a repository.
- Start READ-ONLY: discover actual Git roots and their instruction files (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, nested instructions), access permissions, source/build/tests/CI, current Git status, existing SDLC artifacts, and relevant tech stack.
- Distinguish **available/readable**, **in-scope for task**, and **authorized writable** roots. A multi-root editor window does not grant write permission to all roots.
- Offer a short repository map and exact `CREATE/MERGE/KEEP/CONFLICT/RETIRE` proposal. Ask for explicit approval before writing any workspace profile or changing instructions. Don't generate a config file if the project works without it.
- For repeated multi-repo use, optionally propose a single workspace-owned `.ai-sdlc/workspace.yaml` that names roots and known relationships; user chooses where it lives. Never write copies into all repos. Validate rather than assume declared dependency edges.
- Never install MCP servers, hooks, outside skills (Ponytail/Graphify/Superpowers), dependencies or host configs without explicit approval.
- Preserve owner and organization rules; if incompatible, surface the difference and stop the disputed edit.
- After authorized changes, run `sdlc-doctor` checks or report exactly which host discovery checks were unavailable.
</rules>

<result>
Give discovered roots/roles, instruction conflicts, proposed/approved edits, local host readiness (Claude/Cursor/Codex), Reviewer verification status, optional integration availability and next `sdlc-work` invocation. For conceptual sample structure see `../sdlc-work/references/workspace.md`.
</result>
