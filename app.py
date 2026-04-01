import streamlit as st
import json
import os
import shutil
from datetime import datetime, timedelta
import time
import pandas as pd

# --- 1. INITIAL SETUP ---
if 'user' not in st.session_state: st.session_state.user = None
if 'page' not in st.session_state: st.session_state.page = "main"
if 'is_boss' not in st.session_state: st.session_state.is_boss = False

REGISTRY_FILE = "bpsm_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f: return json.load(f)
    return {}

def update_user(name, data):
    reg = load_registry()
    reg[name] = data
    with open(REGISTRY_FILE, "w") as f: json.dump(reg, f, default=str)

# --- 2. THE CSS FIX (Forces small letters in PIN fields) ---
st.set_page_config(page_title="BPSM Official", layout="wide")
st.markdown("""
    <style>
    input[type="text"] { text-transform: uppercase !important; }
    input[type="password"] { text-transform: none !important; -webkit-text-transform: none !important; }
    .user-box { background-color: #1c1e24; padding: 20px; border-radius: 15px; border: 1px solid #3a3d46; margin-bottom: 20px; }
    .balance-val { color: #00ff88; font-size: 36px; margin: 0; text-align: center; }
    .section-header { background: #252830; padding: 10px; border-radius: 5px; margin-top: 20px; margin-bottom: 10px; font-weight: bold; border-left: 5px solid #ce1126; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ACCESS CONTROL ---
if st.session_state.user is None and not st.session_state.is_boss:
    st.markdown("<h1 style='text-align:center;'>BAGONG PILIPINAS<br>STOCK MARKET</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 SIGN-IN", "📝 REGISTER"])
    
    with t1:
        ln = st.text_input("INVESTOR NAME").upper()
        lp = st.text_input("SECURE PIN", type="password")
        if st.button("VERIFY & ACCESS"):
            reg = load_registry()
            if ln in reg and str(reg[ln].get('pin')) == str(lp):
                st.session_state.user = ln
                st.rerun()
            else: st.error("❌ INVALID CREDENTIALS")

    with t2:
        rn = st.text_input("FULL NAME", key="r1").upper()
        rp = st.text_input("PIN", type="password", key="r2")
        ref = st.text_input("REFERRER", key="r3").upper()
        if st.button("CREATE"):
            update_user(rn, {"pin": rp, "wallet": 0.0, "inv": [], "tx": [], "ref_by": ref, "claimed_refs": []})
            st.success("DONE!"); time.sleep(1); st.rerun()

    with st.expander("🔐 ADMIN"):
        ap = st.text_input("ADMIN PIN", type="password", key="admin_key")
        if st.button("LOG IN AS BOSS"):
            if ap.lower() == "admin123": # Case-insensitive to stop lockouts
                st.session_state.is_boss = True
                st.rerun()
    st.stop()

# --- 4. INVESTOR DASHBOARD ---
if st.session_state.user:
    name = st.session_state.user
    reg = load_registry()
    data = reg[name]
    now = datetime.now()

    # --- LIVE ROI & AUTO-REINVEST ENGINE ---
    changed = False
    MINUTE_RATE = (0.20 / 7) / 1440 
    for i in data.get('inv', []):
        st_t, et_t = datetime.fromisoformat(i['start']), datetime.fromisoformat(i['end'])
        grace_t = et_t + timedelta(hours=1)
        
        # Calculate Live ROI
        mins = (min(now, et_t) - st_t).total_seconds() / 60
        i['live_roi'] = i['amt'] * (mins * MINUTE_RATE)

        # Maturity Payout
        if now >= et_t and not i.get('roi_paid', False):
            data['wallet'] += i['amt'] * 0.20
            i['roi_paid'] = True
            changed = True
        
        # Auto-Reinvest
        if now >= grace_t:
            i.update({"start": now.isoformat(), "end": (now+timedelta(days=7)).isoformat(), "roi_paid": False})
            changed = True
    if changed: update_user(name, data); st.rerun()

    st.markdown(f"<div class='user-box'><p style='text-align:center;'>BALANCE</p><h1 class='balance-val'>₱{data['wallet']:,.2f}</h1></div>", unsafe_allow_html=True)

    if st.session_state.page == "main":
        st.markdown("<div class='section-header'>⏳ ACTIVE CYCLES</div>", unsafe_allow_html=True)
        for idx, t in enumerate(data.get('inv', [])):
            et_t = datetime.fromisoformat(t['end'])
            gr_t = et_t + timedelta(hours=1)
            
            st.markdown(f"""
                <div class='user-box' style='border-left:5px solid #00ff88; padding:15px;'>
                    <b>CAPITAL: ₱{t['amt']:,}</b><br>
                    <span style='color:#00ff88;'>📈 LIVE ROI: ₱{t.get('live_roi',0):,.4f}</span><br>
                    <span style='font-size:12px; color:#8c8f99;'>TOTAL EXPECTED: ₱{t['amt']*0.2:.2f}</span>
                </div>
            """, unsafe_allow_html=True)

            btn_txt = f"PULL OUT WINDOW: {et_t.strftime('%I:%M%p')} - {gr_t.strftime('%I:%M%p')}"
            if et_t <= now < gr_t:
                if st.button(f"✅ PULL CAPITAL (₱{t['amt']:,})", key=f"p{idx}"):
                    data['wallet'] += t['amt']; data['inv'].pop(idx)
                    update_user(name, data); st.rerun()
            else:
                st.button(btn_txt, disabled=True, key=f"d{idx}")

        # --- REFERRALS & HISTORY ---
        st.markdown("<div class='section-header'>👥 REFERRALS</div>", unsafe_allow_html=True)
        all_reg = load_registry()
        refs = [{"INVITEE": k, "1st DEP": f"₱{v['tx'][0]['amt']:,}" if v.get('tx') else "0"} for k,v in all_reg.items() if v.get('ref_by') == name]
        if refs: st.table(pd.DataFrame(refs))

        st.markdown("<div class='section-header'>📜 HISTORY</div>", unsafe_allow_html=True)
        for tx in reversed(data.get('tx', [])):
            st.write(f"{tx['date']} | {tx['type']} | ₱{tx['amt']:,} | {tx['status']}")

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

# --- 5. BOSS PANEL (THE CRITICAL FIX) ---
elif st.session_state.is_boss:
    st.title("👑 BOSS PANEL")
    all_users = load_registry()
    for u_name, u_info in all_users.items():
        for idx, tx in enumerate(u_info.get('tx', [])):
            if tx['status'] == "PENDING_DEP":
                if st.button(f"Approve ₱{tx['amt']} for {u_name}"):
                    # FIX: This records the exact start and end time for the timer!
                    st_time = datetime.now()
                    et_time = st_time + timedelta(days=7)
                    
                    tx['status'] = "SUCCESSFUL_DEP"
                    u_info.setdefault('inv', []).append({
                        "amt": tx['amt'], 
                        "start": st_time.isoformat(), 
                        "end": et_time.isoformat(), 
                        "roi_paid": False
                    })
                    update_user(u_name, u_info); st.rerun()
    if st.button("EXIT BOSS"): st.session_state.is_boss = False; st.rerun()
                
