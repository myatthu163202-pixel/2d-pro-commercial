import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time
import re

# --- ၁။ Page Setup ---
st.set_page_config(page_title="2D Agent Pro", layout="wide", page_icon="💰")

# --- ၂။ User Database (အကောင့်များခွဲထားခြင်း) ---
USERS = {
    "admin": "123456",
    "thiri": "163202"
}

# --- ၃။ Storage (Refresh လုပ်လည်း Link သိမ်းထားရန်) ---
if "user_storage" not in st.session_state:
    st.session_state["user_storage"] = {u: {"sheet": "", "script": ""} for u in USERS}

# --- ၄။ Login စနစ် ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>🔐 Member Login</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("Login", use_container_width=True):
            if u in USERS and USERS[u] == p:
                st.session_state["logged_in"] = True
                st.session_state["username"] = u
                st.rerun()
            else:
                st.error("❌ Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
    st.stop()

curr_user = st.session_state["username"]
user_links = st.session_state["user_storage"][curr_user]

# --- ၅။ Sidebar (Software Setup) ---
st.sidebar.title(f"👋 {curr_user}")
with st.sidebar.expander("🛠 Software Setup", expanded=False):
    # သိမ်းထားတဲ့ Link တွေကို ပြန်ပြပေးခြင်း (Refresh လုပ်လည်း မပျောက်ပါ)
    in_sheet = st.text_input("Google Sheet URL", value=user_links["sheet"])
    in_script = st.text_input("Apps Script URL", value=user_links["script"])
    if st.button("✅ Save Links"):
        st.session_state["user_storage"][curr_user]["sheet"] = in_sheet
        st.session_state["user_storage"][curr_user]["script"] = in_script
        st.success("လင့်ခ်များ သိမ်းဆည်းပြီးပါပြီ။")
        time.sleep(1)
        st.rerun()

sheet_url = user_links["sheet"]
script_url = user_links["script"]

# ပေါက်ဂဏန်းစစ်ရန် Sidebar Settings
st.sidebar.divider()
win_num = st.sidebar.text_input("🎰 ပေါက်ဂဏန်း", max_chars=2)
za_rate = st.sidebar.number_input("💰 ဇ (အဆ)", value=80)

if st.sidebar.button("🚪 Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

if not sheet_url or not script_url:
    st.warning("💡 Setup တွင် Link များကို အရင်ထည့်ပေးပါ။")
    st.stop()

# --- ၆။ Data Loading ---
def get_csv_url(url):
    m = re.search(r"/d/([^/]*)", url)
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv" if m else None

try:
    csv_url = get_csv_url(sheet_url)
    df = pd.read_csv(f"{csv_url}&cachebuster={int(time.time())}")
    # image_65826f.png နှင့် image_6514b3.png ပါ Syntax Error များကို ဤနေရာတွင် စနစ်တကျ ပြင်ဆင်ထားသည်
    df.columns = df.columns.str.strip()
    df['Number'] = df['Number'].astype(str).str.zfill(2)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
except Exception:
    st.error("❌ ဒေတာဆွဲမရပါ။ URL ပြန်စစ်ပါ။")
    st.stop()

# --- ၇။ Dashboard Layout ---
st.title(f"💰 {curr_user}'s 2D Agent Pro")
total_in = df['Amount'].sum() if not df.empty else 0
st.metric("စုစုပေါင်းရောင်းရငွေ", f"{total_in:,.0f} Ks")

# စာရင်းသွင်းရန်
with st
