import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime

# --- 1. SETTINGS & STYLE ---
st.set_page_config(page_title="QuantSuite Pro", layout="wide")

# --- 2. THE LOCK (Security) ---
MASTER_PASSWORD = os.getenv("APP_PASSWORD", "admin123")

def check_password():
    if st.session_state.get("password_correct", False): return True
    st.title("🔒 QuantSuite Pro: Secure Login")
    pwd = st.text_input("Access Key", type="password")
    if st.button("Unlock Dashboard"):
        if pwd == MASTER_PASSWORD:
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("❌ Access Denied")
    return False

# --- 3. THE MATH ENGINE (Quantitative Logic) ---
@st.cache_data(ttl=3600)
def get_analysis(tickers):
    # Download data for stocks + the S&P 500 benchmark
    data = yf.download(tickers + ["^GSPC"], period="1y")['Close']
    returns = data.pct_change().dropna()
    mkt_ret = returns["^GSPC"].mean() * 252
    
    results = []
    for t in tickers:
        stock = yf.Ticker(t)
        # Calculate Alpha, Beta, and Sharpe
        beta = np.cov(returns[t], returns["^GSPC"])[0,1] / np.var(returns["^GSPC"])
        ann_ret = returns[t].mean() * 252
        vol = returns[t].std() * np.sqrt(252)
        alpha = ann_ret - (0.04 + beta * (mkt_ret - 0.04))
        sharpe = (ann_ret - 0.04) / vol
        
               # ⏰ Clock: Next Earnings (Updated Safer Version)
        try:
            cal = stock.calendar
            earn_msg = "N/A"
            if isinstance(cal, dict) and 'Earnings Date' in cal:
                # Get the date safely from the list
                next_earn = cal['Earnings Date'][0] 
                days_to = (next_earn.date() - datetime.now().date()).days
                earn_msg = f"In {days_to} Days" if days_to > 0 else "Today/Past"
        except:
            earn_msg = "N/A"


        results.append({
            "Ticker": t,
            "Price": f"${data[t].iloc[-1]:.2f}",
            "Alpha": alpha,
            "Sharpe": sharpe,
            "Earnings": earn_msg,
            "Volatility": f"{vol:.2%}"
        })
    return pd.DataFrame(results)

# --- 4. THE TV SCREEN (User Interface) ---
if check_password():
    if "my_watchlist" not in st.session_state:
        st.session_state.my_watchlist = "AAPL,MSFT,NVDA,WMT,KO"

    st.sidebar.title("🎮 Command Center")
    page = st.sidebar.radio("View", ["Power Scanner", "News Feed"])
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    if page == "Power Scanner":
        st.header("🔍 Alpha Discovery & Risk Engine")
        watchlist = st.text_area("Your Favorites:", st.session_state.my_watchlist)
        
        if st.button("💾 Save Watchlist"):
            st.session_state.my_watchlist = watchlist
            st.success("Saved!")

               if st.button("🚀 Run Full Analysis"):
            tickers = [t.strip().upper() for t in watchlist.split(",")]
            with st.spinner("Crunching Math..."):
                df = get_analysis(tickers)
                
                # --- This is the part we are fixing ---
                def style_results(val):
                    if isinstance(val, (int, float)):
                        color = 'green' if val > 0 else 'red'
                        return f'color: {color}; font-weight: bold'
                    return ''
                
                st.subheader("Analysis Results")
                st.dataframe(df.style.map(style_results, subset=['Alpha', 'Sharpe']))



    elif page == "News Feed":
        st.header("📰 Live Market Context")
        t_choice = st.selectbox("Select Ticker", st.session_state.my_watchlist.split(","))
        news = yf.Ticker(t_choice.strip()).news
        for item in news[:5]:
            st.write(f"**{item['title']}**")
            st.caption(f"Source: {item['publisher']} | [Read]({item['link']})")
            st.divider()
