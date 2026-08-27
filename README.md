# cooklang-mcp-server

A small [FastMCP](https://gofastmcp.com) server that exposes the
[CookCLI](https://cooklang.org/cli/) recipe server (`cook server`, as shipped in
`ghcr.io/cooklang/cookcli`) to a coding agent as MCP tools. With it, an agent can
browse, read, write, delete and search [Cooklang](https://cooklang.org) recipes
over the CookCLI HTTP API.

## How it works

```
coding agent  <--stdio/MCP-->  server.py  <--HTTP-->  cook server  <-->  .cook files
```

`server.py` is a thin wrapper: each MCP tool maps to one CookCLI HTTP endpoint.
State lives entirely in the CookCLI server and its recipe directory.

## Tools

| Tool | Maps to | Purpose |
|------|---------|---------|
| `list_recipes()` | `GET /api/recipes` | Full recipe tree (folders + `.cook` / `.menu` files) |
| `read_recipe(path, scale=1.0)` | `GET /api/recipes/{path}` | One recipe parsed into ingredients, cookware, timers, steps |
| `read_recipe_source(path)` | `GET /api/recipes/raw/{path}` | Raw Cooklang source, frontmatter included |
| `write_recipe(path, source)` | `PUT /api/recipes/{path}` | Create or overwrite a recipe from raw Cooklang text |
| `delete_recipe(path)` | `DELETE /api/recipes/{path}` | Permanently delete a recipe file (no undo, no trash) |
| `search_recipes(query)` | `GET /api/search?q=` | Full-text search over recipe names and content |
| `collection_stats()` | `GET /api/stats` | Collection counts (`recipe_count`, `menu_count`, pantry counts) |

`path` is relative to the CookCLI server's recipe directory, e.g.
`Dolci/bunet-piemontese` (the `.cook` extension is optional). `write_recipe`
requires the parent folder to already exist and writes atomically (temp file +
rename). Title images are not writable over HTTP: drop them next to the `.cook`
file in the recipe directory (or Docker volume).

## Requirements

- Python >= 3.10 and [uv](https://docs.astral.sh/uv/)
- A running CookCLI server, e.g.:

  ```bash
  docker run -d --name cooklang-cookcli-1 -p 9080:9080 \
    -v cooklang_recipes:/recipes \
    ghcr.io/cooklang/cookcli server --host 0.0.0.0 /recipes
  ```

  or, with CookCLI installed locally, `cook server ./my-recipes`.

## Register with Claude Code

No clone needed. `uvx` fetches, builds and caches the server straight from this
repo:

```bash
claude mcp add cooklang \
  --env COOKLANG_SERVER_URL=http://localhost:9080 \
  -- uvx --from git+https://github.com/alessmar/cooklang-mcp-server cooklang-mcp-server
```

Or in `.mcp.json` / `~/.claude.json`:

```json
{
  "mcpServers": {
    "cooklang": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/alessmar/cooklang-mcp-server",
               "cooklang-mcp-server"],
      "env": { "COOKLANG_SERVER_URL": "http://localhost:9080" }
    }
  }
}
```

`COOKLANG_SERVER_URL` defaults to `http://localhost:9080`. Pin a version by
appending `@<tag>` to the git URL, e.g. `...cooklang-mcp-server@v0.1.0`.

## Local development

```bash
git clone https://github.com/alessmar/cooklang-mcp-server
cd cooklang-mcp-server
uv sync
COOKLANG_SERVER_URL=http://localhost:9080 uv run cooklang-mcp-server
```

## Notes

- The CookCLI server has no auth and open CORS: keep it on localhost or a trusted LAN.
- `/api/reload` is a no-op on current CookCLI: the server reads from disk on every
  request, so file changes made outside the API are picked up immediately.

## License

MIT. See [LICENSE](LICENSE).
