"""Kenwea plugin for AstrBot.

/kenwea check <npm package or https URL>  run the Kenwea notary on it
/kenwea find <words>                     search the Kenwea marketplace

Both call public Kenwea endpoints with no key. The notary is the same MCP
server at https://mcp.kenwea.com/notary/v1 that any MCP client can use; this
plugin calls its kenwea.notary.check tool over plain JSON-RPC.
"""

import json
import re

import aiohttp

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

NOTARY_URL = "https://mcp.kenwea.com/notary/v1"
PRODUCTS_URL = "https://api.kenwea.com/products"
SITE = "https://www.kenwea.com"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "MCP-Protocol-Version": "2025-11-25",
    "User-Agent": "astrbot_plugin_kenwea/1.1.0",
}
# npm names: optional @scope/, then the name, then an optional @version or tag.
NPM_NAME = re.compile(r"^(@[a-z0-9][\w.-]*/)?[a-z0-9][\w.-]*(@[\w.^~<>=*-]+)?$", re.I)

HELP = (
    "Kenwea\n"
    "/kenwea check <npm package or https URL>: run the package's install steps in a no-network sandbox, traced, and get a signed record\n"
    "/kenwea find <words>: search the Kenwea marketplace\n"
    f"More: {SITE}/verify"
)

VERDICT_NOTES = {
    "approved": "Every install step ran to completion and none tried to reach the network. This is not an endorsement.",
    "rejected": "A single file that ran and failed, or a file carrying a provider-formatted credential. Read the reason before going ahead.",
}


def _rest_after(message: str, sub: str) -> str:
    """Everything the user typed after the subcommand, kept whole.

    Read from the raw message rather than from AstrBot's argument parser, which
    splits on spaces, so "/kenwea find json editor" keeps both words.
    """
    words = (message or "").split()
    for i, word in enumerate(words):
        if word.lstrip("/").lower() == sub:
            return " ".join(words[i + 1 :]).strip()
    return ""


@register(
    "astrbot_plugin_kenwea",
    "Kenwea",
    "Check npm packages in a sandbox and search the Kenwea marketplace",
    "1.1.0",
)
class KenweaPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command_group("kenwea")
    def kenwea(self):
        pass

    @kenwea.command("help")
    async def help(self, event: AstrMessageEvent):
        yield event.plain_result(HELP)

    @kenwea.command("check")
    async def check(self, event: AstrMessageEvent):
        target = _rest_after(event.message_str, "check")
        if not target:
            yield event.plain_result(
                "Usage: /kenwea check <npm package or https URL>, for example /kenwea check lodash"
            )
            return
        if target.startswith("https://"):
            arguments = {"artifactRef": target}
        elif NPM_NAME.match(target):
            arguments = {"package": target}
        else:
            yield event.plain_result("That is not an npm package name or an https URL.")
            return
        try:
            result = await self._notary_check(arguments)
        except Exception as exc:  # network errors, timeouts, bad JSON
            logger.warning(f"kenwea notary call failed: {exc}")
            yield event.plain_result(
                "The Kenwea notary could not be reached. Try again in a minute."
            )
            return
        yield event.plain_result(self._format_check(target, result))

    @kenwea.command("find")
    async def find(self, event: AstrMessageEvent):
        query = _rest_after(event.message_str, "find")
        if not query:
            yield event.plain_result(
                "Usage: /kenwea find <words>, for example /kenwea find json editor"
            )
            return
        try:
            products = await self._search(query)
        except Exception as exc:
            logger.warning(f"kenwea search failed: {exc}")
            yield event.plain_result(
                "The Kenwea marketplace could not be reached. Try again in a minute."
            )
            return
        if not products:
            yield event.plain_result(f'Nothing on Kenwea matches "{query}".')
            return
        lines = [f'Kenwea results for "{query}":']
        for p in products[:5]:
            price = (
                "Free"
                if p.get("priceCents") == 0
                else f"{(p.get('priceCents') or 0) / 100:.2f} {p.get('currency') or 'USDT'}"
            )
            lines.append(
                f"- {p.get('title')} ({price})\n  {SITE}/products/{p.get('productId')}"
            )
        yield event.plain_result("\n".join(lines))

    async def _search(self, query: str) -> list:
        """Marketplace search. The API matches the query as one phrase, so for
        several words it searches the longest one and keeps the titles that
        contain every word."""
        words = [w.lower() for w in query.split() if w]
        phrase = query if len(words) <= 1 else max(words, key=len)
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(
            timeout=timeout, headers={"User-Agent": HEADERS["User-Agent"]}
        ) as session:
            async with session.get(
                PRODUCTS_URL, params={"q": phrase, "limit": "50"}
            ) as resp:
                body = await resp.json(content_type=None)
        products = ((body or {}).get("data") or {}).get("products") or []
        if len(words) > 1:
            products = [
                p
                for p in products
                if all(w in (p.get("title") or "").lower() for w in words)
            ]
        return products

    async def _notary_check(self, arguments: dict) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "kenwea.notary.check", "arguments": arguments},
        }
        timeout = aiohttp.ClientTimeout(total=180)
        async with aiohttp.ClientSession(timeout=timeout, headers=HEADERS) as session:
            async with session.post(NOTARY_URL, json=payload) as resp:
                body = await resp.json(content_type=None)
        if "error" in body:
            message = (body["error"] or {}).get("message") or "error"
            raise RuntimeError(message)
        result = body.get("result") or {}
        if result.get("isError"):
            text = (result.get("content") or [{}])[0].get(
                "text"
            ) or "the notary refused this request"
            return {"error": text}
        return json.loads(result["content"][0]["text"])

    @staticmethod
    def _format_check(target: str, data: dict) -> str:
        if "error" in data:
            return f"Kenwea notary: {data['error']}"
        verdict = data.get("verdict") or "unknown"
        resolved = (data.get("package") or {}).get("resolved") or target
        code = data.get("reasonCode")
        lines = [
            f"Kenwea notary: {resolved}",
            f"verdict: {verdict.upper()}" + (f" ({code})" if code else ""),
        ]
        steps = data.get("installSteps")
        if isinstance(steps, list):
            lines.append("at install: " + (", ".join(map(str, steps)) if steps else "nothing runs"))
        observed = data.get("observed")
        if isinstance(observed, dict):
            reached = [str(x) for x in (observed.get("dns") or []) + (observed.get("network") or [])]
            lines.append("reached: " + (", ".join(reached) if reached else "nothing"))
        if data.get("verdictReason"):
            lines.append(f"why: {data['verdictReason']}")
        if verdict in VERDICT_NOTES:
            lines.append(VERDICT_NOTES[verdict])
        if data.get("contentSha256"):
            lines.append(f"sha256: {data['contentSha256']}")
        lines.append(
            "Dependencies are not installed, so this covers the package's own install steps only."
        )
        lines.append(f"Check the signature yourself: {SITE}/verify")
        return "\n".join(lines)

    async def terminate(self):
        pass
