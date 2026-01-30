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

# --- ၃။ Persistence Logic (Refresh လုပ်သော်လည်း Link မပျောက်စေရန်) ---
# Session State ထဲတွင် သိမ်းဆည်းခြင်း
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

# --- ၅။ Sidebar (Link များ အသေမှတ်ထားရန်) ---
st.sidebar.title(f"👋 {curr_user}")

# လက်ရှိ User အတွက် သိမ်းထားသော Link များကို ဆွဲထုတ်ခြင်း
user_links = st.session_state["user_storage"][curr_user]

with st.sidebar.expander("🛠 Software Setup (Link များသိမ်းရန်)", expanded=False):
    # value နေရာတွင် user_links မှ တန်ဖိုးကို ထည့်ထားသဖြင့် Refresh လုပ်သော်လည်း မပျောက်ပါ
    in_sheet = st.text_input("Google Sheet URL", value=user_links["sheet"], key=f"sheet_{curr_user}")
    in_script = st.text_input("Apps Script URL", value=user_links["script"], key=f"script_{curr_user}")
    
    if st.button("✅ Save Links Permanently"):
        st.session_state["user_storage"][curr_user]["sheet"] = in_sheet
        st.session_state["user_storage"][curr_user]["script"] = in_script
        st.success("လင့်ခ်များကို မှတ်သားပြီးပါပြီ။")
        time.sleep(1)
        st.rerun()

sheet_url = user_links["sheet"]
script_url = user_links["script"]

# ပေါက်ဂဏန်းစစ်ရန်နှင့် ဇ (အဆ) သတ်မှတ်ရန်
st.sidebar.divider()
win_num = st.sidebar.text_input("🎰 ပေါက်ဂဏန်းစစ်", max_chars=2)
za_rate = st.sidebar.number_input("💰 ဇ (အဆ) ထည့်", value=80)

if st.sidebar.button("🚪 Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

if not sheet_url or not script_url:
    st.warning("💡 ဘယ်ဘက် Sidebar ရှိ Setup တွင် Link များကို အရင်သိမ်းပေးပါ။")
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
except Exception as e:
    st.error("❌ ဒေတာဆွဲမရပါ။ Link ပြန်စစ်ပါ။")
    st.stop()

# --- ၇။ Main Dashboard ---
st.title(f"💰 {curr_user}'s 2D Dashboard")
total_in = df['Amount'].sum() if not df.empty else 0
st.metric("စုစုပေါင်းရောင်းရငွေ", f"{total_in:,.0f} Ks")

# စာရင်းအသစ်သွင်းခြင်း (မြန်မာစံတော်ချိန် အလိုအလျောက်ပါဝင်သည်)
with st.expander("📝 စာရင်းအသစ်သွင်းရန်"):
    with st.form("entry_form", clear_on_submit=True):
        name = st.text_input("ထိုးသူအမည်")
        num = st.text_input("ထိုးမည်ဂဏန်း", max_chars=2)
        amt = st.number_input("ပိုက်ဆံပမာဏ", min_value=100, step=100)
        if st.form_submit_button("✅ သိမ်းဆည်းမည်"):
            if name and num:
                mm_time = datetime.now(timezone(timedelta(hours=6, minutes=30))).strftime("%I:%M %p")
                try:
                    requests.post(script_url, json={"action": "insert", "Customer": name, "Number": str(num).zfill(2), "Amount": int(amt), "Time": mm_time})
                    st.success("သွင်းပြီးပါပြီ။")
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error("❌ ပေးပို့မှု မအောင်မြင်ပါ။")

# --- ၈။ အရောင်းဇယားနှင့် နာမည်စစ်ဆေးခြင်း ---
st.divider()
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("📊 အရောင်းဇယား")
    search = st.text_input("🔎 နာမည်စစ်ရန် (ရှာရန်)")
    view_df = df[df['Customer'].str.contains(search, case=False, na=False)] if search else df
    st.dataframe(view_df, use_container_width=True, hide_index=True)

with c2:
    if win_num:
        st.subheader("🏆 ပေါက်သူများ")
        winners = df[df['Number'] == win_num].copy()
        if not winners.empty:
            winners['Prize'] = winners['Amount'] * za_rate
            st.table(winners[['Customer', 'Amount', 'Prize']])
            st.error(f"စုစုပေါင်းလျော်ကြေး: {winners['Prize'].sum():,.0f} Ks")
        else:
            st.info("ပေါက်သူမရှိပါ။")

# --- ၉။ ပြင်ဆင်ခြင်းနှင့် အကုန်ဖျက်ခြင်း ---
st.divider()
col_edit, col_clear = st.columns([2, 1])

with col_edit:
    st.subheader("⚙️ တစ်ခုချင်းစီ ပြင်ဆင်ရန် (မဖျက်ပါ)")
    if not df.empty:
        for i, row in df.iterrows():
            with st.expander(f"👤 {row['Customer']} | 🔢 {row['Number']}"):
                with st.form(f"edit_{i}"):
                    u_name = st.text_input("အမည်", value=row['Customer'])
                    u_num = st.text_input("ဂဏန်း", value=row['Number'], max_chars=2)
                    u_amt = st.number_input("ပမာဏ", value=int(row['Amount']))
                    if st.form_submit_button("💾 ပြင်ဆင်မှုသိမ်းမည်"):
                        try:
                            requests.post(script_url, json={
                                "action": "update", "row_index": int(i)+2,
                                "Customer": u_name, "Number": str(u_num).zfill(2), "Amount": int(u_amt)
                            })
                            st.success("ပြင်ဆင်ပြီးပါပြီ။")
                            time.sleep(0.5)
                            st.rerun()
                        except:
                            st.error("❌ ပြင်မရပါ။")

with col_clear:
    st.subheader("⚠️ အကုန်ဖျက်ရန်")
    if st.button("🔥 စာရင်းအားလုံးဖျက်မည်", use_container_width=True):
        try:
            requests.post(script_url, json={"action": "clear_all"})
            st.warning("အကုန်ဖျက်ပြီးပါပြီ။")
            time.sleep(1)
            st.rerun()
        except:
            st.error("❌ ဖျက်မရပါ။ လင့်ခ်များကို ပြန်စစ်ပါ။")
