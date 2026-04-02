import streamlit as st
import json
import os
import time
from datetime import datetime, timedelta

# ==========================================
# BLOCK 1: THE CORE ENGINE (DATA & STATE)
# ==========================================
def load_registry():
    if os.path.exists("bpsm_registry.json"):
        try:
            with open("bpsm_registry.json", "r") as f: 
                return json.load(f)
        except: 
            return {}
    return {}

def update_user(name, data):
    reg = load_registry()
    reg[name] = data
    with open("bpsm_registry.json", "w") as f: 
        json.dump(reg, f, indent=4, default=str)

# Initialize session states
if 'page' not in st.session_state: st.session_state.page = "ad"
if 'user' not in st.session_state: st.session_state.user = None
if 'is_boss' not in st.session_state: st.session_state.is_boss = False
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False
if 'sub_page' not in st.session_state: st.session_state.sub_page = "select"

# ==========================================
# BLOCK 2: INTERFACE STYLES (UI)
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .ad-panel { background: #1c1e26; border-radius: 8px; border: 1px dashed #00eeff; padding: 20px; text-align: center; }
    .stButton>button:contains("⛔") {
        background-color: transparent !important; border: none !important; color: #8c8f99 !important;
        font-size: 15px !important; padding: 0 !important; margin-left: -5px !important; display: inline !important;
        min-height: 0px !important; width: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# BLOCK 3: PAGE 1 - THE ADVERTISEMENT
# ==========================================
if st.session_state.page == "ad" and not st.session_state.user and not st.session_state.is_boss:
    st.markdown('<h1 style="text-align:center; font-size:45px; font-weight:900; background:linear-gradient(90deg, #ff007f, #ffaa00, #00ff88, #00eeff); -webkit-background-clip: text; color: transparent; margin-bottom:20px;">INTERNATIONAL STOCK MARKET EXCHANGE</h1>', unsafe_allow_html=True)

    col_l, col_btn1, col_btn2, col_r = st.columns([0.35, 0.1, 0.2, 0.35])
    with col_btn1:
        if st.button("⛔", key="mid_gate_trigger"):
            st.session_state.admin_mode = not st.session_state.admin_mode
    with col_btn2:
        if st.button("🚀 JOIN NOW!", key="jump_to_login"):
            st.session_state.page = "login"
            st.rerun()

    st.markdown("""
        <div class="ad-panel" style="margin-top: 15px;">
            <p style="color:#00eeff; font-weight:bold; font-size:18px; margin-bottom:10px; text-align:center;">How We Generate Your Profit:</p>
            <p style="color:#8c8f99; font-size:16px; line-height:1.6; text-align:justify;">
                Your single capital is diversified and cycled multiple times through our advanced AI-managed scalping algorithm every hour. 
                Instead of holding a stock for a year, we take small 0.05% profits from thousands of trades, combining them to provide you 
                with your precise, ticking 20% guaranteed profit over the 7-day cycle.
            </p>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.admin_mode:
        code = st.text_input("Security Code", type="password")
        if code == "0102030405":
            st.session_state.is_boss = True
            st.session_state.admin_mode = False
            st.rerun()

# ==========================================
# BLOCK 4: PAGE 2 - ACCESS PORTAL (LOGIN/REG)
# ==========================================
elif st.session_state.page == "login" and not st.session_state.user and not st.session_state.is_boss:
    st.markdown("<h1 style='text-align:center; color:#00eeff;'>ACCESS PORTAL</h1>", unsafe_allow_html=True)
    
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("MEMBER LOG IN", use_container_width=True):
            st.session_state.sub_page = "login_form"
    with col_nav2:
        if st.button("REGISTER AS MEMBER", use_container_width=True):
            st.session_state.sub_page = "reg_form"

    st.markdown("---")

    if st.session_state.sub_page == "login_form":
        u_name_raw = st.text_input("FULL USERNAME (ALL CAPS)", key="l_u").upper().strip()
        u_pin = st.text_input("6-DIGIT PIN", type="password", max_chars=6, key="l_p")
        
        if st.button("ENTER DASHBOARD", use_container_width=True):
            reg = load_registry()
            name_v1 = u_name_raw
            name_v2 = u_name_raw.replace(" ", "_")
            user_data = reg.get(name_v1) or reg.get(name_v2)
            
            if user_data and str(user_data.get('pin')) == str(u_pin):
                st.session_state.user = name_v1 if name_v1 in reg else name_v2
                st.session_state.sub_page = "select"
                st.rerun()
            else:
                st.error("❌ INVALID: Name or 6-Digit PIN does not match.")
    
    elif st.session_state.sub_page == "reg_form":
        f = st.text_input("FIRST NAME").upper().strip()
        m = st.text_input("MIDDLE NAME").upper().strip()
        l = st.text_input("LAST NAME").upper().strip()
        p1 = st.text_input("6-DIGIT PIN", type="password", max_chars=6)
        inv = st.text_input("INVITOR OR 'DIRECT'").upper().strip()
        
        if st.button("CREATE ACCOUNT") and f and l and len(p1) == 6:
            db_key = f"{f}_{m}_{l}"
            update_user(db_key, {"pin": p1, "wallet": 0.0, "inv": [], "full_name": f"{f} {m} {l}", "referred_by": inv})
            st.success("Registration Successful! Please Log In.")
            st.session_state.sub_page = "login_form"
            st.rerun()

# ==========================================
# BLOCK 5: THE USER DASHBOARD
# ==========================================
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    
    # --- MATURITY LOGIC ---
    current_invs = data.get('inv', [])
    updated_invs = []
    payout_triggered = False
    for i in current_invs:
        end_time = datetime.fromisoformat(i['start_time']) + timedelta(days=7)
        if datetime.now() >= end_time:
            data['wallet'] += (i['amount'] * 1.20)
            payout_triggered = True
        else:
            updated_invs.append(i)
    
    if payout_triggered:
        data['inv'] = updated_invs
        update_user(st.session_state.user, data)
        st.balloons()

    # --- UI DISPLAY ---
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.markdown(f"### BPSM\nWelcome, {data.get('full_name')}")
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

    st.markdown("<br>### ⌛ ACTIVE CYCLES", unsafe_allow_html=True)
    if not data.get('inv'):
        st.info("No active cycles. Contact Admin to start.")
    
    for inv in data.get('inv', []):
        start = datetime.fromisoformat(inv['start_time'])
        elapsed = (datetime.now() - start).total_seconds()
        total_sec = 7 * 24 * 3600
        percent = min(elapsed / total_sec, 1.0)
        roi = (inv['amount'] * 0.20) * percent
        
        rem = (start + timedelta(days=7)) - datetime.now()
        d, h, m = rem.days, rem.seconds // 3600, (rem.seconds // 60) % 60
        s = rem.seconds % 60

        st.markdown(f"""
            <div style="background:#16191f; border-left: 4px solid #00ff88; padding:15px; border-radius:5px; margin-bottom:10px; border: 1px solid #2d303a;">
                <p style="margin:0; color:white;">Capital: <b>₱{inv['amount']:,.1f}</b></p>
                <h2 style="color:#00ff88; margin:0;">₱{roi:,.4f}</h2>
                <p style="color:#ff4b4b; font-weight:bold; font-size:14px;">⌛ {d}D {h}H {m}M {s}S REMAINING</p>
            </div>
        """, unsafe_allow_html=True)

    # --- THE HEARTBEAT ---
    time.sleep(1)
    st.rerun()

# ==========================================
# BLOCK 6: ADMIN PANEL
# ==========================================
elif st.session_state.is_boss:
    st.title("👑 ADMIN PANEL")
    if st.button("EXIT ADMIN"):
        st.session_state.is_boss = False
        st.rerun()

    reg = load_registry()
    target = st.selectbox("Select User", list(reg.keys()))
    amt = st.number_input("Capital Amount", min_value=100.0)
    
    if st.button("ACTIVATE CYCLE"):
        reg[target]['inv'].append({"amount": amt, "start_time": datetime.now().isoformat()})
        update_user(target, reg[target])
        st.success("Cycle Started!")

    st.divider()
    st.write("Database:", reg)
        
