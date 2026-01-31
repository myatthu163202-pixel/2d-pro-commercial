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
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv" if m else None

try:
    csv_url = get_csv_url(sheet_url)
    # cachebuster ဖြင့် ဒေတာအသစ်ကို အမြဲဆွဲယူသည်
    df = pd.read_csv(f"{csv_url}&cachebuster={int(time.time())}")
    df.columns = df.columns.str.strip()
    df['Number'] = df['Number'].astype(str).str.zfill(2)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
except Exception:
    st.error("❌ ဒေတာဆွဲမရပါ။ လင့်ခ်များ မှန်မမှန် ပြန်စစ်ပါ။")
    st.stop()

# --- ၆။ Main Dashboard ---
st.title(f"💰 {curr_user}'s 2D Pro Dashboard")
total_in = df['Amount'].sum() if not df.empty else 0
st.metric("စုစုပေါင်းရောင်းရငွေ", f"{total_in:,.0f} Ks")

# စာရင်းအသစ်သွင်းခြင်း (မြန်မာစံတော်ချိန်ဖြင့်)
with st.expander("📝 စာရင်းအသစ်သွင်းရန်", expanded=True):
    with st.form("entry_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1: f_name = st.text_input("ထိုးသူအမည်")
        with col2: f_num = st.text_input("ထိုးမည်ဂဏန်း", max_chars=2)
        with col3: f_amt = st.number_input("ပိုက်ဆံပမာဏ", min_value=100, step=100)
        if st.form_submit_button("✅ သိမ်းဆည်းမည်"):
            if f_name and f_num:
                # Syntax fix: မြန်မာစံတော်ချိန် ယူပုံ
                mm_tz = timezone(timedelta(hours=6, minutes=30))
                mm_time = datetime.now(mm_tz).strftime("%I:%M %p")
                try:
                    requests.post(script_url, json={
                        "action": "insert", 
                        "Customer": f_name, 
                        "Number": str(f_num).zfill(2), 
                        "Amount": int(f_amt), 
                        "Time": mm_time
                    })
                    st.success("သွင်းပြီးပါပြီ။")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    # Syntax fix: brackets and quotes
                    st.error(f"❌ ပေးပို့မှု Error - {str(e)}")

# --- ၇။ ပြင်ဆင်ခြင်း (တစ်ခုချင်းစီ ပြန်ပြင်ရန် - မှားသွားလျှင် ဤနေရာတွင်ပြင်ပါ) ---
st.divider()
st.subheader("⚙️ စာရင်းများ ပြန်ပြင်ရန်")

if not df.empty:
    for i, row in df.iterrows():
        # Syntax fix: int(i) bracket ပိတ်ခြင်း
        actual_row_idx = int(i) + 2
        with st.expander(f"👤 {row['Customer']} | 🔢 {row['Number']} | 💰 {row['Amount']} Ks"):
            with st.form(f"edit_{i}"):
                e_name = st.text_input("အမည်ပြင်ရန်", value=row['Customer'])
                e_num = st.text_input("ဂဏန်းပြင်ရန်", value=row['Number'], max_chars=2)
                e_amt = st.number_input("ပမာဏပြင်ရန်", value=int(row['Amount']))
                if st.form_submit_button("💾 သိမ်းဆည်းမည်"):
                    try:
                        res = requests.post(script_url, json={
                            "action": "update", 
                            "row_index": actual_row_idx, 
                            "Customer": e_name, 
                            "Number": str(e_num).zfill(2), 
                            "Amount": int(e_amt)
                        })
                        if res.status_code == 200:
                            st.success("✅ ပြင်ဆင်ပြီးပါပြီ။")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("❌ Apps Script URL ကို စစ်ဆေးပါ။")
                    except:
                        st.error("❌ ပြင်မရပါ။")

# --- ၈။ ဇယား နှင့် ရှာဖွေခြင်း (နာမည်စစ်ခြင်း) ---
st.divider()
st.subheader("📊 အရောင်းဇယား")
search_name = st.text_input("🔎 နာမည်စစ်ရန် (နာမည်ရိုက်ထည့်ပါ)")

filtered_df = df.copy()
if search_name:
    filtered_df = filtered_df[filtered_df['Customer'].str.contains(search_name, case=False, na=False)]

# ပေါက်ဂဏန်းစစ်ဆေးခြင်း နှင့် ဇ တွက်ခြင်း
if win_num:
    winners = filtered_df[filtered_df['Number'] == win_num].copy()
    if not winners.empty:
        st.success(f"🎊 ပေါက်ဂဏန်း {win_num} အတွက် ပေါက်သူများ")
        winners['လျော်ကြေး'] = winners['Amount'] * za_rate
        st.table(winners[['Customer', 'Number', 'Amount', 'လျော်ကြေး']])
    else:
        st.info("ပေါက်သူမရှိသေးပါ။")

st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# --- ၉။ စာရင်းအသစ်အတွက် အကုန်ဖျက်ခြင်း (နေ့စဉ် စာရင်းရှင်းရန်) ---
st.divider()
if st.button("🔥 စာရင်းအားလုံးကို အကုန်ဖျက်မည် (နေ့စဉ်စာရင်းရှင်းရန်)"):
    try:
        requests.post(script_url, json={"action": "clear_all"})
        st.warning("အကုန်ဖျက်ပြီးပါပြီ။ စာရင်းအသစ် ပြန်စနိုင်ပါပြီ။")
        time.sleep(2)
        st.rerun()
    except:
        st.error("❌ Error တက်သွားပါသည်။")
