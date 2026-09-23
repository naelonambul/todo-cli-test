# Changes

Each unit of work is a **change packet**, `changes/<id>/`. The root `intent.md` and `spec.md` are the durable product baseline. There is no root plan: an active plan lives only in its packet.

`python3 scripts/repo.py status` is the index. It computes every packet's state from repository facts and authored claims. Nothing it reports is stored as a writable label.

## Packet contents

| File | Purpose |
|---|---|
| `change.json` | Authored claims only: `id`, `kind`, `base`, the `baseline` digests it was authored against, `write_scope`, and `approvals`. |
| `intent.md` | Full proposed next root `intent.md`. Only for kinds that change intent. |
| `spec.md` | Full proposed next root `spec.md`. Only for kinds that change behavior or contracts. |
| `plan.md` | How the change is implemented and proven. |
| `closure.json` | Created only when the change closes. |

Start from `changes/_template/`. For a change-local `intent.md` or `spec.md`, copy the current root file and edit the copy. It replaces the root file whole when the change closes, which makes "merged into the baseline" checkable byte for byte.

## Kinds

| Kind | Required | Optional | Inherits root baseline |
|---|---|---|---|
| `product-init` | intent, spec, plan | none | no: establishes it |
| `intent` | intent, plan | spec | yes |
| `behavior` | spec, plan | none | yes |
| `implementation` | plan | none | yes |
| `incident` | plan | spec | yes |
| `architecture` | plan | spec | yes |
| `repository` | plan | none | no: process and tooling only; may not modify an established root intent or spec |

Root `intent.md` and `spec.md` start with the `<!-- sdlc:baseline-unestablished -->` marker. The first product change is a `product-init` change, and it removes the marker when its accepted copies are merged. Until then, kinds that inherit the baseline are blocked.

## Computed state

```text
stage:      intent | spec | plan | implementation | closed
freshness:  current | stale | frozen
approval:   none | unverified | verified
readiness:  blocked | ready
```

- **Order.** Approvals follow `intent -> spec -> plan`, both in chain position and in timestamp order. A downstream approval without its upstream approval blocks.
- **Freshness.** `stale` means a recorded `baseline` digest no longer matches the root file, or an approval is bound to bytes that have since changed. A stale change is blocked until it is refreshed and re-approved.
- **Readiness.** `ready` means every chain artifact carries a current approval and nothing blocks. While a change is not ready, only its own packet may change. Any other changed path blocks.

## Approval claims

```json
{"artifact": "plan.md", "sha256": "sha256:<digest printed by status>", "by": "<owner>", "at": "2026-09-23T10:00:00Z"}
```

Only the human owner adds a claim, after reviewing exactly those bytes. `repo.py status` prints each artifact's current digest.

A digest-bound claim yields `approval=unverified`. The digest detects staleness and accidental mismatch. **It is not identity proof**: anyone, an agent included, can compute it. A claim without `sha256` counts as `none`. In solo/manual mode `unverified` is enough for readiness.

`verified` is reserved for a provider path that proves a distinct human approval under merge enforcement the agent identity cannot bypass. The template has no such path, so it never reports `verified`.

An agent-side hook or tool policy that refuses agent edits to `approvals` adds friction and an audit trail. It is still not authentication, because an agent that can edit the policy can bypass it.

## Identity and write scope

- **Local.** `--change <id>` is authoritative. A branch named `change/<id>` or `change/<id>/...`, or a diff that touches exactly one packet, is a convenience inference only. Disagreement or ambiguity blocks.
- **Pull request.** The body carries `Change-ID: <id>`. CI passes it explicitly, and a missing, repeated or unknown ID blocks. One PR is one change.
- **Scope.** Every changed path between the base (the PR base, or the merge-base with the baseline branch) and the candidate must fall inside `changes/<id>/` or match a `write_scope` pattern (`*`, `?`, `**`, trailing `/`). Patterns are relative POSIX paths with no `.` or `..` segments.

## Closure

To close a change:

1. Merge accepted change-local `intent.md` and `spec.md` into the root by replacing the root file with the packet copy.
2. Add `closure.json`:

```json
{"schema": 1, "baseline": {"spec.md": "sha256:<resulting root digest>"}, "packet_sha256": "sha256:<packet digest>", "evidence": ["<CI run or verify evidence reference>"]}
```

`baseline` lists exactly the root artifacts the packet carries. `packet_sha256` covers the packet without `closure.json`. The closure never names a commit.

A pull request can only validate a **candidate** closure: approvals current, deltas merged, digests matching the candidate tree, and evidence present. After merge, the **authoritative anchor** is derived from the baseline branch's first-parent history. It is the first commit whose tree contains `closure.json` while its first parent's tree does not. That is the squash commit (the recommended default), the merge commit, or the rebased commit that adds the file.

The change is `frozen` once its digests verify at that anchor. From then on, any byte difference under `changes/<id>/` relative to the anchor is an integrity failure. Later root baseline changes do not stale a frozen change, because it was verified at its own anchor.

Shallow history cannot establish anchors or bases, so it blocks. CI fetches full history.
