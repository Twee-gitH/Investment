import streamlit as st
import time
from datetime import datetime, timedelta

# --- 1. SETTINGS & THEME ---
st.set_page_config(page_title="BP Market", page_icon="🇵🇭")

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
        font-size: 2.2em
        
