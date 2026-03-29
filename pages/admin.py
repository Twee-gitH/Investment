# --- 6. THE HIDDEN BOSS PANEL ---
st.divider()
with st.expander("⚠️"):
    # This is where you enter 'Orange01!'
    boss_input = st.text_input("Key", type="password", label_visibility="collapsed")
    if st.button("ENTER"):
        if boss_input == "Orange01!":
            st.session_state.is_boss = True
            st.rerun()

if st.session_state.get("is_boss"):
    st.divider()
    all_users = load_registry()
    total_val = sum(u.get('wallet', 0.0) for u in all_users.values())
    st.metric("💰 TOTAL SYSTEM ASSETS", f"₱{total_val:,.2f}")

    # THE MASTER TOGGLE BUTTON
    if "show_controls" not in st.session_state:
        st.session_state.show_controls = False

    btn_label = "🔒 CLOSE CONTROL CENTER" if st.session_state.show_controls else "🔓 OPEN CONTROL CENTER"
    if st.button(btn_label):
        st.session_state.show_controls = not st.session_state.show_controls
        st.rerun()

    if st.session_state.show_controls:
        # 1. PENDING APPROVALS
        st.markdown("<div class='section-header'>🔔 PENDING APPROVALS</div>", unsafe_allow_html=True)
        for un, ud in all_users.items():
            for i, tx in enumerate(ud.get('tx', [])):
                if tx['type'] == 'DEP' and tx['status'] == 'PENDING':
                    st.info(f"{un}: ₱{tx['amt']:,}")
                    if st.button(f"Approve {un}", key=f"a_{un}_{i}"):
                        all_users[un]['wallet'] += tx['amt']
                        all_users[un]['tx'][i]['status'] = 'APPROVED'
                        with open(REGISTRY_FILE, "w") as f: json.dump(all_users, f, default=str)
                        st.rerun()

        # 2. MANUAL ADJUSTMENT (The 500-50k dropdown)
        st.markdown("<div class='section-header'>🛠️ MANUAL ADJUSTMENT</div>", unsafe_allow_html=True)
        target = st.selectbox("Investor", list(all_users.keys()))
        mod_amt = st.selectbox("Amount PHP", options=[500, 1000, 5000, 10000, 50000])
        if st.button(f"CONFIRM: ADD ₱{mod_amt:,}"):
            all_users[target]['wallet'] += mod_amt
            all_users[target].setdefault('tx', []).append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "type": "ADMIN_ADJ", "amt": mod_amt, "status": "COMPLETED"
            })
            with open(REGISTRY_FILE, "w") as f: json.dump(all_users, f, default=str)
            st.success("Balance Updated!"); st.rerun()

        # 3. SYSTEM BROADCAST & MAINT
        st.markdown("<div class='section-header'>📢 BROADCAST & FEES</div>", unsafe_allow_html=True)
        m_state = st.toggle("MAINTENANCE MODE", value=is_maintenance_on())
        fee_val = st.number_input("WD Fee %", value=get_wd_fee(), step=0.5)
        if st.button("SAVE SYSTEM STATE"):
            set_maintenance(m_state); set_wd_fee(fee_val); st.success("Updated")
        
        new_msg = st.text_area("Market Update:", value=get_status_msg())
        if st.button("PUSH BROADCAST"):
            set_status_msg(new_msg); st.rerun()

        # 4. DATABASE BACKUP
        st.markdown("<div class='section-header'>💾 DATABASE BACKUP</div>", unsafe_allow_html=True)
        df = pd.DataFrame.from_dict(all_users, orient='index')
        st.download_button("📥 DOWNLOAD CSV", df.to_csv().encode('utf-8'), "BPSM_Backup.csv", "text/csv")

    st.write("<br>", unsafe_allow_html=True)
    if st.button("🔴 LOGOUT BOSS"):
        st.session_state.is_boss = False
        st.session_state.show_controls = False
        st.rerun()

time.sleep(1)
st.rerun()
