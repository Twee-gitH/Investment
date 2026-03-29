import streamlit as st
import json
import os
import pandas as pd

# --- DATA ENGINE ---
REGISTRY_FILE = "bpsm_registry.json"

def load_data():
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_data(data):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, default=str)

# --- YOUR ORIGINAL PROGRAM LOGIC STARTS HERE ---
# (Keep all your existing code for login, registration, and cycles above this line)

reg = load_data()

# --- YOUR ORIGINAL PROGRAM LOGIC ENDS HERE ---

st.divider()

# --- ⚠️ THE HIDDEN BOSS PANEL ---
with st.expander("⚠️"):
    # This matches the "Orange01!" key from your screenshot
    boss_key = st.text_input("Security Key", type="password", placeholder="...")
    if st.button("ENTER"):
        if boss_key == "Orange01!":
            st.session_state.is_boss = True
            st.success("Access Granted")
        else:
            st.error("Denied")

if st.session_state.get("is_boss"):
    st.divider()
    
    # CALCULATE TOTAL SYSTEM VALUE
    total_pool = sum(d.get('wallet', 0.0) for d in reg.values())
    
    st.markdown("### 🏛️ MASTER CONTROL")
    st.metric("💰 TOTAL ASSET POOL", f"₱{total_pool:,.2f}")
    
    # DASHBOARD TABS
    t1, t2, t3, t4 = st.tabs(["🔔 REQUESTS", "🛠️ EDIT", "👥 DATA", "💾 BACKUP"])
    
    with t1:
        st.subheader("Pending Approvals")
        for user, d in reg.items():
            for i, tx in enumerate(d.get('tx', [])):
                if tx['type'] == 'DEP' and tx['status'] == 'PENDING':
                    st.info(f"{user}: ₱{tx['amt']:,}")
                    if st.button(f"Approve {user}", key=f"a_{user}_{i}"):
                        reg[user]['wallet'] += tx['amt']
                        reg[user]['tx'][i]['status'] = 'APPROVED'
                        save_data(reg)
                        st.rerun()
    
    with t2:
        st.subheader("Quick Adjustment")
        if reg:
            target = st.selectbox("Investor", list(reg.keys()))
            amt = st.number_input("Amount (PHP)", step=100.0)
            if st.button("UPDATE BALANCE"):
                reg[target]['wallet'] += amt
                save_data(reg)
                st.success("Balance updated.")
    
    with t3:
        st.subheader("Investor Database")
        for user, d in reg.items():
            with st.expander(f"👤 {user} (₱{d['wallet']:,.2f})"):
                st.write(f"**PIN:** `{d['pin']}`")
                st.write("**Recent Logs:**")
                st.write(d.get('tx', []))

    with t4:
        st.subheader("Data Protection")
        if reg:
            # Convert JSON to a format you can open in Excel
            df = pd.DataFrame.from_dict(reg, orient='index')
            csv = df.to_csv().encode('utf-8')
            st.download_button(
                label="📥 DOWNLOAD CSV BACKUP",
                data=csv,
                file_name=f"BPSM_Backup_{pd.Timestamp.now().strftime('%Y-%m-%d')}.csv",
                mime="text/csv",
            )
            st.write("Download this file to your phone to keep a record of all balances.")
    
    if st.button("LOGOUT"):
        st.session_state.is_boss = False
        st.rerun()
                        
