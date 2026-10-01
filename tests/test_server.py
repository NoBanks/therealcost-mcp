"""MCP surface tests. list_tools and call_tool are imported as functions and awaited directly
(pattern: lambda-cloud-mcp/tests/test_server.py)."""

import json
from datetime import date
from urllib.parse import parse_qs, urlparse

import pytest

from therealcost_mcp import server as S
from therealcost_mcp.server import INSTRUCTIONS, call_tool, list_tools

EXPECTED_TOOLS = {"credit_card_payoff", "debt_consolidation", "loan_cost_by_term",
                  "crypto_trade_cost", "emergency_fund", "list_guides"}
DISCLAIMER = "Education only. Not financial advice."
BOOKS = "https://therealcost.nohumannearby.com/books/"
LONG_DASHES = (chr(8212), chr(8211))


async def run(name, args):
    out = await call_tool(name, args)
    assert len(out) == 1 and out[0].type == "text"
    return json.loads(out[0].text)


def qs(url):
    return {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setattr(S, "_today", lambda: date(2026, 10, 1))


async def test_list_tools_registers_six_tools():
    tools = await list_tools()
    assert {t.name for t in tools} == EXPECTED_TOOLS
    for t in tools:
        assert t.inputSchema["type"] == "object"
        assert "Education only" in t.description or t.name == "list_guides"


def test_server_instructions_mention_guides_and_site():
    assert "therealcost.nohumannearby.com" in INSTRUCTIONS
    assert "$4.99" in INSTRUCTIONS and "$9.98" in INSTRUCTIONS and "$24.95" in INSTRUCTIONS
    assert BOOKS in INSTRUCTIONS
    assert "not financial advice" in INSTRUCTIONS
    assert S.server.instructions == INSTRUCTIONS


async def test_every_calculator_result_has_disclaimer_formula_link_and_go_deeper():
    calls = {
        "credit_card_payoff": {"balance": 5000, "apr": 24, "payment": 200},
        "debt_consolidation": {"debts": [{"balance": 6000, "apr": 24.99, "payment": 200}], "loan_apr": 13, "loan_term_months": 48},
        "loan_cost_by_term": {"principal": 25000, "apr": 8},
        "crypto_trade_cost": {"amount": 1000, "fee_pct": 0.6, "spread_pct": 0.5},
        "emergency_fund": {"monthly_expenses": 2500, "months_covered": 3, "saved": 500, "monthly_add": 300},
    }
    for name, args in calls.items():
        r = await run(name, args)
        assert r["disclaimer"] == DISCLAIMER, name
        assert len(r["formula"]) > 60, name
        assert r["calculator_url"].startswith("https://therealcost.nohumannearby.com/calculators/"), name
        assert r["go_deeper"]["link"] == BOOKS, name
        assert "The Real Cost" in r["go_deeper"]["text"], name
        assert all(g["free_sample_chapter"].endswith("chapter-1.pdf") for g in r["go_deeper"]["guides"]), name
        text = json.dumps(r, ensure_ascii=False)
        assert "/dl/" not in text, name
        assert not any(d in text for d in LONG_DASHES), name


async def test_credit_card_payoff_matches_site_example():
    r = await run("credit_card_payoff", {"balance": 5000, "apr": 24, "payment": 200})
    res = r["result"]
    assert res["minimum_only"]["months"] == 234
    assert res["minimum_only"]["total_interest"] == 8886.95
    assert res["fixed_payment"]["months"] == 36
    assert res["fixed_payment"]["total_interest"] == 2000.56
    assert res["difference"]["months"] == 198
    assert r["calculator_url"] == ("https://therealcost.nohumannearby.com/calculators/credit-card-payoff/"
                                   "?balance=5000&apr=24&minPct=1&minFloor=25&plusInterest=1&fixedPayment=200")
    assert r["go_deeper"]["guides"][0]["title"] == "The Real Cost of Credit Card Debt"


async def test_credit_card_minimum_only_without_payment():
    r = await run("credit_card_payoff", {"balance": 3000, "apr": 22.99, "min_pct": 3, "min_floor": 35, "min_plus_interest": False})
    assert r["result"]["minimum_only"]["months"] == 136
    assert "fixed_payment" not in r["result"]
    assert "fixedPayment" not in qs(r["calculator_url"])
    assert qs(r["calculator_url"])["plusInterest"] == "0"


async def test_credit_card_fixed_payment_never_pays_off_warns():
    r = await run("credit_card_payoff", {"balance": 5000, "apr": 24, "payment": 50})
    assert r["result"]["fixed_payment"]["never_pays_off"] is True
    assert any("never reaches zero" in w for w in r["warnings"])


async def test_debt_consolidation_site_example():
    debts = [{"balance": 6000, "apr": 24.99, "payment": 200}, {"balance": 3000, "apr": 27.99, "payment": 110},
             {"balance": 2500, "apr": 19.99, "payment": 90}]
    r = await run("debt_consolidation", {"debts": debts, "loan_apr": 13, "loan_term_months": 48, "origination_fee_pct": 5})
    loan = r["result"]["loan"]
    assert loan["amount"] == round(11500 / 0.95, 2)
    assert r["result"]["current"]["monthly_payment"] == 400
    q = qs(r["calculator_url"])
    assert q["d1b"] == "6000" and q["d2r"] == "27.99" and q["d3p"] == "90"
    assert q["loanApr"] == "13" and q["loanMonths"] == "48" and q["feePct"] == "5"
    titles = {g["title"] for g in r["go_deeper"]["guides"]}
    assert titles == {"The Real Cost of Credit Card Debt", "The Real Cost of Loans and Big Purchases"}


async def test_debt_consolidation_hand_case_and_unused_rows_zeroed():
    r = await run("debt_consolidation", {"debts": [{"balance": 1200, "apr": 0, "payment": 100}, {"balance": 600, "apr": 0, "payment": 50}],
                                         "loan_apr": 0, "loan_term_months": 12, "origination_fee_pct": 10})
    assert r["result"]["loan"]["amount"] == 2000
    assert r["result"]["loan"]["total_cost"] == 200
    assert r["result"]["current_interest_minus_loan_cost"] == -200
    assert qs(r["calculator_url"])["d3b"] == "0"


async def test_debt_consolidation_more_than_three_debts_links_plain_page():
    debts = [{"balance": 1000, "apr": 20, "payment": 100}] * 4
    r = await run("debt_consolidation", {"debts": debts, "loan_apr": 10, "loan_term_months": 24})
    assert r["calculator_url"] == "https://therealcost.nohumannearby.com/calculators/debt-consolidation/"
    assert "calculator_note" in r


async def test_debt_consolidation_never_pays_warns():
    r = await run("debt_consolidation", {"debts": [{"balance": 1000, "apr": 24, "payment": 10}], "loan_apr": 10, "loan_term_months": 24})
    assert r["result"]["current"]["total_interest"] is None
    assert r["warnings"]


async def test_loan_cost_by_term_site_example():
    r = await run("loan_cost_by_term", {"principal": 25000, "apr": 8, "terms": [36, 60]})
    a, b = r["result"]["terms"]
    assert a["monthly_payment"] == 783.41 and b["monthly_payment"] == 506.91
    assert qs(r["calculator_url"]) == {"amount": "25000", "apr": "8", "termA": "36", "termB": "60"}
    assert r["go_deeper"]["guides"][0]["title"] == "The Real Cost of Loans and Big Purchases"


async def test_loan_cost_default_terms():
    r = await run("loan_cost_by_term", {"principal": 12000, "apr": 0})
    assert [t["months"] for t in r["result"]["terms"]] == [36, 48, 60, 72, 84]
    assert all(t["total_interest"] == 0 for t in r["result"]["terms"])


async def test_crypto_trade_cost_hand_case_and_recurring():
    r = await run("crypto_trade_cost", {"amount": 1000, "fee_pct": 1, "spread_pct": 1, "weekly_buy": 25, "flat_fee_per_buy": 1})
    rt = r["result"]["round_trip"]
    assert rt["proceeds_at_same_price"] == 960.6
    assert rt["total_cost"] == 39.4
    assert r["result"]["recurring"]["yearly_cost"] == 77.87
    q = qs(r["calculator_url"])
    assert q["weekly"] == "25" and q["freq"] == "52" and q["flatFee"] == "1"
    assert r["go_deeper"]["guides"][0]["title"] == "The Real Cost of Crypto Fees and Taxes"
    assert "note" in r["go_deeper"]


async def test_crypto_without_recurring_omits_it():
    r = await run("crypto_trade_cost", {"amount": 100, "fee_pct": 0, "spread_pct": 0, "network_fee_buy": 5, "network_fee_sell": 5})
    assert "recurring" not in r["result"]
    assert r["result"]["round_trip"]["total_cost"] == 10
    assert "weekly" not in qs(r["calculator_url"])


async def test_emergency_fund_site_example():
    r = await run("emergency_fund", {"monthly_expenses": 2500, "months_covered": 3, "saved": 500, "monthly_add": 300})
    res = r["result"]
    assert res["goal"] == 7500
    assert res["months_to_goal"] == 24
    assert res["reached_month"] == "October 2028"
    assert res["by_target"]["monthly_needed"] == 583.33
    assert res["by_target"]["months"] == 12
    assert qs(r["calculator_url"]) == {"expenses": "2500", "monthsCover": "3", "saved": "500",
                                       "monthly": "300", "apy": "0", "target": "12"}
    assert r["go_deeper"]["guides"][0]["title"] == "The Real Cost of Everyday Spending"


async def test_emergency_fund_target_date():
    r = await run("emergency_fund", {"monthly_expenses": 2500, "months_covered": 3, "saved": 500, "target_date": "2027-10"})
    assert r["result"]["by_target"]["months"] == 12
    assert r["result"]["by_target"]["monthly_needed"] == 583.33
    assert r["result"]["never_reaches_goal"] is True


async def test_emergency_fund_target_date_in_past_is_error():
    r = await run("emergency_fund", {"monthly_expenses": 2500, "months_covered": 3, "target_date": "2026-09-15"})
    assert r["error"]["type"] == "validation_error"


async def test_list_guides():
    r = await run("list_guides", {})
    assert [g["pages"] for g in r["guides"]] == [112, 110, 123, 110, 115, 109, 117, 115, 125, 103]
    assert len({g["title"] for g in r["guides"]}) == 10
    assert all(g["price"] == "$4.99" for g in r["guides"])
    assert all(g["free_sample_chapter"].startswith("https://therealcost.nohumannearby.com/samples/") for g in r["guides"])
    assert r["pricing"]["all_3_guides"] == "$9.98"
    assert r["pricing"]["complete_set_all_10"] == "$24.95"
    assert r["complete_set"]["price"] == "$24.95" and "10 for the price of 5" in r["complete_set"]["note"]
    assert r["complete_set"]["link"] == BOOKS and len(r["complete_set"]["guides"]) == 10
    assert "buy.stripe.com" not in json.dumps(r)
    assert "guides 1-3 only" in r["pricing"]["note"]
    assert len(r["pricing"]["starter_pack_guides"]) == 3
    assert r["link"] == BOOKS
    assert r["disclaimer"] == DISCLAIMER
    assert "/dl/" not in json.dumps(r)


@pytest.mark.parametrize("name,args", [
    ("credit_card_payoff", {"balance": -5, "apr": 24}),
    ("credit_card_payoff", {"balance": 5000}),
    ("credit_card_payoff", {"balance": 5000, "apr": 24, "bogus": 1}),
    ("debt_consolidation", {"debts": [], "loan_apr": 10, "loan_term_months": 12}),
    ("loan_cost_by_term", {"principal": 1000, "apr": 150}),
    ("crypto_trade_cost", {"amount": 1000, "fee_pct": 100, "spread_pct": 1}),
    ("emergency_fund", {"monthly_expenses": 100, "months_covered": 3, "target_date": "next year"}),
    ("emergency_fund", {"monthly_expenses": 100, "months_covered": 3, "target_date": "2027-01", "target_months": 6}),
])
async def test_invalid_input_returns_structured_error(name, args):
    r = await run(name, args)
    assert r["error"]["type"] == "validation_error"
    assert r["error"]["details"]
    assert r["disclaimer"] == DISCLAIMER


async def test_unknown_tool():
    r = await run("nope", {})
    assert r["error"]["type"] == "unknown_tool"
