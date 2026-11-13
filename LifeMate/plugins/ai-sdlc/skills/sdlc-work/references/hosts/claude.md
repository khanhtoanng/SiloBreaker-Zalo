# Claude Code host notes

- Local development: start `claude --plugin-dir /absolute/path/to/plugins/ai-sdlc` from a project repository. Confirm namespaced skills (typically `/ai-sdlc:sdlc-work`, `/ai-sdlc:sdlc-setup`, `/ai-sdlc:sdlc-doctor`) in a real session.
- A persistent optional local marketplace is provided at repository root `.claude-plugin/marketplace.json` if needed; it is not required for `--plugin-dir`.
- For multiple independent repos launch from a chosen root and add other roots with `--add-dir`, or otherwise provide explicit allowed access. Added directories do not guarantee automatic loading of all root-level instructions, so read relevant `CLAUDE.md` / `AGENTS.md` and nested rules explicitly.
- Use genuine Agent delegation for independent review. Bundled native `agents/sdlc-reviewer.md` should be discovered; if tool restrictions prevent Git commands, Coordinator must supply diffs and untracked content. Verify actual review context and permissions.
- No auto hooks or third-party MCP servers are bundled. Never interpret `--add-dir` as authorization to edit every added repository.
