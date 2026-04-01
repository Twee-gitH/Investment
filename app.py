import streamlit as st
import json
import os
from datetime import datetime, timedelta
import time
import pandas as pd

# --- 1. DATA ENGINE ---
REGISTRY_FILE = "bpsm_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def update_user(name, data):
    reg = load_registry()
    reg[name] = data
    with open(REGISTRY_FILE, "w") as f: json.dump(reg, f, default=str)

# --- 2. SESSION & UI ---
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
            update_user(rn, {"pin": rp, "wallet": 0.0, "inv": [], "tx": [], "ref_by": ref, "bonus_status": {}})
            st.success("SUCCESS"); st.rerun()

    with st.expander("🔐 ADMIN"):
        # REQUIREMENT 3: ADMIN CODE UPDATED
        ap = st.text_input("ADMIN PIN", type="password")
        if st.button("ENTER BOSS MODE"):
            if ap == "0102030405": 
                st.session_state.is_boss = True
                st.rerun()
    st.stop()

# --- 4. INVESTOR DASHBOARD ---
if st.session_state.user:
    name = st.session_state.user
    data = load_registry().get(name)
    now = datetime.now()

    # REQUIREMENT 1: AUTO ROI & REINVEST
    changed = False
    for i in data.get('inv', []):
        st_t, et_t = datetime.fromisoformat(i['start']), datetime.fromisoformat(i['end'])
        grace_t = et_t + timedelta(hours=1)
        
        if now >= et_t and not i.get('roi_paid', False):
            profit = i['amt'] * 0.20
            data['wallet'] += profit
            i['roi_paid'] = True
            data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "WEEKLY ROI", "amt": profit, "status": "SUCCESSFUL"})
            changed = True
        
        if now >= grace_t:
            i.update({"start": now.isoformat(), "end": (now + timedelta(days=7)).isoformat(), "roi_paid": False})
            data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "AUTO-REINVEST", "amt": i['amt'], "status": "SUCCESSFUL"})
            changed = True
    if changed: update_user(name, data); st.rerun()

    st.write(f"### Investor: {name} | Balance: ₱{data['wallet']:,.2f}")
    
    st.markdown("<div class='section-header'>⏳ ACTIVE CYCLES</div>", unsafe_allow_html=True)
    for idx, t in enumerate(data.get('inv', [])):
        st_t, et_t = datetime.fromisoformat(t['start']), datetime.fromisoformat(t['end'])
        # REQUIREMENT 1: EXACT DATE & TIME OF APPROVAL AND MATURITY
        st.markdown(f"""
            <div class='user-box'>
                <b>Capital: ₱{t['amt']:,}</b><br>
                Approved Date/Time: {st_t.strftime('%Y-%m-%d %I:%M:%S %p')}<br>
                Maturity Date/Time: {et_t.strftime('%Y-%m-%d %I:%M:%S %p')}
            </div>
        """, unsafe_allow_html=True)
        if et_t <= now < (et_t + timedelta(hours=1)):
            if st.button(f"PULL CAPITAL ₱{t['amt']:,}", key=f"p{idx}"):
                data['wallet'] += t['amt']; data['inv'].pop(idx)
                update_user(name, data); st.rerun()

    # REQUIREMENT 2: COMMISSION REQUEST BUTTONS
    st.markdown("<div class='section-header'>👥 REFERRAL COMMISSIONS</div>", unsafe_allow_html=True)
    all_u = load_registry()
    for u_n, u_i in all_u.items():
        if u_i.get('ref_by') == name:
            f_dep = next((tx['amt'] for tx in u_i.get('tx', []) if tx['status'] == "SUCCESSFUL_DEP"), 0)
            comm = f_dep * 0.20
            b_status = data.get('bonus_status', {}).get(u_n, "AVAILABLE")
            
            c1, c2 = st.columns([3, 2])
            c1.write(f"Invitee: {u_n} | Bonus: ₱{comm:,.2f}")
            if comm > 0:
                if b_status == "AVAILABLE":
                    if c2.button(f"Request Bonus", key=f"req_{u_n}"):
                        data.setdefault('bonus_status', {})[u_n] = "REQUESTED"
                        update_user(name, data); st.rerun()
                else:
                    c2.write(f"Status: **{b_status}**")

    st.markdown("<div class='section-header'>📜 TRANSACTION HISTORY</div>", unsafe_allow_html=True)
    st.table(pd.DataFrame(data.get('tx', [])))

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

# --- 5. REQUIREMENT 4: FULL ADMIN PANEL ---
elif st.session_state.is_boss:
    st.title("👑 ADMIN OVERVIEW")
    all_users = load_registry()
    
    for u_name, u_data in all_users.items():
        with st.expander(f"Investor: {u_name} | PIN: {u_data.get('pin')} | Wallet: ₱{u_data.get('wallet'):,.2f}"):
            # All Transactions for this user
            st.write("### Transactions & Requests")
            for idx, tx in enumerate(u_data.get('tx', [])):
                colA, colB = st.columns([3, 1])
                colA.write(f"{tx['date']} | {tx['type']} | ₱{tx['amt']:,} | {tx['status']}")
                if tx['status'] == "PENDING_DEP":
                    if colB.button("APPROVE", key=f"app_{u_name}_{idx}"):
                        st_t = datetime.now()
                        tx['status'] = "SUCCESSFUL_DEP"
                        u_data.setdefault('inv', []).append({"amt": tx['amt'], "start": st_t.isoformat(), "end": (st_t + timedelta(days=7)).isoformat(), "roi_paid": False})
                        update_user(u_name, u_data); st.rerun()

            # Manage Bonus Requests
            st.divider()
            st.write("### Bonus Claim Requests")
            for inv_name, status in u_data.get('bonus_status', {}).items():
                if status == "REQUESTED":
                    st.write(f"Request from {u_name} for referring {inv_name}")
                    ca, cb = st.columns(2)
                    if ca.button(f"CONFIRM RECEIVE", key=f"conf_{u_name}_{inv_name}"):
                        # Find amount to pay
                        i_data = all_users.get(inv_name, {})
                        f_amt = next((t['amt'] for t in i_data.get('tx', []) if t['status'] == "SUCCESSFUL_DEP"), 0)
                        u_data['wallet'] += (f_amt * 0.20)
                        u_data['bonus_status'][inv_name] = "RECEIVED"
                        update_user(u_name, u_data); st.rerun()
                    if cb.button(f"SET TO FAILED", key=f"fail_{u_name}_{inv_name}"):
                        u_data['bonus_status'][inv_name] = "FAILED"
                        update_user(u_name, u_data); st.rerun()
                        
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
        
