"""Pydantic input models for therealcost-mcp tools. Unknown fields are rejected."""

from __future__ import annotations

from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_MONEY = 100_000_000

Money = Annotated[float, Field(ge=0, le=MAX_MONEY)]
PositiveMoney = Annotated[float, Field(gt=0, le=MAX_MONEY)]
Rate = Annotated[float, Field(ge=0, le=100)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreditCardPayoffInput(_Strict):
    balance: PositiveMoney = Field(description="Current card balance in US dollars, e.g. 5000.")
    apr: Rate = Field(description="Card APR in percent, e.g. 24 for 24%.")
    payment: Optional[PositiveMoney] = Field(
        None, description="Fixed monthly payment to compare against paying only the minimum, e.g. 200.")
    min_pct: Rate = Field(1.0, description="Minimum payment percent of the balance (many cards use 1).")
    min_floor: Money = Field(25.0, description="Dollar floor on the minimum payment, from the statement.")
    min_plus_interest: bool = Field(
        True, description="True if the minimum is min_pct of the balance PLUS that month's interest "
                          "(common); False if it is min_pct of the balance only.")


class DebtItem(_Strict):
    balance: PositiveMoney = Field(description="Debt balance in dollars.")
    apr: Rate = Field(description="Debt APR in percent.")
    payment: PositiveMoney = Field(description="Current monthly payment on this debt in dollars.")
    name: Optional[str] = Field(None, max_length=60, description="Optional label, e.g. 'Visa'.")


class DebtConsolidationInput(_Strict):
    debts: list[DebtItem] = Field(min_length=1, max_length=10, description="Debts kept as they are today.")
    loan_apr: Rate = Field(description="Consolidation loan APR in percent.")
    loan_term_months: int = Field(ge=1, le=600, description="Consolidation loan term in months, e.g. 48.")
    origination_fee_pct: float = Field(
        0.0, ge=0, lt=100, description="Origination fee in percent, taken out of the loan (so the loan is sized up).")


class LoanCostByTermInput(_Strict):
    principal: PositiveMoney = Field(description="Amount borrowed in dollars.")
    apr: Rate = Field(description="Loan APR in percent.")
    terms: list[Annotated[int, Field(ge=1, le=600)]] = Field(
        default_factory=lambda: [36, 48, 60, 72, 84], min_length=1, max_length=12,
        description="Loan terms in months to compare. The first two pre-fill the site calculator.")


class CryptoTradeCostInput(_Strict):
    amount: PositiveMoney = Field(description="Dollar amount of the buy, e.g. 1000.")
    fee_pct: float = Field(ge=0, lt=100, description="Trading fee per trade in percent, e.g. 0.6.")
    spread_pct: float = Field(ge=0, lt=100, description="Spread per trade in percent, e.g. 0.5.")
    network_fee_buy: Money = Field(0.0, description="Flat network or withdrawal fee after the buy, dollars.")
    network_fee_sell: Money = Field(0.0, description="Flat network fee to move coins back to sell, dollars.")
    weekly_buy: Optional[PositiveMoney] = Field(
        None, description="Recurring buy amount in dollars; adds the yearly cost of recurring buys.")
    buys_per_year: int = Field(52, ge=1, le=365, description="Recurring buys per year: 52 weekly, 26 biweekly, 12 monthly.")
    flat_fee_per_buy: Money = Field(0.0, description="Flat fee some platforms add on each small recurring buy.")


class EmergencyFundInput(_Strict):
    monthly_expenses: Money = Field(description="Monthly must-pay expenses in dollars.")
    months_covered: int = Field(ge=1, le=60, description="Months of expenses the fund should cover, e.g. 3.")
    saved: Money = Field(0.0, description="Amount already saved in dollars.")
    monthly_add: Money = Field(0.0, description="Amount added each month in dollars.")
    apy: Rate = Field(0.0, description="Savings account APY in percent (0 counts only deposits).")
    target_months: Optional[int] = Field(
        None, ge=1, le=600, description="Reach the goal in this many months (default 12).")
    target_date: Optional[str] = Field(
        None, pattern=r"^\d{4}-(0[1-9]|1[0-2])(-\d{2})?$",
        description="Reach the goal by this month, YYYY-MM or YYYY-MM-DD. Overrides target_months.")

    @model_validator(mode="after")
    def _one_target(self) -> "EmergencyFundInput":
        if self.target_date is not None and self.target_months is not None:
            raise ValueError("Give target_months or target_date, not both.")
        return self


class ListGuidesInput(_Strict):
    pass
