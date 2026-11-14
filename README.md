PALACE SPY Signals

A web app for SPY research signals and a manual Investopedia paper-trade journal.

## Included
- SPY 5-minute and daily technical indicators
- VIX context
- Separate 0DTE and weekly scans
- CALL / PUT / NO TRADE decision
- Suggested strike, expiration, indicative midpoint, stop and target
- Supabase Auth login and per-user RLS storage
- Manual paper-trade journal for Investopedia fills

## Important data limitation
This starter version uses Yahoo Finance via `yfinance`. It is unofficial, can be delayed/incomplete, and does not provide a dependable executable real-time options quote feed. This is not a validated predictive model. Do not use it to place real-money trades. A licensed real-time OPRA options feed and rigorous backtesting are required before live use.

## Local run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Notes
- The app does not connect to Investopedia or submit orders. You manually place simulated orders and record your actual fills.
- Streamlit Cloud may sleep when inactive; click Refresh market data to fetch a new scan.
- A signal snapshot is saved only when you click the save button.
- The rules engine is intentionally transparent. The displayed score is not a statistical probability of profit.
