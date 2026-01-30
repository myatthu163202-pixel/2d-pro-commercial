import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time
import re

# --- ၁။ Page Setup ---
st.set_page_config(page_title="2D Agent Pro", layout="wide", page_icon="💰")

# --- ၂။ User Database (အကောင့်တစ်ခုနှင့်တစ်ခု Sheet မတူအောင်ခွဲထားခြင်း) ---
USERS = {"admin": "123456", "thiri": "163202"}

# --- ၃။ Link Storage (Refresh လုပ်လည်း မပျောက်အောင် သိမ်းထားသည့်စနစ်) ---
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

# --- ၅။ Sidebar (Link တစ်ခါထည့်ရုံဖြင့် မှတ်ထားပေးမည့်စနစ်) ---
st.sidebar.title(f"👋 {curr_user}")
with st.sidebar.expander("🛠 Software Setup", expanded=False):
    # သိမ်းထားသည့် Link ရှိလျှင် အလိုအလျောက် ပြန်ဖော်ပေးခြင်း
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

# ပေါက်ဂဏန်းစစ်ရန်နှင့် ဇ (အဆ) ထည့်ရန်
st.sidebar.divider()
win_num = st.sidebar.text_input("🎰 ပေါက်ဂဏန်းစစ်", max_chars=2)
za_rate = st.sidebar.number_input("💰 ဇ (အဆ) ထည့်", value=80)

if st.sidebar.button("🚪 Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

if not sheet_url or not script_url:
    st.warning("💡 Setup တွင် Link များကို အရင်ထည့်ပေးပါ။")
    st.stop()

# --- ၆။ Data Loading (Syntax Error များအားလုံးကို ဤနေရာတွင် ရှင်းထားသည်) ---
def get_csv_url(url):
    m = re.search(r"/d/([^/]*)", url)
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv" if m else None

try:
    csv_url = get_csv_url(sheet_url)
    # image_642833.png ပါ Syntax Error ကို ဤနေရာတွင် ပြင်ထားသည်
    df = pd.read_csv(f"{csv_url}&cachebuster={int(time.time())}")
    df.columns = df.columns.str.strip()
    df['Number'] = df['Number'].astype(str).str.zfill(2)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"❌ ဒေတာဆွဲမရပါ။ Link ပြန်စစ်ပါ။ (
