import streamlit as st
import json
import os
from datetime import datetime, timedelta

# ==========================================
# BLOCK 1: THE CORE ENGINE (DATA & STATE)
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

# Initialize all variables to prevent crashes
if 'page' not in st.session_state: st.session_state.page = "ad"
if 'user' not in st.session_state: st.session_state.user = None
if 'is_boss' not in st.session_state: st.session_state.is_boss = False
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False

# ==========================================
# BLOCK 2: INTERFACE STYLES (UI)
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .ad-panel { background: #1c1e26; border-radius: 8px; border: 1px dashed #00eeff; padding: 20px; text-align: center; }
    /* Hidden Admin Button as a Period */
    .stButton>button:contains("⛔") {
        background-color: transparent !important; border: none !important; color: #8c8f99 !important;
        font-size: 15px !important; padding: 0 !important; margin-left: -5px !important; display: inline !important;
        min-height: 0px !important; width: auto !important;
    }
    .module-card { background: #1a1e26; padding: 15px; border-radius: 10px; border: 1px solid #2d303a; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# BLOCK 3: PAGE 1 - THE ADVERTISEMENT
# ==========================================
if st.session_state.page == "ad" and not st.session_state.user and not st.session_state.is_boss:
    # 1. MEGA RAINBOW TITLE
    st.markdown('<h1 style="text-align:center; font-size:45px; font-weight:900; background:linear-gradient(90deg, #ff007f, #ffaa00, #00ff88, #00eeff); -webkit-background-clip: text; color: transparent; margin-bottom:5px;">INTERNATIONAL STOCK MARKET EXCHANGE</h1>', unsafe_allow_html=True)

    # 2. CENTERED ADMIN BUTTON (Between Title and Box)
    col_left, col_center, col_right = st.columns([0.46, 0.08, 0.46])
    with col_center:
        # We use a standard button here so it's easier to click when centered
        if st.button("⛔", key="mid_admin_btn", help="System Status"):
            st.session_state.admin_mode = not st.session_state.admin_mode

    # 3. THE ADVERTISEMENT BOX (Text is now fully inside)
    st.markdown("""
        <div class="ad-panel">
            <p style="color:#00eeff; font-weight:bold; font-size:18px; margin-bottom:10px;">How We Generate Your Profit:</p>
            <p style="color:#8c8f99; font-size:16px; line-height:1.6;">
                Your single capital is diversified and cycled multiple times through our advanced AI-managed scalping algorithm every hour. 
                Instead of holding a stock for a year, we take small 0.05% profits from thousands of trades, combining them to provide you 
                with your precise, ticking 20% guaranteed profit over the 7-day cycle. Your money is always moving, never dormant!
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 4. JOIN BUTTON
    st.markdown("<br>", unsafe_allow_html=True) # Adds a small space
    if st.button("🚀 JOIN NOW!", use_container_width=True, key="main_join_btn"):
        st.session_state.page = "login"
        st.rerun()

    # Secret Admin Gate (Appears only when ⛔ is clicked)
    if st.session_state.admin_mode:
        code = st.text_input("Security Code", type="password", key="admin_gate_input")
        if code == "0102030405":
            st.session_state.is_boss = True
            st.session_state.admin_mode = False
            st.rerun()
            

# ==========================================
# BLOCK 4: PAGE 2 - ACCESS PORTAL (LOGIN)
# ==========================================
elif st.session_state.page == "login" and not st.session_state.user:
    st.markdown("<h1 style='text-align:center; color:#00eeff;'>ACCESS PORTAL</h1>", unsafe_allow_html=True)
    u_name = st.text_input("Username", key="login_u")
    u_pin = st.text_input("6-Digit PIN", type="password", key="login_p")
    
    if st.button("ENTER DASHBOARD", use_container_width=True, key="exec_login"):
        reg = load_registry()
        if u_name in reg and str(reg[u_name].get('pin')) == str(u_pin):
            st.session_state.user = u_name
            st.rerun()
        else: st.error("Invalid Credentials")
    
    if st.button("← BACK", key="back_ad"):
        st.session_state.page = "ad"
        st.rerun()

# ==========================================
# BLOCK 5: THE USER DASHBOARD (MODULAR)
# ==========================================
elif st.session_state.user:
    name = st.session_state.user
    data = load_registry().get(name)
    st.title(f"Welcome, {name}")

    # --- DEPOSIT BLOCK ---
    with st.expander("📥 DEPOSIT CAPITAL", expanded=False):
        st.markdown('<div class="module-card">', unsafe_allow_html=True)
        dep_amt = st.number_input("Amount (₱)", 1000, key="d_amt")
        if st.button("SUBMIT DEPOSIT", key="d_btn"): st.success("Pending Approval")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- WITHDRAW BLOCK ---
    with st.expander("📤 WITHDRAW PROFITS", expanded=False):
        st.markdown('<div class="module-card">', unsafe_allow_html=True)
        st.write(f"Balance: ₱{data.get('wallet', 0):,.2f}")
        if st.button("REQUEST PAYOUT", key="w_btn"): st.info("Processing...")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- COMMISSION BLOCK ---
    with st.expander("💰 COMMISSIONS", expanded=False):
        st.write(f"Earned: ₱{data.get('comm', 0):,.2f}")
        if st.button("CLAIM TO WALLET", key="c_btn"): st.rerun()

    # --- REINVEST BLOCK ---
    with st.expander("🔄 REINVEST", expanded=False):
        if st.button("START NEW CYCLE", key="r_btn"): st.success("Cycle Active")

    if st.button("LOGOUT"):
        st.session_state.user = None
        st.session_state.page = "ad"
        st.rerun()

# ==========================================
# BLOCK 6: ADMIN CONTROL
# ==========================================
elif st.session_state.is_boss:
    st.title("👑 ADMIN PANEL")
    if st.button("EXIT ADMIN"):
        st.session_state.is_boss = False
        st.rerun()
        
