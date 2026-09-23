---
name: context7
description: Use Context7 for authoritative, version-aware external library, framework, SDK, and API documentation. Trigger when implementation or planning depends on external API behavior or current library documentation; do not use it for repository-local questions or present ordinary web search as Context7 evidence.
---

# Context7

Use Context7 only when external library or API documentation materially reduces uncertainty.

## Use it for external documentation

- Identify the actual library, framework, SDK, or API and the version or dependency range used by the repository when available.
- Prefer the configured Context7 integration. If the machine exposes the validated CLI entry point through `npx ctx7`, use that entry point rather than inventing another interface.
- Query the narrow API or behavior needed for the current task.
- Apply retrieved documentation to the repository's actual dependency version and local usage.

## Keep the boundary clear

- Do not use Context7 to answer repository-local architecture, symbol, history, or behavior questions that should be answered from the repository itself.
- Do not perform ordinary web search and describe the result as Context7 output.
- Do not make Context7 mandatory for work that does not depend on external documentation.
- If Context7 is unavailable, state that clearly and use another authoritative source only when the task allows it.

## Verify application

Treat documentation as external evidence, not proof that the local code already behaves that way. Verify important conclusions against the repository and its tests.
