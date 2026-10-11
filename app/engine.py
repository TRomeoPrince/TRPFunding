from __future__ import annotations

import os
import random
import time
from datetime import datetime, timedelta

from .models import AccountStatus, FundedAccount
from .mt5_gateway import MT5Gateway
from .notifications import TelegramNotifier
from .risk import calculate_snapshot, monitoring_interval_seconds
from .storage import Storage


class RiskEngine:
    def __init__(self, accounts: list[FundedAccount], storage: Storage) -> None:
        self.accounts = accounts
        self.storage = storage
        self.mt5 = MT5Gateway()
        self.notifier = TelegramNotifier()
        self.simulation_mode = os.getenv("SIMULATION_MODE", "true").lower() != "false"

    def run_forever(self) -> None:
        self.notifier.send(
            f"TRP Funding engine started. Accounts: {len(self.accounts)}. "
            f"Simulation: {self.simulation_mode}"
        )

        while True:
            due = [
                a for a in self.accounts
                if a.enabled and a.status != AccountStatus.DISABLED and a.next_check_at <= datetime.now()
            ]

            if not due:
                time.sleep(0.5)
                continue

            # Randomize accounts within the same due window so no one account is always last.
            random.shuffle(due)
            # Previously riskier accounts still get priority when due.
            due.sort(key=lambda a: max(a.daily_dd_pct / 4.0, a.overall_dd_pct / 10.0), reverse=True)

            for account in due:
                self._check_account(account)

    def _check_account(self, account: FundedAccount) -> None:
        try:
            info = self.mt5.connect(account)
            snapshot = calculate_snapshot(account, info.equity, info.balance)

            account.last_equity = snapshot.equity
            account.last_balance = snapshot.balance
            account.daily_dd_pct = snapshot.daily_dd_pct
            account.overall_dd_pct = snapshot.overall_dd_pct
            account.last_check_at = datetime.now()
            account.last_error = None

            self.storage.save_snapshot(account, snapshot)

            print(
                f"[{account.name}] equity={snapshot.equity:.2f} "
                f"dailyDD={snapshot.daily_dd_pct:.2f}% "
                f"overallDD={snapshot.overall_dd_pct:.2f}%"
            )

            if snapshot.breached_daily or snapshot.breached_overall:
                self._handle_breach(account, snapshot)
                interval = 2.0
            else:
                interval = monitoring_interval_seconds(snapshot.effective_dd_pct)

            account.next_check_at = datetime.now() + timedelta(seconds=interval)

        except Exception as exc:
            account.status = AccountStatus.ERROR
            account.last_error = str(exc)
            account.next_check_at = datetime.now() + timedelta(seconds=15)
            self.storage.event(account, "ERROR", "ACCOUNT_CHECK_FAILED", str(exc))
            self.notifier.send(f"⚠️ {account.name} check failed\n{exc}")
        finally:
            self.mt5.shutdown()

    def _handle_breach(self, account, snapshot) -> None:
        first_breach = account.status != AccountStatus.BREACHED
        account.status = AccountStatus.BREACHED

        reason = []
        if snapshot.breached_daily:
            reason.append(f"daily DD {snapshot.daily_dd_pct:.2f}%")
        if snapshot.breached_overall:
            reason.append(f"overall DD {snapshot.overall_dd_pct:.2f}%")
        reason_text = ", ".join(reason)

        if first_breach:
            self.storage.event(account, "CRITICAL", "BREACH", reason_text)
            self.notifier.send(
                f"🚨 ACCOUNT BREACH\n"
                f"Trader: {account.name}\n"
                f"Login: {account.login}\n"
                f"Equity: {snapshot.equity:.2f}\n"
                f"Balance: {snapshot.balance:.2f}\n"
                f"Reason: {reason_text}\n"
                f"Action: {'SIMULATION ONLY' if self.simulation_mode else 'LIQUIDATING'}\n"
                f"Manual step: change MT5 password and transfer remaining funds."
            )

        if self.simulation_mode:
            return

        close_results = self.mt5.close_all_positions()
        cancel_results = self.mt5.cancel_all_orders()
        flat = self.mt5.is_flat()

        self.storage.event(
            account,
            "CRITICAL",
            "LIQUIDATION_ATTEMPT",
            f"flat={flat}; positions={close_results}; orders={cancel_results}",
        )

        if not flat:
            self.notifier.send(
                f"🚨 LIQUIDATION INCOMPLETE\n{account.name}\n"
                f"Manual intervention required immediately."
            )
