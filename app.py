import streamlit as st

# Set Page Config for Mobile
st.set_page_config(page_title="Bagong Pilipinas Stock Market", page_icon="📈")

# Custom CSS to make it look like a Professional App
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        height: 3em;
        background-color: #1d4ed8;
        color: white;
        font-weight: bold;
    }
    .payout-card {
        background-color: #0f172a;
        padding: 20px;
        border-radius: 20px;
        color: #4ade80;
        text-align: center;
    }
    </style>
    """, unsafe_allow_view_resolve=True)

# 1. LOGIN SYSTEM
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🇵🇭 BAGONG PILIPINAS")
    st.subheader("Stock Market Portal")
    user = st.text_input("Username")
    pas = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if user and pas: # Simple bypass for now
            st.session_state['logged_in'] = True
            st.rerun()
else:
    # 2. DASHBOARD
    menu = ["📈 Invest", "💸 Withdraw", "👤 Profile"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "📈 Invest":
        st.header("Investment Tiers")
        st.info("Daily ROI Payouts every 24 Hours")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("$100 (10%)"):
                st.session_state['amt'] = 110
        with col2:
            if st.button("$500 (20%)"):
                st.session_state['amt'] = 600
        with col3:
            if st.button("$1000 (30%)"):
                st.session_state['amt'] = 1300

        if 'amt' in st.session_state:
            st.markdown(f"""
                <div class="payout-card">
                    <p style="color:gray; font-size:12px;">PROJECTED 24HR PAYOUT</p>
                    <h1 style="margin:0;">${st.session_state['amt']}</h1>
                </div>
            """, unsafe_allow_html=True)
            if st.button("CONFIRM STAKE"):
                st.success("Investment Active! Check back in 24 hours.")

    elif choice == "💸 Withdraw":
        st.header("Withdraw Funds")
        st.metric("Available Balance", "$4,250.00")
        address = st.text_input("Wallet Address / GCASH Number")
        w_amt = st.number_input("Amount to Withdraw", min_value=10)
        if st.button("PROCESS WITHDRAWAL"):
            st.warning("Request Sent. Processing takes 5-30 mins.")
      
