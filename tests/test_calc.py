"""Port of site/tests/calc-math.test.js (The Real Cost site). Same hand-checked cases and the
same cross-checks against the channel's finance/script_gen.py values, so the site and this
server agree number for number."""

import math

import pytest

from therealcost_mcp import calc as M


def near(got, want, tol=0.005):
    assert abs(got - want) <= tol, f"got {got}, want {want}"


# ---------------------------------------------------------------- loan payment formula
def test_payment_textbook_cases():
    near(M.payment(10000, 6, 36), 304.22, 0.005)
    near(M.payment(1200, 0, 12), 100, 1e-9)
    near(M.payment(100000, 12, 1), 101000, 1e-6)


def test_payment_matches_script_gen():
    near(M.payment(10000, 6, 36), 304.2193745155571, 1e-9)
    near(M.payment(25000, 8, 60), 506.9098572103464, 1e-9)


def test_payment_zero_months_is_nan():
    assert math.isnan(M.payment(1000, 5, 0))


# ---------------------------------------------------------------- credit card
def test_payoff_fixed_hand_walked_11_months():
    r = M.payoff_fixed(1000, 12, 100)
    assert r["ok"] is True
    assert r["months"] == 11
    near(r["interest"], 58.98, 0.01)
    near(r["balances"][1], 910, 1e-9)
    near(r["balances"][2], 819.1, 1e-9)
    near(r["total_paid"], 1058.98, 0.01)
    assert r["balances"][-1] == 0


def test_payoff_fixed_zero_apr():
    r = M.payoff_fixed(1000, 0, 100)
    assert r["months"] == 10
    near(r["interest"], 0, 1e-12)


def test_payoff_fixed_never_covers_interest():
    r = M.payoff_fixed(1000, 24, 20)
    assert r["ok"] is False and r["reason"] == "never"


def test_min_payment_fn():
    fn = M.min_payment_fn(24, 1, 25, True)
    near(fn(5000 * 1.02), 150, 1e-9)
    near(fn(100 * 1.02), 25, 1e-9)
    pct_only = M.min_payment_fn(24, 3, 35, False)
    near(pct_only(3000), 90, 1e-9)


def test_payoff_matches_script_gen():
    a = M.payoff_fixed(5000, 24, 200)
    assert a["months"] == 36
    near(a["interest"], 2000.5632814214787, 1e-6)
    b = M.payoff_minimum(5000, 24, 1, 25, True)
    assert b["months"] == 234
    near(b["interest"], 8886.949077624658, 1e-6)
    c = M.payoff_minimum(3000, 22.99, 3, 35, False)
    assert c["months"] == 136
    near(c["interest"], 3785.563881614237, 1e-6)
    d = M.payoff_fixed(6000, 24.99, 200)
    assert d["months"] == 48
    near(d["interest"], 3511.5167089324696, 1e-6)


def test_credit_card_difference():
    r = M.credit_card(5000, 24, 1, 25, True, 200)
    near(r["interest_difference"], 8886.949077624658 - 2000.5632814214787, 1e-6)
    assert r["months_difference"] == 198


# ---------------------------------------------------------------- debt consolidation
def test_consolidation_zero_interest_fee_sizes_loan():
    r = M.consolidation([{"balance": 1200, "apr": 0, "payment": 100}, {"balance": 600, "apr": 0, "payment": 50}], 0, 12, 10)
    assert r["current"]["months"] == 12
    near(r["current"]["interest"], 0, 1e-9)
    near(r["current"]["monthly"], 150, 1e-9)
    near(r["loan"]["amount"], 2000, 1e-9)
    near(r["loan"]["fee"], 200, 1e-9)
    near(r["loan"]["monthly"], 2000 / 12, 1e-9)
    near(r["loan"]["interest"], 0, 1e-9)
    near(r["loan"]["cost"], 200, 1e-9)


def test_consolidation_no_fee_standard_payment():
    r = M.consolidation([{"balance": 10000, "apr": 24, "payment": 300}], 6, 36, 0)
    near(r["loan"]["amount"], 10000, 1e-9)
    near(r["loan"]["monthly"], 304.22, 0.005)
    near(r["loan"]["interest"], 304.2193745155571 * 36 - 10000, 1e-6)


def test_consolidation_never_pays_marks_not_ok():
    r = M.consolidation([{"balance": 1000, "apr": 24, "payment": 10}], 10, 24, 0)
    assert r["current"]["ok"] is False


# ---------------------------------------------------------------- loan by term
def test_loan_by_term():
    a, b = M.loan_by_term(25000, 8, [36, 60])
    near(a["payment"], 783.41, 0.005)
    near(b["payment"], 506.91, 0.005)
    near(a["interest"], a["payment"] * 36 - 25000, 1e-9)
    near(b["total_paid"], 506.9098572103464 * 60, 1e-6)
    assert b["interest"] > a["interest"]


