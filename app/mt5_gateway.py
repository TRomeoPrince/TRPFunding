from __future__ import annotations

import os
from dataclasses import dataclass

import MetaTrader5 as mt5

from .models import FundedAccount


@dataclass
class AccountInfo:
    equity: float
    balance: float


class MT5Gateway:
    def __init__(self) -> None:
        self.terminal_path = os.getenv("MT5_TERMINAL_PATH", "").strip() or None

    def connect(self, account: FundedAccount) -> AccountInfo:
        kwargs = {}
        if self.terminal_path:
            kwargs["path"] = self.terminal_path

        if not mt5.initialize(**kwargs):
            code, msg = mt5.last_error()
            raise RuntimeError(f"MT5 initialize failed: {code} {msg}")

        if not mt5.login(account.login, password=account.password, server=account.server):
            code, msg = mt5.last_error()
            raise RuntimeError(f"MT5 login failed: {code} {msg}")

        info = mt5.account_info()
        if info is None:
            raise RuntimeError("MT5 account_info() returned None")

        return AccountInfo(equity=float(info.equity), balance=float(info.balance))

    def positions(self):
        return mt5.positions_get() or ()

    def orders(self):
        return mt5.orders_get() or ()

    def close_all_positions(self) -> list[str]:
        results: list[str] = []
        for pos in self.positions():
            tick = mt5.symbol_info_tick(pos.symbol)
            if tick is None:
                results.append(f"{pos.ticket}: no tick")
                continue

            order_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
            price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": order_type,
                "position": pos.ticket,
                "price": price,
                "deviation": 50,
                "magic": 260011,
                "comment": "TRPFunding risk liquidation",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = mt5.order_send(request)
            results.append(f"{pos.ticket}: {getattr(result, 'retcode', None)}")
        return results

    def cancel_all_orders(self) -> list[str]:
        results: list[str] = []
        for order in self.orders():
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": order.ticket,
                "comment": "TRPFunding risk cancel",
            }
            result = mt5.order_send(request)
            results.append(f"{order.ticket}: {getattr(result, 'retcode', None)}")
        return results

    def is_flat(self) -> bool:
        return len(self.positions()) == 0 and len(self.orders()) == 0

    def shutdown(self) -> None:
        mt5.shutdown()
