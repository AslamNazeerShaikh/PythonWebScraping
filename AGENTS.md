## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Agent Skills (OpenCode)

This project uses skills installed under `.opencode/skills/` (plus shared
checklists under `.opencode/references/`), per
https://github.com/addyosmani/agent-skills/blob/main/docs/opencode-setup.md.

### Core Rules

- If a task matches a skill, invoke it with the `skill` tool before acting.
- Skills live in `.opencode/skills/<skill-name>/SKILL.md`; follow the skill
  workflow strictly; do not partially apply it.
- Never skip required steps such as spec, plan, or test when a skill demands
  them. Project gates are non-negotiable: `pytest` must stay at
  100% coverage (`--cov-fail-under=100`), SQLite stays the source of truth,
  no CAPTCHA solving, no secrets in commits.
- Commit messages follow Conventional Commits v1.0.0
  (see `docs/CONVENTIONAL_COMMITS.md`): `<type>[scope]: <description>`.
- Framework calls must be source-driven: verify against official docs and
  cite URLs (spec in `docs/WEB_API.md` lists the canonical sources).

### Intent → Skill Mapping

- Feature / new endpoint or UI → `spec-driven-development`, then
  `api-and-interface-design` (contract first), `incremental-implementation`,
  `test-driven-development`
- WebAPI structure / routers / layout → `api-and-interface-design` plus the
  FastAPI bigger-applications guide (`src/web/main.py` + `routers/` + `dependencies.py`)
- Planning / breakdown → `planning-and-task-breakdown`
- Bug / failure / unexpected behavior → `debugging-and-error-recovery`
- Code review → `code-review-and-quality`
- Refactoring / simplification → `code-simplification`
- UI work (dashboard) → `frontend-ui-engineering` (Tailwind v4 + IBM Plex Mono,
  flat zinc/emerald, no AI-slop aesthetics)
- API docs / decisions → `documentation-and-adrs` (update `docs/WEB_API.md`)
- High-stakes or unfamiliar change → `doubt-driven-development`
- New dependency or framework pattern → `source-driven-development`
- Security question / focused review → `security-audit` (guidance mode only)
- Explicit codebase audit / pen test / full security review, or requested
  report artifacts → `security-audit` (full six-phase audit mode). Run the
  Node validators in `.opencode/skills/security-audit/` against
  `coverage-ledger.json` and `findings.json` as the skill directs. Default
  output directory is outside the repo unless the user picks an
  ignored path.

### Execution Model

For every request:

1. Determine if any skill applies (even a small chance). Combine with the
   graphify rules above: codebase questions go through the graph first.
2. Load the skill with the `skill` tool.
3. Follow the skill workflow exactly (spec → plan → tasks → implement).
4. Verify with the repo's own commands (`pytest`, live `curl` against the
   running server) before declaring done.
