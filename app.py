import streamlit as st
import json
import os
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
    .hist-card { background: #1c1e26; padding: 15px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #00ff88; }
    .stButton>button:contains("⛔") {
        background-color: transparent !important; border: none !important; color: #444 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# BLOCK 3: PAGE ROUTING
# ==========================================

# --- ADMIN PANEL ---
if st.session_state.is_boss:
    st.title("👑 ADMIN CONTROL CENTER")
    if st.button("EXIT ADMIN"):
        st.session_state.is_boss = False
        st.rerun()
    
    reg = load_registry()
    st.subheader("🔔 PENDING APPROVALS")
    for username, u_data in reg.items():
        pending_list = u_data.get('pending_actions', [])
        for idx, action in enumerate(pending_list):
            with st.expander(f"{action['type']} - {username} (₱{action.get('amount', 0):,.2f})"):
                ca, cr = st.columns(2)
                if ca.button("✅ APPROVE", key=f"app_{username}_{idx}"):
                    if action['type'] == "DEPOSIT":
                        # Logic for Referral Commission (First Deposit Only)
                        if not u_data.get('has_deposited'):
                            ref_name = u_data.get('referral')
                            if ref_name in reg:
                                commission = action['amount'] * 0.20
                                reg[ref_name].setdefault('commissions', []).append({
                                    "referee": username,
                                    "deposit": action['amount'],
                                    "amt": commission,
                                    "status": "UNCLAIMED"
                                })
                            u_data['has_deposited'] = True
                        
                        u_data.setdefault('inv', []).append({"amount": action['amount'], "start_time": datetime.now().isoformat()})
                    
                    if action['type'] == "COMMISSION_REQUEST":
                        # Admin simply clears the request; money logic happens on user side
                        pass

                    u_data.setdefault('history', []).append({
                        "type": action['type'], "amount": action['amount'],
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "CONFIRMED"
                    })
                    u_data['pending_actions'].pop(idx)
                    # We save the entire registry here because we modified the Referrer's data too
                    with open("bpsm_registry.json", "w") as f: json.dump(reg, f, indent=4, default=str)
                    st.rerun()
                    

# --- USER DASHBOARD ---
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    if 'wallet' not in data: data['wallet'] = 0.0
    
    col1, col2 = st.columns([0.8, 0.2])
    with col1: st.write(f"Logged in as: **{data.get('full_name')}**")
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
    if c3.button("♻️ REINVEST"):
        if data['wallet'] > 0:
            amt = data['wallet']
            data['wallet'] = 0.0
            data.setdefault('inv', []).append({"amount": amt, "start_time": datetime.now().isoformat()})
            data.setdefault('history', []).append({
                "type": "RECYCLE", "amount": amt, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "RECYCLE RUNNING"
            })
            update_user(st.session_state.user, data); st.rerun()

    if st.session_state.action_type == "DEP":
        with st.form("d"):
            st.markdown("### 📥 DEPOSIT REQUEST")
            amt_d = st.number_input("Amount to Deposit", min_value=100.0)
            uploaded_file = st.file_uploader("Browse/Upload Deposit Receipt", type=['jpg', 'jpeg', 'png'])
            if st.form_submit_button("SEND TO ADMIN"):
                if uploaded_file is not None:
                    data.setdefault('pending_actions', []).append({
                        "type": "DEPOSIT", "amount": amt_d, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "WAITING CONFIRMATION"
                    })
                    update_user(st.session_state.user, data)
                    st.success("Receipt sent! Waiting for Admin."); st.session_state.action_type = None; st.rerun()
                else: st.error("Please upload your receipt first!")

    # --- RUNNING CAPITALS SECTION ---
    st.markdown("### 🚀 RUNNING CAPITALS")
    active = data.get('inv', [])
    if not active: st.info("No running capitals.")
    else:
        now = datetime.now()
        for idx, a in enumerate(active):
            start_dt = datetime.fromisoformat(a['start_time'])
            end_dt = start_dt + timedelta(days=7)
            st.markdown(f"<div class='hist-card'><b>RUNNING CAPITAL</b>: ₱{a['amount']:,.2f}<br><small>Matures: {end_dt.strftime('%Y-%m-%d %H:%M')}</small></div>", unsafe_allow_html=True)
            if now >= end_dt:
                if st.button(f"📥 PULL OUT ₱{a['amount']*1.20:,.2f}", key=f"p_{idx}"):
                    data['wallet'] += (a['amount'] * 1.20)
                    active.pop(idx)
                    update_user(st.session_state.user, data); st.rerun()
                    
    # --- REFERRAL & COMMISSION SECTION ---
    st.markdown("### 🤝 REFERRAL COMMISSIONS (20%)")
    comms = data.get('commissions', [])
    if not comms:
        st.info("No referral commissions yet.")
    else:
        for c_idx, c in enumerate(comms):
            col_ref, col_btn = st.columns([0.7, 0.3])
            with col_ref:
                st.write(f"👤 **{c['referee']}** | Deposit: ₱{c['deposit']:,.2f} | **Bonus: ₱{c['amt']:,.2f}**")
            with col_btn:
                if c['status'] == "UNCLAIMED":
                    if st.button(f"CLAIM ₱{c['amt']:,.2f}", key=f"ref_{c_idx}"):
                        # Add to wallet and mark as claimed
                        data['wallet'] += c['amt']
                        c['status'] = "CLAIMED"
                        # Notify Admin
                        data.setdefault('pending_actions', []).append({
                            "type": "COMMISSION_CLAIMED", "amount": c['amt'], 
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        update_user(st.session_state.user, data); st.rerun()
                else:
                    st.success("✅ CLAIMED")
                    
    
    # --- HISTORY SECTION ---
    st.markdown("### 📜 TRANSACTION HISTORY")
    st.subheader("⏳ PENDING REQUESTS")
    for p in data.get('pending_actions', []):
        lbl = "WAITING CONFIRMATION" if p['type'] == "DEPOSIT" else "WITHDRAWAL REQUESTED"
        st.write(f"**{lbl}**: ₱{p['amount']:,.2f} | {p['date']}")
    st.subheader("✅ COMPLETED HISTORY")
    for h in reversed(data.get('history', [])):
        st.write(f"**{h['status']}**: ₱{h['amount']:,.2f} | {h['date']}")

# --- LOGIN / REGISTER ---
elif st.session_state.page == "login":
    st.title("ACCESS PORTAL")
    if st.button("Back"): st.session_state.page = "ad"; st.rerun()
    tab_login, tab_reg = st.tabs(["LOGIN", "REGISTER NEW ACCOUNT"])
    with tab_login:
        st.info("⚠️ PLEASE USE YOUR FULL NAME (NAME MIDDLE NAME LASTNAME) TO LOGIN.")
        u = st.text_input("FULL NAME").upper().strip()
        p = st.text_input("6-DIGIT PIN", type="password", key="login_pin")
        if st.button("LOGIN"):
            reg = load_registry()
            if u in reg and str(reg[u]['pin']) == str(p):
                st.session_state.user = u; st.rerun()
            else: st.error("Invalid Full Name or PIN")
    with tab_reg:
        full_name = st.text_input("NAME MIDDLE NAME AND LASTNAME").upper().strip()
        st.warning("PIN MUST BE EXACTLY 6 DIGIT NUMBERS ONLY")
        p1 = st.text_input("CREATE 6-DIGIT PIN", type="password", max_chars=6)
        p2 = st.text_input("CONFIRM 6-DIGIT PIN", type="password", max_chars=6)
        ref_name = st.text_input("REFERRAL NAME (ACTIVE INVESTOR)").upper().strip()
        if st.button("REGISTER"):
            reg = load_registry()
            if not full_name: st.error("NAME FIELD REQUIRED")
            elif full_name in reg: st.warning("ALREADY REGISTERED")
            elif len(p1) != 6 or not p1.isdigit(): st.error("6 NUMBERS ONLY")
            elif p1 != p2: st.error("PIN MISMATCH")
            elif ref_name not in reg: st.error("REFERRAL NOT FOUND")
            else:
                reg[full_name] = {"pin": p1, "wallet": 0.0, "inv": [], "full_name": full_name, "referral": ref_name, "pending_actions": [], "history": []}
                update_user(full_name, reg[full_name]); st.success("SUCCESS! PLEASE LOGIN.")

# --- SIMPLE ADVERTISEMENT FRONT PAGE ---
else:
    st.markdown("<h1 style='color: #007BFF; margin-bottom: 0;'>ISMEX OFFICIAL</h1>", unsafe_allow_html=True)
    st.markdown("### Transform your initial investment into a powerhouse of growth through our precision-engineered market cycles.")
    st.divider()
    st.info("### 🚀 Grow your capital by 20% every 7 days.")
    col_a, col_b = st.columns([0.1, 0.9])
    if col_a.button("⛔"): st.session_state.admin_mode = not st.session_state.admin_mode
    if col_b.button("🚀 GET STARTED / LOGIN", use_container_width=True): st.session_state.page = "login"; st.rerun()
    if st.session_state.admin_mode:
        if st.text_input("Admin Key", type="password") == "0102030405":
            st.session_state.is_boss = True; st.rerun()
            
