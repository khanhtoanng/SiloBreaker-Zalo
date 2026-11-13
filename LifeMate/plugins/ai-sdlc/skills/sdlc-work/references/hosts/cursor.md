# Cursor host notes

- Local development: copy the plugin folder (including `.cursor-plugin/plugin.json`, `skills/`, `agents/`) into `~/.cursor/plugins/local/ai-sdlc/`; then restart/reload Cursor and inspect Customize → Plugins. A symlink pointing outside the local plugin folder can be skipped by Cursor.
- Cursor-native manifest enables skills plus `agents/sdlc-reviewer.md`. Verify that it is discovered, and that native delegated review actually ran; don't infer it from a YAML file alone.
- Multi-root Cursor workspace can contain independent repositories. The runtime must inspect instructions in every relevant root and verify access; a local IDE session is different from restricted cloud/worktree execution.
- Project rules and `AGENTS.md` / `CLAUDE.md` remain project-owned. Do not auto-add an always-on rule for all projects; invoking `sdlc-work` is explicit.
- Cursor plugin format is host-native; portable `plugin.json` is kept for Claude/Codex interoperability. Test both current host interpretation and plugin discovery before using native-specific claims.
