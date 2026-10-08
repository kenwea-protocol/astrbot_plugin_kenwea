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
verdict: MANUAL_REVIEW (no_install_steps)
at install: nothing runs
why: nothing of this package's own runs when it is installed: it declares no preinstall, install or postinstall script and ships no binding.gyp. ...
sha256: 870c0fe1096223a58d4f8832d08a7e651ea2fcadb8e6877b2fdc26b662d481dd
```

## What the verdict means

The plugin prints what runs at install, what those steps tried to reach, and the verdict with its reason code.

- `approved` (`ran_ok`): every install step ran to completion and none tried to reach the network. It is not an endorsement.
- `manual_review` with `ran_tried_network`: a step tried to reach the network; the reply names what.
- `manual_review` with `install_step_failed`: a step ran and failed, often for want of a dependency the check does not install. Evidence neither way.
- `manual_review` with `no_install_steps`: most packages run nothing at install, and the verdict says exactly that rather than "pass".
- `manual_review` with `step_timed_out`, `runner_busy` or `not_run`: Kenwea's own limit; nothing is concluded about the package.
- `rejected`: only for a single file that ran and failed, or a provider-formatted credential.

The verdict is signed with Kenwea's published Ed25519 key and bound to the sha256 of the bytes it read, so you can check it yourself at https://www.kenwea.com/verify without trusting Kenwea.

## Limits

- Dependencies are not installed, so the check covers the package's own install steps, not its dependency tree.
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
