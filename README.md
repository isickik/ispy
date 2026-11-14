# PALACE SPY Signals

A Streamlit web app for SPY research signals and a manual Investopedia paper-trade journal.

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

## Deploy on Streamlit Community Cloud
1. Create a new GitHub repository, e.g. `palace-spy-signals`.
2. Upload `app.py`, `requirements.txt`, `supabase_schema.sql`, and `.streamlit/config.toml`.
3. In Supabase, create a project.
4. Open Supabase SQL Editor and run all of `supabase_schema.sql`.
5. In Supabase Authentication settings, disable public sign-ups if you want invite-only accounts. Add users from the Supabase dashboard.
6. In Streamlit Community Cloud, create an app from the GitHub repo; main file is `app.py`.
7. In Streamlit app Settings → Secrets, add:

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_ANON_KEY = "YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY"
```

Use the project's publishable/anon key only. Never put the Supabase service-role key in Streamlit secrets or client-side code.

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
