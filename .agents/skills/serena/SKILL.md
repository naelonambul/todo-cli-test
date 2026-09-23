---
name: serena
description: Use Serena for code-symbol and structural repository analysis when semantic navigation materially helps, especially in unfamiliar or larger codebases, cross-file symbol discovery, or targeted code understanding. Avoid it for trivial isolated edits, and prevent Serena indexing metadata from contaminating the real repository.
---

# Serena

Use Serena as a navigation and structural-analysis aid, not as repository authority.

## Decide whether Serena is worth using

Use it when symbol extraction, semantic navigation, or structural code understanding is likely to save significant manual search. Skip it for small isolated edits where direct repository inspection is faster and clearer.

## Preserve repository cleanliness

Current Serena CLI behavior may create a `.serena/` directory in the indexed project.

Default to a zero-footprint workflow for ad hoc analysis:

1. Identify the smallest sufficiently complete project/subtree needed for accurate analysis, including relevant config when necessary.
2. Copy it to a temporary location outside the repository.
3. Run Serena indexing/analysis in that temporary copy.
4. Inspect the results, then verify important conclusions against the real repository before editing.

Only index the real working tree when repository policy explicitly permits it and generated `.serena/` state is safely ignored. Never commit `.serena/` metadata.

## Avoid distorted analysis

A partial temporary copy can hide configuration, references, generated sources, or cross-tree relationships. If those are material to the question, copy a sufficiently complete tree or use direct repository inspection instead of trusting an incomplete Serena model.

## Verify conclusions

Use Serena results to locate and understand code. Confirm actual behavior in source, tests, build configuration, or runtime evidence before making consequential changes.
