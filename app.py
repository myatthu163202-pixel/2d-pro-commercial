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
def get_user_db():
    # အကောင့်တစ်ခုချင်းစီအတွက် လင့်ခ်များကို သီးခြားသိမ်းဆည်းထားမည်
    return {}

user_db = get_user_db()

# --- ၃။ User Database ---
USERS = {"admin": "123456", "thiri": "163202"}

# --- ၄။ Login စနစ် ---
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
                if u not in user_db:
                    user_db[u] = {"sheet": "", "script": ""}
                st.rerun()
            else:
                st.error("❌ Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
    st.stop()

curr_user = st.session_state["username"]

# --- ၅။ Sidebar (Settings & Tools) ---
st.sidebar.title(f"👋 {curr_user}")

# Link Setup (တစ်ခါထည့်ရုံဖြင့် မှတ်ထားမည်)
with st.sidebar.expander("⚙️ Software Setup"):
    in_sheet = st.text_input("Google Sheet URL", value=user_db[curr_user]["sheet"])
    in_script = st.text_input("Apps Script URL", value=user_db[curr_user]["script"])
    if st.button("✅ Save Links Permanently"):
        user_db[curr_user]["sheet"] = in_sheet
        user_db[curr_user]["script"] = in_script
        st.success("လင့်ခ်များကို သိမ်းဆည်းပြီးပါပြီ။")
        time.sleep(1)
        st.rerun()

sheet_url = user_db[curr_user]["sheet"]
script_url = user_db[curr_user]["script"]

st.sidebar.divider()
# ပေါက်ဂဏန်းစစ်ခြင်း နှင့် ဇ (အဆ)
win_num = st.sidebar.text_input("🎰 ပေါက်ဂဏန်းစစ်", max_chars=2)
za_rate = st.sidebar.number_input("💰 ဇ (အဆ) ထည့်", value=80)

if st.sidebar.button("🚪 Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

if not sheet_url or not script_url:
    st.warning("💡 Sidebar ရှိ Setup တွင် Link များကို အရင်ထည့်ပေးပါ။")
    st.stop()

# --- ၆။ Data Loading ---
def get_csv_url(url):
    m = re.search(r"/d/([^/]*)", url)
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv" if m else None

try:
    csv_url = get_csv_url(sheet_url)
    # cachebuster သုံးပြီး Update ဖြစ်ထားတဲ့ ဒေတာအသစ်ကို အတင်းဆွဲယူခိုင်းခြင်း
    df = pd.read_csv(f"{csv_url}&cachebuster={int(time.time())}")
    df.columns = df.columns.str.strip()
    df['Number'] = df['Number'].astype(str).str.zfill(2)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
except Exception:
    st.error("❌ ဒေတာဆွဲမရပါ။ Link မှန်မမှန် ပြန်စစ်ပါ။")
    st.stop()

# --- ၇။ Main Dashboard ---
st.title(f"📊 {curr_user}'s 2D Agent Dashboard")

# ကိန်းဂဏန်းများပြသခြင်း
total_in = df['Amount'].sum() if not df.empty else 0
st.metric("စုစုပေါင်းရောင်းရငွေ", f"{total_in:,.0f} Ks")

# စာရင်းအသစ်သွင်းခြင်း
with st.expander("📝 စာရင်းအသစ်သွင်းရန်", expanded=True):
    with st.form("entry_form", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1: f_name = st.text_input("ထိုးသူအမည်")
        with col_f2: f_num = st.text_input("ထိုးမည်ဂဏန်း", max_chars=2)
        with col_f3: f_amt = st.number_input("ပိုက်ဆံပမာဏ", min_value=100, step=100)
        
        if st.form_submit_button("💾 သိမ်းဆည်းမည်"):
            if f_name and f_num:
                # မြန်မာစံတော်ချိန် သတ်မှတ်ခြင်း
                mm_time = datetime.now(timezone(timedelta(hours=6, minutes=30))).strftime("%I:%M %p")
                try:
                    requests.post(script_url, json={"action": "insert", "Customer": f_name, "Number": str(f_num).zfill(2), "Amount": int(f_amt), "Time": mm_time})
                    st.success("သွင်းပြီးပါပြီ။")
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error("❌ ပေးပို့မှု Error တက်နေပါသည်။")

# --- ၈။ ပြင်ဆင်ခြင်း (တစ်ခုချင်းစီ ပြင်ဆင်ရန်) ---
st.divider()
st.subheader("⚙️ တစ်ခုချင်းစီ ပြင်ဆင်ခြင်း (ဖျက်မည်မဟုတ်ပါ)")

if not df.empty:
    for i, row in df.iterrows():
        # Sheet ထဲက Row အမှန်ကို တွက်ခြင်း (Syntax fix: int(i) ကို သေချာပိတ်သည်)
        actual_row = int(i) + 2
        with st.expander(f"👤 {row['Customer']} | 🔢 {row['Number']} | 💰 {row['Amount']} Ks"):
            with st.form(f"edit_{i}"):
                e_name = st.text_input("အမည်ပြင်ရန်", value=row['Customer'])
                e_num = st.text_input("ဂဏန်းပြင်ရန်", value=row['Number'], max_chars=2)
                e_amt = st.number_input("ပမာဏပြင်ရန်", value=int(row['Amount']), step=100)
                
                if st.form_submit_button("💾 ပြင်ဆင်မှု သိမ်းမည်"):
                    try:
                        res = requests.post(script_url, json={
                            "action": "update", "row_index": actual_row,
                            "Customer": e_name, "Number": str(e_num).zfill(2), "Amount": int(e_amt)
                        })
                        if res.status_code == 200:
                            st.success("✅ ပြင်ဆင်ပြီးပါပြီ။")
                            time.sleep(2) # Sheet update ဖြစ်ချိန်ကို စောင့်ပေးခြင်း
                            st.rerun()
                    except:
                        st.error("❌ ပြင်မရပါ။")

# --- ၉။ အရောင်းဇယားနှင့် ရှာဖွေခြင်း ---
st.divider()
st.subheader("📊 အရောင်းဇယား")
search_name = st.text_input("🔎 နာမည်စစ်ရန် (နာမည်ဖြင့်ရှာရန်)")

# ဇယားထုတ်ခြင်း
display_df = df.copy()
if search_name:
    display_df = display_df[display_df['Customer'].str.contains(search_name, case=False, na=False)]

# ပေါက်ဂဏန်းရှိလျှင် အရောင်ဖြင့်ပြခြင်း
if win_num:
    st.info(f"🎰 ပေါက်ဂဏန်း {win_num} ၏ ရလဒ်များ")
    winners = display_df[display_df['Number'] == win_num].copy()
    if not winners.empty:
        winners['Payout'] = winners['Amount'] * za_rate
        st.dataframe(winners, use_container_width=True)
    else:
        st.write("ပေါက်သူမရှိပါ။")

st.write("📖 စာရင်းအားလုံး")
st.dataframe(display_df, use_container_width=True, hide_index=True)

# အကုန်ဖျက်ရန်
st.divider()
if st.button("🔥 စာရင်းအားလုံးကို အကုန်ဖျက်မည်"):
    try:
        requests.post(script_url, json={"action": "clear_all"})
        st.warning("စာရင်းအားလုံးကို ဖျက်လိုက်ပါပြီ။")
        time.sleep(2)
        st.rerun()
    except:
        st.error("❌ ဖျက်မရပါ။")
