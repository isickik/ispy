import os
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

try:
    from supabase import create_client
except Exception:
    create_client = None

APP_NAME = "PALACE SPY SIGNALS"
NY = ZoneInfo("America/New_York")

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Manrope', sans-serif; }
.stApp { background: #080b11; color: #f3f5f8; }
.block-container { max-width: 1280px; padding-top: 2rem; padding-bottom: 3rem; }
[data-testid="stHeader"] { background: rgba(8,11,17,0.9); }
[data-testid="stSidebar"] { background: #0e1420; }
.palace-brand { text-align:center; letter-spacing:.34em; font-size:12px; color:#9ba8bb; font-weight:700; }
.palace-title { text-align:center; font-size:38px; line-height:1.1; font-weight:800; letter-spacing:.10em; margin-top:8px; color:#f6f7fb; }
.palace-sub { text-align:center; color:#7f8ca1; font-size:11px; letter-spacing:.18em; margin-top:8px; }
.panel { background:#111824; border:1px solid #202c3d; border-radius:16px; padding:20px 22px; }
.metric-label { color:#8e9bb0; font-size:11px; letter-spacing:.13em; text-transform:uppercase; }
.metric-value { color:#f5f7fa; font-family:'DM Mono',monospace; font-size:25px; font-weight:500; margin-top:7px; }
.signal-call { background:linear-gradient(135deg,rgba(21,128,91,.20),rgba(17,24,36,1) 65%); border:1px solid #176b51; }
.signal-put { background:linear-gradient(135deg,rgba(190,55,65,.20),rgba(17,24,36,1) 65%); border:1px solid #81353e; }
.signal-none { background:#111824; border:1px solid #344154; }
.signal-word { font-size:35px; font-weight:800; letter-spacing:.08em; }
.mono { font-family:'DM Mono',monospace; }
.small-muted { color:#8b98ab; font-size:12px; }
hr { border-color:#202c3d !important; }
div.stButton > button { border-radius:10px; font-weight:700; min-height:42px; }
[data-testid="stDataFrame"] { border:1px solid #202c3d; border-radius:12px; }
</style>
""", unsafe_allow_html=True)

# ---------- Secrets / Auth ----------
def secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)

SUPABASE_URL = secret("SUPABASE_URL")
SUPABASE_KEY = secret("SUPABASE_ANON_KEY")
supabase = None
if SUPABASE_URL and SUPABASE_KEY and create_client:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Streamlit reruns the script on every interaction; restore the Supabase
        # Auth session from Streamlit session state so RLS keeps working.
        saved_access = st.session_state.get("access_token")
        saved_refresh = st.session_state.get("refresh_token")
        if saved_access and saved_refresh:
            supabase.auth.set_session(saved_access, saved_refresh)
    except Exception:
        supabase = None

def logout():
    for key in ["user", "access_token", "refresh_token", "auth_email"]:
        st.session_state.pop(key, None)
    st.rerun()

def login_screen():
    st.markdown('<div class="palace-brand">PALACE</div><div class="palace-title">SPY SIGNALS</div><div class="palace-sub">A MARKET RESEARCH & PAPER-TRADING DESK</div>', unsafe_allow_html=True)
    st.write("")
    if not supabase:
        st.error("Supabase is not configured. Add SUPABASE_URL and SUPABASE_ANON_KEY in Streamlit secrets.")
        st.code('[secrets]\nSUPABASE_URL = "https://YOUR_PROJECT.supabase.co"\nSUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY"', language="toml")
        st.info("For local testing only, set PALACE_LOCAL_MODE = true in secrets. Do not deploy public access in local mode.")
        if str(secret("PALACE_LOCAL_MODE", "false")).lower() == "true":
            with st.form("local_login"):
                email = st.text_input("Email")
                password = st.text_input("Local access code", type="password")
                go = st.form_submit_button("Enter PALACE", use_container_width=True)
            if go and password == secret("PALACE_LOCAL_PASSWORD", "") and email:
                st.session_state.user = {"id": "local-user", "email": email}
                st.session_state.auth_email = email
                st.rerun()
            elif go:
                st.error("Incorrect access code.")
        st.stop()

    st.markdown('<div class="panel" style="max-width:460px;margin:20px auto;">', unsafe_allow_html=True)
    mode = st.radio(" ", ["Sign in", "Create account"], horizontal=True, label_visibility="collapsed")
    with st.form("auth_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Continue", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    if submit:
        try:
            if mode == "Sign in":
                result = supabase.auth.sign_in_with_password({"email": email, "password": password})
            else:
                result = supabase.auth.sign_up({"email": email, "password": password})
            user = getattr(result, "user", None)
            session = getattr(result, "session", None)
            if user:
                if session:
                    st.session_state.access_token = session.access_token
                    st.session_state.refresh_token = session.refresh_token
                st.session_state.user = {"id": user.id, "email": user.email}
                st.session_state.auth_email = user.email
                st.rerun()
            elif mode == "Create account":
                st.success("Check your email to confirm your account, then sign in.")
            else:
                st.error("Sign-in did not return a session. Check your email/password and Supabase email settings.")
        except Exception as e:
            st.error(f"Authentication failed: {e}")
    st.caption("Account access is managed through Supabase Authentication. Disable public sign-ups in Supabase if you want invite-only access.")

if "user" not in st.session_state:
    login_screen()
    # login_screen returns normally when Supabase is configured but no user has
    # signed in yet. Stop here so the dashboard never reads a missing session key.
    st.stop()

USER = st.session_state.user
USER_ID = USER["id"]

# ---------- Database ----------
def db_insert(table, payload):
    if not supabase or USER_ID == "local-user":
        st.session_state.setdefault(f"local_{table}", [])
        row = dict(payload)
        row.setdefault("id", f"local-{len(st.session_state[f'local_{table}']) + 1}")
        row.setdefault("created_at", datetime.now(NY).isoformat())
        st.session_state[f"local_{table}"].append(row)
        return True
    try:
        supabase.table(table).insert(payload).execute()
        return True
    except Exception as e:
        st.error(f"Could not save to Supabase: {e}")
        return False

def db_select(table, limit=200):
    if not supabase or USER_ID == "local-user":
        return st.session_state.get(f"local_{table}", [])
    try:
        res = supabase.table(table).select("*").eq("user_id", USER_ID).order("created_at", desc=True).limit(limit).execute()
        return res.data or []
    except Exception as e:
        st.warning(f"Could not load {table}: {e}")
        return []

def db_update_trade(trade_id, payload):
    if not supabase or USER_ID == "local-user":
        rows = st.session_state.get("local_paper_trades", [])
        for row in rows:
            if row.get("id") == trade_id:
                row.update(payload)
        return True
    try:
        supabase.table("paper_trades").update(payload).eq("id", trade_id).eq("user_id", USER_ID).execute()
        return True
    except Exception as e:
        st.error(f"Could not update trade: {e}")
        return False

# ---------- Market data ----------
@st.cache_data(ttl=60, show_spinner=False)
def load_market_data():
    ticker = yf.Ticker("SPY")
    intraday = ticker.history(period="5d", interval="5m", auto_adjust=True)
    daily = ticker.history(period="1y", interval="1d", auto_adjust=True)
    vix = yf.Ticker("^VIX").history(period="5d", interval="1d", auto_adjust=True)
    info = ticker.fast_info
    return intraday, daily, vix, dict(info) if info else {}

@st.cache_data(ttl=180, show_spinner=False)
def load_option_chain(expiry):
    ticker = yf.Ticker("SPY")
    return ticker.option_chain(expiry)

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def compute_indicators(intraday, daily, vix):
    if intraday.empty or daily.empty:
        raise ValueError("Market data is unavailable.")
    x = intraday.dropna(subset=["Close"]).copy()
    d = daily.dropna(subset=["Close"]).copy()
    x["ema9"] = x["Close"].ewm(span=9, adjust=False).mean()
    x["ema21"] = x["Close"].ewm(span=21, adjust=False).mean()
    x["rsi"] = rsi(x["Close"])
    x["vwap"] = (x["Close"] * x["Volume"]).cumsum() / x["Volume"].replace(0, np.nan).cumsum()
    d["ema20"] = d["Close"].ewm(span=20, adjust=False).mean()
    d["ema50"] = d["Close"].ewm(span=50, adjust=False).mean()
    d["rsi"] = rsi(d["Close"])
    last = x.iloc[-1]
    prev = x.iloc[-4] if len(x) >= 4 else x.iloc[0]
    day = d.iloc[-1]
    vix_value = float(vix["Close"].dropna().iloc[-1]) if not vix.empty else np.nan
    move_15m = (float(last.Close) / float(prev.Close) - 1) * 100
    return {
        "price": float(last.Close),
        "ema9": float(last.ema9),
        "ema21": float(last.ema21),
        "vwap": float(last.vwap) if pd.notna(last.vwap) else float(last.Close),
        "rsi_5m": float(last.rsi) if pd.notna(last.rsi) else 50.0,
        "daily_close": float(day.Close),
        "daily_ema20": float(day.ema20),
        "daily_ema50": float(day.ema50),
        "daily_rsi": float(day.rsi) if pd.notna(day.rsi) else 50.0,
        "vix": vix_value,
        "move_15m": move_15m,
        "timestamp": str(x.index[-1]),
        "intraday": x,
        "daily": d,
    }

def market_score(ind):
    score = 0
    reasons = []
    if ind["ema9"] > ind["ema21"]:
        score += 1
        reasons.append("5-minute EMA 9 is above EMA 21")
    else:
        score -= 1
        reasons.append("5-minute EMA 9 is below EMA 21")
    if ind["price"] > ind["vwap"]:
        score += 1
        reasons.append("SPY is above intraday VWAP")
    else:
        score -= 1
        reasons.append("SPY is below intraday VWAP")
    if ind["daily_close"] > ind["daily_ema20"] > ind["daily_ema50"]:
        score += 1
        reasons.append("Daily trend is bullish")
    elif ind["daily_close"] < ind["daily_ema20"] < ind["daily_ema50"]:
        score -= 1
        reasons.append("Daily trend is bearish")
    if ind["rsi_5m"] > 55:
        score += 1
        reasons.append("Short-term momentum is positive")
    elif ind["rsi_5m"] < 45:
        score -= 1
        reasons.append("Short-term momentum is negative")
    if ind["move_15m"] > 0.12:
        score += 1
        reasons.append("Recent 15-minute move is upward")
    elif ind["move_15m"] < -0.12:
        score -= 1
        reasons.append("Recent 15-minute move is downward")
    return score, reasons

def ny_now():
    return datetime.now(NY)

def is_regular_session(now):
    if now.weekday() >= 5:
        return False
    t = now.time()
    return datetime.strptime("09:35", "%H:%M").time() <= t <= datetime.strptime("15:45", "%H:%M").time()

def choose_expiries(expirations, now):
    today = now.date()
    parsed = []
    for e in expirations:
        try:
            dt = datetime.strptime(e, "%Y-%m-%d").date()
            dte = (dt - today).days
            if dte >= 0:
                parsed.append((e, dte))
        except Exception:
            pass
    zero = next((e for e, d in parsed if d == 0), None)
    weekly = next((e for e, d in parsed if 5 <= d <= 14), None)
    if weekly is None:
        weekly = next((e for e, d in parsed if 1 <= d <= 21), None)
    return zero, weekly

def select_contract(chain_df, side, spot):
    if chain_df is None or chain_df.empty:
        return None
    df = chain_df.copy()
    required = ["strike", "bid", "ask", "lastPrice", "impliedVolatility", "volume", "openInterest"]
    for c in required:
        if c not in df.columns:
            df[c] = np.nan
    df["mid"] = (pd.to_numeric(df["bid"], errors="coerce") + pd.to_numeric(df["ask"], errors="coerce")) / 2
    df["spread_pct"] = (df["ask"] - df["bid"]) / df["mid"].replace(0, np.nan) * 100
    df = df[
        (df["mid"] > 0.05) &
        (df["bid"] > 0) &
        (df["ask"] >= df["bid"]) &
        (df["spread_pct"] <= 35) &
        (df["openInterest"].fillna(0) >= 10)
    ].copy()
    if df.empty:
        return None
    # Select near-the-money with modest directional moneyness.
    target = spot * (1.002 if side == "CALL" else 0.998)
    df["distance"] = (df["strike"] - target).abs()
    df = df.sort_values(["distance", "spread_pct"], ascending=[True, True])
    row = df.iloc[0]
    return {
        "strike": float(row["strike"]),
        "bid": float(row["bid"]),
        "ask": float(row["ask"]),
        "mid": float(row["mid"]),
        "iv": float(row["impliedVolatility"]) if pd.notna(row["impliedVolatility"]) else np.nan,
        "volume": int(row["volume"]) if pd.notna(row["volume"]) else 0,
        "open_interest": int(row["openInterest"]) if pd.notna(row["openInterest"]) else 0,
        "spread_pct": float(row["spread_pct"]),
    }

def build_signal(ind, expirations, now, strategy):
    score, reasons = market_score(ind)
    # Require a clear directional score and avoid chasing extreme momentum.
    if abs(score) < 3:
        return {"strategy": strategy, "side": "NO TRADE", "reason": "Signals are mixed; no directional edge passed the filter.", "score": score, "reasons": reasons}
    if (score >= 3 and ind["rsi_5m"] > 78) or (score <= -3 and ind["rsi_5m"] < 22):
        return {"strategy": strategy, "side": "NO TRADE", "reason": "Momentum is too extended; avoid chasing.", "score": score, "reasons": reasons}
    if not is_regular_session(now):
        return {"strategy": strategy, "side": "NO TRADE", "reason": "Outside the preferred regular-session entry window.", "score": score, "reasons": reasons}
    side = "CALL" if score > 0 else "PUT"
    zero_exp, weekly_exp = choose_expiries(expirations, now)
    expiry = zero_exp if strategy == "0DTE" else weekly_exp
    if not expiry:
        return {"strategy": strategy, "side": "NO TRADE", "reason": f"No suitable {strategy} expiration was returned by the data provider.", "score": score, "reasons": reasons}
    try:
        chain = load_option_chain(expiry)
        options = chain.calls if side == "CALL" else chain.puts
        contract = select_contract(options, side, ind["price"])
    except Exception:
        contract = None
    if not contract:
        return {"strategy": strategy, "side": "NO TRADE", "reason": "No contract passed the quote, spread and liquidity filters.", "score": score, "reasons": reasons}
    entry = round(contract["mid"], 2)
    if entry <= 0:
        return {"strategy": strategy, "side": "NO TRADE", "reason": "Invalid option midpoint.", "score": score, "reasons": reasons}
    return {
        "strategy": strategy, "side": side, "expiry": expiry,
        "strike": contract["strike"], "entry": entry,
        "stop": round(entry * 0.70, 2), "target": round(entry * 1.50, 2),
        "score": score, "reasons": reasons, "contract": contract,
        "reason": "Directional filters aligned and a contract passed basic liquidity checks."
    }

# ---------- Header ----------
left, center, right = st.columns([1, 2, 1])
with center:
    st.markdown('<div class="palace-brand">PALACE</div><div class="palace-title">SPY SIGNALS</div><div class="palace-sub">THE MARKET, REDUCED TO ONE DECISION</div>', unsafe_allow_html=True)
with right:
    st.markdown(f'<div style="text-align:right;color:#8996aa;font-size:12px;padding-top:12px;">{USER.get("email","")}</div>', unsafe_allow_html=True)
    if st.button("Sign out", use_container_width=True):
        logout()

st.write("")
tab_signal, tab_journal, tab_method = st.tabs(["SIGNAL DESK", "PAPER TRADE JOURNAL", "SYSTEM"])

# ---------- Fetch ----------
with st.spinner("Reading SPY market data and options chains..."):
    try:
        intraday, daily, vix, fast_info = load_market_data()
        indicators = compute_indicators(intraday, daily, vix)
        expirations = yf.Ticker("SPY").options
        data_error = None
    except Exception as e:
        indicators, expirations, data_error = None, [], str(e)

with tab_signal:
    if data_error:
        st.error(f"Market data unavailable: {data_error}")
        st.info("Try refreshing. Yahoo Finance data is an unofficial source and may be delayed or incomplete.")
    else:
        now = ny_now()
        spot = indicators["price"]
        score, reasons = market_score(indicators)
        zero_signal = build_signal(indicators, expirations, now, "0DTE")
        weekly_signal = build_signal(indicators, expirations, now, "WEEKLY")

        # Choose one best opportunity. Both are displayed for transparency.
        candidates = [s for s in [zero_signal, weekly_signal] if s["side"] in ("CALL", "PUT")]
        selected = max(candidates, key=lambda s: (abs(s["score"]), 1 if s["strategy"] == "WEEKLY" else 0)) if candidates else None

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f'<div class="panel"><div class="metric-label">SPY LAST</div><div class="metric-value">${spot:,.2f}</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="panel"><div class="metric-label">MARKET BIAS</div><div class="metric-value">{ "BULLISH" if score > 0 else "BEARISH" if score < 0 else "NEUTRAL"}</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="panel"><div class="metric-label">SIGNAL SCORE</div><div class="metric-value">{score:+d} / 5</div></div>', unsafe_allow_html=True)
        with m4:
            vix_text = f"{indicators['vix']:.2f}" if np.isfinite(indicators["vix"]) else "N/A"
            st.markdown(f'<div class="panel"><div class="metric-label">VIX</div><div class="metric-value">{vix_text}</div></div>', unsafe_allow_html=True)

        st.write("")
        if selected:
            klass = "signal-call" if selected["side"] == "CALL" else "signal-put"
            st.markdown(f"""
            <div class="panel {klass}">
              <div class="metric-label">PALACE'S TOP PAPER-TRADE SETUP · {selected['strategy']}</div>
              <div class="signal-word">{selected['side']}</div>
              <div style="font-size:22px;font-weight:800;margin-top:4px;">SPY ${selected['strike']:,.0f} {selected['side']}</div>
              <div class="small-muted">Expiration: {selected['expiry']} · Signal score: {selected['score']:+d}/5</div>
              <hr>
              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;">
                <div><div class="metric-label">LIMIT ENTRY</div><div class="metric-value">${selected['entry']:.2f}</div></div>
                <div><div class="metric-label">STOP (OPTION)</div><div class="metric-value">${selected['stop']:.2f}</div></div>
                <div><div class="metric-label">TARGET (OPTION)</div><div class="metric-value">${selected['target']:.2f}</div></div>
              </div>
              <div class="small-muted" style="margin-top:14px;">Illustrative research signal. Verify the exact contract and live bid/ask in Investopedia before entering.</div>
            </div>
            """, unsafe_allow_html=True)
            st.write("")
            st.warning("This is a rules-based research signal, not a probability of profit or a guarantee. The option midpoint may be delayed and can differ from an executable price.")
        else:
            st.markdown('<div class="panel signal-none"><div class="metric-label">PALACE DECISION</div><div class="signal-word">NO TRADE</div><div class="small-muted">Neither strategy currently passes the entry filters. Protecting capital is a valid signal.</div></div>', unsafe_allow_html=True)

        st.write("")
        st.subheader("Both strategy scans")
        c1, c2 = st.columns(2)
        for col, sig in zip([c1, c2], [zero_signal, weekly_signal]):
            with col:
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.markdown(f"**{sig['strategy']}**")
                if sig["side"] == "NO TRADE":
                    st.markdown("### NO TRADE")
                else:
                    st.markdown(f"### {sig['side']} · ${sig['strike']:,.0f}")
                    st.write(f"Expiration: `{sig['expiry']}`")
                    st.write(f"Entry: `${sig['entry']:.2f}` · Stop: `${sig['stop']:.2f}` · Target: `${sig['target']:.2f}`")
                st.caption(sig["reason"])
                st.markdown("</div>", unsafe_allow_html=True)

        st.write("")
        with st.expander("What the system is seeing"):
            st.write(f"**Data timestamp:** {indicators['timestamp']}")
            st.write(f"**5-minute RSI:** {indicators['rsi_5m']:.1f}")
            st.write(f"**Daily RSI:** {indicators['daily_rsi']:.1f}")
            st.write(f"**VWAP:** ${indicators['vwap']:.2f}")
            st.write(f"**15-minute move:** {indicators['move_15m']:+.2f}%")
            for reason in reasons:
                st.write(f"• {reason}")
            st.caption("The score is a simple transparent rules engine, not a trained predictive model. It does not currently calculate constituent breadth or use a live institutional options feed.")

        # Save signal snapshots, de-dupe by date/strategy/side/contract for this session.
        if st.button("Save today's signal snapshot", use_container_width=True):
            for sig in [zero_signal, weekly_signal]:
                payload = {
                    "user_id": USER_ID,
                    "strategy": sig["strategy"],
                    "side": sig["side"],
                    "expiry": sig.get("expiry"),
                    "strike": sig.get("strike"),
                    "entry_price": sig.get("entry"),
                    "stop_price": sig.get("stop"),
                    "target_price": sig.get("target"),
                    "signal_score": sig["score"],
                    "spy_price": spot,
                    "reason": sig["reason"],
                    "market_timestamp": indicators["timestamp"],
                }
                db_insert("signals", payload)
            st.success("Signal snapshots saved.")

        st.caption(f"Market clock: {now.strftime('%A, %b %d · %I:%M:%S %p ET')} · Auto-refresh is manual; use the refresh button below.")
        if st.button("Refresh market data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

with tab_journal:
    st.subheader("Investopedia paper-trade journal")
    st.caption("Enter the fill you actually received in Investopedia. PALACE does not place orders.")
    with st.form("new_trade"):
        a, b, c = st.columns(3)
        with a:
            strategy = st.selectbox("Strategy", ["0DTE", "WEEKLY"])
            side = st.selectbox("Direction", ["CALL", "PUT"])
        with b:
            strike = st.number_input("Strike", min_value=0.0, value=680.0, step=1.0)
            expiry = st.date_input("Expiration", value=date.today() + timedelta(days=7))
        with c:
            entry = st.number_input("Your entry premium", min_value=0.0, value=1.00, step=0.05)
            contracts = st.number_input("Contracts", min_value=1, value=1, step=1)
        notes = st.text_input("Notes (optional)")
        save = st.form_submit_button("Log paper trade", use_container_width=True)
    if save:
        if entry <= 0:
            st.error("Enter a valid fill price.")
        else:
            payload = {
                "user_id": USER_ID, "strategy": strategy, "side": side,
                "strike": float(strike), "expiry": expiry.isoformat(),
                "entry_price": float(entry), "contracts": int(contracts),
                "status": "OPEN", "notes": notes,
            }
            if db_insert("paper_trades", payload):
                st.success("Paper trade logged.")
                st.rerun()

    trades = db_select("paper_trades")
    if trades:
        st.write("")
        st.subheader("Open and completed trades")
        for trade in trades:
            with st.container(border=True):
                cols = st.columns([2, 1, 1, 1, 1])
                cols[0].markdown(f"**SPY {trade.get('strike')} {trade.get('side')}**")
                cols[0].caption(f"{trade.get('strategy')} · Exp {trade.get('expiry')}")
                cols[1].metric("Entry", f"${float(trade.get('entry_price') or 0):.2f}")
                cols[2].metric("Contracts", str(trade.get("contracts", 1)))
                status = trade.get("status", "OPEN")
                cols[3].metric("Status", status)
                if status == "OPEN":
                    with cols[4]:
                        if st.button("Close", key=f"close_{trade.get('id', id(trade))}"):
                            st.session_state[f"closing_{trade.get('id', id(trade))}"] = True
                    if st.session_state.get(f"closing_{trade.get('id', id(trade))}"):
                        with st.form(f"close_form_{trade.get('id', id(trade))}"):
                            exit_price = st.number_input("Exit premium", min_value=0.0, value=float(trade.get("entry_price") or 0), step=0.05, key=f"exit_{trade.get('id', id(trade))}")
                            if st.form_submit_button("Save close"):
                                pnl = (exit_price - float(trade.get("entry_price") or 0)) * 100 * int(trade.get("contracts") or 1)
                                db_update_trade(trade["id"], {"exit_price": float(exit_price), "pnl": float(pnl), "status": "CLOSED", "closed_at": datetime.now(NY).isoformat()})
                                st.rerun()
                else:
                    exit_price = trade.get("exit_price")
                    pnl = trade.get("pnl")
                    cols[4].metric("P/L", f"${float(pnl or 0):+.2f}")
    else:
        st.info("No paper trades logged yet. Log the fills you place in Investopedia to build your record.")

    closed = [t for t in trades if t.get("status") == "CLOSED"]
    if closed:
        pnl_values = [float(t.get("pnl") or 0) for t in closed]
        wins = sum(1 for p in pnl_values if p > 0)
        total = len(pnl_values)
        st.write("")
        k1, k2, k3 = st.columns(3)
        k1.metric("Closed trades", total)
        k2.metric("Win rate", f"{wins / total * 100:.1f}%")
        k3.metric("Net simulated P/L", f"${sum(pnl_values):+.2f}")

with tab_method:
    st.subheader("What this version does")
    st.markdown("""
    - Reads SPY 5-minute and daily candles plus the VIX index.
    - Scores trend and momentum using EMA 9/21, VWAP, daily EMA 20/50, RSI and recent price movement.
    - Checks both same-day expiration and a 5–14 day weekly expiration when available.
    - Filters option contracts for positive bid/ask, a maximum quoted spread and minimum open interest.
    - Produces CALL, PUT or NO TRADE, with a suggested midpoint entry, -30% option stop and +50% option target.
    - Stores signal snapshots and your manually entered Investopedia paper trades in Supabase.
    """)
    st.warning("Important limitations: Yahoo Finance data is unofficial and may be delayed, incomplete or unavailable. The option chain snapshot is not guaranteed to be real-time. This first release is a transparent rules-based prototype—not an AI model, not a proven edge, and not a recommendation to buy an option. Never assume a displayed midpoint is fillable.")
    st.markdown("**Before real-money use:** add a licensed real-time OPRA options data provider, backtest with point-in-time data including bid/ask and slippage, and validate the strategy out-of-sample. 0DTE options can lose 100% of premium very quickly.")
    st.markdown("**Investopedia workflow:** copy the suggested expiration/strike/direction, confirm the exact contract in the simulator, enter a limit order, then record your actual fill in the journal.")

st.markdown("---")
st.markdown('<div class="palace-sub">PALACE · PRIVATE MARKET RESEARCH · NOT FINANCIAL ADVICE</div>', unsafe_allow_html=True)
