import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time
import re

# --- ၁။ Page အပြင်အဆင် ---
st.set_page_config(page_title="2D Agent Pro", layout="wide", page_icon="💰")

# --- ၂။ VIP User စာရင်း (ဒီမှာ အကောင့်တွေ ထပ်တိုးနိုင်တယ်) ---
USERS = {
    "admin": "123456",
    "thiri": "163202"
}

# --- ၃။ User တစ်ယောက်ချင်းစီအတွက် သီးသန့် Link သိမ်းမည့်စနစ် ---
# လူတိုင်းအတွက် သီးသန့် memory ခွဲပေးလိုက်တာမို့ တစ်ယောက်နဲ့တစ်ယောက် လင့်ခ်မရောတော့ပါ
if "user_storage" not in st.session_state:
    st.session_state["user_storage"] = {}

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
                    # User login ဝင်တာနဲ့ သူ့အတွက် သီးသန့် memory အခန်းလေး ဖွင့်ပေးလိုက်မယ်
                    if u not in st.session_state["user_storage"]:
                        st.session_state["user_storage"][u] = {"sheet": "", "script": ""}
                    st.rerun()
                else:
                    st.error("❌ Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
        return False
    return True

if check_password():
    curr_user = st.session_state["username"]
    # လက်ရှိ User ရဲ့ သီးသန့် လင့်ခ်များကို ဆွဲထုတ်ခြင်း
    user_links = st.session_state["user_storage"][curr_user]

    # --- Sidebar Section ---
    st.sidebar.title(f"👋 မင်္ဂလာပါ {curr_user}")
    
    with st.sidebar.expander("🛠 Software Setup (Link ပြောင်းရန်)", expanded=True):
        in_sheet = st.text_input("Google Sheet URL", value=user_links["sheet"])
        in_script = st.text_input("Apps Script URL", value=user_links["script"])
        
        if st.button("✅ Link များမှတ်ထားမည်"):
            # မိမိရဲ့ သီးသန့်အခန်းထဲမှာပဲ သိမ်းဆည်းခြင်း
            st.session_state["user_storage"][curr_user]["sheet"] = in_sheet
            st.session_state["user_storage"][curr_user]["script"] = in_script
            st.success(f"{curr_user} အတွက် လင့်ခ်များကို မှတ်သားပြီးပါပြီ။")
            st.rerun()

    sheet_url = user_links["sheet"]
    script_url = user_links["script"]

    if not sheet_url or not script_url:
        st.warning("💡 Setup တွင် သင့်ကိုယ်ပိုင် Link များကို အရင်ထည့်ပေးပါ။")
        st.stop()

    # --- မင်းကြိုက်တဲ့ ကျန်တဲ့ Code အပိုင်းတွေ (Dashboard, Insert, Delete) ---
    # (ဒီအောက်ကအပိုင်းတွေကို မင်းမူလအတိုင်း ဘာမှမပြောင်းဘဲ ဆက်လက်လုပ်ဆောင်ပါလိမ့်မယ်)
    
    def get_csv_url(url):
        m = re.search(r"/d/([^/]*)", url)
        return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv" if m else None

    csv_url = get_csv_url(sheet_url)

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
        st.error("❌ ချိတ်ဆက်မှု မှားယွင်းနေပါသည်။")
        st.stop()

    st.title("💰 2D Agent Pro Dashboard")
    
    # ... (ကျန်တဲ့ Insert, View Table, Delete အပိုင်းတွေက မင်းကြိုက်တဲ့အတိုင်း အလုပ်လုပ်နေပါမယ်)
    st.sidebar.header("⚙️ Admin Settings")
    win_num = st.sidebar.text_input("🎰 ပေါက်ဂဏန်း", max_chars=2)
    za_rate = st.sidebar.number_input("💰 ဇ (အဆ)", value=80)
    
    if st.sidebar.button("🚪 Log out"):
        st.session_state["logged_in"] = False
        st.rerun()
        
    total_in = df['Amount'].sum() if not df.empty else 0
    st.success(f"💵 စုစုပေါင်းရောင်းရငွေ: {total_in:,.0f} Ks")
    
    # (မှတ်ချက် - ရှေ့က ကုဒ်အတိုင်း Insert form နဲ့ Table တွေ ဆက်လက်ပါရှိပါမယ်)
