import os
import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import streamlit.components.v1 as components

from core_predictor import generate_dual_forecast
from chart_widgets import render_panel_chart, render_mt4_structure_chart
from structure_scanner import analyze_market_structure
from snapshot_generator import generate_mt4_snapshot
from trade_executor import evaluate_and_place_trade

st.set_page_config(page_title="Forex Confirmation Matrix & MT4 Structure", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .block-container {
        padding-top: 0.2rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0.3rem !important;
        padding-right: 0.3rem !important;
    }
    header {visibility: hidden;} footer {visibility: hidden;}
    div[data-testid="stVerticalBlock"] > div { gap: 0.1rem !important; }
    </style>
""", unsafe_allow_html=True)

# 1. Initialize Active States
pair_list = [
    "EURUSD=X", "USDJPY=X", "GBPUSD=X", "USDCHF=X", 
    "AUDUSD=X", "USDCAD=X", "NZDUSD=X", "EURJPY=X", "GBPJPY=X"
]

if "selected_pair" not in st.session_state:
    st.session_state["selected_pair"] = "USDJPY=X"

if "saved_snapshots" not in st.session_state:
    st.session_state["saved_snapshots"] = []

if "active_trades" not in st.session_state:
    st.session_state["active_trades"] = []

if "daily_counts" not in st.session_state:
    st.session_state["daily_counts"] = {}

tf_config = {
    "15m": {"interval": "15m", "periods": ["1mo", "5d", "7d"]},
    "30m": {"interval": "30m", "periods": ["1mo", "5d", "7d"]},
    "1h":  {"interval": "1h",  "periods": ["1mo", "3mo"]},
    "4h":  {"interval": "1h",  "periods": ["3mo", "6mo"]}
}

@st.cache_data(ttl=60)
def fetch_data(ticker, tf):
    cfg = tf_config[tf]
    data = pd.DataFrame()
    ticker_obj = yf.Ticker(ticker)

    for period in cfg["periods"]:
        try:
            data = ticker_obj.history(period=period, interval=cfg["interval"])
            if not data.empty: break
        except Exception: continue

    if data.empty:
        raise ValueError(f"No market data returned for {ticker} on {tf}.")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data.columns = [str(c).capitalize() for c in data.columns]
    data = data[['Open', 'High', 'Low', 'Close']].dropna().copy()

    # Pre-calculate EMAs for Adam Khoo setup
    data['EMA_6'] = data['Close'].ewm(span=6, adjust=False).mean()
    data['EMA_18'] = data['Close'].ewm(span=18, adjust=False).mean()
    data['EMA_50'] = data['Close'].ewm(span=50, adjust=False).mean()
    data['EMA_200'] = data['Close'].ewm(span=200, adjust=False).mean()

    if tf == "4h":
        data = data.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()

    return data.tail(60)

# Create Main Tabs
tab_live, tab_gallery = st.tabs(["⚡ Live Trading Matrix", "📸 Trade Snapshot Gallery"])

with tab_live:
    col_left, col_right = st.columns([1.3, 1])

    # --- RIGHT SIDE: CONTROLS & MT4 STRUCTURE CHART ---
    with col_right:
        c_title, c_pair, c_tf, c_cross, c_snap, c_btn = st.columns([1.4, 1.2, 0.8, 0.8, 0.9, 0.6])
        
        with c_title: 
            st.markdown("<h4 style='margin:0; color:#FFFFFF;'>⚡ Forex Matrix</h4>", unsafe_allow_html=True)
        
        with c_pair:
            curr_idx = pair_list.index(st.session_state["selected_pair"]) if st.session_state["selected_pair"] in pair_list else 0
            symbol = st.selectbox("Pair", pair_list, index=curr_idx, key="pair_select", label_visibility="collapsed")
            st.session_state["selected_pair"] = symbol

        with c_tf: timeframe = st.selectbox("TF", ["15m", "30m", "1h", "4h"], index=0, label_visibility="collapsed")
        with c_cross: crosshair_enabled = st.toggle("🎯 Cross", value=False)
        with c_snap: test_snapshot_btn = st.button("📸 Snap")
        with c_btn: refresh = st.button("🔄")

        try:
            df = fetch_data(st.session_state["selected_pair"], timeframe)
            struct_info = analyze_market_structure(df)

            st.markdown(f"""
                <div style="background-color: #1E1E1E; padding: 4px 10px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: white; font-weight: bold; font-size: 13px;">MT4 Structure: {st.session_state['selected_pair'].replace('=X','')} ({timeframe})</span>
                    <span style="color: {struct_info['color']}; font-weight: bold; font-size: 13px;">{struct_info['status']}</span>
                </div>
            """, unsafe_allow_html=True)

            # Manual Test Snapshot Button
            if test_snapshot_btn:
                trade_result = evaluate_and_place_trade(
                    df, st.session_state["selected_pair"], timeframe,
                    st.session_state["active_trades"], st.session_state["daily_counts"]
                )
                
                if trade_result and trade_result.get("id") == "DAILY_CAP_REACHED":
                    st.warning("⚠️ Daily cap of 3 trades reached for today. System paused taking new trades.")
                elif trade_result:
                    st.session_state["active_trades"].append(trade_result)
                    fig_snap = generate_mt4_snapshot(df, trade_result)
                    st.session_state["saved_snapshots"].append({
                        "title": f"Trade #{trade_result['id']} - {trade_result['type']} {st.session_state['selected_pair'].replace('=X','')}",
                        "fig": fig_snap
                    })
                    st.success(f"Executed paper trade! Visual saved to 'Trade Snapshot Gallery'.")
                else:
                    # If no natural setup exists, generate mock sample
                    sample_trade = {
                        "id": f"TEST_{len(st.session_state['saved_snapshots']) + 1}",
                        "pair": st.session_state["selected_pair"],
                        "timeframe": timeframe,
                        "type": "BUY",
                        "entry_time": df.index[-5],
                        "entry_price": float(df['Close'].iloc[-5]),
                        "sl": float(df['Low'].iloc[-10]),
                        "tp": float(df['High'].iloc[-1] * 1.002)
                    }
                    fig_snap = generate_mt4_snapshot(df, sample_trade)
                    st.session_state["saved_snapshots"].append({
                        "title": f"Test Snapshot - {st.session_state['selected_pair'].replace('=X','')}",
                        "fig": fig_snap
                    })
                    st.info("No natural Adam Khoo pullback setup active right now. Generated test MT4 snapshot in Gallery.")

            fig_mt4 = render_mt4_structure_chart(df, struct_info, show_crosshair=crosshair_enabled)
            st.plotly_chart(fig_mt4, use_container_width=True, config={'displayModeBar': False})

            # --- WATCHLIST SWITCH BUTTONS ---
            st.markdown("<p style='margin:0; padding:2px 0 0 0; color:#AAAAAA; font-size:11px;'><b>Active Patterns:</b></p>", unsafe_allow_html=True)
            
            active_found = False
            feed_cols = st.columns(len(pair_list) - 1)
            col_i = 0

            for p in pair_list:
                if p != st.session_state["selected_pair"]:
                    try:
                        p_df = fetch_data(p, timeframe)
                        p_info = analyze_market_structure(p_df)
                        if p_info['status'] != "CHOPPY / NO TREND":
                            active_found = True
                            clean_p = p.replace("=X", "")
                            with feed_cols[col_i]:
                                if st.button(f"{clean_p}", key=f"btn_{p}"):
                                    st.session_state["selected_pair"] = p
                                    st.rerun()
                            col_i += 1
                    except Exception:
                        continue
            
            if not active_found:
                st.markdown("<div style='background-color:#111111; padding:4px; border-radius:4px; font-size:11px; color:#666666;'>No active trend patterns detected in other watchlist pairs right now.</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Data error: {e}")

    # --- LEFT SIDE: 9-PANEL PREDICTION MATRIX ---
    with col_left:
        st.markdown(f"<p style='margin:0; padding:0; color:#AAAAAA; font-size:12px;'><b>9-Panel Forecast Matrix: {st.session_state['selected_pair'].replace('=X','')}</b></p>", unsafe_allow_html=True)
        indicators = [
            ("Moving Averages", "MA"), ("Fibonacci Retracement", "FIB"), ("RSI Momentum", "RSI"),
            ("Bollinger Bands", "BOLL"), ("MACD Oscillator", "MACD"), ("Supertrend Indicator", "SUPERTREND"),
            ("Ichimoku Cloud", "ICHIMOKU"), ("ADX Trend Strength", "ADX"), ("Parabolic SAR", "PSAR")
        ]

        row1, row2, row3 = st.columns(3), st.columns(3), st.columns(3)
        grid = [row1, row2, row3]

        try:
            for idx, (title, code) in enumerate(indicators):
                col = grid[idx // 3][idx % 3]
                pred_fast, pred_slow = generate_dual_forecast(df, code)
                fig = render_panel_chart(df, pred_fast, pred_slow, title, show_crosshair=crosshair_enabled)
                
                with col:
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        except Exception as e:
            st.error(f"Matrix load error: {e}")

# --- TAB 2: TRADE GALLERY REVIEW ---
with tab_gallery:
    st.markdown("### 📸 Generated MT4 Trade Snapshots")
    if st.session_state["saved_snapshots"]:
        for snap in reversed(st.session_state["saved_snapshots"]):
            st.markdown(f"#### {snap['title']}")
            st.plotly_chart(snap["fig"], use_container_width=True)
    else:
        st.info("No snapshots generated yet. Go to the 'Live Trading Matrix' tab and click '📸 Snap' to test!")
