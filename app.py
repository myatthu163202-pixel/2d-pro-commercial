import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time
import re

# --- ၁။ Page Setup ---
st.set_page_config(page_title="2D Agent Pro", layout="wide", page_icon="💰")

# --- ၂။ Link Persistence (Refresh ခံနိုင်ရည်ရှိရန်) ---
@st.cache_resource
def get_link_db():
    return {"admin": {"sheet": "", "script": ""}, "thiri": {"sheet": "", "script": ""}}

permanent_db = get_link_db()

# --- ၃။ User Database ---
USERS = {"admin": "123456", "thiri": "163202"}

# --- ၄။ Login စနစ် ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>🔐 Member Login</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        if st.button("Login", use_container_width=True):
            if u in USERS and USERS[u] == p:
                st.session_state["logged_in"] = True
                st.session_state["username"] = u
                st.rerun()
            else:
                st.error("❌ Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
    st.stop()

curr_user = st.session_state["username"]
saved_links = permanent_db[curr_user]

# --- ၅။ Sidebar (Link များ သိမ်းဆည်းခြင်း) ---
st.sidebar.title(f"👋 {curr_user}")
with st.sidebar.expander("🛠 Software Setup", expanded=(not saved_links["sheet"])):
    in_sheet = st.text_input("Google Sheet URL", value=saved_links["sheet"])
    in_script = st.text_input("Apps Script URL", value=saved_links["script"])
    if st.button("✅ Save Links Permanently"):
        permanent_db[curr_user]["sheet"] = in_sheet
        permanent_db[curr_user]["script"] = in_script
        st.success("လင့်ခ်များကို မှတ်သားပြီးပါပြီ။")
        time.sleep(1)
        st.rerun()

sheet_url = permanent_db[curr_user]["sheet"]
script_url = permanent_db[curr_user]["script"]

st.sidebar.divider()
win_num = st.sidebar.text_input("🎰 ပေါက်ဂဏန်းစစ်", max_chars=2)
za_rate = st.sidebar.number_input("💰 ဇ (အဆ) ထည့်", value=80)

if st.sidebar.button("🚪 Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

# Syntax Error fix (expected ':')
if not sheet_url or not script_url:
    st.warning("💡 Sidebar ရှိ Setup တွင် Link များကို အရင်သိမ်းပေးပါ။")
    st.stop()

# --- ၆။ Data Loading (ဇယားမှာ အသစ်ပေါ်အောင် အတင်းဆွဲခိုင်းခြင်း) ---
def get_csv_url(url):
    m = re.search(r"/d/([^/]*)", url)
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv" if m else None

try:
    csv_url = get_csv_url(sheet_url)
    # cachebuster သုံးပြီး Update ဖြစ်ထားတဲ့ ဒေတာအသစ်ကို အတင်းဆွဲယူခိုင်းခြင်း
    df = pd.read_csv(f"{csv_url}&cachebuster={int(time.time())}")
    df.columns = df.columns.str.strip()
    df['Number'] = df['Number'].astype(str).str.zfill(2)
    df['Amount'] = pd.to_numeric(df['Amount'], errors
