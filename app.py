import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time
import re

# --- ၁။ Page အပြင်အဆင် ---
st.set_page_config(page_title="2D Agent Pro", layout="wide", page_icon="💰")

# --- ၂။ VIP User စာရင်း ---
USERS = {
    "admin": "123456",
    "thiri": "163202"
}

# --- ၃။ User တစ်ယောက်ချင်းစီအတွက် Link Storage ---
# KeyError မတက်အောင် ဤနေရာတွင် ကြိုတင်သတ်မှတ်ထားသည်
if "user_storage" not in st.session_state:
    st.session_state["user_storage"] = {u: {"sheet": "", "script": ""} for u in USERS}

# --- ၄။ Login စနစ် ---
def check_password():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if not st.session_state["logged_in"]:
        st.markdown("<h2 style='text-align: center;'>🔐 Member Login</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            u = st.text_input("Username", key="l_user")
            p = st.text_input("Password", type="password", key="l_pw")
            if st.button("Login", use_container_width=True):
                if u in USERS and USERS[u] == p:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = u
                    st.rerun()
                else:
                    st.error("❌ Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
        return False
    return True

if check_password():
    curr_user = st.session_state["username"]
    user_links = st.session_state["user_storage"][curr_user] #

    # --- Sidebar Section ---
    st.sidebar.title(f"👋 မင်္ဂလာပါ {curr_user}")
    
    with st.sidebar.expander("🛠 Software Setup (Link ပြောင်းရန်)", expanded=True):
        in_sheet = st.text_input("Google Sheet URL", value=user_links["sheet"])
        in_script = st.text_input("Apps Script URL", value=user_links["script"])
        
        if st.button("✅ Link များမှတ်ထားမည်"):
            st.session_state["user_storage"][curr_user]["sheet"] = in_sheet
            st.session_state["user_storage"][curr_user]["script"] = in_script
            st.success("လင့်ခ်များကို မှတ်သားပြီးပါပြီ။")
            time.sleep(1)
            st.rerun()

    sheet_url = user_links["sheet"]
    script_url = user_links["script"]

    if not sheet_url or not script_url:
        st.warning("💡 အပေါ်က Setup တွင် သင့်ကိုယ်ပိုင် Link များကို အရင်ထည့်ပေးပါ။")
        st.stop()

    def get_csv_url(url):
        m = re.search(r"/d/([^/]*)", url)
        return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv" if m else None

    csv_url = get_csv_url(sheet_url)

    # ဒေတာဆွဲယူခြင်း
    try:
        def load_data():
            url = f"{csv_url}&cachebuster={int(
