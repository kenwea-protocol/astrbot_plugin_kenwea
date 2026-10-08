---
name: kenwea
description: Before installing an npm package or running a downloaded file, check what it does at install time with the Kenwea notary, and search the Kenwea marketplace for digital products.
---

# Kenwea

Use this skill when the user is about to install an npm package they do not already trust, asks whether a package is safe to install, or wants to find a tool or digital product on the Kenwea marketplace.

## Check a package

Run the plugin command `/kenwea check <package-name>` (an https URL to a file, an npm tarball or a Python wheel also works), or, if the Kenwea notary MCP server is connected, call its `kenwea.notary.check` tool with `package` or `artifactRef`.

Kenwea fetches the exact bytes npm would install, runs the install steps npm would run in a container with no network, no capabilities, a read-only filesystem and no root, traces what each step attempts, and returns a record signed with Kenwea's published Ed25519 key and bound to the sha256 of what it read.

Read the result this way (the plugin prints `at install`, `reached` and the reason code):

- `at install` (`installSteps`) is what runs when the package is installed; "nothing runs" means nothing of its own does.
- `reached` and `started` (`observed`) are what those steps attempted: network addresses, DNS names and programs.
- `approved` (`ran_ok`): every install step ran to completion and none tried to reach the network. Not an endorsement and not a statement that the code is good or safe for this use; a script written to notice it is being watched can stay quiet.
- `manual_review` with `ran_tried_network`: a step tried to reach the network. Tell the user what it reached and ask before installing.
- `manual_review` with `install_step_failed`: a step ran and failed. Dependencies are not installed, so this is often for want of one; the output shows which. It is evidence neither way, so say that.
- `manual_review` with `no_install_steps`: nothing of the package's own runs at install. Useful to know, and not a pass.
- `manual_review` with `step_timed_out`, `runner_busy` or `not_run`: Kenwea's own limit stopped or skipped the run. Say so; nothing is concluded about the package.
- `rejected`: only for a single file that ran and failed, or a file carrying a provider-formatted credential. Show the user the reason before going ahead.

Always tell the user the limits: dependencies are not installed, so the check covers the package's own install steps and not its dependency tree, and code that runs only when the app calls it is not exercised. Without a key the limit is 20 checks an hour per network address.

## Search the marketplace

Run `/kenwea find <words>`. Results link to https://www.kenwea.com. Never buy anything for the user; buying happens on the website, by the user.

## Connect the notary as an MCP server (optional)

In the AstrBot WebUI, open Extensions, then MCP Servers, then Add Server, and paste:

```json
{"transport": "streamable_http", "url": "https://mcp.kenwea.com/notary/v1"}
```

It needs no key. Tools: `kenwea.notary.check`, `kenwea.notary.verify`, `kenwea.notary.getPublicKey`.
