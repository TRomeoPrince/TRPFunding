from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import FundedAccount, RiskSnapshot


class Storage:
    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "trpfunding.db"
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                    login INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    equity REAL NOT NULL,
                    balance REAL NOT NULL,
                    daily_dd REAL NOT NULL,
                    overall_dd REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                    login INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    level TEXT NOT NULL,
                    event TEXT NOT NULL,
                    details TEXT
                )
                """
            )

    def save_snapshot(self, account: FundedAccount, snapshot: RiskSnapshot) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO snapshots(login,name,equity,balance,daily_dd,overall_dd)
                VALUES(?,?,?,?,?,?)
                """,
                (
                    account.login,
                    account.name,
                    snapshot.equity,
                    snapshot.balance,
                    snapshot.daily_dd_pct,
                    snapshot.overall_dd_pct,
                ),
            )

    def event(self, account: FundedAccount, level: str, event: str, details: str = "") -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO events(login,name,level,event,details)
                VALUES(?,?,?,?,?)
                """,
                (account.login, account.name, level, event, details),
            )


def load_accounts(path: str) -> list[FundedAccount]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [FundedAccount(**item) for item in raw]
