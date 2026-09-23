# Agent Evals

Regression evaluations for repository agent behavior and configuration.

There are deliberately none yet. Deterministic checks (`scripts/repo.py`, its tests, CI) come first. Add an eval only when a real agent failure occurs that those checks cannot cheaply express, for example:

- a repeated agent mistake or a review finding that should not recur;
- an incident or escaped defect caused by agent behavior;
- a change to `AGENTS.md`, skills, hooks, or agent-driving configuration that needs regression coverage.

Each eval is the smallest case that reproduces the failure, plus the checks that make a result acceptable. Prefer real discriminating cases over synthetic filler.
