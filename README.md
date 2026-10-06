# Kenwea for AstrBot

Check an npm package in a no-network sandbox before you install it, and search the Kenwea marketplace, from any chat AstrBot runs in.

## Commands

| Command | What it does |
| --- | --- |
| `/kenwea check <package or https URL>` | Asks the Kenwea notary to fetch the exact package npm would install, run its install scripts in a container with no network, and return a signed verdict. |
| `/kenwea find <words>` | Searches the Kenwea marketplace and links the matches. |
| `/kenwea help` | Shows the commands. |

Example:

```
/kenwea check left-pad
Kenwea notary: left-pad@1.3.0
verdict: MANUAL_REVIEW
why: this package declares no preinstall, install or postinstall script, so nothing of its own runs when it is installed. ...
sha256: 870c0fe1096223a58d4f8832d08a7e651ea2fcadb8e6877b2fdc26b662d481dd
```

## What the verdict means

- `approved`: the package's install scripts ran and exited zero. It is not an endorsement.
- `rejected`: something in the install surface failed or looked dangerous. Read the reason.
- `manual_review`: nothing was run that could pass. Most packages have no install script at all, and the verdict says exactly that rather than "pass".

The verdict is signed with Kenwea's published Ed25519 key and bound to the sha256 of the bytes it read, so you can check it yourself at https://www.kenwea.com/verify without trusting Kenwea.

## Limits

- Dependencies are not installed, so the check covers the package's own install scripts, not its dependency tree.
- Code that only runs when your app calls it is not exercised.
- No account or key needed. The notary allows 20 checks an hour per network address, shared by everyone using your bot.

## Also included

A skill in `skills/kenwea/SKILL.md` that tells AstrBot's agent when to check a package before installing it. You can also connect the notary as an MCP server: in the WebUI open Extensions, MCP Servers, Add Server, and paste

```json
{"transport": "streamable_http", "url": "https://mcp.kenwea.com/notary/v1"}
```

## Privacy

The plugin sends the package name or URL you check, and your search words, to Kenwea. Nothing else is sent, and it needs no permissions on your chat platform.

## License

MIT. Kenwea: https://www.kenwea.com
