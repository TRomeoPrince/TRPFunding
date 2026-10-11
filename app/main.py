from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from .engine import RiskEngine
from .storage import Storage, load_accounts


def main() -> None:
    load_dotenv()

    accounts_path = Path("config/accounts.json")
    if not accounts_path.exists():
        raise SystemExit(
            "Missing config/accounts.json. Copy config/accounts.example.json first."
        )

    accounts = load_accounts(str(accounts_path))
    accounts = [a for a in accounts if a.enabled]

    if not accounts:
        raise SystemExit("No enabled accounts configured.")

    storage = Storage(os.getenv("DATA_DIR", "data"))
    engine = RiskEngine(accounts, storage)

    print(f"TRP Funding Risk Engine starting with {len(accounts)} account(s).")
    print(f"Simulation mode: {engine.simulation_mode}")
    engine.run_forever()


if __name__ == "__main__":
    main()
