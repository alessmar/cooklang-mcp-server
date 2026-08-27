"""FastMCP server that exposes the CookCLI recipe server to a coding agent.

Wraps the HTTP API of `cook server` (as run by the ghcr.io/cooklang/cookcli
container) so an agent can browse, read, write and delete Cooklang recipes as
MCP tools.

Run:  COOKLANG_SERVER_URL=http://localhost:9080 python server.py
"""

import os

import httpx
from fastmcp import FastMCP

BASE_URL = os.environ.get("COOKLANG_SERVER_URL", "http://localhost:9080")

mcp = FastMCP("cooklang")
http = httpx.Client(base_url=BASE_URL, timeout=15.0)


@mcp.tool
def list_recipes() -> dict:
    """Return the full recipe tree: folders and .cook / .menu files.

    Every node has children, name, path, recipe. `recipe` is null for a
    directory and non-null for a file.
    """
    r = http.get("/api/recipes")
    r.raise_for_status()
    return r.json()


@mcp.tool
def read_recipe(path: str, scale: float = 1.0) -> dict:
    """Read one recipe parsed into ingredients, cookware, timers and steps.

    path: recipe path relative to the recipe directory, e.g.
    "Dolci/bunet-piemontese" (the .cook extension is optional).
    scale: multiply quantities by this factor during parsing.
    """
    r = http.get(f"/api/recipes/{path}", params={"scale": scale})
    r.raise_for_status()
    return r.json()


@mcp.tool
def read_recipe_source(path: str) -> str:
    """Return the raw Cooklang source text of a recipe, frontmatter included."""
    r = http.get(f"/api/recipes/raw/{path}")
    r.raise_for_status()
    return r.text


@mcp.tool
def write_recipe(path: str, source: str) -> dict:
    """Create or overwrite a recipe. `source` is raw Cooklang text.

    The parent folder must already exist. A missing .cook extension is added
    automatically. Writes are atomic (temp file + rename).
    """
    r = http.put(
        f"/api/recipes/{path}",
        content=source.encode("utf-8"),
        headers={"Content-Type": "text/plain; charset=utf-8"},
    )
    r.raise_for_status()
    return r.json()


@mcp.tool
def delete_recipe(path: str) -> dict:
    """Permanently delete a recipe file. There is no undo and no trash."""
    r = http.request("DELETE", f"/api/recipes/{path}")
    r.raise_for_status()
    return r.json()


@mcp.tool
def search_recipes(query: str) -> list[dict]:
    """Full-text search over recipe names and content. Returns name + path."""
    r = http.get("/api/search", params={"q": query})
    r.raise_for_status()
    return r.json()


@mcp.tool
def collection_stats() -> dict:
    """Return collection counts (recipe_count, menu_count, pantry_* counts)."""
    r = http.get("/api/stats")
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    # stdio transport: what a local coding agent (Claude Code, etc.) expects.
    mcp.run()
