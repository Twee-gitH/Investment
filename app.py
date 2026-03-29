import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import time

# --- CONSTANTS ---
DB_FILE = "market_pro_data.json"
DAILY_ROI = 0.20  # 20%
MIN_WITHDRAW = 500.0

# --- DATA ENGINE ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return None

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, default=str)

# --- UI CONFIG ---
st.set_page_config(page_title="BP Market Pro", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .status-pending { color: #f59e0b; font-weight: bold; }
    .status-completed { color: #10b981; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- AUTH LOGIC ---
if 'user' not in st.session_state:
    st.session_state.user = load_db()

if st.session_state.user is None:
    st.title("🇵🇭 BP Market: Professional")
    tab1, tab2 = st.tabs(["Register", "Admin Login"])
    
    with tab1:
        name = st.text_input("FULL NAME (As per Govt ID)").upper()
        pin = st.text_input("SECURE 6-DIGIT PIN", type="password", max_chars=6)
        if st.button("CREATE INVESTOR ACCOUNT", use_container_width=True):
            if name and len(pin) == 6:
                user_data = {
                    "name": name, "pin": pin,
                    "wallet_balance": 0.0,
                    "investments": [],
                    "transactions": [] # Ledger for deposits/withdrawals
                }
                save_db(user_data)
                st.session_state.user = user_data
                st.rerun()
    stop = True
else:
    stop = False

if not stop:
    user = st.session_state.user
    
    # --- CALCULATE LIVE GROWTH ---
    active_inv_total = 0.0
    matured_total = 0.0
    
    for inv in user['investments']:
        start = datetime.fromisoformat(inv['start_time'])
        end = datetime.fromisoformat(inv['release_time'])
        now = datetime.now()
        
        if now >= end:
            matured_total += (inv['amount'] + inv['profit'])
        else:
            active_inv_total += inv['amount']

    total_liquid = user['wallet_balance'] + matured_total

    # --- SIDEBAR NAV ---
    with st.sidebar:
        st.title("🛡️ SECURE ACCESS")
        st.write(f"User: **{user['name']}**")
        show_bal = st.toggle("Show Balance", value=True)
        if st.button("LOGOUT / RESET"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.session_state.user = None
            st.rerun()

    # --- TOP METRICS ---
    st.header("Financial Overview")
    m1, m2, m3 = st.columns(3)
    display_bal = f"₱{total_liquid:,.2f}" if show_bal else "₱ ••••••"
    m1.metric("TOTAL LIQUID BALANCE", display_bal)
    m2.metric("ACTIVE INVESTMENTS", f"₱{active_inv_total:,.2f}")
    m3.metric("PLATFORM ROI", f"{DAILY_ROI*100}%", "24 Hours")

    st.divider()

    # --- CORE TABS ---
    tab_inv, tab_wallet, tab_history = st.tabs(["🚀 Invest", "💳 Wallet & Cashout", "📜 Ledger"])

    with tab_inv:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("New Position")
            inv_amt = st.number_input("Amount (PHP)", min_value=100.0, step=100.0)
            if st.button("START INVESTMENT", use_container_width=True):
                if total_liquid >= inv_amt:
                    # Deduct from balance/matured funds logic
                    new_inv = {
                        "amount": inv_amt,
                        "profit": inv_amt * DAILY_ROI,
                        "start_time": datetime.now().isoformat(),
                        "release_time": (datetime.now() + timedelta(hours=24)).isoformat()
                    }
                    user['investments'].append(new_inv)
                    # Simple deduction logic (Prioritize wallet, then matured)
                    if user['wallet_balance'] >= inv_amt:
                        user['wallet_balance'] -= inv_amt
                    else:
                        # Logic to clear matured investments once used
                        st.warning("Invested from matured funds.")
                    
                    save_db(user)
                    st.success("Investment successfully deployed!")
                    st.rerun()
                else:
                    st.error("Insufficient Liquid Funds. Please Deposit first.")

        with col2:
            st.subheader("Active Contracts")
            for i, inv in enumerate(user['investments']):
                end = datetime.fromisoformat(inv['release_time'])
                if datetime.now() < end:
                    time_left = end - datetime.now()
                    st.info(f"💰 **₱{inv['amount']:,}** → Maturity in {str(time_left).split('.')[0]}")

    with tab_wallet:
        w_col1, w_col2 = st.columns(2)
        with w_col1:
            st.subheader("Add Funds (Deposit)")
            st.caption("Send via GCash: 0912-XXX-XXXX")
            ref_no = st.text_input("Reference Number (Last 6 Digits)")
            d_amt = st.number_input("Amount Deposited", min_value=100.0)
            if st.button("NOTIFY ADMIN OF DEPOSIT"):
                user['transactions'].append({
                    "date": datetime.now().isoformat(),
                    "type": "DEPOSIT",
                    "amount": d_amt,
                    "ref": ref_no,
                    "status": "PENDING"
                })
                save_db(user)
                st.toast("Deposit notification sent!")

        with w_col2:
            st.subheader("Cashout")
            c_amt = st.number_input("Withdraw Amount", min_value=MIN_WITHDRAW)
            c_pin = st.text_input("Enter Transaction PIN", type="password")
            if st.button("REQUEST CASHOUT"):
                if c_amt <= total_liquid and c_pin == user['pin']:
                    user['transactions'].append({
                        "date": datetime.now().isoformat(),
                        "type": "WITHDRAWAL",
                        "amount": c_amt,
                        "status": "PENDING"
                    })
                    # Immediately lock funds
                    user['wallet_balance'] -= c_amt 
                    save_db(user)
                    st.warning("Funds locked. Pending Admin Transfer.")
                else:
                    st.error("Check Balance or PIN.")

    with tab_history:
        st.subheader("Transaction Ledger")
        if user['transactions']:
            df = pd.DataFrame(user['transactions'])
            st.dataframe(df, use_container_width=True)
        else:
            st.write("No transactions found.")

    # --- AUTO REFRESH ---
    time.sleep(2)
    st.rerun()
            
