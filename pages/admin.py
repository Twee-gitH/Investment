import streamlit as st
import json
import os

# --- DATA ENGINE ---
REGISTRY_FILE = "bpsm_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r") as f:
                return json.load(f)
        except: return {}
    return {}

def save_all(data):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, default=str)

# --- ADMIN SECURE UI ---
st.set_page_config(page_title="BPSM ADMIN", layout="wide")

st.sidebar.header("🛡️ Admin Security")
admin_key = st.sidebar.text_input("Enter Admin Key", type="password")

# CHANGE 'MASTER123' to your preferred password
if admin_key == "MASTER123":
    st.title("👨‍💼 BPSM MASTER CONTROL")
    reg = load_registry()

    if not reg:
        st.warning("No investors found in the registry.")
    else:
        # --- SECTION 1: MANUAL ADJUSTMENTS (NEW!) ---
        st.header("🛠️ Manual Asset Adjustment")
        with st.expander("Click to Modify a User's Balance"):
            target_user = st.selectbox("Select Investor", options=list(reg.keys()))
            mod_type = st.radio("Action", ["Add Funds (+)", "Deduct Funds (-)"])
            amount = st.number_input("Amount (PHP)", min_value=1.0, step=100.0)
            reason = st.text_input("Note (e.g., Error Correction, Bonus)")
            
            if st.button("EXECUTE ADJUSTMENT"):
                if mod_type == "Add Funds (+)":
                    reg[target_user]['wallet'] += amount
                    change_txt = f"ADMIN ADD: ₱{amount}"
                else:
                    reg[target_user]['wallet'] -= amount
                    change_txt = f"ADMIN DEDUCT: ₱{amount}"
                
                # Log the manual change in their history
                from datetime import datetime
                reg[target_user].setdefault('tx', []).append({
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "type": "ADJ",
                    "amt": amount,
                    "status": f"COMPLETED ({reason})" if reason else "COMPLETED"
                })
                
                save_all(reg)
                st.success(f"Successfully modified {target_user}'s balance!")
                st.rerun()

        st.divider()

        # --- SECTION 2: APPROVALS ---
        st.header("🔔 Action Required")
        
        # Pending Deposits
        st.subheader("📥 Deposit Requests")
        for user, d in reg.items():
            for i, tx in enumerate(d.get('tx', [])):
                if tx['type'] == 'DEP' and tx['status'] == 'PENDING':
                    with st.expander(f"💰 ₱{tx['amt']:,} from {user}"):
                        st.write(f"**Ref #:** {tx.get('ref', 'N/A')}")
                        if st.button(f"Approve Deposit", key=f"dep_{user}_{i}"):
                            reg[user]['wallet'] += tx['amt']
                            reg[user]['tx'][i]['status'] = 'APPROVED'
                            save_all(reg)
                            st.success(f"Funded {user}!")
                            st.rerun()

        # Pending Withdrawals
        st.subheader("📤 Withdrawal Requests")
        for user, d in reg.items():
            for i, tx in enumerate(d.get('tx', [])):
                if tx['type'] == 'WD' and tx['status'] == 'PENDING':
                    with st.expander(f"💸 ₱{tx['amt']:,} to {user}"):
                        if st.button(f"Confirm Payout Paid", key=f"wd_{user}_{i}"):
                            reg[user]['tx'][i]['status'] = 'APPROVED'
                            save_all(reg)
                            st.success(f"Payout for {user} cleared.")
                            st.rerun()

        st.divider()

        # --- SECTION 3: USER DIRECTORY ---
        st.header("👥 Investor Database")
        search = st.text_input("Search User by Name").upper()

        for user, d in reg.items():
            if search in user:
                with st.container():
                    st.markdown(f"### 👤 {user}")
                    col1, col2 = st.columns(2)
                    col1.metric("Wallet Balance", f"₱{d['wallet']:,.2f}")
                    col2.metric("Active Cycles", len(d.get('inv', [])))

                    with st.expander("📄 Full History & PIN"):
                        st.write(f"**Secure PIN:** `{d['pin']}`")
                        st.write(f"**Referral Earnings:** ₱{d.get('commissions', 0.0):,.2f}")
                        st.write("**Recent Logs:**")
                        for t in reversed(d.get('tx', []))[:5]:
                            st.write(f"- {t['date']} | {t['type']} | ₱{t['amt']:,} | {t['status']}")
                    st.divider()
else:
    st.error("Admin Key Required")
