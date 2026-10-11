from __future__ import annotations

from datetime import date

from .models import FundedAccount, RiskSnapshot

DAILY_DD_LIMIT = 4.0
OVERALL_DD_LIMIT = 10.0


def ensure_daily_anchor(account: FundedAccount, equity: float) -> None:
    today = date.today().isoformat()
    if account.day_anchor_date != today or account.day_anchor_equity is None:
        account.day_anchor_date = today
        account.day_anchor_equity = equity


def calculate_snapshot(account: FundedAccount, equity: float, balance: float) -> RiskSnapshot:
    ensure_daily_anchor(account, equity)

    daily_anchor = account.day_anchor_equity or equity
    daily_dd = max(0.0, (daily_anchor - equity) / daily_anchor * 100.0) if daily_anchor > 0 else 0.0

    overall_dd = (
        max(0.0, (account.initial_capital - equity) / account.initial_capital * 100.0)
        if account.initial_capital > 0
        else 0.0
    )

    # Normalize proximity so either rule can drive monitoring priority.
    daily_proximity = daily_dd / DAILY_DD_LIMIT if DAILY_DD_LIMIT else 0.0
    overall_proximity = overall_dd / OVERALL_DD_LIMIT if OVERALL_DD_LIMIT else 0.0
    effective = max(daily_proximity, overall_proximity) * DAILY_DD_LIMIT

    return RiskSnapshot(
        equity=equity,
        balance=balance,
        daily_dd_pct=daily_dd,
        overall_dd_pct=overall_dd,
        effective_dd_pct=effective,
        breached_daily=daily_dd >= DAILY_DD_LIMIT,
        breached_overall=overall_dd >= OVERALL_DD_LIMIT,
    )


def monitoring_interval_seconds(effective_dd_pct: float) -> float:
    if effective_dd_pct <= 1.0:
        return 120.0
    if effective_dd_pct <= 3.0:
        return 60.0
    if effective_dd_pct <= 3.5:
        return 20.0
    if effective_dd_pct < 3.6:
        return 10.0
    if effective_dd_pct < 4.0:
        return 2.0
    return 0.5
