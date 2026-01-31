import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time
import re

# --- ၁။ Page Setup ---
st.set_page_config(page_title="2D Agent Pro", layout="wide", page_icon="💰")

# --- ၂။ Link Persistence (Refresh လုပ်လည်း မပျောက်စေရန်) ---
@st.cache_resource
def get_user_storage():
    # admin နှင့် thiri အတွက် သီးခြား sheet သိမ်းရန် နေရာ
    return {
        "admin": {"sheet": "", "script": ""},
        "thiri": {"sheet": "", "script": ""}
    }

user_db = get_user_storage()

# --- ၃။ Login စနစ် ---
USERS = {"admin": "123456", "thiri": "163202"}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>🔐 Member Login</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if u in USERS and USERS[u] == p:
                st.session_state["logged_in"] = True
                st.session_state["username"] = u
                st.rerun()
            else:
                st.error("❌ Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
    st.stop()

curr_user = st.session_state["username"]

# --- ၄။ Sidebar (Settings & Tools) ---
st.sidebar.title(f"👋 {curr_user}")

with st.sidebar.expander("🛠 Software Setup", expanded=(not user_db[curr_user]["sheet"])):
    in_sheet = st.text_input("Google Sheet URL", value=user_db[curr_user]["sheet"])
    in_script = st.text_input("Apps Script URL", value=user_db[curr_user]["script"])
    if st.button("✅ Save Links Permanently"):
        user_db[curr_user]["sheet"] = in_sheet
        user_db[curr_user]["script"] = in_script
        st.success("လင့်ခ်များကို မှတ်သားပြီးပါပြီ။")
        time.sleep(1)
        st.rerun()

sheet_url = user_db[curr_user]["sheet"]
script_url = user_db[curr_user]["script"]

st.sidebar.divider()
win_num = st.sidebar.text_input("🎰 ပေါက်ဂဏန်းစစ်", max_chars=2)
za_rate = st.sidebar.number_input("💰 ဇ (အဆ) ထည့်", value=80)

if st.sidebar.button("🚪 Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

if not sheet_url or not script_url:
    st.warning("💡 Sidebar ရှိ Setup တွင် Link များကို အရင်ထည့်ပေးပါ။")
    st.stop()

# --- ၅။ Data Loading (Cache Buster သုံးထားသည်) ---
def get_csv_url(url):
    m = re.search(r"/d/([^/]*)", url)
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv" if m else
