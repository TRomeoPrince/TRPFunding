from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    BREACHED = "BREACHED"
    ERROR = "ERROR"
    DISABLED = "DISABLED"


@dataclass
class FundedAccount:
    name: str
    login: int
    password: str
    server: str
    initial_capital: float
    enabled: bool = True

    status: AccountStatus = AccountStatus.ACTIVE
    day_anchor_equity: Optional[float] = None
    day_anchor_date: Optional[str] = None
    last_equity: Optional[float] = None
    last_balance: Optional[float] = None
    daily_dd_pct: float = 0.0
    overall_dd_pct: float = 0.0
    next_check_at: datetime = field(default_factory=datetime.now)
    last_check_at: Optional[datetime] = None
    last_error: Optional[str] = None


@dataclass
class RiskSnapshot:
    equity: float
    balance: float
    daily_dd_pct: float
    overall_dd_pct: float
    effective_dd_pct: float
    breached_daily: bool
    breached_overall: bool
