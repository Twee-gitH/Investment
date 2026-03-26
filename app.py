import streamlit as st
import time
from datetime import datetime, timedelta

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="BP Market", page_icon="🇵🇭")
st.markdown("""
<style>
    .stApp { margin-top: 20px; }
    input[type="text"] { text-transform: uppercase; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; background-color: #0038a8; color: white; font-weight: bold; border: none; }
    .logo-text { text-align: center; color: #0038a8; font-weight: 900; font-size: 2.2em; line-height: 1.2; }
    .info-box { background-color: #f8fafc; padding: 15px; border-radius: 10px; border: 1px solid #0038a8; margin-bottom: 15px; }
    .owner-card { background-color: #f1f5f9; padding: 10px; border-radius: 8px; border-left: 5px solid #0038a8; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 2. LOGO ---
st.markdown('<p class="logo-text">🇵🇭 BAGONG<br>PILIPINAS</p>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b; font-weight: bold;'>AUTHORIZED STOCK MARKET PORTAL</p>", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = "login"
if 'users_db' not in st.session_state: st.session_state.users_db = []
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'pending_deposits' not in st.session_state: st.session_state.pending_deposits = []

# --- 4. LOGIN PAGE ---
if st.session_state.page == "login":
    st.subheader("LOGIN")
    l_name = st.text_input("FULL NAME").upper()
    l_pin = st.text_input("PASSWORD / PIN", type="password")
    
    if st.button("ENTER MARKET"):
        if l_name == "ADMIN" and l_pin == "090807":
            st.session_state.page = "admin"
            st.rerun()
        else:
            user = next((u for u in st.session_state.users_db if u['name'] == l_name and u['pin'] == l_pin), None)
            if user:
                st.session_state.current_user = user
                st.session_state.page = "dashboard"
                st.rerun()
            else: st.error("INVALID CREDENTIALS")
    
    if st.button("NO ACCOUNT? SIGN UP"):
        st.session_state.page = "signup"
        st.rerun()

# --- 5. SIGN UP PAGE ---
elif st.session_state.page == "signup":
    st.subheader("CREATE ACCOUNT")
    reg_name = st.text_input("FULL NAME").upper()
    pin1 = st.text_input("CREATE 6-DIGIT PIN", type="password", max_chars=6)
    
    if st.button("COMPLETE REGISTRATION"):
        if reg_name and len(pin1) == 6:
            st.session_state.users_db.append({"name": reg_name, "pin": pin1, "investments": []})
            st.success("✅ SUCCESS! PLEASE LOGIN.")
            time.sleep(1)
            st.session_state.page = "login"
            st.rerun()

# --- 6. OWNER ADMIN DASHBOARD ---
elif st.session_state.page == "admin":
    st.subheader("👑 OWNER DASHBOARD")
    
    tab1, tab2 = st.tabs(["👥 INVESTOR LIST", "📥 PENDING APPROVALS"])
    
    with tab1:
        if not st.session_state.users_db: st.info("No investors yet.")
        for u in st.session_state.users_db:
            principal = sum(i['amount'] for i in u['investments'])
            interest = principal * 0.20
            st.markdown(f"""
            <div class="owner-card">
                <b>Investor:</b> {u['name']}<br>
                <b>Principal:</b> ₱{principal:,.2f} | <b>Interest (20%):</b> ₱{interest:,.2f}<br>
                <b>Total Value:</b> ₱{principal + interest:,.2f}
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        if not st.session_state.pending_deposits: st.info("No pending deposits.")
        for i, dep in enumerate(st.session_state.pending_deposits):
            st.write(f"User: {dep['user']} | Amount: ₱{dep['amount']:,}")
            if st.button("APPROVE PAYMENT", key=f"app_{i}"):
                for u in st.session_state.users_db:
                    if u['name'] == dep['user']:
                        u['investments'].append({"amount": dep['amount']})
                st.session_state.pending_deposits.pop(i)
                st.rerun()

    if st.button("LOGOUT"):
        st.session_state.page = "login"
        st.rerun()

# --- 7. USER DASHBOARD ---
elif st.session_state.page == "dashboard":
    u = st.session_state.current_user
    st.markdown(f"""
    <div class="info-box">
        <h4 style="color:#0038a8; margin-top:0;">📊 INVESTMENT UTILIZATION</h4>
        <p style="font-size:0.85em;">YOUR EVERY PENNY IS USED TO TRADE IN THE STOCK MARKET OR BLACK MARKET INTERNATIONAL TRADING OF COMMODITIES AND ETC. WE SECURE HIGH RETURNS THROUGH GLOBAL LIQUIDITY MARKETS.</p>
    </div>
    """, unsafe_allow_html=True)

    principal = sum(i['amount'] for i in u['investments'])
    interest = principal * 0.20
    st.metric("TOTAL BALANCE", f"₱{principal + interest:,.2f}", f"+₱{interest:,.2f}")

    st.subheader("📥 INVEST")
    amt = st.selectbox("PESO AMOUNT", [500, 1000, 5000, 10000, 50000])
    if st.button(f"PROCEED TO PAY ₱{amt:,}"):
        st.session_state.pending_deposits.append({"user": u['name'], "amount": float(amt)})
        st.success("Request sent to Owner!")

    if st.button("LOGOUT"):
        st.session_state.page = "login"
        st.rerun()
                                              
