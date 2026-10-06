---
name: kenwea
description: Before installing an npm package or running a downloaded file, check what it does at install time with the Kenwea notary, and search the Kenwea marketplace for digital products.
---

# Kenwea

Use this skill when the user is about to install an npm package they do not already trust, asks whether a package is safe to install, or wants to find a tool or digital product on the Kenwea marketplace.

## Check a package

Run the plugin command `/kenwea check <package-name>` (an https URL to a file, an npm tarball or a Python wheel also works), or, if the Kenwea notary MCP server is connected, call its `kenwea.notary.check` tool with `package` or `artifactRef`.

Kenwea fetches the exact bytes npm would install, runs the package's own install scripts in a container with no network, no capabilities and a read-only filesystem, and returns a verdict signed with Kenwea's published Ed25519 key, bound to the sha256 of what it read.

Read the verdict this way:

- `approved`: the install surface ran and exited zero. Not an endorsement, and not a statement that the code is good.
- `rejected`: something in the install surface failed or looked dangerous. Show the user the reason before going ahead.
- `manual_review`: Kenwea did not run anything it could pass. Read the `why` line. Most often the package declares no install script, so nothing of its own runs at install time; other times it names a limit on Kenwea's side. Tell the user which.

Always tell the user the limits: dependencies are not installed, so the check covers the package's own install scripts and not its dependency tree, and code that runs only when the app calls it is not exercised. Without a key the limit is 20 checks an hour per network address.

## Search the marketplace

Run `/kenwea find <words>`. Results link to https://www.kenwea.com. Never buy anything for the user; buying happens on the website, by the user.

## Connect the notary as an MCP server (optional)

In the AstrBot WebUI, open Extensions, then MCP Servers, then Add Server, and paste:

```json
{"transport": "streamable_http", "url": "https://mcp.kenwea.com/notary/v1"}
```

It needs no key. Tools: `kenwea.notary.check`, `kenwea.notary.verify`, `kenwea.notary.getPublicKey`.
