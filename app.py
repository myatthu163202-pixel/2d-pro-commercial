import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time
import re

# --- ၁။ Page အပြင်အဆင် ---
st.set_page_config(page_title="2D Agent Pro (Secure)", layout="wide", page_icon="💰")

# --- ၂။ VIP User စာရင်း ---
USERS = {
    "admin": "123456"
}

# --- ၃။ လင့်ခ်များကို ဤနေရာတွင် အသေထည့်ပါ ---
# အောက်က မျက်တောင်ဖွင့်ပိတ်ထဲမှာ မင်းရဲ့လင့်ခ်အစစ်တွေကို ထည့်လိုက်ရင် တစ်သက်လုံး ထပ်ထည့်စရာမလိုတော့ဘူး
DEFAULT_SHEET_URL = "YOUR_SHEET_URL" 
DEFAULT_SCRIPT_URL = "YOUR_SCRIPT_URL"

# --- ၄။ Login စနစ် ---
def check_password():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        st.markdown("<h2 style='text-align: center;'>🔐 Member Login</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            user = st.text_input("Username", key="login_user")
            pw = st.text_input("Password", type="password", key="login_pw")
            if st.button("Login", use_container_width=True):
                if user in USERS and USERS[user] == pw:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = user
                    st.rerun()
                else:
                    st.error("❌ Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
        return False
    return True

if check_password():
    # --- Sidebar Section ---
    st.sidebar.title(f"👋 မင်္ဂလာပါ {st.session_state['username']}")
    
    # Setup ကို Expander ထဲမှာ အမြဲမှတ်မိနေအောင် လုပ်ထားတယ်
    with st.sidebar.expander("🛠 Software Setup (Link များ)", expanded=False):
        user_sheet_url = st.text_input("Google Sheet URL", value=DEFAULT_SHEET_URL)
        user_script_url = st.text_input("Apps Script URL", value=DEFAULT_SCRIPT_URL)

    # လင့်ခ်မထည့်ရသေးရင် Error ပြပေးမယ်
    if not user_sheet_url or not user_script_url or user_sheet_url == "YOUR_SHEET_URL":
        st.warning("⚠️ GitHub ကုဒ်ထဲတွင် လင့်ခ်များကို အရင်ဆုံး အစားထိုးထည့်ပေးပါ။")
        st.stop()

    # URL မှ ID ကိုယူသည့် Function
    def get_csv_url(url):
        sheet_id_match = re.search(r"/d/([^/]*)", url)
        if sheet_id_match:
            sheet_id = sheet_id_match.group(1)
            return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        return None

    csv_clean_url = get_csv_url(user_sheet_url)

    # ဒေတာဆွဲယူခြင်း
    try:
        def load_data():
