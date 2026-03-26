import streamlit as st

# Helper to force Uppercase
def to_upper(text):
    return text.upper() if text else ""

st.set_page_config(page_title="Bagong Pilipinas Registration", page_icon="🇵🇭")

# Custom Styling
st.markdown("""
    <style>
    .stTextInput input { text-transform: uppercase; }
    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        background-color: #1d4ed8;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = "signup"

# --- SIGN UP PAGE ---
if st.session_state.page == "signup":
    st.markdown("<h2 style='text-align: center;'>📝 ACCOUNT REGISTRATION</h2>", unsafe_allow_html=True)
    st.info("NOTE: ALL FIELDS WILL BE AUTOMATICALLY SAVED IN ALL-CAPS")

    with st.form("registration_form"):
        # Personal Info
        full_name = st.text_input("FULL NAME").upper()
        age = st.number_input("AGE", min_value=18, max_value=100)
        country = st.text_input("COUNTRY", value="PHILIPPINES", disabled=True)

        # Location Dropdowns
        region = st.selectbox("REGION", [
            "REGION I (Ilocos Region)", "REGION II (Cagayan Valley)", "REGION III (Central Luzon)",
            "REGION IV-A (CALABARZON)", "MIMAROPA REGION", "REGION V (Bicol Region)",
            "REGION VI (Western Visayas)", "REGION VII (Central Visayas)", "REGION VIII (Eastern Visayas)",
            "REGION IX (Zamboanga Peninsula)", "REGION X (Northern Mindanao)", "REGION XI (Davao Region)",
            "REGION XII (SOCCSKSARGEN)", "REGION XIII (Caraga)", "NCR (National Capital Region)", "CAR", "BARMM"
        ])
        
        city = st.text_input("CITY / MUNICIPALITY").upper()
        barangay = st.text_input("BARANGAY").upper()
        
        email = st.text_input("EMAIL ADDRESS (FOR 6-DIGIT CODE)")
        password = st.text_input("CREATE PASSWORD", type="password")

        submit = st.form_submit_button("REGISTER & SEND CODE")

        if submit:
            if not full_name or not city or not barangay or not email:
                st.error("PLEASE FILL UP ALL FIELDS")
            else:
                st.session_state.user_data = {
                    "name": full_name,
                    "location": f"{barangay}, {city}, {region}"
                }
                st.success("REGISTRATION DATA SAVED. REDIRECTING TO VERIFICATION...")
                st.session_state.page = "verify"
                st.rerun()

# --- VERIFICATION PAGE ---
elif st.session_state.page == "verify":
    st.title("🔐 VERIFY EMAIL")
    st.write(f"A CODE WAS SENT TO YOUR EMAIL.")
    otp = st.text_input("ENTER 6-DIGIT CODE", max_chars=6)
    
    if st.button("CONFIRM"):
        # For now, we allow any 6 digits to proceed
        if len(otp) == 6:
            st.session_state.page = "dashboard"
            st.rerun()
        else:
            st.error("INVALID CODE")

# --- DASHBOARD ---
elif st.session_state.page == "dashboard":
    st.success(f"WELCOME TO THE MARKET, {st.session_state.user_data['name']}!")
    st.write(f"LOCATION: {st.session_state.user_data['location']}")
    if st.button("LOGOUT"):
        st.session_state.page = "signup"
        st.rerun()
        
