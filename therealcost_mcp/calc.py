"""The Real Cost calculator math, ported line for line from the site's
site/assets/js/calc-math.js so a number from this server matches the number on
https://therealcost.nohumannearby.com. Keep the two in step: if a formula changes on the
site, change it here and port the matching test case.

Pure functions, no I/O. Education only. Not financial advice.
"""

from __future__ import annotations

import math
from typing import Callable

MAX_MONTHS = 1200  # 100-year ceiling, same as the site


def monthly_rate(apr_pct: float) -> float:
    return apr_pct / 100 / 12


def payment(principal: float, apr_pct: float, months: int) -> float:
    """Fixed monthly payment on an amortized loan."""
    r = monthly_rate(apr_pct)
    if months <= 0:
        return math.nan
    return principal / months if r == 0 else principal * r / (1 - (1 + r) ** (-months))


def payoff(balance: float, apr_pct: float, pay_fn: Callable[[float], float]) -> dict:
    """Month-by-month payoff. Each month: interest = balance * APR/12, the payment is computed
    from the balance after interest and capped at what is owed.
    ok False with reason "never" when a payment never covers the month's interest."""
    r = monthly_rate(apr_pct)
    months = 0
    interest = 0.0
    paid = 0.0
    first = None
    balances = [balance]
    while balance > 0.005:
        i = balance * r
        p = pay_fn(balance + i)
        if p <= i + 0.004:
            return {"ok": False, "reason": "never", "interest_first_month": i,
                    "payment_first_month": p, "balances": balances}
        applied = min(p, balance + i)
        if first is None:
            first = applied
        interest += i
        paid += applied
        balance = balance + i - applied
        months += 1
        balances.append(max(balance, 0))
        if months > MAX_MONTHS:
            return {"ok": False, "reason": "toolong", "balances": balances}
    return {"ok": True, "months": months, "interest": interest, "total_paid": paid,
            "first_payment": first or 0, "balances": balances}


def payoff_fixed(balance: float, apr_pct: float, monthly_payment: float) -> dict:
    return payoff(balance, apr_pct, lambda _b: monthly_payment)


def min_payment_fn(apr_pct: float, min_pct: float, floor_dollars: float,
                   plus_interest: bool) -> Callable[[float], float]:
    """minimum = max(min_pct% of the balance [plus that month's interest], floor).
    b is the balance after this month's interest."""
    r = monthly_rate(apr_pct)

    def fn(b: float) -> float:
        before = b / (1 + r)
        pct = before * r + before * min_pct / 100 if plus_interest else b * min_pct / 100
        return max(pct, floor_dollars)

    return fn


def payoff_minimum(balance: float, apr_pct: float, min_pct: float, floor_dollars: float,
                   plus_interest: bool) -> dict:
    return payoff(balance, apr_pct, min_payment_fn(apr_pct, min_pct, floor_dollars, plus_interest))


def credit_card(balance: float, apr: float, min_pct: float, min_floor: float,
                plus_interest: bool, fixed_payment: float) -> dict:
    minimum = payoff_minimum(balance, apr, min_pct, min_floor, plus_interest)
    fixed = payoff_fixed(balance, apr, fixed_payment)
    out = {"minimum": minimum, "fixed": fixed}
    if minimum["ok"] and fixed["ok"]:
        out["interest_difference"] = minimum["interest"] - fixed["interest"]
        out["months_difference"] = minimum["months"] - fixed["months"]
    return out


def consolidation(debts: list[dict], loan_apr: float, loan_months: int, fee_pct: float) -> dict:
    """debts: [{balance, apr, payment}] kept as they are, vs one loan that pays them all off.
    The origination fee comes out of the loan: loan_amount = total / (1 - fee%).
    Loan cost = interest + fee."""
    total = monthly = interest = 0.0
    months = 0
    rows = []
    ok = True
    for d in debts:
        total += d["balance"]
        monthly += d["payment"]
        r = payoff_fixed(d["balance"], d["apr"], d["payment"])
        rows.append(r)
        if not r["ok"]:
            ok = False
            continue
        interest += r["interest"]
        months = max(months, r["months"])
    fee_share = fee_pct / 100
    loan_amount = math.nan if fee_share >= 1 else total / (1 - fee_share)
    fee = loan_amount - total
    loan_payment = payment(loan_amount, loan_apr, loan_months)
    loan_interest = loan_payment * loan_months - loan_amount
    return {
        "current": {"ok": ok, "total": total, "monthly": monthly, "interest": interest,
                    "months": months, "debts": rows},
        "loan": {"ok": math.isfinite(loan_payment), "amount": loan_amount, "fee": fee,
                 "monthly": loan_payment, "interest": loan_interest, "cost": loan_interest + fee,
                 "months": loan_months, "total_paid": loan_payment * loan_months},
    }


