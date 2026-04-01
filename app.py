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
    input[type="text"] { text-transform: uppercase !important; }
    input[type="password"] { text-transform: none !important; -webkit-text-transform: none !important; }
    .user-box { background-color: #1c1e24; padding: 20px; border-radius: 15px; border: 1px solid #3a3d46; text-align: center; margin-bottom: 20px; }
    .balance-val { color: #00ff88; font-size: 36px; margin: 0; }
    .section-header { background: #252830; padding: 10px; border-radius: 5px; margin-top: 20px; margin-bottom: 10px; font-weight: bold; border-left: 5px solid #ce1126; }
    .meta-text { color: #8c8f99; font-size: 13px; }
    .timer-text { color: #ffcc00; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ACCESS CONTROL ---
if st.session_state.user is None and not st.session_state.is_boss:
    st.markdown("<div style='background: linear-gradient(135deg, #0038a8 0%, #ce1126 100%); padding: 40px 20px; text-align: center;'><h1>BAGONG PILIPINAS<br>STOCK MARKET</h1></div>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["🔑 SIGN-IN", "📝 REGISTER"])
    with t1:
        ln = st.text_input("INVESTOR NAME", key="login_name").upper()
        lp = st.text_input("SECURE PIN", type="password", key="login_pin")
        if st.button("VERIFY & ACCESS"):
            reg = load_registry()
            if ln in reg and reg[ln].get('pin') == lp:
                st.session_state.user = ln
                st.rerun()
            else: st.error("❌ INVALID CREDENTIALS")
            
    with t2:
        rn = st.text_input("FULL LEGAL NAME", key="reg_name").upper()
        rp1 = st.text_input("CREATE PIN", type="password", key="reg_pin1")
        rp2 = st.text_input("CONFIRM PIN", type="password", key="reg_pin2")
        referrer = st.text_input("REFERRER NAME", key="reg_ref").upper()
        if st.button("CREATE ACCOUNT"):
            reg = load_registry()
            if len(rn.split()) < 2: st.error("❌ INPUT FULL NAME.")
            elif rp1 != rp2: st.error("❌ PINS DO NOT MATCH.")
            elif not referrer or referrer not in reg: st.error("❌ VALID REFERRER REQUIRED.")
            else:
                update_user(rn.upper(), {"pin": rp1, "wallet": 0.0, "inv": [], "tx": [], "ref_by": referrer, "claimed_refs": []})
                st.success("✅ REGISTERED!"); time.sleep(1); st.rerun()

    with st.expander("🔐 ADMIN"):
        ap = st.text_input("ADMIN PIN", type="password")
        if st.button("LOG IN AS BOSS"):
            if ap == "Admin123":
                st.session_state.is_boss = True
                st.rerun()
    st.stop()

# --- 5. INVESTOR DASHBOARD ---
if st.session_state.user:
    name = st.session_state.user
    reg = load_registry()
    data = reg[name]
    now = datetime.now()

    # --- 20% WEEKLY ROI PROCESSOR ---
    changed = False
    for i in data.get('inv', []):
        try:
            m_time = datetime.fromisoformat(i['end'])
            if now >= m_time and not i.get('roi_paid', False):
                profit = i['amt'] * 0.20
                data['wallet'] += profit
                i['roi_paid'] = True
                data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "WEEKLY ROI", "amt": profit, "status": "SUCCESSFUL"})
                changed = True
        except: continue
    if changed: update_user(name, data); st.rerun()

    st.markdown(f"<div class='user-box'><p style='color:#8c8f99;'>BALANCE</p><h1 class='balance-val'>₱{data['wallet']:,.2f}</h1><p>Account: {name}</p></div>", unsafe_allow_html=True)

    if st.session_state.page == "main":
        c1, c2, c3 = st.columns(3)
        if c1.button("📥 DEPOSIT"): st.session_state.page = "dep"; st.rerun()
        if c2.button("📤 WITHDRAW"): st.session_state.page = "wd"; st.rerun()
        if c3.button("♻️ RE-INVEST"): st.session_state.page = "rei"; st.rerun()

        # --- TICKING TIMER & PULL OUT SECTION ---
        st.markdown("<div class='section-header'>⏳ ACTIVE CYCLES (7 DAYS)</div>", unsafe_allow_html=True)
        inv_list = data.get('inv', [])
        if not inv_list:
            st.info("No active investment cycles.")
        
        for idx, t in enumerate(reversed(inv_list)):
            actual_idx = len(inv_list) - 1 - idx
            start_t = datetime.fromisoformat(t['start'])
            end_t = datetime.fromisoformat(t['end'])
            
            st.markdown(f"""
                <div class='user-box' style='text-align:left; padding:15px;'>
                    <p class='meta-text'>📅 Deposited: {start_t.strftime('%Y-%m-%d %I:%M %p')}</p>
                    <p class='meta-text'>🏁 Maturity: {end_t.strftime('%Y-%m-%d %I:%M %p')}</p>
                    <b style='font-size:18px;'>Capital: ₱{t['amt']:,}</b>
                </div>
            """, unsafe_allow_html=True)
            
            if now < end_t:
                # The Countdown Timer
                time_left = end_t - now
                st.button(f"LOCKED (⏳ {str(time_left).split('.')[0]})", key=f"lock_{actual_idx}", disabled=True)
            else:
                # The Pull Out Button (Only appears after timeframe)
                if st.button(f"✅ PULL CAPITAL (₱{t['amt']:,})", key=f"pull_{actual_idx}"):
                    data['wallet'] += t['amt']
                    data['inv'].pop(actual_idx)
                    update_user(name, data)
                    st.rerun()

        # --- REFERRALS ---
        st.markdown("<div class='section-header'>👥 MY REFERRALS</div>", unsafe_allow_html=True)
        reg_all = load_registry()
        my_refs = []
        total_bonus = 0
        for u_name, u_info in reg_all.items():
            if u_info.get('ref_by') == name:
                first_dep = next((tx['amt'] for tx in u_info.get('tx', []) if tx['status'] == "SUCCESSFUL_DEP"), 0)
                claimed = u_name in data.get('claimed_refs', [])
                bonus = (first_dep * 0.20) if (first_dep > 0 and not claimed) else 0
                total_bonus += bonus
                my_refs.append({"INVITEE": u_name, "STATUS": "✅ PAID" if claimed else (f"₱{first_dep:,}" if first_dep > 0 else "INACTIVE")})
        
        if my_refs:
            st.table(pd.DataFrame(my_refs))
            if total_bonus > 0:
                if st.button(f"🎁 CLAIM ₱{total_bonus:,.2f} BONUS"):
                    data.setdefault('claimed_refs', []).extend([r['INVITEE'] for r in my_refs if "₱" in r['STATUS']])
                    data['wallet'] += total_bonus
                    update_user(name, data); st.rerun()

        # --- HISTORY ---
        st.markdown("<div class='section-header'>📜 HISTORY</div>", unsafe_allow_html=True)
        for t in reversed(data.get('tx', [])):
            st.write(f"{t['date']} | {t['type']} | ₱{t['amt']:,} | {t['status']}")

    elif st.session_state.page == "dep":
        d_amt = st.number_input("Deposit Amount", 1000.0)
        if st.button("SUBMIT"):
            data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "DEPOSIT", "amt": d_amt, "status": "PENDING_DEP"})
            update_user(name, data); st.session_state.page = "main"; st.rerun()
        if st.button("⬅️ BACK"): st.session_state.page = "main"; st.rerun()

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

# --- 6. BOSS PANEL ---
elif st.session_state.is_boss:
    st.title("👑 BOSS CONTROL")
    all_users = load_registry()
    for u_name, u_info in all_users.items():
        for idx, tx in enumerate(u_info.get('tx', [])):
            if tx['status'] == "PENDING_DEP":
                if st.button(f"Approve ₱{tx['amt']} Dep for {u_name}"):
                    u_info['tx'][idx]['status'] = "SUCCESSFUL_DEP"
                    # Important: Set start and end time here so the timer works!
                    st_time = datetime.now()
                    u_info.setdefault('inv', []).append({
                        "amt": tx['amt'], 
                        "start": st_time.isoformat(),
                        "end": (st_time + timedelta(days=7)).isoformat(), 
                        "roi_paid": False
                    })
                    update_user(u_name, u_info); st.rerun()
    if st.button("EXIT BOSS MODE"): st.session_state.is_boss = False; st.rerun()
    
