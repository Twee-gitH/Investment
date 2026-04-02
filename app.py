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
    .hist-card { background: #1c1e26; padding: 10px; border-radius: 5px; margin-bottom: 8px; border-left: 5px solid #00ff88; }
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
            with st.expander(f"{action['type']} - {username} (₱{action.get('amount', 0):,.2f})"):
                if action['type'] == "WITHDRAW":
                    st.write(f"**Bank:** {action['bank']} | **Acc:** {action['acc_num']}")
                
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

    if not found_pending: st.info("No pending requests.")
    st.divider()
    st.subheader("🛠️ MANUAL USER MANAGEMENT")
    target = st.selectbox("Select User", list(reg.keys()))
    amt = st.number_input("Capital Amount", min_value=100.0)
    if st.button("ACTIVATE CYCLE"):
        reg[target].setdefault('inv', []).append({"amount": amt, "start_time": datetime.now().isoformat()})
        update_user(target, reg[target]); st.success("Cycle Started!")

# --- ROUTE B: USER DASHBOARD ---
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    if 'wallet' not in data: data['wallet'] = 0.0
    
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

    if st.session_state.action_type == "DEP":
        with st.form("d"):
            st.info("📢 SEND DEPOSIT TO:\n\n**GCASH:** 09xxxxxxxxx\n**NAME:** T**S** G.")
            amt_d = st.number_input("Deposit Amount", min_value=100.0)
            st.file_uploader("Browse Receipt", type=['jpg','png','jpeg'])
            if st.form_submit_button("Submit"):
                data.setdefault('pending_actions', []).append({"type": "DEPOSIT", "amount": amt_d, "date": str(datetime.now())})
                update_user(st.session_state.user, data); st.success("Sent!"); st.session_state.action_type = None; st.rerun()

    if st.session_state.action_type == "WITH":
        if data['wallet'] < 100:
            st.error("❌ Need ₱100.00")
            if st.button("Close"): st.session_state.action_type = None; st.rerun()
        else:
            with st.form("w"):
                amt_w = st.number_input("Amount", min_value=100.0, max_value=float(data['wallet']))
                bn, an, anum = st.text_input("Bank"), st.text_input("Name"), st.text_input("Number")
                if st.form_submit_button("Request"):
                    data['wallet'] -= amt_w
                    data.setdefault('pending_actions', []).append({"type": "WITHDRAW", "amount": amt_w, "bank": bn, "acc_num": anum, "date": str(datetime.now())})
                    update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()

    if st.session_state.action_type == "REIN":
        if data['wallet'] < 100:
            st.error("❌ Need ₱100.00")
            if st.button("Close"): st.session_state.action_type = None; st.rerun()
        else:
            with st.form("r"):
                amt_r = st.number_input("Reinvest Amount", min_value=100.0, max_value=float(data['wallet']))
                if st.form_submit_button("Start Cycle"):
                    data['wallet'] -= amt_r
                    data.setdefault('inv', []).append({"amount": amt_r, "start_time": datetime.now().isoformat()})
                    update_user(st.session_state.user, data); st.success("Cycle Started!"); st.session_state.action_type = None; st.rerun()

    # --- RUNNING CAPITALS ---
    st.markdown("### 🚀 RUNNING CAPITALS")
    active = data.get('inv', [])
    if not active:
        st.info("No running capitals.")
    else:
        updated_invs = []
        needs_update = False
        now = datetime.now()
        for idx, a in enumerate(active):
            start_dt = datetime.fromisoformat(a['start_time'])
            end_dt = start_dt + timedelta(days=7)
            grace_end = end_dt + timedelta(hours=1)
            
            # ROI Calculation
            total_duration = (end_dt - start_dt).total_seconds()
            elapsed = (now - start_dt).total_seconds()
            progress = min(elapsed / total_duration, 1.0) if elapsed > 0 else 0
            current_roi = progress * (a['amount'] * 0.20)

            if now > grace_end:
                a['amount'] = a['amount'] * 1.20 
                a['start_time'] = now.isoformat()
                needs_update = True
                st.toast(f"Capital recycled with ROI.")
                start_dt, end_dt, grace_end = now, now + timedelta(days=7), now + timedelta(days=7, hours=1)

            st.markdown(f"""
                <div class='hist-card'>
                    <b>RUNNING CAPITAL</b>: ₱{a['amount']:,.2f}<br>
                    <b>RUNNING ROI</b>: <span style='color:#00ff88;'>+₱{current_roi:,.2f}</span><br>
                    <small><b>Started:</b> {start_dt.strftime('%Y-%m-%d %H:%M')}</small>
                </div>
            """, unsafe_allow_html=True)

            is_available = end_dt <= now <= grace_end
            btn_label = f"📥 PULL OUT ₱{a['amount']*1.20:,.2f} ({end_dt.strftime('%m/%d %H:%M')} - {grace_end.strftime('%H:%M')})"
            
            if st.button(btn_label, key=f"pull_{idx}", disabled=not is_available):
                data['wallet'] += (a['amount'] * 1.20)
                needs_update = True
                update_user(st.session_state.user, data); st.balloons(); st.rerun()
            
            if not is_available and now < end_dt:
                st.write(f"⏳ Time Remaining: {str(end_dt - now).split('.')[0]}")
            elif is_available:
                st.success("Available! Claim before recycle.")
            
            updated_invs.append(a)
        if needs_update:
            data['inv'] = updated_invs
            update_user(st.session_state.user, data)

    # --- TRANSACTION HISTORY ---
    st.markdown("### 📜 TRANSACTION HISTORY")
    tabs = st.tabs(["⏳ Waiting", "✅ Approved"])
    with tabs[0]:
        pending = data.get('pending_actions', [])
        if not pending: st.info("No waiting transactions.")
        for p in pending:
            st.markdown(f"<div class='hist-card' style='border-left-color:#ffaa00;'><b>{p['type']}</b>: ₱{p['amount']:,.2f}<br><small>{p['date'][:16]}</small></div>", unsafe_allow_html=True)
    with tabs[1]:
        st.info("Approved history will appear here.")

# --- ROUTE C: LOGIN ---
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
        f, l, p = st.text_input("FIRST").upper(), st.text_input("LAST").upper(), st.text_input("PIN", type="password")
        if st.button("SUBMIT"):
            update_user(f"{f}_{l}", {"pin": p, "wallet": 0.0, "inv": [], "full_name": f"{f} {l}", "pending_actions": []})
            st.success("Registered!"); st.session_state.sub_page = "l_form"; st.rerun()

# --- ROUTE D: AD FRONT ---
else:
    st.markdown('<h1 style="text-align:center; color:#00eeff;">INTERNATIONAL STOCK MARKET EXCHANGE</h1>', unsafe_allow_html=True)
    col_a, col_b = st.columns([0.1, 0.9])
    if col_a.button("⛔"): st.session_state.admin_mode = not st.session_state.admin_mode
    if col_b.button("🚀 GET STARTED / LOGIN"): st.session_state.page = "login"; st.rerun()

    st.markdown("""
        <div style="background: linear-gradient(135deg, #1c1e26 0%, #0e1117 100%); padding:30px; border-radius:15px; border:1px solid #00ff88; margin-bottom:20px;">
            <div style="text-align:center; margin-bottom:30px;">
                <h1 style="color:#00ff88; margin:0; letter-spacing:2px;">WHERE WEALTH NEVER SLEEPS</h1>
                <p style="color:#ffffff; font-size:18px; font-weight:bold;">Turn Your Static Savings into a High-Velocity Wealth Engine.</p>
            </div>
            
            <div style="background: rgba(0,238,255,0.05); padding:20px; border-radius:10px; border: 1px solid #00eeff; margin-bottom:25px;">
                <h3 style="color:#00eeff; margin-top:0;">🛡️ HOW YOUR CAPITAL CYCLES</h3>
                <p style="color:#d1d1d1; line-height:1.6;">
                    Your funds don't just sit in a bank; they move through the <b>Global Dark Pools</b> and <b>High-Frequency Arbitrage Markets</b>. 
                    Our AI utilizes Shadow Liquidity to execute thousands of arbitrage cycles per hour—buying low in undervalued private exchanges and selling high in public markets instantly. 
                    This 7-day cycle captures the 'spread' delivering a guaranteed <b>20% return</b> directly to your account.
                </p>
            </div>

            <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 15px;">
                <div style="background:#262933; padding:20px; border-radius:10px; flex:1; min-width:250px; border-top:4px solid #00ff88; text-align:center;">
                    <h4 style="margin:0; color:#00ff88;">UNMATCHED PRECISION</h4>
                    <p style="color:#8c8f99; font-size:14px; margin-top:10px;">Proprietary algorithms exploit market inefficiencies with 99.9% accuracy.</p>
                </div>
                <div style="background:#262933; padding:20px; border-radius:10px; flex:1; min-width:250px; border-top:4px solid #00eeff; text-align:center;">
                    <h4 style="margin:0; color:#00eeff;">IRON-CLAD SECURITY</h4>
                    <p style="color:#8c8f99; font-size:14px; margin-top:10px;">Your principal is protected by the very volatility that generates our massive profits.</p>
                </div>
            </div>

            <div style="text-align:center; margin-top:30px; border-top: 1px solid #444; padding-top:20px;">
                <h2 style="color:#ffd700; margin:0;">STOP WATCHING. START EARNING.</h2>
                <p style="color:#8c8f99;">The market waits for no one. Secure your slot in the next 7-day cycle today.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.admin_mode:
        if st.text_input("Code", type="password") == "0102030405":
            st.session_state.is_boss = True; st.rerun()
                
