# Agent surface support

`AGENTS.md` is the canonical repository instruction source, and `.agents/skills/` holds the only copy of each shared skill. Whether a given agent surface actually receives them depends on the host, its version, and user or admin settings. This page records what has been smoke-tested. A surface is supported only when a smoke test on that surface passes.

Hard repository rules must never depend on an agent having read `AGENTS.md`. They are enforced by `scripts/repo.py`, tests, and CI.

## Claude Code

### Instructions

Claude Code's built-in `agents-md` behavior (default mode `claude-md-or-agents-md`) loads `AGENTS.md` only as a fallback:

- A project `CLAUDE.md`, `.claude/CLAUDE.md`, or `CLAUDE.local.md` between the project root and the working directory **shadows** `AGENTS.md`. The fallback stays out unless that file imports it with a line such as `@AGENTS.md`.
- User or managed settings can select a mode (`claude-md`, `managed-only`) in which project `AGENTS.md` is never loaded, with no repository change.
- Explore and Plan agents, and custom agents configured with `omitClaudeMd`, receive no project instructions at all.

For these reasons the template ships **no** `CLAUDE.md`. If a project adds one, it must import `AGENTS.md` rather than restate or replace it. `CLAUDE.local.md` is a personal, untracked file, so it can silently disable the fallback on one machine. Avoid it, or import `AGENTS.md` from it.

### Skills

Claude Code discovers project skills under `.claude/skills/`, not `.agents/skills/`. Each skill therefore has a thin adapter: a relative symlink `.claude/skills/<name> -> ../../.agents/skills/<name>`. Edit only the canonical body under `.agents/skills/`.

On checkouts where Git symlinks are disabled (for example Windows with `core.symlinks=false`), each adapter becomes a small text file that contains the link target. The skills are then silently unavailable. Enable symlinks (`git config core.symlinks true`, plus Windows Developer Mode or equivalent privilege) and re-checkout.

## Smoke-test results

| Date | Surface | Setup | `AGENTS.md` delivered | Project skills discovered |
|---|---|---|---|---|
| 2026-09-23 | Claude Code CLI 2.1.280 | no `CLAUDE.md`, no `.claude/skills` adapters | yes | 0/5 |
| 2026-09-23 | Claude Code CLI 2.1.280 | no `CLAUDE.md`, adapters present | yes | 5/5 |
| 2026-09-23 | Claude Code CLI 2.1.280 | `CLAUDE.md` without `@AGENTS.md`, adapters present | **no** (shadowed) | 5/5 |
| 2026-09-23 | Claude Code CLI 2.1.280 | `CLAUDE.md` importing `@AGENTS.md`, adapters present | yes | not asked |
| 2026-09-23 | Claude desktop app (Code tab) | session opened before adapters existed | not observed | not observed |

The desktop app is **not verified**. Re-run the procedure below from a desktop session before claiming support. No other agent surface (Codex, Cursor, …) has been tested.

## Smoke-test procedure

Run it against a scratch copy of the repository, never the working checkout:

```sh
git clone . /tmp/agent-smoke && cd /tmp/agent-smoke
claude -p 'Answer from your loaded context only; do not call any tool. Line 1: "AGENTS=yes" if your context contains a document headed "Repository Agent Instructions", else "AGENTS=no". Line 2: "SKILLS=" followed by a comma-separated list of the project skills listed as available to you.' \
  --disallowedTools "Read,Bash,Grep,Glob,Edit,Write,Agent"
```

Keep the `Skill` tool allowed. Some hosts do not list skills when it is disallowed. Repeat the command with a shadowing `CLAUDE.md` to confirm the negative case, then add a row to the results table.
