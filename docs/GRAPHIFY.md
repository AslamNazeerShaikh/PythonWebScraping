# Graphify — queryable knowledge graph of this repo

[Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) turns a
codebase into a **queryable knowledge graph** (AST-parsed, no vector store):
god nodes, communities, cross-file `calls`/`imports` edges, each tagged
`EXTRACTED` (in source) or `INFERRED`. Installed here: CLI `graphify 0.9.58`
(package `graphifyy`) + the opencode skill (`.opencode/`, `AGENTS.md`).

## Artifacts (`graphify-out/`, committed)

| File | Purpose |
|---|---|
| `graph.html` | Open in a browser — clickable force-directed graph |
| `GRAPH_REPORT.md` | Highlights: god nodes, surprising links, questions |
| `graph.json` | Full graph — `query`/`path`/`explain` read this |
| `cache/` + dotfiles | Incremental state (committed for speed) |

Current snapshot: **364 nodes · 737 edges · 12 communities**, 97% EXTRACTED,
0 API cost (code-only extraction — tree-sitter AST, nothing leaves the machine).

## This repo's map (from `GRAPH_REPORT.md`)

God nodes: `FakePage` (38 edges), `Job` (31), `run_scrape()`, `upsert_jobs()`,
`launch_context()` — i.e. fakes, validation gate, pipeline, persistence,
launcher. No import cycles. `Job` is the top cross-community bridge.

## Usage (no API key needed for code)

```bash
~/.local/bin/graphify query "what connects auth to the database?"
~/.local/bin/graphify path "run_scrape" "JobRow"
~/.local/bin/graphify explain "launch_context"
~/.local/bin/graphify update .   # after code changes (AST-only, free)
```

Docs/`.md` semantic passes need a backend key; code-only is the default here.

## Repo wiring

- `.graphifyignore` excludes `vendor/` (1000 third-party uBOL files would
  drown project communities) and `docs/evidence/` (binary noise).
  `.gitignore` is respected automatically.
- `.opencode/plugins/graphify.js` nudges toward `graphify query` before
  raw greps; `AGENTS.md` holds the query-first rules. Rebuild hooks fire on
  commit/branch-switch after `graphify hook install` (per-clone, local-only).
- Install: `uv tool install graphifyy` (official package is `graphifyy`
  double-y; command stays `graphify`). Project skill:
  `graphify install --project --platform opencode`.
