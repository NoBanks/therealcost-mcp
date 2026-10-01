# therealcost-mcp

**Free money calculators for AI agents, from [The Real Cost](https://therealcost.nohumannearby.com).**

The Real Cost by NoBanks Nearby is a free set of US money calculators with the math shown:
credit card payoff, debt consolidation, loan cost by term, crypto trading fees and emergency fund.
This MCP server lets Claude and other AI assistants run those exact calculators and hand the user
a link to the same calculator on the site, already filled in with their numbers, so they can check
the math and keep adjusting it.

- Site: https://therealcost.nohumannearby.com
- All calculators: https://therealcost.nohumannearby.com/calculators/
- Guides: https://therealcost.nohumannearby.com/books/

**Education only. Not financial advice.** Results are estimates from the numbers entered.

<!-- mcp-name: io.github.NoBanks/therealcost-mcp -->

## What every result includes

Each calculator tool returns JSON with:

| Key | What it is |
| --- | --- |
| `result` | The numbers (months, total interest, payments, costs) |
| `summary` | The result in one plain-English paragraph |
| `formula` | The formula in words, so the user can see how the number was made |
| `calculator_url` | The matching page on therealcost.nohumannearby.com, pre-filled with the inputs |
| `warnings` | Present when a plan never pays off or never reaches the goal |
| `go_deeper` | The matching guide and chapters, with the guides link |
| `source` | "The Real Cost by NoBanks Nearby, https://therealcost.nohumannearby.com" |
| `disclaimer` | "Education only. Not financial advice." |

The math is a line-for-line port of the site's own calculator code, and the test suite reuses the
site's hand-checked cases, so a number from this server matches the number on the site.
No network calls, no API keys, no tracking.

## The guides

The Real Cost also publishes three plain-English guides that go deeper than any one calculation,
with every number worked out step by step (PDF and EPUB):

| Guide | Pages | Goes with |
| --- | --- | --- |
| The Real Cost of Credit Card Debt | 112 | credit card payoff, debt consolidation |
| The Real Cost of Loans and Big Purchases | 110 | loan cost by term, debt consolidation |
| The Real Cost of Everyday Spending | 123 | emergency fund, crypto trade cost |

$4.99 each, or all 3 for $9.98, at https://therealcost.nohumannearby.com/books/

Free sample chapters (Chapter 1 of each guide, PDF):

- https://therealcost.nohumannearby.com/samples/the-real-cost-of-credit-card-debt-chapter-1.pdf
- https://therealcost.nohumannearby.com/samples/the-real-cost-of-loans-and-big-purchases-chapter-1.pdf
- https://therealcost.nohumannearby.com/samples/the-real-cost-of-everyday-spending-chapter-1.pdf

The server tells connected agents about the guides in its instructions, and each calculator result
names the matching guide, its relevant chapters and its free sample chapter in a calm one-line `go_deeper` block. The calculators are free and complete
on their own.

## Install

Requires Python 3.10+. The easiest runner is [uv](https://docs.astral.sh/uv/).

### Claude Code

```bash
claude mcp add therealcost -- uvx --from git+https://github.com/NoBanks/therealcost-mcp therealcost-mcp
```

### Claude Desktop

Add this to `claude_desktop_config.json` (Settings, Developer, Edit Config), then restart Claude Desktop:

```json
{
  "mcpServers": {
    "therealcost": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/NoBanks/therealcost-mcp", "therealcost-mcp"]
    }
  }
}
```

### From a local clone

```bash
git clone https://github.com/NoBanks/therealcost-mcp
cd therealcost-mcp
pip install -e .
therealcost-mcp   # speaks MCP over stdio
```

Then point your client at the `therealcost-mcp` command (Claude Code: `claude mcp add therealcost -- therealcost-mcp`).

## Tools

### `credit_card_payoff`

Months and total interest to clear a card balance paying only the minimum, versus a fixed monthly payment.

| Input | Type | Default | Notes |
| --- | --- | --- | --- |
| `balance` | number | required | dollars |
| `apr` | number | required | percent, 24 means 24% |
| `payment` | number | none | fixed monthly payment to compare |
| `min_pct` | number | 1 | minimum = this % of the balance |
| `min_floor` | number | 25 | dollar floor on the minimum |
| `min_plus_interest` | boolean | true | minimum also includes that month's interest |

```json
{"name": "credit_card_payoff", "arguments": {"balance": 5000, "apr": 24, "payment": 200}}
```

Result (abridged): minimum only 234 months and $8,886.95 interest; $200 a month 36 months and
$2,000.56 interest; link
`https://therealcost.nohumannearby.com/calculators/credit-card-payoff/?balance=5000&apr=24&minPct=1&minFloor=25&plusInterest=1&fixedPayment=200`

### `debt_consolidation`

Current debts versus one consolidation loan, including the origination fee (taken out of the loan, so
the loan is sized up to total / (1 - fee%)).

| Input | Type | Default | Notes |
| --- | --- | --- | --- |
| `debts` | array | required | 1 to 10 items of `{balance, apr, payment, name?}` |
| `loan_apr` | number | required | percent |
| `loan_term_months` | integer | required | 1 to 600 |
| `origination_fee_pct` | number | 0 | percent |

```json
{"name": "debt_consolidation", "arguments": {
  "debts": [{"balance": 6000, "apr": 24.99, "payment": 200},
            {"balance": 3000, "apr": 27.99, "payment": 110},
            {"balance": 2500, "apr": 19.99, "payment": 90}],
  "loan_apr": 13, "loan_term_months": 48, "origination_fee_pct": 5}}
```

### `loan_cost_by_term`

Monthly payment, total interest and total paid for one loan over several terms.

| Input | Type | Default | Notes |
| --- | --- | --- | --- |
| `principal` | number | required | dollars |
| `apr` | number | required | percent |
| `terms` | integer array | [36, 48, 60, 72, 84] | months; the first two pre-fill the site |

```json
{"name": "loan_cost_by_term", "arguments": {"principal": 25000, "apr": 8, "terms": [36, 60]}}
```

Result (abridged): 36 months $783.41 a month; 60 months $506.91 a month.

### `crypto_trade_cost`

Trading fee, spread and network fees on a buy and a later sale at the same price, the price rise
needed to break even, and the yearly cost of recurring buys.

| Input | Type | Default | Notes |
| --- | --- | --- | --- |
| `amount` | number | required | dollars bought |
| `fee_pct` | number | required | trading fee per trade, percent |
| `spread_pct` | number | required | spread per trade, percent |
| `network_fee_buy` | number | 0 | flat dollars after the buy |
| `network_fee_sell` | number | 0 | flat dollars to move coins back to sell |
| `weekly_buy` | number | none | recurring buy amount; adds the yearly cost |
| `buys_per_year` | integer | 52 | 52 weekly, 26 biweekly, 12 monthly |
| `flat_fee_per_buy` | number | 0 | flat fee some platforms add on small buys |

```json
{"name": "crypto_trade_cost", "arguments": {"amount": 1000, "fee_pct": 0.6, "spread_pct": 0.5,
  "network_fee_buy": 2.5, "network_fee_sell": 2.5, "weekly_buy": 25, "flat_fee_per_buy": 0.99}}
```

### `emergency_fund`

Goal = monthly expenses x months to cover. Months to reach it, and the monthly amount needed to reach
it by a target.

| Input | Type | Default | Notes |
| --- | --- | --- | --- |
| `monthly_expenses` | number | required | must-pay expenses per month |
| `months_covered` | integer | required | 1 to 60 |
| `saved` | number | 0 | already saved |
| `monthly_add` | number | 0 | added each month |
| `apy` | number | 0 | savings APY, percent |
| `target_months` | integer | 12 | reach the goal in this many months |
| `target_date` | string | none | `YYYY-MM` or `YYYY-MM-DD`, instead of `target_months` |

```json
{"name": "emergency_fund", "arguments": {"monthly_expenses": 2500, "months_covered": 3,
  "saved": 500, "monthly_add": 300, "target_date": "2027-10"}}
```

Result (abridged): goal $7,500.00; 24 months to reach it at $300 a month; $583.33 a month reaches it in 12 months.

### `list_guides`

No inputs. Returns the three guides (title, subtitle, pages, what each covers, price), the 3-guide
price, and the guides link.

```json
{"name": "list_guides", "arguments": {}}
```

### Errors

Bad input never crashes the server. It returns:

```json
{"error": {"type": "validation_error", "message": "Invalid input for credit_card_payoff.",
  "details": [{"field": "apr", "message": "Field required"}]},
 "disclaimer": "Education only. Not financial advice."}
```

## Calculator link parameters (for the site)

`calculator_url` uses the site's own form field ids as query parameters, so the site can pre-fill
each form by reading `?name=value` into the field with that id. Numbers are plain (`5000`, `24.99`);
booleans are `1` or `0`.

| Calculator page | Parameters |
| --- | --- |
| `/calculators/credit-card-payoff/` | `balance`, `apr`, `minPct`, `minFloor`, `plusInterest`, `fixedPayment` |
| `/calculators/debt-consolidation/` | `d1b`, `d1r`, `d1p`, `d2b`, `d2r`, `d2p`, `d3b`, `d3r`, `d3p` (balance, APR, payment per debt), `loanApr`, `loanMonths`, `feePct` |
| `/calculators/loan-term/` | `amount`, `apr`, `termA`, `termB` |
| `/calculators/crypto-trade-cost/` | `amount`, `feePct`, `spreadPct`, `networkBuy`, `networkSell`, `weekly`, `freq`, `flatFee` |
| `/calculators/emergency-fund/` | `expenses`, `monthsCover`, `saved`, `monthly`, `apy`, `target` |

Notes: unused debt rows are sent as `dNb=0` so the form's example rows are not counted. With more
than 3 debts the link opens the plain page (the form has 3 rows) and the result says so. Some site
fields are dropdowns (loan terms, months to cover, target, frequency); a value outside the dropdown's
options needs the site to add that option or fall back to its default.

## Development

```bash
pip install -e ".[dev]"
pytest
```

`tests/test_calc.py` is a port of the site's `site/tests/calc-math.test.js` (same hand-checked cases
and the same cross-checks), and `tests/test_server.py` awaits `list_tools` and `call_tool` directly.

## License

MIT. The Real Cost by NoBanks Nearby.
