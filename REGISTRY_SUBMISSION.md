# Registry submission plan: therealcost-mcp

Prepared 2026-10-01. Nothing below has been submitted. Ryan decides each step.
Every page below was checked on 2026-10-01 (receipts at the bottom).

## Order

1. **Official MCP Registry** first. Smithery and PulseMCP read from it, so one publish reaches several directories.
2. **Glama** (indexes from the GitHub repo).
3. **mcp.so** (web form; free review queue, or an optional paid fast lane).
4. **Smithery** (web dashboard, login required).

PulseMCP is not taking direct submissions and points to the Official MCP Registry, so step 1 covers it.

## Text to submit (same everywhere)

- **Name:** The Real Cost
- **Server id (official registry):** `io.github.NoBanks/therealcost-mcp`
- **Repository:** https://github.com/NoBanks/therealcost-mcp
- **Website:** https://therealcost.nohumannearby.com
- **Short description (under 100 characters):**
  Free US money calculators with the math shown, from The Real Cost. Education only.
- **Long description:**
  The Real Cost's free money calculators as MCP tools: credit card payoff (minimum payment vs a fixed
  payment), debt consolidation (current debts vs one loan with its origination fee), loan cost by term,
  crypto trading fees and spread (round trip, break-even price rise, yearly cost of recurring buys) and
  emergency fund timelines. Every result shows the formula in words and links to the matching calculator
  on therealcost.nohumannearby.com, already filled in with the user's numbers. Pure math, no API key, no
  network calls. The math is a line-for-line port of the site's own calculators and is tested against the
  site's hand-checked cases. Education only. Not financial advice.
- **Category / tags:** Finance, Personal finance, Calculators, Education
- **Tools:** credit_card_payoff, debt_consolidation, loan_cost_by_term, crypto_trade_cost, emergency_fund, list_guides
- **License:** MIT
- **Install (stdio):** `uvx --from git+https://github.com/NoBanks/therealcost-mcp therealcost-mcp`

## 1. Official MCP Registry

Docs: https://modelcontextprotocol.io/registry/quickstart and https://modelcontextprotocol.io/registry/package-types

The registry stores metadata only and points at a published package. For a Python server that means a
**PyPI release must exist first** (Ryan's call). Ownership is proven by the line
`mcp-name: io.github.NoBanks/therealcost-mcp` in the README that PyPI shows; it is already in this
repo's README as an HTML comment, and `server.json` is already filled in.

Steps, only after Ryan approves a PyPI release:

```bash
cd /Users/nobanksnearby/Documents/Clawdbot/MCP_FACTORY/builds/therealcost-mcp
# a) PyPI release (needs Ryan's PyPI account / token)
python3.11 -m pip install --upgrade build twine
python3.11 -m build
python3.11 -m twine upload dist/*
# confirm the marker is on PyPI:
curl -s https://pypi.org/pypi/therealcost-mcp/json | grep -o "mcp-name: io.github.NoBanks/therealcost-mcp"

# b) publisher CLI
brew install mcp-publisher
mcp-publisher login github        # device code flow in the browser, as GitHub user NoBanks
mcp-publisher publish             # reads ./server.json

# c) verify
curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.NoBanks/therealcost-mcp"
```

Versions in `server.json` (both `version` fields) must match the PyPI version on every release.

## 2. Glama

Page: https://glama.ai/mcp/servers, then the "Add MCP Server" button.
Fields: GitHub repository URL, display name, short description (use the text above).
Glama runs automatic checks (license detection, security scan, health test). The repo already has a
`glama.json` naming NoBanks as maintainer, which lets the listing be claimed.

## 3. mcp.so

Page: https://mcp.so/submit (choose the "MCP Server" tab).
Fields: Repository URL (required) and Name. Sign-in may be needed.
The page offers an optional $39 one-time fee for instant publishing and featured placement; the free
review path is enough. Do not pay without Ryan.

## 4. Smithery

Page: https://smithery.ai/new (redirects to sign-in, then the new-server page).
Smithery mostly lists servers it can reach by URL or pulls from the Official MCP Registry, so after
step 1 this may already be covered; check for the listing before submitting by hand.

## Receipts (checked 2026-10-01)

- modelcontextprotocol.io/registry/quickstart: `mcp-publisher` install, `init`, `login github`, `publish`, search API.
- modelcontextprotocol.io/registry/package-types: PyPI uses `registryType: "pypi"`, ownership via `mcp-name:` in the README, comment form allowed.
- glama.ai/mcp/faq: "Add MCP Server" with GitHub repository URL, display name and short description; glama.json controls indexing.
- mcp.so/submit: form with Repository URL (required), Name, type tabs, optional $39 fast lane.
- smithery.ai/new: 308 redirect to smithery.ai/servers/new, which requires login.
- PulseMCP not taking direct submissions, points to the Official MCP Registry (third-party roundups, 2026).
