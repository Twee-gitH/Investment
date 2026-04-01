import streamlit as st
import json
import os
import random
from datetime import datetime, timedelta

# --- 1. DATA STORAGE ---
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
    with open(REGISTRY_FILE, "w") as f: 
        json.dump(reg, f, default=str)

# --- 2. GLOBAL STYLES (LOCKED TO YOUR ORIGINAL SCREENSHOTS) ---
st.set_page_config(page_title="BPSM Official", layout="wide")

st.markdown("""
    <style>
    input[type="text"] { text-transform: uppercase !important; }
    
    .balance-card { 
        background: #1c1e24; padding: 20px; border-radius: 10px; 
        border: 1px solid #3a3d46; text-align: center; margin-bottom: 15px; 
    }
    .balance-label { color: #8c8f99; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
    .balance-val { color: #00ff88; font-size: 38px; font-weight: bold; margin: 0; }
    
    .section-header { 
        background: #252830; padding: 10px; border-radius: 5px; 
        margin-top: 15px; font-weight: bold; border-left: 5px solid #ce1126; 
        color: white; text-transform: uppercase; font-size: 14px;
    }
    
    .user-box { 
        background-color: #1c1e24; padding: 20px; border-radius: 12px; 
        border: 1px solid #3a3d46; margin-bottom: 5px; border-left: 6px solid #00ff88; 
    }
    .roi-text { color: #00ff88; font-family: 'Courier New', monospace; font-size: 32px; font-weight: bold; line-height: 1.2; }
    .meta-label { color: #8c8f99; font-size: 14px; }
    
    .stButton>button { 
        width: 100%; border-radius: 6px; padding: 12px; 
        background-color: #252830; border: 1px solid #3a3d46; 
        color: #8c8f99; font-size: 13px; text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION & LOGIN ---
if 'user' not in st.session_state: st.session_state.user = None
if 'is_boss' not in st.session_state: st.session_state.is_boss = False

if st.session_state.user is None and not st.session_state.is_boss:
    st.title("BAGONG PILIPINAS STOCK MARKET")
    t1, t2 = st.tabs(["SIGN-IN", "REGISTER"])
    with t1:
        ln, lp = st.text_input("NAME").upper(), st.text_input("PIN", type="password")
        if st.button("LOGIN"):
            reg = load_registry()
            if ln in reg and str(reg[ln].get('pin')) == str(lp):
                st.session_state.user = ln; st.rerun()
    with t2:
        rn = st.text_input("FULL NAME", key="r1").upper()
        rp = st.text_input("CREATE PIN", type="password", key="r2")
        ref = st.text_input("REFERRER NAME", key="r3").upper()
        if st.button("REGISTER ACCOUNT"):
            update_user(rn, {"pin": rp, "wallet": 0.0, "inv": [], "tx": [], "ref_by": ref, "reg_date": datetime.now().strftime("%Y-%m-%d")})
            st.success("SUCCESSFUL"); st.rerun()
    with st.expander("🔐 ADMIN"):
        if st.text_input("ADMIN PIN", type="password") == "0102030405":
            if st.button("ENTER BOSS MODE"): st.session_state.is_boss = True; st.rerun()
    st.stop()

# --- 4. INVESTOR DASHBOARD ---
if st.session_state.user:
    name = st.session_state.user
    data = load_registry().get(name)
    now = datetime.now()

    # ROI CALC ENGINE
    MINUTE_RATE = (0.20 / 7) / 1440 
    changed = False
    for i in data.get('inv', []):
        st_t, et_t = datetime.fromisoformat(i['start']), datetime.fromisoformat(i['end'])
        calc_now = min(now, et_t)
        i['accumulated_roi'] = max(0, i['amt'] * (((calc_now - st_t).total_seconds() / 60) * MINUTE_RATE))
        if now >= et_t and not i.get('roi_paid', False):
            data['wallet'] += (i['amt'] * 0.20); i['roi_paid'] = True; changed = True
    if changed: update_user(name, data); st.rerun()

    # BALANCE
    st.markdown(f'<div class="balance-card"><p class="balance-label">WITHDRAWABLE BALANCE</p><p class="balance-val">₱{data["wallet"]:,.2f}</p></div>', unsafe_allow_html=True)

    # --- THE FIXED DEPOSIT SECTION ---
    st.markdown("<div class='section-header'>📥 DEPOSIT CAPITAL</div>", unsafe_allow_html=True)
    d_amt = st.number_input("Amount to Deposit", min_value=1000, step=500)
    file = st.file_uploader("Upload Receipt", type=['jpg','png','jpeg'])
    if st.button("SUBMIT DEPOSIT REQUEST"):
        if file is not None:
            # We add the request to 'tx' list so Admin can see it
            data.setdefault('tx', []).append({
                "amt": d_amt, 
                "status": "PENDING_DEP", 
                "receipt": file.name, 
                "date": now.isoformat()
            })
            update_user(name, data)
            st.success("Sent to Admin for approval!")
            st.rerun()
        else:
            st.error("Please upload a receipt photo first.")

    # ACTIVE CYCLES
    st.markdown("<div class='section-header'>⌛ ACTIVE CYCLES</div>", unsafe_allow_html=True)
    inv_list = data.get('inv', [])
    for idx, t in enumerate(reversed(inv_list)):
        actual_idx = len(inv_list) - 1 - idx
        st_t, et_t = datetime.fromisoformat(t['start']), datetime.fromisoformat(t['end'])
        st.markdown(f"""
            <div class='user-box'>
                <b>Capital: ₱{t['amt']:,}</b><br>
                <span class='roi-text'>Accumulated ROI: ₱{t.get('accumulated_roi', 0):,.4f}</span><br>
                <b>Maturity:</b> {et_t.strftime('%Y-%m-%d %I:%M %p')}
            </div>
        """, unsafe_allow_html=True)

    if st.button("LOGOUT"):
        st.session_state.user = None
        st.rerun()

# --- 5. ADMIN OVERVIEW ---
elif st.session_state.is_boss:
    st.title("👑 BOSS OVERVIEW")
    all_users = load_registry()
    for u_name, u_data in all_users.items():
        # Look for the pending deposits in the user's transaction list
        for tx in u_data.get('tx', []):
            if tx['status'] == "PENDING_DEP":
                st.write(f"USER: {u_name} | Amount: ₱{tx['amt']} | Receipt: {tx['receipt']}")
                if st.button(f"APPROVE {tx['amt']} for {u_name}"):
                    tx['status'] = "SUCCESSFUL_DEP"
                    # Create the actual investment cycle
                    u_data.setdefault('inv', []).append({
                        "amt": tx['amt'], 
                        "start": datetime.now().isoformat(), 
                        "end": (datetime.now() + timedelta(days=7)).isoformat(), 
                        "roi_paid": False
                    })
                    update_user(u_name, u_data)
                    st.rerun()
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
        
