# therealcost-mcp listings log

Description used everywhere:
Free money calculators for AI agents from The Real Cost by NoBanks Nearby: credit card payoff, debt consolidation, loan cost by term, crypto trade cost and emergency fund, with the math shown and links to pre-filled calculators. Education only, not financial advice.

(The official registry's server.json description field is capped at 100 characters, so server.json keeps the short version.)

| Date | Listing | URL | Status | Notes |
|---|---|---|---|---|
| 2026-10-01 | PyPI | https://pypi.org/project/therealcost-mcp/ | BLOCKED | No PyPI token on this Mac (no ~/.pypirc, no PYPI/TWINE vars in ~/.hermes/.env). Name is free (404). Build 0.1.0 at commit 3c84228 passes twine check, 53 tests pass, wheel installs in a fresh venv and lists all 6 tools over stdio. Ryan must create the account/token, then: `TWINE_USERNAME=__token__ TWINE_PASSWORD=<token> python3.11 -m twine upload dist/*` |
| 2026-10-01 | Official MCP Registry | https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.NoBanks/therealcost-mcp | BLOCKED (waits on PyPI) | mcp-publisher 1.8.1 installed via brew; `mcp-publisher validate` says server.json is valid; README has `mcp-name: io.github.NoBanks/therealcost-mcp`. Registry checks the PyPI package, so publish after PyPI: `mcp-publisher login github` then `mcp-publisher publish`. PulseMCP and Smithery read from this registry. |
| 2026-10-01 | Glama | https://glama.ai/mcp/servers/NoBanks/therealcost-mcp | LIVE | Auto-indexed from GitHub (Finance, Education & Learning), score badge serving. "Claim" needs a Glama login (optional). |
| 2026-10-01 | awesome-mcp-servers (punkpeye) | https://github.com/punkpeye/awesome-mcp-servers/pull/15493 | PENDING REVIEW | One-line entry in Finance & Fintech, alphabetical, with Glama badge, per CONTRIBUTING.md. |
| 2026-10-01 | mcp.so | https://github.com/chatmcp/mcpso/issues/1#issuecomment-5938727954 | PENDING REVIEW | The mcp.so/submit web form now only offers the paid $39 path (not used). Submitted through the free route the maintainers run: issue #1 "Submit Your MCP Servers here". |
| 2026-10-01 | mcpservers.org (wong2 awesome-mcp-servers site) | https://mcpservers.org/submit | APPROVED (2026-10-02, per approval email to nobanksnearby@gmail.com) | Free plan, category Finance. Approved within a day of submission. wong2's GitHub list takes no PRs and points here. |
| 2026-10-01 | Smithery | https://smithery.ai/new | SKIPPED for now | Requires login; Smithery pulls from the Official MCP Registry, so check after the registry publish before submitting by hand. |
| 2026-10-01 | PulseMCP | n/a | COVERED BY REGISTRY | No direct submissions; ingests the Official MCP Registry. |
| 2026-10-01 | appcypher/awesome-mcp-servers | https://github.com/appcypher/awesome-mcp-servers | SKIPPED | Repository is archived. |
