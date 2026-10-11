# TRP Funding Risk Engine

Private multi-account MT5 risk-management engine for real-money funded traders.

## Core rules
- Daily drawdown limit: 4% equity-based
- Maximum drawdown limit: 10% equity-based
- No per-trade risk cap
- No max-open-position cap
- Adaptive monitoring:
  - 0.00%–1.00% DD: every 120s
  - 1.01%–3.00% DD: every 60s
  - 3.01%–3.50% DD: every 20s
  - 3.51%–3.59% DD: every 10s
  - 3.60%–3.99% DD: every 2s
  - >=4.00% daily DD or >=10.00% max DD: liquidate
- Simulation mode is ON by default.

## Architecture
The engine rotates through many MT5 accounts. Each account gets an adaptive next-check time based on the worse of daily or overall drawdown proximity.

On breach:
1. Mark the account breached.
2. Close open positions.
3. Cancel pending orders.
4. Verify the account is flat.
5. Send an alert.
6. Continue aggressive checks until the operator manually secures the account.

## Setup
1. Install Python 3.11+ on Windows.
2. Install MetaTrader 5.
3. Clone this repository.
4. Run:
   ```bat
   pip install -r requirements.txt
   copy .env.example .env
   copy config\accounts.example.json config\accounts.json
   ```
5. Add MT5 account entries to `config\accounts.json`.
6. Start in simulation mode:
   ```bat
   python -m app.main
   ```

## Safety
Do not enable live liquidation until demo-account testing has confirmed:
- reliable login switching,
- correct equity reads,
- correct drawdown calculations,
- reliable position close/order cancel behavior,
- acceptable polling latency.

Broker-side password changes and fund transfers remain manual.
