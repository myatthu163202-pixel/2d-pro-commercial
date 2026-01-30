import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time
import re

# --- ၁။ Page အပြင်အဆင် ---
st.set_page_config(page_title="2D Agent Pro (Secure)", layout="wide", page_icon="💰")

# --- ၂။ VIP User စာရင်း ---
USERS = {"admin": "123456"}

# --- ၃။ Link များကို Refresh လုပ်လည်း မှတ်မိနေစေမည့် စနစ် ---
if "user_links" not in st.session_state:
    st.session_state["user_links"] = {"sheet": "", "script": ""}

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
    
    # 🛠 Software Setup (ဒီနေရာမှာ ရိုက်ထည့်တာကို မှတ်ထားပေးမှာပါ)
    with st.sidebar.expander("🛠 Software Setup (Link များ)", expanded=True):
        input_sheet = st.text_input("Google Sheet URL", value=st.session_state["user_links"]["sheet"])
        input_script = st.text_input("Apps Script URL", value=st.session_state["user_links"]["script"])
        
        if st.button("✅ Link များသိမ်းမည်"):
            st.session_state["user_links"]["sheet"] = input_sheet
            st.session_state["user_links"]["script"] = input_script
            st.success("မှတ်သားပြီးပါပြီ။")
            st.rerun()

    sheet_url = st.session_state["user_links"]["sheet"]
    script_url = st.session_state["user_links"]["script"]

    if not sheet_url or not script_url:
        st.info("💡 ပထမဆုံးအကြိမ်အဖြစ် Link များကို တစ်ခါပဲ ထည့်ပေးပါ။")
        st.stop()

    def get_csv_url(url):
        match = re.search(r"/d/([^/]*)", url)
        return f"https://docs.google.com/spreadsheets/d/{match.group(1)}/export?format=csv" if match else None

    csv_url = get_csv_url(sheet_url)

    # ဒေတာဆွဲယူခြင်း
    try:
        def load_data():
            url = f"{csv_url}&cachebuster={int(time.time())}"
            data = pd.read_csv(url)
            if not data.empty:
                data.columns = data.columns.str.strip()
                data['Number'] = data['Number'].astype(str).str.zfill(2)
                data['Amount'] = pd.to_numeric(data['Amount'], errors='coerce').fillna(0)
            return data
        df = load_data()
    except:
        st.error("❌ Link ချိတ်ဆက်မှု မှားယွင်းနေပါသည်။")
        st.stop()

    # --- ၅။ Dashboard (မင်းကြိုက်တဲ့ပုံစံအတိုင်း) ---
    st.title("💰 2D Agent Pro Dashboard")
    
    st.sidebar.header("⚙️ Admin Settings")
    win_num = st.sidebar.text_input("🎰
