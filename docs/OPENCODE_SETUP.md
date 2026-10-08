# OpenCode Setup (v2) — plugins, skills, MCP servers

> All paths below verified live on opencode v2.0.25. The repo migrated from
> opencode 1.x config syntax; v2 reference:
> https://opencode.ai/v2/docs/config,
> https://opencode.ai/v2/docs/mcp-servers,
> https://opencode.ai/v2/docs/plugins.

## 1. Config file — `.opencode/opencode.json`

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugins": [],
  "mcp": {
    "servers": {
      "github": { "...": "remote, see §3" },
      "agent-skills": { "...": "local stdio, see §3" }
    }
  }
}
```

v1 → v2 renames that bit us (verified in server logs):

| v1 (broken on v2) | v2 (this repo) |
|---|---|
| `"plugin": [...]` (singular) | `"plugins": [...]` (plural; `[]` + auto-discovery) |
| `"mcp": { "<name>": {...} }` flat | `"mcp": { "servers": { "<name>": {...} } }` nested |
| `"enabled": true` on a server | connect automatically; use `"disabled": true` to silence |
| plugin exports `GraphifyPlugin` / `server()` | default export `{ id, setup(ctx) }` |

Do NOT list `.opencode/plugins/*.js` files in `"plugins"` — they are
auto-discovered, and an explicit entry is misread as an npm package spec
(`NpmInstallFailedError`, `plugin check` → `check failed`).

## 2. Plugin — `.opencode/plugins/graphify.js`

v2 shape (`export default { id: "graphify", async setup(ctx) {...} }`),
registers `ctx.tool.hook("execute.before")` to prepend a knowledge-graph
reminder to the first `bash` call when `graphify-out/graph.json` exists.
Reference implementation copied from
https://github.com/AslamNazeerShaikh/QuarkZip/blob/main/.opencode/plugins/graphify.js.

## 3. MCP servers

| Server | Type | Purpose | Auth / env |
|---|---|---|---|
| `github` | remote `https://api.githubcopilot.com/mcp/` (`oauth: false`) | GitHub platform tools for the agent | `Authorization: Bearer {env:GITHUB_PERSONAL_ACCESS_TOKEN}` — export it, never commit it (see `.env.example`) |
| `agent-skills` | local stdio `npx -y awesome-agent-skills-mcp` | On-demand catalog of 300+ agent skills (VoltAgent awesome-agent-skills): `list_skills`, `get_skill`, `invoke_skill`, `refresh_skills` | none. `SKILLS_CACHE_DIR=~/.cache/awesome-agent-skills`, `SKILLS_SYNC_INTERVAL=60` |

`agent-skills` notes (all verified live, details in
`docs/LINKEDIN_RESEARCH.md` §4):

- Cold start takes ~96 s (repo sync + README parse) → per-server
  `timeout: { startup: 180000, catalog: 120000 }` (default 30 s times out).
- Runs with `"codemode": false`: its tools declare `outputSchema` but
  return text-only content, which Code Mode rejects.
- Its search index is lossy — verify any skill against the catalog README
  before relying on it.

## 4. Skills — `.opencode/skills/`

Auto-discovered by OpenCode (directory with `SKILL.md`, or flat `*.md`).
Current: `graphify/` (knowledge-graph workflow — see `docs/GRAPHIFY.md`).

## 5. Verify (run after any change here)

```bash
opencode plugin list    # expect: graphify  local  .../graphify.js
opencode plugin check   # expect: No package plugins found
opencode mcp list       # expect: ✓ agent-skills + ✓ github (connected)
opencode debug config   # resolved merge of global + project configs
```

To silence a server without deleting it: `"disabled": true` on the entry.
