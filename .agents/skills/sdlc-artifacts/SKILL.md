---
name: sdlc-artifacts
description: Manage change packets (`changes/<id>/`) and the root `intent.md`/`spec.md` baseline. Use when starting a product or a change, interrogating requirements, drafting or revising intent/spec/plan, preparing an owner approval, checking readiness, deciding whether implementation is authorized, or closing a change.
---

# SDLC Artifacts

The lifecycle rules are executable. `python3 scripts/repo.py status --change <id>` computes stage, freshness, approval and readiness, and blocks out-of-order, stale, or out-of-scope work. `changes/README.md` defines the model. This skill covers the judgment around it.

## Start a change

1. Pick an id (lowercase, digits, inner hyphens) and a kind from `changes/README.md`. A new product's first change is `product-init`.
2. Copy `changes/_template/` to `changes/<id>/`. For a change-local `intent.md` or `spec.md`, copy the current root file into the packet and edit the copy.
3. Fill in `change.json`:
   - `base.commit`, the commit the change starts from;
   - `baseline`, the root `intent.md` and `spec.md` digests printed by `status`, for kinds that inherit the baseline;
   - `write_scope`, the paths the change needs, as narrow as practical.
4. Work on a branch named `change/<id>`, and use `Change-ID: <id>` in the pull request.

## Develop each artifact in order

- **Intent.** Interrogate ambiguity before drafting: problem, outcome, affected users and systems, constraints, scope, success criteria, and open questions. Any agent-specific interrogation interface is a convenience only.
- **Spec.** Only after the intent is approved. Turn it into requirements, behavior, design, interfaces, data, dependencies, risks, and acceptance criteria. Carry unresolved questions forward instead of inventing answers.
- **Plan.** Only after the spec is approved, or inherited for kinds that carry no spec. Write it so an agent with no conversation history can implement it: files and components, order of work, proof, risks, and rollback. Challenge the riskiest step.

Never let a downstream artifact silently contradict an approved upstream one. Surface the conflict to the owner.

## Approval

- Only the human owner approves. Never infer approval from content, Git state, an earlier message, or your own judgment.
- When asked to record an approval the owner has explicitly given in this session, add a claim with the digest `status` prints for exactly the reviewed bytes. Editing the artifact afterwards makes the claim stale, which is intended.
- Describe local approval honestly: it is `unverified` process metadata. It detects staleness but does not prove identity.

## Implement

- Implement only when `status --change <id>` reports `readiness=ready`. Before that, change nothing outside the packet.
- Read the approved intent, spec and plan throughout. The plan is not the only authority.
- If a material departure from the approved plan is needed, stop, revise `plan.md`, and get a fresh owner approval.
- Never revise an approved upstream artifact to make implementation easier or to justify code after the fact.

## Close

Follow the Closure section of `changes/README.md`: merge accepted deltas into the root, add `closure.json` with evidence, and let CI validate the candidate. After merge the packet is frozen: never edit it again. Record follow-up work as a new change.
