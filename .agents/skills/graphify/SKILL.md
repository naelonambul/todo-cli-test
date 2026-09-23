---
name: graphify
description: Use Graphify for architecture, dependency, call, and cross-file relationship analysis when a source graph materially improves understanding. Trigger for structural or cross-cutting questions; skip routine small edits, keep generated graph output outside the repository, and verify graph conclusions against source.
---

# Graphify

Use Graphify when the problem is genuinely graph-shaped: architecture, cross-file dependencies, call relationships, or broad structural impact.

## Use it selectively

Good candidates include:

- unfamiliar architecture with many interacting files;
- dependency or call relationships that are difficult to establish by direct search;
- cross-cutting refactors where affected relationships matter;
- structural review where a source graph can test an architectural assumption.

Do not make Graphify a ritual for small isolated changes.

## Keep output outside the repository

Use Graphify's output option to write generated results to a temporary location outside the repository, for example under `/tmp`, rather than leaving `graphify-out/` or other generated graph data in the working tree.

If exact CLI syntax or output format is uncertain, inspect the installed command's help instead of guessing flags.

## Verify conclusions

Treat generated graphs as analysis aids. Confirm consequential relationships in the actual source, configuration, and tests before changing code or declaring impact.
