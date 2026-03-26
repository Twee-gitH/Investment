import streamlit as st
import time
from datetime import datetime, timedelta

# --- 1. APP CONFIG & STYLE ---
st.set_page_config(page_title="BP Market", page_icon="🇵🇭")

st.markdown("""
    <style>
    .stApp { margin-top: 50px; }
    input { text-transform: uppercase; }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background-color: #0038a8;
        color: white;
        font-weight: bold;
        border: none;
        margin-top: 10px;
    }
    .transaction-card {
        background-color: #f1f5f9;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 5px;
        border-left: 5px solid #0038a8;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE "MEMORY" (SESSION STATE) ---
if 'principal' not in st.session_state:
    st.session_state.principal = 0.0      # Total amount deposited
if 'profit' not in st.session_state:
    st.session_state.profit = 0.0         # 10% daily earnings
if 'history' not in st.session_state:
    st.session_state.history = []         # List of transactions
if 'page' not in st.session_state:
    st.session_state.page = "signup"

# --- 3. REGISTRATION PAGE ---
if st.session_state.page == "signup":
    st.markdown("<h2 style='text-align: center;'>🇵🇭 ACCOUNT REGISTRATION</h2>", unsafe_allow_html=True)
    full_name = st.text_input("FULL NAME").upper()
    region = st.selectbox("REGION", ["NCR", "REGION I", "REGION II", "REGION III", "REGION IV-A", "REGION V", "REGION VI", "REGION VII", "REGION VIII", "REGION IX", "REGION X", "REGION XI", "REGION XII", "REGION XIII", "BARMM", "CAR"])
    city = st.text_input("CITY / MUNICIPALITY").upper()
    barangay = st.text_input("BARANGAY").upper()
    email = st.text_input("EMAIL").upper()
    password = st.text_input("PASSWORD", type="password")

    if st.button("CREATE ACCOUNT"):
        if full_name and city and email:
            st.session_state.user_name = full_name
            st.session_state.page = "dashboard"
            st.rerun()

# --- 4. DASHBOARD PAGE ---
elif st.session_state.page == "dashboard":
    # Logic: Calculate 10% daily profit (Simulated for display)
    # Non-compounded means: Profit = Principal * 0.10
    daily_gain = st.session_state.principal * 0.10
    total_balance = st.session_state.principal + st.session_state.profit

    st.markdown(f"### WELCOME, {st.session_state.user_name}")
    st.caption("INVESTOR STATUS: VERIFIED ✅")
    
    col1, col2 = st.columns(2)
    col1.metric("TOTAL BALANCE", f"${total_balance:,.2f}")
    col2.metric("DAILY PROFIT (10%)", f"${daily_gain:,.2f}")

    st.markdown("---")
    
    # --- DEPOSIT SECTION ---
    st.subheader("📥 DEPOSIT")
    amounts = [100, 500, 1000, 5000, 10000, 20000, 30000, 50000]
    deposit_val = st.selectbox("SELECT AMOUNT", amounts)
    
    if st.button(f"CONFIRM DEPOSIT: ${deposit_val:,}"):
        with st.status("Processing Deposit...", expanded=False) as status:
            time.sleep(1)
            st.session_state.principal += float(deposit_val)
            # Add to History
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.history.insert(0, f"💰 DEPOSIT: +${deposit_val:,} | {now}")
            status.update(label="Deposit Confirmed!", state="complete")
        st.rerun()

    st.markdown("---")
    
    # --- WITHDRAW SECTION ---
    st.subheader("📤 WITHDRAW")
    st.caption("MINIMUM WITHDRAWAL: $500.00")
    w_amount = st.number_input("AMOUNT TO WITHDRAW", min_value=0.0)
    
    if st.button("REQUEST WITHDRAWAL"):
        if w_amount < 500:
            st.error("❌ MINIMUM WITHDRAWAL IS $500.00")
        elif w_amount > total_balance:
            st.error("❌ INSUFFICIENT BALANCE")
        else:
            with st.spinner("Processing..."):
                time.sleep(2)
                st.session_state.principal -= w_amount # Subtracting from total
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                st.session_state.history.insert(0, f"💸 WITHDRAW: -${w_amount:,} | {now}")
                st.success("Withdrawal Request Sent to Admin!")
                st.rerun()

    # --- TRANSACTION HISTORY ---
    st.markdown("---")
    st.subheader("📜 TRANSACTION HISTORY")
    if not st.session_state.history:
        st.write("No transactions yet.")
    else:
        for item in st.session_state.history:
            st.markdown(f'<div class="transaction-card">{item}</div>', unsafe_allow_html=True)

    if st.button("LOGOUT"):
        st.session_state.page = "signup"
        st.rerun()
        