def loan_by_term(principal: float, apr_pct: float, terms: list[int]) -> list[dict]:
    out = []
    for m in terms:
        p = payment(principal, apr_pct, m)
        out.append({"months": m, "payment": p, "interest": p * m - principal, "total_paid": p * m})
    return out


def crypto_round_trip(amount: float, fee_pct: float, spread_pct: float,
                      network_buy: float, network_sell: float) -> dict:
    """Buy: trading fee, then spread on what is left, then a flat network fee.
    Sale: flat network fee, then spread, then trading fee. Price held flat.
    break_even_rise_pct = price rise needed before the sale returns the original dollars."""
    f = fee_pct / 100
    s = spread_pct / 100
    buy_fee = amount * f
    buy_spread = (amount - buy_fee) * s
    held = amount - buy_fee - buy_spread - network_buy
    before_sale = held - network_sell
    sell_spread = before_sale * s
    sell_fee = (before_sale - sell_spread) * f
    proceeds = before_sale - sell_spread - sell_fee
    cost = amount - proceeds
    keep = (1 - s) * (1 - f)
    m = (amount / keep + network_sell) / held if keep > 0 and held > 0 else math.nan
    return {
        "buy_fee": buy_fee, "buy_spread": buy_spread, "network_buy": network_buy,
        "network_sell": network_sell, "sell_spread": sell_spread, "sell_fee": sell_fee,
        "held": held, "proceeds": proceeds, "cost": cost,
        "cost_pct": cost / amount * 100 if amount > 0 else 0,
        "break_even_rise_pct": (m - 1) * 100,
    }


def recurring_buys(amount: float, fee_pct: float, spread_pct: float, flat_fee: float,
                   buys_per_year: int) -> dict:
    """Buy-side cost on every purchase, totaled for a year."""
    f = fee_pct / 100
    s = spread_pct / 100
    per_buy = amount * f + (amount - amount * f) * s + flat_fee
    return {
        "per_buy": per_buy, "buys": buys_per_year, "invested": amount * buys_per_year,
        "yearly_cost": per_buy * buys_per_year,
        "cost_pct": per_buy / amount * 100 if amount > 0 else 0,
    }


def emergency_fund(goal: float, start: float, monthly: float, apy: float) -> dict:
    """Each month the balance earns APY/12 (compounded monthly), then the deposit is added."""
    r = monthly_rate(apy)
    bal = start
    months = 0
    balances = [bal]
    deposits = start
    if bal >= goal:
        return {"ok": True, "months": 0, "balances": balances, "deposited": deposits,
                "interest": 0.0, "final_balance": bal}
    if monthly <= 0 and r <= 0:
        return {"ok": False, "reason": "never", "balances": balances}
    while bal < goal - 0.005:
        bal = bal * (1 + r) + monthly
        deposits += monthly
        months += 1
        balances.append(bal)
        if months > MAX_MONTHS:
            return {"ok": False, "reason": "toolong", "balances": balances}
    return {"ok": True, "months": months, "balances": balances, "deposited": deposits,
            "interest": bal - deposits, "final_balance": bal}


def monthly_needed(goal: float, start: float, apy: float, n: int) -> float:
    """Monthly deposit needed to reach goal in n months."""
    r = monthly_rate(apy)
    if n <= 0:
        return math.nan
    grown = start * (1 + r) ** n
    gap = goal - grown
    if gap <= 0:
        return 0.0
    return gap / n if r == 0 else gap * r / ((1 + r) ** n - 1)


def future_value(monthly_deposit: float, annual_pct: float, years: float) -> float:
    r = monthly_rate(annual_pct)
    n = int(math.floor(years * 12 + 0.5))  # JS Math.round, not banker rounding
    return monthly_deposit * n if r == 0 else monthly_deposit * ((1 + r) ** n - 1) / r
