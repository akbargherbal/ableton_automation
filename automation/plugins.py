"""automation.plugins — external plugin discovery and resolution.

Mirrors MCP_Server/server.py's matching so plugins can be resolved and loaded
straight through the LOM client, without a running MCP host.
"""

from __future__ import annotations

import re

from .lom import LomClient, discover_plugins

_CACHE: dict[str, list[dict]] = {}


def normalize(value: str) -> str:
    if not value:
        return ""
    cleaned = re.sub(r"[\s\-_]+", " ", value.strip().lower())
    return re.sub(r"\s+", " ", cleaned)


def _tokens(value: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", value.lower()) if t]


def match_score(plugin_name: str, query: str) -> int:
    name = normalize(plugin_name)
    q = normalize(query)
    if not q:
        return 1
    if name == q:
        return 1000
    if name.startswith(q):
        return 900
    query_tokens = _tokens(query)
    name_tokens = set(_tokens(plugin_name))
    if query_tokens and all(t in name_tokens for t in query_tokens):
        return 700 + sum(len(t) for t in query_tokens)
    if q in name:
        return 600 + len(q)
    return 0


def list_plugins(client: LomClient, refresh: bool = False) -> list[dict]:
    key = f"{client.host}:{client.port}"
    if not refresh and key in _CACHE:
        return _CACHE[key]
    found = discover_plugins(client)
    _CACHE[key] = found
    return found


class AmbiguousPlugin(LookupError):
    """More than one plugin matched with equal strength."""


def plugin_haystack(plugin: dict) -> str:
    """Searchable text for a plugin: its browser name plus its vendor path.

    Plugin browser names are often vendor-less ("Pro-Q 4"), so matching against
    "FabFilter" only works if the path (plugins/FabFilter/Pro-Q 4) is included.
    """
    return f"{plugin.get('name', '')} {plugin.get('path', '')}"


def resolve_plugin(client: LomClient, query: str, exact: bool = False,
                   refresh: bool = False) -> dict:
    """Return the single best plugin match, or raise LookupError."""
    plugins = list_plugins(client, refresh=refresh)
    scored = [(max(match_score(p["name"], query), match_score(plugin_haystack(p), query)), p)
              for p in plugins]
    if exact:
        scored = [(s, p) for s, p in scored if s >= 1000]
    scored = [(s, p) for s, p in scored if s > 0]
    if not scored:
        raise LookupError(
            f"No external plugin matched {query!r}. "
            f"Try list_plugins() for the {len(plugins)} discovered plugins."
        )
    top = max(s for s, _ in scored)
    winners = [p for s, p in scored if s == top]
    if len(winners) > 1 and top < 1000:
        names = ", ".join(p["name"] for p in winners[:5])
        raise AmbiguousPlugin(
            f"Multiple plugins match {query!r}: {names}. Be more specific "
            "(include the vendor) or pass exact=True."
        )
    return winners[0]
