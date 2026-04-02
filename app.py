import streamlit as st
import json
import os
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# ==========================================
# BLOCK 1: DATA ENGINE
# ==========================================
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
        json.dump(reg, f, indent=4, default=str)

# ==========================================
# BLOCK 2: UI STYLING
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    
    .rainbow-banner { 
        background-color: #1a1e26; border-radius: 10px; padding: 20px 10px; 
        text-align: center; margin-bottom: 20px; border: 1px solid #2d303a; 
    }
    .main-title { 
        font-weight: bold; font-size: 22px; display: inline;
        background: linear-gradient(90deg, #ff007f, #ffaa00, #00ff88, #00eeff);
        -webkit-background-clip: text; color: transparent;
    }
    
    .ad-panel { background: #1c1e26; border-radius: 8px; border: 1px dashed #00eeff; padding: 15px; margin-bottom: 20px; text-align: center;}

    .balance-card { background: #1c1e26; padding: 25px; border-radius: 12px; border: 1px solid #2d303a; text-align: center; margin-bottom: 20px;}
    .cycle-card { background-color: #1c1e26; padding: 20px; border-radius: 12px; border: 1px solid #2d303a; border-left: 4px solid #00ff88; margin-bottom: 15px; }
    
    /* STEALTH ADMIN ICON STYLING */
    .stButton>button:contains("⛔") {
        background-color: transparent !important;
        border: none !important;
        color: white !important;
        font-size: 20px !important;
        padding: 0 !important;
        width: auto !important;
        box-shadow: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# BLOCK 3: AUTH & SECURE ADMIN ICON
# ==========================================
if 'user' not in st.session_state: st.session_state.user = None
if 'is_boss' not in st.session_state: st.session_state.is_boss = False
if 'show_admin_login' not in st.session_state: st.session_state.show_admin_login = False

if st.session_state.user is None and not st.session_state.is_boss:
    # Banner with Integrated Secret Trigger
    st.markdown('<div class="rainbow-banner">', unsafe_allow_html=True)
    c_t1, c_btn, c_t2 = st.columns([0.15, 0.05, 0.8])
    with c_t1: st.markdown('<p class="main-title">INTL</p>', unsafe_allow_html=True)
    with c_btn:
        if st.button("⛔"): 
            st.session_state.show_admin_login = not st.session_state.show_admin_login
    with c_t2: st.markdown('<p class="main-title">STOCK MARKET EXCHANGE</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Secret PIN box appears only when ⛔ is clicked
    if st.session_state.show_admin_login:
        admin_pin = st.text_input("Security Code", type="password")
        if admin_pin == "0102030405":
            st.session_state.is_boss = True
            st.session_state.show_admin_login = False
            st.rerun()

    st.markdown('<div class="ad-panel"><p style="color:#8c8f99; font-size:12px;">High-frequency HFT cycling active for real-time profit generation.</p></div>', unsafe_allow_html=True)
    
    u_name = st.text_input("Username")
    u_pin = st.text_input("PIN", type="password")
    
    if st.button("ENTER DASHBOARD"):
        reg = load_registry()
        if u_name in reg and str(reg[u_name].get('pin')) == str(u_pin):
            st.session_state.user = u_name
            st.rerun()
        else: st.error("Access Denied")

# ==========================================
# BLOCK 4: USER DASHBOARD (Live ROI)
# ==========================================
if st.session_state.user:
    st_autorefresh(interval=1000, key="ticker")
    name = st.session_state.user
    data = load_registry().get(name)
    now = datetime.now()
    ROI_PER_SEC = 0.20 / 604800

    st.markdown(f'<div class="balance-card"><p style="color:#8c8f99; font-size:12px;">WITHDRAWABLE BALANCE</p><h1 style="color:#00ff88; margin:0;">₱{data["wallet"]:,.2f}</h1></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        with st.expander("📥 DEPOSIT"):
            amt = st.number_input("Amount", 1000, step=500)
            if st.file_uploader("Receipt") and st.button("CONFIRM"):
                data.setdefault('tx', []).append({"type":"DEP","amt":amt,"status":"PENDING","date":now.isoformat()})
                update_user(name, data); st.rerun()
    with c2:
        if st.button("LOGOUT"):
            st.session_state.user = None
            st.rerun()

    st.markdown("### ⌛ ACTIVE CYCLES")
    for inv in reversed(data.get('inv', [])):
        st_t, et_t = datetime.fromisoformat(inv['start']), datetime.fromisoformat(inv['end'])
        if now < et_t:
            val = inv['amt'] * ROI_PER_SEC * (now - st_t).total_seconds()
            time_str = str(et_t - now).split('.')[0]
            banner = f"LOCKED UNTIL {et_t.strftime('%b %d, %I:%M %p')}"
        else:
            val = inv['amt'] * 0.20
            time_str = "✅ MATURED"
            banner = "READY TO PULL OUT"

        st.markdown(f"""
            <div class="cycle-card">
                <p style="margin:0; color:white;">Capital: <b>₱{inv['amt']:,}</b></p>
                <div style="color:#00ff88; font-size:11px; font-weight:bold; margin-top:5px;">ACCUMULATED ROI:</div>
                <h2 style="color:#00ff88; margin:0; font-family:monospace;">₱{val:,.4f}</h2>
                <p style="color:#ff4b4b; margin:0; font-weight:bold; font-size:14px;">⌛ {time_str}</p>
                <div style="background:#252830; padding:8px; border-radius:5px; font-size:11px; margin-top:10px; text-align:center;">{banner}</div>
            </div>
        """, unsafe_allow_html=True)

# ==========================================
# BLOCK 5: ADMIN (Unique ID Crash Fix)
# ==========================================
elif st.session_state.is_boss:
    st.title("👑 ADMIN CONTROL")
    reg = load_registry()
    for u_n, u_d in reg.items():
        for i, tx in enumerate(u_d.get('tx', [])):
            if tx['status'] == "PENDING":
                st.info(f"REQ: {u_n} | {tx['type']} | ₱{tx['amt']}")
                # Unique key prevents DuplicateElementId error
                if st.button(f"APPROVE REQ", key=f"adm_{u_n}_{i}"):
                    tx['status'] = "SUCCESS"
                    if tx['type'] == "DEP":
                        u_d.setdefault('inv', []).append({"amt":tx['amt'], "start":datetime.now().isoformat(), "end":(datetime.now()+timedelta(days=7)).isoformat()})
                    update_user(u_n, u_d); st.rerun()
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
        
