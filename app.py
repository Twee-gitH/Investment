import streamlit as st
import json
import os
import shutil
from datetime import datetime, timedelta
import time
import pandas as pd

# --- 1. SESSION INITIALIZER ---
if 'user' not in st.session_state: st.session_state.user = None
if 'page' not in st.session_state: st.session_state.page = "main"
if 'is_boss' not in st.session_state: st.session_state.is_boss = False
if 'confirm_amt' not in st.session_state: st.session_state.confirm_amt = False

if not os.path.exists("receipts"):
    os.makedirs("receipts")

# --- 2. DATA ENGINE ---
REGISTRY_FILE = "bpsm_registry.json"
BACKUP_FILE = "bpsm_backup.json"

def load_registry():
    for file in [REGISTRY_FILE, BACKUP_FILE]:
        if os.path.exists(file):
            try:
                with open(file, "r") as f:
                    return json.load(f)
            except: continue
    return {}

def update_user(name, data):
    reg = load_registry()
    reg[name] = data
    with open(REGISTRY_FILE, "w") as f:
        json.dump(reg, f, default=str)
    shutil.copy(REGISTRY_FILE, BACKUP_FILE)

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
    .ticker-wrap { background: #000; color: #0dcf70; padding: 12px 0; position: fixed; bottom: 0; width: 100%; font-size: 0.85rem; border-top: 1px solid #2a2b30; z-index: 999; overflow: hidden; }
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .ticker-text { display: inline-block; white-space: nowrap; animation: ticker 25s linear infinite; font-weight: bold; }
    .stButton>button { border-radius: 12px !important; height: 3.5rem !important; font-weight: bold !important; width: 100%; }
    .roi-text { color: #0dcf70; font-weight: bold; font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ACCESS CONTROL ---
if st.session_state.user is None and not st.session_state.is_boss:
    st.markdown("<div style='background: linear-gradient(135deg, #0038a8 0%, #ce1126 100%); padding: 40px 20px; text-align: center;'><h1>BAGONG PILIPINAS<br>STOCK MARKET</h1><p>Automatic Weekly Payouts | 20% Weekly ROI</p></div>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 SIGN-IN", "📝 REGISTER"])
    
    with t1:
        ln = st.text_input("INVESTOR NAME", key="login_name").upper()
        lp = st.text_input("SECURE PIN", type="password", max_chars=6, key="login_pin")
        if st.button("VERIFY & ACCESS"):
            reg = load_registry()
            if ln in reg and reg[ln].get('pin') == lp:
                st.session_state.user = ln
                st.rerun()
            else:
                st.error("Invalid Credentials")
    
    with t2:
        rn = st.text_input("FULL LEGAL NAME", key="reg_name").upper()
        rp = st.text_input("CREATE 6-DIGIT PIN", type="password", max_chars=6, key="reg_pin")
        referrer = st.text_input("REFERRER NAME (REQUIRED)", key="reg_ref").upper()
        if st.button("CREATE ACCOUNT"):
            reg = load_registry()
            if not referrer: st.error("Referrer required.")
            elif referrer not in reg: st.error("Referrer not found.")
            elif rn in reg: st.error("Already registered.")
            elif rn and len(rp) == 6:
                new_data = {"pin": rp, "wallet": 0.0, "inv": [], "tx": [], "ref_by": referrer, "bonus_claimed": False}
                update_user(rn, new_data)
                st.success("Account Created!")
                time.sleep(1.5); st.rerun()
    
    st.divider()
    with st.expander("MASTER ACCESS"):
        key = st.text_input("Admin Key", type="password", key="admin_key")
        if st.button("ENTER CONTROL PANEL"):
            if key == "Orange01!":
                st.session_state.is_boss = True
                st.rerun()
    st.stop()

# --- 5. INVESTOR PORTAL ---
if st.session_state.user:
    name = st.session_state.user
    reg = load_registry()
    data = reg[name]
    now = datetime.now()

    # ROI Processor
    payout_triggered = False
    for i in data.get('inv', []):
        try:
            end_time = datetime.fromisoformat(i['end'])
            if now >= end_time: 
                profit_amt = i['amt'] * 0.20
                data['wallet'] += profit_amt
                i['start'] = now.isoformat()
                i['end'] = (now + timedelta(days=7)).isoformat()
                data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "WEEKLY ROI CREDIT", "amt": profit_amt, "status": "SUCCESSFUL"})
                payout_triggered = True
        except: continue
    if payout_triggered: update_user(name, data); st.rerun()

    st.markdown(f"<div class='user-box'><p style='color:#8c8f99;'>BALANCE</p><h1 class='balance-val'>₱{data['wallet']:,.2f}</h1><p style='color:#8c8f99;'>Account: {name}</p></div>", unsafe_allow_html=True)

    if st.session_state.page == "dep":
        st.markdown("<div class='section-header'>📥 DEPOSIT</div>", unsafe_allow_html=True)
        d_amt = st.number_input("Amount", min_value=1000.0)
        receipt = st.file_uploader("Receipt", type=['jpg','png'])
        if st.button("SUBMIT"):
            if receipt:
                f_path = f"receipts/{name}_{int(time.time())}.png"
                with open(f_path, "wb") as f: f.write(receipt.getbuffer())
                data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "DEPOSIT", "amt": d_amt, "status": "PENDING_DEP", "receipt_path": f_path})
                update_user(name, data); st.session_state.page = "main"; st.rerun()
        if st.button("⬅️ BACK"): st.session_state.page = "main"; st.rerun()

    elif st.session_state.page == "wd":
        st.markdown("<div class='section-header'>📤 WITHDRAW</div>", unsafe_allow_html=True)
        w_amt = st.number_input("Amount", min_value=1000.0, max_value=max(1000.0, data['wallet']))
        if st.button("SUBMIT"):
            data['wallet'] -= w_amt
            data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "WITHDRAWAL", "amt": w_amt, "status": "PENDING_WD"})
            update_user(name, data); st.session_state.page = "main"; st.rerun()
        if st.button("⬅️ BACK"): st.session_state.page = "main"; st.rerun()

    else:
        c1, c2 = st.columns(2)
        with c1: 
            if st.button("📥 DEPOSIT"): st.session_state.page = "dep"; st.rerun()
        with c2: 
            if st.button("📤 WITHDRAW"): st.session_state.page = "wd"; st.rerun()

        # Referral Section
        st.markdown("<div class='section-header'>👥 MY REFERRALS</div>", unsafe_allow_html=True)
        for u_name, u_info in reg.items():
            if u_info.get('ref_by') == name:
                first_dep = 0.0
                for tx in u_info.get('tx', []):
                    if tx['type'] == "DEPOSIT" and tx['status'] == "SUCCESSFUL_DEP":
                        first_dep = tx['amt']
                        break
                
                bonus_amt = first_dep * 0.20
                if first_dep > 0:
                    status = u_info.get('bonus_claimed', "NOT_CLAIMED")
                    if status == "APPROVED": st.write(f"✅ {u_name} | Bonus ₱{bonus_amt:,.2f} Claimed")
                    elif status == "PENDING": st.write(f"⏳ {u_name} | Bonus PENDING Approval")
                    else:
                        if st.button(f"CLAIM 20% BONUS FROM {u_name} (₱{bonus_amt:,.2f})"):
                            u_info['bonus_claimed'] = "PENDING"
                            update_user(u_name, u_info); st.rerun()
                else: st.write(f"👤 {u_name} | No Deposit Yet")

        st.markdown("<div class='section-header'>⏳ ACTIVE CYCLES</div>", unsafe_allow_html=True)
        for idx, t in enumerate(reversed(data.get('inv', []))):
            rem = datetime.fromisoformat(t['end']) - now
            st.write(f"Capital: ₱{t['amt']:,} | Time Left: {str(rem).split('.')[0]}")

    if st.sidebar.button("LOGOUT"): st.session_state.user = None; st.rerun()

