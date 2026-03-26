import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_autorefresh import st_autorefresh

# --- APP ---
st.set_page_config(page_title="ALPHA SCANNER 2.4", layout="wide")
st_autorefresh(interval=20000, key="refresh")

st.title("🚀 ALPHA SCANNER 2.4 (ALWAYS WORKING)")

# --- SAFE DATA ---
@st.cache_data(ttl=60)
def get_data():
    symbols = {
        "GOLD": "GC=F",
        "OIL": "CL=F",
        "NASDAQ": "^IXIC",
        "SP500": "^GSPC",
        "BTC": "BTC-USD"
    }

    series_list = []

    # TRY REAL DATA
    for name, ticker in symbols.items():
        try:
            data = yf.download(
                ticker,
                period="5d",
                interval="15m",
                progress=False
            )

            if data is not None and not data.empty:
                s = data["Close"].rename(name)
                series_list.append(s)

        except:
            pass

    # IF DATA FAIL → FAKE DATA
    if not series_list:
        st.warning("⚠️ Real data failed → using simulation")

        index = pd.date_range(end=pd.Timestamp.now(), periods=200, freq="15min")

        df = pd.DataFrame(index=index)

        for asset in ["GOLD", "OIL", "NASDAQ", "SP500", "BTC"]:
            price = 100 + np.cumsum(np.random.randn(200))
            df[asset] = price

        return df

    df = pd.concat(series_list, axis=1)
    df = df.ffill().dropna()

    return df

# --- STRATEGY ---
def analyze(asset, series):
    if len(series) < 50:
        return {
            "asset": asset,
            "signal": "NO DATA",
            "score": 0,
            "price": 0,
            "reason": "Not enough data"
        }

    price = series.iloc[-1]

    ema_fast = series.ewm(span=10).mean().iloc[-1]
    ema_slow = series.ewm(span=30).mean().iloc[-1]
    ema200 = series.ewm(span=200).mean().iloc[-1]

    score = 0
    reasons = []

    if price > ema200:
        score += 30
        reasons.append("Uptrend")
    else:
        score += 15
        reasons.append("Downtrend")

    if ema_fast > ema_slow:
        score += 25
        reasons.append("Momentum Up")
    else:
        score += 15
        reasons.append("Momentum Down")

    vol = series.pct_change().rolling(20).std().iloc[-1]
    if not np.isnan(vol) and vol < series.pct_change().std():
        score += 20
        reasons.append("Low Vol")

    signal = "WAIT"
    if ema_fast > ema_slow and price > ema200:
        signal = "ENTER BUY"
    elif ema_fast < ema_slow and price < ema200:
        signal = "ENTER SELL"

    return {
        "asset": asset,
        "signal": signal,
        "score": int(score),
        "price": float(price),
        "reason": ", ".join(reasons)
    }

# --- RUN ---
df = get_data()

results = []
for col in df.columns:
    results.append(analyze(col, df[col]))

table = pd.DataFrame(results)
table["score"] = table["score"].fillna(0)

st.subheader("📊 MARKET SCANNER")
st.dataframe(table, use_container_width=True)

best = table.sort_values("score", ascending=False).iloc[0]

st.divider()
st.subheader("🎯 BEST TRADE")

if best["signal"] == "ENTER BUY":
    st.success(f"🟢 BUY {best['asset']} | Score: {best['score']}")

elif best["signal"] == "ENTER SELL":
    st.error(f"🔴 SELL {best['asset']} | Score: {best['score']}")

else:
    st.info(f"⏳ WAIT | {best['asset']} | Score: {best['score']}")