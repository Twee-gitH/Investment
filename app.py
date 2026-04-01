import streamlit as st
import json
import os
import shutil
from datetime import datetime, timedelta
import time
import pandas as pd

# --- 1. DATA ENGINE ---
REGISTRY_FILE = "bpsm_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f: return json.load(f)
    return {}

def update_user(name, data):
    reg = load_registry()
    reg[name] = data
    with open(REGISTRY_FILE, "w") as f: json.dump(reg, f, default=str)

# --- 2. UI & SESSION ---
if 'user' not in st.session_state: st.session_state.user = None
if 'is_boss' not in st.session_state: st.session_state.is_boss = False
st.set_page_config(page_title="BPSM Official", layout="wide")

st.markdown("""
    <style>
    input[type="text"] { text-transform: uppercase !important; }
    input[type="password"] { text-transform: none !important; -webkit-text-transform: none !important; }
    .user-box { background-color: #1c1e24; padding: 15px; border-radius: 10px; border: 1px solid #3a3d46; margin-bottom: 10px; }
    .section-header { background: #252830; padding: 8px; border-radius: 5px; margin-top: 15px; font-weight: bold; border-left: 5px solid #ce1126; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ACCESS CONTROL ---
if st.session_state.user is None and not st.session_state.is_boss:
    st.title("BAGONG PILIPINAS STOCK MARKET")
    t1, t2 = st.tabs(["SIGN-IN", "REGISTER"])
    with t1:
        ln = st.text_input("NAME").upper()
        lp = st.text_input("PIN", type="password")
        if st.button("LOGIN"):
            reg = load_registry()
            if ln in reg and str(reg[ln].get('pin')) == str(lp):
                st.session_state.user = ln
                st.rerun()
    with t2:
        rn = st.text_input("FULL NAME", key="r1").upper()
        rp = st.text_input("CREATE PIN", type="password", key="r2")
        ref = st.text_input("REFERRER", key="r3").upper()
        if st.button("REGISTER ACCOUNT"):
            update_user(rn, {"pin": rp, "wallet": 0.0, "inv": [], "tx": [], "ref_by": ref, "bonus_requests": {}})
            st.success("SUCCESS"); st.rerun()

    with st.expander("🔐 ADMIN"):
        ap = st.text_input("ADMIN PIN", type="password")
        if st.button("ENTER BOSS MODE"):
            if ap == "0102030405": # UPDATED ADMIN CODE
                st.session_state.is_boss = True
                st.rerun()
    st.stop()

# --- 4. INVESTOR DASHBOARD ---
if st.session_state.user:
    name = st.session_state.user
    reg = load_registry()
    data = reg[name]
    now = datetime.now()

    # ROI & AUTO-REINVEST LOGIC
    changed = False
    for i in data.get('inv', []):
        st_t, et_t = datetime.fromisoformat(i['start']), datetime.fromisoformat(i['end'])
        grace_t = et_t + timedelta(hours=1)
        
        # Auto-add ROI to Balance at Maturity
        if now >= et_t and not i.get('roi_paid', False):
            profit = i['amt'] * 0.20
            data['wallet'] += profit
            i['roi_paid'] = True
            data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "WEEKLY ROI", "amt": profit, "status": "SUCCESSFUL"})
            changed = True
        
        # Auto-Reinvest after Grace Period
        if now >= grace_t:
            i.update({"start": now.isoformat(), "end": (now + timedelta(days=7)).isoformat(), "roi_paid": False})
            data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "AUTO-REINVEST", "amt": i['amt'], "status": "LOCKED"})
            changed = True
    if changed: update_user(name, data); st.rerun()

    st.write(f"### Welcome, {name} | Balance: ₱{data['wallet']:,.2f}")
    
    # Cycles Display
    st.markdown("<div class='section-header'>⏳ ACTIVE CYCLES</div>", unsafe_allow_html=True)
    for idx, t in enumerate(data.get('inv', [])):
        st_t, et_t = datetime.fromisoformat(t['start']), datetime.fromisoformat(t['end'])
        st.markdown(f"""
            <div class='user-box'>
                <b>Capital: ₱{t['amt']:,}</b><br>
                Approved: {st_t.strftime('%Y-%m-%d %I:%M %p')}<br>
                Maturity: {et_t.strftime('%Y-%m-%d %I:%M %p')}
            </div>
        """, unsafe_allow_html=True)
        if et_t <= now < (et_t + timedelta(hours=1)):
            if st.button(f"PULL CAPITAL ₱{t['amt']:,}", key=f"p{idx}"):
                data['wallet'] += t['amt']; data['inv'].pop(idx)
                update_user(name, data); st.rerun()

    # Referral Bonus System
    st.markdown("<div class='section-header'>👥 REFERRAL BONUSES</div>", unsafe_allow_html=True)
    all_u = load_registry()
    for u_name, u_info in all_u.items():
        if u_info.get('ref_by') == name:
            first_dep = next((tx['amt'] for tx in u_info.get('tx', []) if tx['status'] == "SUCCESSFUL_DEP"), 0)
            comm = first_dep * 0.20
            status = data.get('bonus_requests', {}).get(u_name, "AVAILABLE")
            
            col1, col2 = st.columns([3, 2])
            col1.write(f"Invitee: {u_name} | Bonus: ₱{comm:,.2f}")
            if comm > 0:
                if status == "AVAILABLE":
                    if col2.button(f"Request Bonus", key=f"req_{u_name}"):
                        data.setdefault('bonus_requests', {})[u_name] = "REQUESTED"
                        update_user(name, data); st.rerun()
                else:
                    col2.write(f"**{status}**")

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

# --- 5. ADMIN PANEL ---
elif st.session_state.is_boss:
    st.title("👑 ADMIN OVERVIEW")
    all_users = load_registry()
    
    for u_name, u_data in all_users.items():
        with st.container():
            st.markdown(f"### Investor: {u_name} (PIN: {u_data.get('pin')})")
            st.write(f"Wallet: ₱{u_data.get('wallet',0):,.2f}")
            
            # Action Buttons for Admin
            c1, c2, c3 = st.columns(3)
            # 1. Approve Deposits
            for idx, tx in enumerate(u_data.get('tx', [])):
                if tx['status'] == "PENDING_DEP":
                    if c1.button(f"Approve Dep ₱{tx['amt']}", key=f"app_{u_name}_{idx}"):
                        st_t = datetime.now()
                        tx['status'] = "SUCCESSFUL_DEP"
                        u_data.setdefault('inv', []).append({"amt": tx['amt'], "start": st_t.isoformat(), "end": (st_t + timedelta(days=7)).isoformat(), "roi_paid": False})
                        update_user(u_name, u_data); st.rerun()

            # 2. Manage Bonus Requests
            for inv_name, b_status in u_data.get('bonus_requests', {}).items():
                if b_status == "REQUESTED":
                    st.write(f"🎁 Bonus Request for referring {inv_name}")
                    if c2.button(f"Pay Bonus to {u_name}", key=f"pay_{u_name}_{inv_name}"):
                        # Logic: Find the invitee's first deposit for the actual amount
                        inv_data = all_users.get(inv_name, {})
                        f_dep = next((t['amt'] for t in inv_data.get('tx', []) if t['status'] == "SUCCESSFUL_DEP"), 0)
                        u_data['wallet'] += (f_dep * 0.20)
                        u_data['bonus_requests'][inv_name] = "RECEIVED"
                        update_user(u_name, u_data); st.rerun()
                    if c3.button(f"Fail/Deny", key=f"fail_{u_name}_{inv_name}"):
                        u_data['bonus_requests'][inv_name] = "FAILED"
                        update_user(u_name, u_data); st.rerun()

            with st.expander("View Full Transactions"):
                st.table(pd.DataFrame(u_data.get('tx', [])))
            st.divider()

    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
    
