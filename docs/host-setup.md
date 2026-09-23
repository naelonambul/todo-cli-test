# One-time host setup (GitHub)

GitHub does not copy repository settings from a template. Configure each repository created from it separately. None of this changes the repository's contents.

## Merge policy

- Allow **squash merge** only (recommended), with one change per pull request. `repo.py` derives each change's closure anchor from the first-parent history of `main`, so merge commits and rebase-merges also work if a project prefers them.
- Keep `main` linear enough that first-parent history is meaningful: no direct pushes that bypass pull requests.

## Required check

Where the plan allows it (public repositories, or private repositories on GitHub Pro, Team, or Enterprise), protect `main` with a branch protection rule or ruleset:

- Require the **`summary`** status check from the `repository` workflow. It fails unless every job succeeded.
- Require branches to be **up to date** before merging (strict checks), so the validated candidate is the merge candidate.
- Block force pushes and deletion of `main`.

On a private repository on GitHub Free, the branch protection and rulesets APIs return 403 ("Upgrade to GitHub Pro or make this repository public"). CI is then **advisory**. The post-merge `push` run on `main`, which runs the full suite and validates closures, is the first authoritative gate on the merged tree.

## Trust mode

Decide two things explicitly and record the decision in `docs/`:

1. **Does the coding agent use a distinct, constrained GitHub identity?** A pull-request author cannot approve their own pull request. If the agent and the owner share one identity, provider reviews cannot show independent owner approval.
2. **Can `main` be enforced?** See above.

| Setup | Approval that may be claimed |
|---|---|
| Shared identity, or no enforcement | `unverified`: digest-bound local claims; staleness detection, not identity proof |
| Distinct agent identity **and** enforced required review plus required `summary` check | Provider-verified approval becomes possible. `repo.py` still reports `unverified`, because the template has no provider-verification path. |

A distinct agent identity without enforcement is useful for provenance but is not verified approval.