def test_loan_by_term_zero_apr():
    for r in M.loan_by_term(12000, 0, [12, 24, 48]):
        near(r["interest"], 0, 1e-9)
        near(r["payment"], 12000 / r["months"], 1e-9)


# ---------------------------------------------------------------- crypto
def test_crypto_round_trip_hand_checked():
    r = M.crypto_round_trip(1000, 1, 1, 0, 0)
    near(r["buy_fee"], 10, 1e-9)
    near(r["buy_spread"], 9.9, 1e-9)
    near(r["held"], 980.1, 1e-9)
    near(r["sell_spread"], 9.801, 1e-9)
    near(r["sell_fee"], 9.70299, 1e-9)
    near(r["proceeds"], 960.59601, 1e-9)
    near(r["cost"], 39.40399, 1e-9)
    near(r["cost_pct"], 3.940399, 1e-9)
    near(r["break_even_rise_pct"], (1000 / (980.1 * 0.99 * 0.99) - 1) * 100, 1e-9)


def test_crypto_flat_network_fees():
    r = M.crypto_round_trip(100, 0, 0, 5, 5)
    near(r["proceeds"], 90, 1e-9)
    near(r["cost"], 10, 1e-9)
    near(r["break_even_rise_pct"], (105 / 95 - 1) * 100, 1e-9)


def test_crypto_break_even_returns_original():
    r = M.crypto_round_trip(1000, 0.6, 0.5, 2.5, 2.5)
    m = 1 + r["break_even_rise_pct"] / 100
    back = (r["held"] * m - 2.5) * (1 - 0.5 / 100) * (1 - 0.6 / 100)
    near(back, 1000, 1e-6)


def test_recurring_buys_hand_checked():
    r = M.recurring_buys(25, 1, 1, 1, 52)
    near(r["per_buy"], 1.4975, 1e-9)
    near(r["yearly_cost"], 77.87, 1e-9)
    near(r["invested"], 1300, 1e-9)
    near(r["cost_pct"], 5.99, 1e-9)


# ---------------------------------------------------------------- emergency fund
def test_emergency_fund_zero_interest_rounds_up():
    assert M.emergency_fund(1200, 0, 100, 0)["months"] == 12
    assert M.emergency_fund(1200, 200, 100, 0)["months"] == 10
    assert M.emergency_fund(7500, 500, 300, 0)["months"] == 24
    assert M.emergency_fund(500, 900, 100, 0)["months"] == 0


def test_emergency_fund_with_interest_matches_future_value():
    near(M.future_value(300, 4, 2), 7482.866324315959, 1e-6)
    r = M.emergency_fund(7482, 0, 300, 4)
    assert r["months"] == 24
    near(r["balances"][24], 7482.866324315959, 1e-6)
    near(r["interest"], 7482.866324315959 - 7200, 1e-6)


def test_emergency_fund_never():
    assert M.emergency_fund(1000, 0, 0, 0)["ok"] is False


def test_monthly_needed_inverse():
    near(M.monthly_needed(7500, 500, 0, 12), 7000 / 12, 1e-9)
    near(M.monthly_needed(7482.866324315959, 0, 4, 24), 300, 1e-6)
    near(M.monthly_needed(100, 500, 0, 12), 0, 1e-12)


@pytest.mark.parametrize("years,expected", [(0.5 / 12, 1), (1.5 / 12, 2), (2.5 / 12, 3)])
def test_future_value_rounds_half_up_like_js(years, expected):
    # JS Math.round rounds .5 up; Python round() would round 0.5 and 2.5 down to even
    assert M.future_value(1, 0, years) == expected


def test_site_default_examples_match_node_output():
    # values printed by node from site/assets/js/calc-math.js on 2026-10-01 (site example inputs)
    r = M.crypto_round_trip(1000, 0.6, 0.5, 2.5, 2.5)
    near(r["proceeds"], 973.2351908999999, 1e-9)
    near(r["break_even_rise_pct"], 2.743117359049818, 1e-9)
    near(M.recurring_buys(25, 0.6, 0.5, 0.99, 52)["yearly_cost"], 65.741, 1e-9)
    d = M.consolidation([{"balance": 6000, "apr": 24.99, "payment": 200}, {"balance": 3000, "apr": 27.99, "payment": 110},
                         {"balance": 2500, "apr": 19.99, "payment": 90}], 13, 48, 5)
    near(d["current"]["interest"], 6219.328833950285, 1e-6)
    assert d["current"]["months"] == 48
    near(d["loan"]["monthly"], 324.75389766136647, 1e-9)
    near(d["loan"]["cost"], 4088.1870877455913, 1e-6)
