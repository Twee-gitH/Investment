import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import time

# --- 1. DATA PERSISTENCE ---
REGISTRY_FILE = "bpsm_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r") as f:
                return json.load(f)
        except: return {}
    return {}

def save_user(name, pin):
    reg = load_registry()
    if name in reg: return False
    reg[name] = {"pin": pin, "wallet": 0.0, "inv": [], "tx": []}
    with open(REGISTRY_FILE, "w") as f:
        json.dump(reg, f, default=str)
    return True

def update_user(name, data):
    reg = load_registry()
    reg[name] = data
    with open(REGISTRY_FILE, "w") as f:
        json.dump(reg, f, default=str)

# --- 2. MOBILE-FIT DESIGN ---
st.set_page_config(page_title="BPSM Official", layout="centered")

st.markdown("""
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    </head>
    <style>
    .block-container { padding: 1rem !important; max-width: 100% !important; }
    .stApp { background-color: #0b0c0e; color: white; }
    
    /* Headers */
    .brand { text-align: center; color: #ffffff; font-family: 'Arial Black'; font-size: 1.8rem; margin-bottom: 0; }
    .sub-brand { text-align: center; color: #ce1126; font-size: 0.7rem; letter-spacing: 2px; margin-top: -5px; margin-bottom: 15px; }

    /* Inputs: BLACK TEXT, NO ZOOM */
    .stTextInput input, .stNumberInput input {
        color: #000000 !important; 
        -webkit-text-fill-color: #000000 !important;
        background-color: #ffffff !important;
        border-radius: 10px !important;
        height: 3.5rem !important;
        font-size: 16px !important;
        font-weight: bold !important;
    }

    /* Action Row Icons */
    .action-row { display: flex; justify-content: space-around; margin: 15px 0; }
    .icon-circle {
        width: 50px; height: 50px; background-color: #17181c;
        border: 1px solid #2a2b30; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto; font-size: 1.2rem;
    }
    .action-text { font-size: 0.7rem; color: #8c8f99; text-align: center; margin-top: 5px; font-weight: bold; }

    /* Neon Green Button */
    .stButton>button {
        width: 100% !important; border-radius: 10px; height: 3.8rem; font-size: 1.1rem; font-weight: 900;
        background: #0dcf70 !important; color: #0b0c0e !important;
        border: none !important; box-shadow: 0 4px 12px rgba(13, 207, 112, 0.3);
    }

    /* Profit/Timer Cards */
    .trade-card {
        background-color: #17181c; padding: 12px; border-radius: 10px;
        border: 1px solid #2a2b30; margin-bottom: 10px;
    }
    .timer-text { color: #0dcf70; font-family: monospace; font-weight: bold; font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION ---
if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.markdown("<h1 class='brand'>BPSM</h1><p class='sub-brand'>BAGONG PILIPINAS STOCK MARKET</p>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 LOGIN", "📝 REGISTER"])
    with t1:
        l_name = st.text_input("NAME", key="l_n").upper()
        l_pin = st.text_input("PIN", type="password", max_chars=6, key="l_p")
        if st.button("SIGN IN"):
            reg = load_registry()
            if l_name in reg and reg[l_name]['pin'] == l_pin:
                st.session_state.user = l_name
                st.rerun()
            else: st.error("Incorrect Details")
    with t2:
        r_name = st.text_input("FULL NAME", key="r_n").upper()
        r_pin = st.text_input("SET 6-DIGIT PIN", type="password", max_chars=6, key="r_p")
        if st.button("CREATE ACCOUNT"):
            if r_name and len(r_pin) == 6:
                if save_user(r_name, r_pin): st.success("Account Ready!")
                else: st.error("Name taken.")

# --- 4. DASHBOARD ---
else:
    name = st.session_state.user
    reg = load_registry()
    data = reg[name]
    now = datetime.now()

    # Calculate Matured Profits
    matured_total = 0
    active_trades = []
    for i in data['inv']:
        if now >= datetime.fromisoformat(i['end']):
            matured_total += (i['amt'] + i['prof'])
        else:
            active_trades.append(i)
    
    # Update wallet with matured funds and clear them from active list
    if matured_total > 0:
        data['wallet'] += matured_total
        data['inv'] = active_trades
        update_user(name, data)

    st.markdown(f"<h2 style='text-align:center;'>Welcome, {name}</h2>", unsafe_allow_html=True)
    st.metric("AVAILABLE BALANCE", f"₱{data['wallet']:,.2f}")

    # Action Icons
    st.markdown("""
        <div class="action-row">
            <div class="action-item"><div class="icon-circle">📥</div><div class="action-text">Deposit</div></div>
            <div class="action-item"><div class="icon-circle">📤</div><div class="action-text">Withdraw</div></div>
            <div class="action-item"><div class="icon-circle">📊</div><div class="action-text">Market</div></div>
            <div class="action-item"><div class="icon-circle">⋯</div><div class="action-text">More</div></div>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🚀 INVEST", "💳 WALLET", "📋 ACTIVE"])

    with tab1:
        st.write("#### 10% Profit / 24 Hours")
        amt = st.number_input("Enter Amount (PHP)", min_value=100.0, step=100.0)
        if st.button("START INVESTMENT"):
            if data['wallet'] >= amt:
                data['wallet'] -= amt
                end_time = (now + timedelta(hours=24)).isoformat()
                data['inv'].append({"amt": amt, "prof": amt * 0.10, "start": now.isoformat(), "end": end_time})
                update_user(name, data)
                st.success(f"Investment of ₱{amt} started!")
                st.rerun()
            else: st.error("Insufficient Funds.")

    with tab2:
        mode = st.radio("Select Action", ["Deposit", "Withdraw"], horizontal=True)
        if mode == "Deposit":
            st.info("GCash: 0912-345-6789")
            d_amt = st.number_input("Amount Sent", min_value=100.0)
            ref = st.text_input("Ref Number")
            if st.button("SUBMIT PROOF"):
                data['tx'].append({"type": "DEP", "amt": d_amt, "ref": ref, "status": "PENDING"})
                update_user(name, data)
                st.success("Reported to Admin.")
        else:
            w_amt = st.number_input("Withdraw Amount", min_value=100.0)
            if st.button("REQUEST CASHOUT"):
                if data['wallet'] >= w_amt:
                    data['wallet'] -= w_amt
                    data['tx'].append({"type": "WD", "amt": w_amt, "status": "PENDING"})
                    update_user(name, data)
                    st.warning("Request Sent.")
                else: st.error("Inadequate Balance.")

    with tab3:
        if not active_trades:
            st.write("No active investments.")
        for trade in active_trades:
            end = datetime.fromisoformat(trade['end'])
            rem = end - now
            # Format time remaining
            hours, remainder = divmod(rem.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            st.markdown(f"""
                <div class="trade-card">
                    <b>Principal:</b> ₱{trade['amt']:,.2f} <br>
                    <b>Profit (10%):</b> <span style="color:#0dcf70;">+₱{trade['prof']:,.2f}</span> <br>
                    <b>Releasing in:</b> <span class="timer-text">{time_str}</span>
                </div>
            """, unsafe_allow_html=True)

    if st.sidebar.button("LOGOUT"):
        st.session_state.user = None
        st.rerun()
    
    # Auto-refresh timer every 10 seconds
    time.sleep(10)
    st.rerun()
    