# --- 6. BOSS PANEL ---
elif st.session_state.is_boss:
    all_users = load_registry()
    st.markdown("### 👑 MASTER CONTROL")

    # --- PENDING REFERRAL BONUSES ---
    st.markdown("<div class='section-header'>🎁 PENDING REFERRAL BONUSES</div>", unsafe_allow_html=True)
    for u_name, u_info in all_users.items():
        if u_info.get('bonus_claimed') == "PENDING":
            ref = u_info.get('ref_by')
            f_dep = next((t['amt'] for t in u_info.get('tx', []) if t['type']=="DEPOSIT" and t['status']=="SUCCESSFUL_DEP"), 0)
            b_amt = f_dep * 0.20
            if st.button(f"APPROVE ₱{b_amt:,.2f} for {ref} (Invited {u_name})"):
                all_users[ref]['wallet'] += b_amt
                all_users[u_name]['bonus_claimed'] = "APPROVED"
                update_user(u_name, all_users[u_name])
                update_user(ref, all_users[ref]); st.rerun()

    # --- RESTORED: INVESTOR DATABASE ---
    st.markdown("<div class='section-header'>📋 INVESTOR DATABASE (NAMES, PINS, REFERRALS)</div>", unsafe_allow_html=True)
    db_list = [{"NAME": u, "PIN": i.get('pin'), "WALLET": f"₱{i.get('wallet',0):,.2f}", "REFERRER": i.get('ref_by','DIRECT')} for u,i in all_users.items()]
    st.table(pd.DataFrame(db_list))

    # --- RESTORED: TRANSACTION HISTORY ---
    with st.expander("🔍 VIEW ALL INDIVIDUAL TRANSACTIONS"):
        for u_name, u_info in all_users.items():
            st.write(f"**{u_name}**"); st.json(u_info.get('tx', [])); st.divider()

    # --- RESTORED: REAL-TIME ROI TRACKER ---
    st.markdown("<div class='section-header'>📈 REAL-TIME INVESTOR ROI</div>", unsafe_allow_html=True)
    for u_name, u_info in all_users.items():
        for inv in u_info.get('inv', []):
            rem = datetime.fromisoformat(inv['end']) - datetime.now()
            st.write(f"👤 {u_name} | Capital: ₱{inv['amt']:,} | ⏳ {str(rem).split('.')[0]}")

    # --- PENDING DEPOSITS/WITHDRAWALS ---
    st.markdown("<div class='section-header'>🔔 PENDING ACTIONS</div>", unsafe_allow_html=True)
    for u_name, u_info in all_users.items():
        for idx, tx in enumerate(u_info.get('tx', [])):
            if tx['status'] == "PENDING_DEP":
                if st.button(f"Approve ₱{tx['amt']:,} Deposit: {u_name}"):
                    all_users[u_name]['tx'][idx]['status'] = "SUCCESSFUL_DEP"
                    st_t = datetime.now()
                    all_users[u_name].setdefault('inv', []).append({"amt": tx['amt'], "start": st_t.isoformat(), "end": (st_t + timedelta(days=7)).isoformat()})
                    update_user(u_name, all_users[u_name]); st.rerun()
            elif tx['status'] == "PENDING_WD":
                if st.button(f"Approve ₱{tx['amt']:,} Withdrawal: {u_name}"):
                    all_users[u_name]['tx'][idx]['status'] = "SUCCESSFUL_WD"
                    update_user(u_name, all_users[u_name]); st.rerun()
    
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
        
