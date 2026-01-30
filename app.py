import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time
import re

# --- ၁။ Page Setup ---
st.set_page_config(page_title="2D Agent Pro", layout="wide", page_icon="💰")

# --- ၂။ User Database ---
USERS = {"admin": "123456", "thiri": "163202"}

# --- ၃။ Storage (Refresh လုပ်လည်း Link မပျောက်အောင်) ---
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

# --- ၅။ Sidebar (Link များသိမ်းရန်) ---
st.sidebar.title(f"👋 {curr_user}")
with st.sidebar.expander("🛠 Software Setup", expanded=False):
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

# Sidebar Settings
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
    df.columns = df.columns.str.strip()
    df['Number'] = df['Number'].astype(str).str.zfill(2)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
except Exception:
    st.error("❌ ဒေတာဆွဲမရပါ။ URL ပြန်စစ်ပါ။")
    st.stop()

# --- ၇။ Dashboard ---
st.title(f"💰 {curr_user}'s 2D Agent Pro")
total_in = df['Amount'].sum() if not df.empty else 0
st.metric("စုစုပေါင်းရောင်းရငွေ", f"{total_in:,.0f} Ks")

# စာရင်းသွင်းရန်
with st.expander("📝 စာရင်းအသစ်သွင်းရန်"):
    with st.form("entry_form", clear_on_submit=True):
        name = st.text_input("နာမည်")
        num = st.text_input("ဂဏန်း", max_chars=2)
        amt = st.number_input("ငွေပမာဏ", min_value=100, step=100)
        if st.form_submit_button("✅ သိမ်းဆည်းမည်"):
            if name and num:
                now = datetime.now(timezone(timedelta(hours=6, minutes=30))).strftime("%I:%M %p")
                requests.post(script_url, json={"action": "insert", "Customer": name, "Number": str(num).zfill(2), "Amount": int(amt), "Time": now})
                st.success("သွင်းပြီးပါပြီ။")
                time.sleep(1)
                st.rerun()

# --- ၈။ ဇယားနှင့် ပေါက်ဂဏန်းစစ်ဆေးခြင်း ---
st.divider()
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("📊 အရောင်းဇယား")
    search = st.text_input("🔎 နာမည်ဖြင့်ရှာရန်")
    view_df = df[df['Customer'].str.contains(search, case=False, na=False)] if search else df
    st.dataframe(view_df, use_container_width=True, hide_index=True)

with c2:
    if win_num:
        st.subheader("🏆 ပေါက်သူများ")
        winners = df[df['Number'] == win_num].copy()
        if not winners.empty:
            winners['Prize'] = winners['Amount'] * za_rate
            st.table(winners[['Customer', 'Amount', 'Prize']])
            total_prize = winners['Prize'].sum()
            st.error(f"စုစုပေါင်းလျော်ကြေး: {total_prize:,.0f} Ks")
        else:
            st.info("ပေါက်သူမရှိပါ။")

# --- ၉။ တစ်ခုချင်းဖျက်ရန်နှင့် အကုန်ဖျက်ရန် ---
st.divider()
col_del_1, col_del_2 = st.columns([2, 1])

with col_del_1:
    # ပုံ 651592 ပါအတိုင်း တစ်ခုချင်းဖျက်ရန် UI
    st.subheader("🗑 စာရင်းပြုပြင်ရန် (တစ်ခုချင်းဖျက်ရန်)")
    if not df.empty:
        for i, row in df.iterrows():
            tx, bt = st.columns([4, 1])
            tx.write(f"👤 {row['Customer']} | 🔢 {row['Number']} | 💵 {int(row['Amount'])} Ks")
            
            # ခလုတ်နှိပ်လျှင် ပျက်အောင် row_index ကို +2 လုပ်ပြီးပို့သည်
            if bt.button("ဖျက်", key=f"del_{i}"):
                target_row = int(i) + 2
                try:
                    resp = requests.post(script_url, json={"action": "delete", "row_index": target_row})
                    if resp.status_code == 200:
                        st.success(f"ဖျက်ပြီးပါပြီ။")
