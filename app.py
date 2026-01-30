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

# --- ၅။ Sidebar (Link များ အသေသိမ်းဆည်းခြင်း) ---
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

if not sheet_url or not script_url:
    st.warning("💡 Sidebar ရှိ Setup တွင် Link များကို အရင်သိမ်းပေးပါ။")
    st.stop()

# --- ၆။ Data Loading (Cache ပြဿနာ ရှင်းထားသည်) ---
def get_csv_url(url):
    m = re.search(r"/d/([^/]*)", url)
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv" if m else None

try:
    csv_url = get_csv_url(sheet_url)
    # cachebuster သုံးပြီး Update ဖြစ်ထားတဲ့ ဒေတာအသစ်ကို အတင်းဆွဲယူသည်
    df = pd.read_csv(f"{csv_url}&cachebuster={int(time.time())}")
    df.columns = df.columns.str.strip()
    df['Number'] = df['Number'].astype(str).str.zfill(2)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
except Exception:
    st.error("❌ ဒေတာဆွဲမရပါ။ Link ပြန်စစ်ပါ။")
    st.stop()

# --- ၇။ Main Dashboard ---
st.title(f"💰 {curr_user}'s 2D Agent Pro")
total_in = df['Amount'].sum() if not df.empty else 0
st.metric("စုစုပေါင်းရောင်းရငွေ", f"{total_in:,.0f} Ks")

# စာရင်းအသစ်သွင်းခြင်း
with st.expander("📝 စာရင်းအသစ်သွင်းရန်"):
    with st.form("entry_form", clear_on_submit=True):
        f_name = st.text_input("ထိုးသူအမည်")
        f_num = st.text_input("ထိုးမည်ဂဏန်း", max_chars=2)
        f_amt = st.number_input("ပိုက်ဆံပမာဏ", min_value=100, step=100)
        if st.form_submit_button("✅ သိမ်းဆည်းမည်"):
            if f_name and f_num:
                mm_time = datetime.now(timezone(timedelta(hours=6, minutes=30))).strftime("%I:%M %p")
                try:
                    requests.post(script_url, json={"action": "insert", "Customer": f_name, "Number": str(f_num).zfill(2), "Amount": int(f_amt), "Time": mm_time})
                    st.success("သွင်းပြီးပါပြီ။")
                    time.sleep(1.5)
                    st.rerun()
                except:
                    st.error("❌ ပေးပို့မှု Error တက်နေပါသည်။")

# --- ၈။ ပြင်ဆင်ခြင်းအပိုင်း (ဇယားချက်ချင်းပြောင်းရန် ၂ စက္ကန့် စောင့်ခိုင်းထားသည်) ---
st.divider()
st.subheader("⚙️ စာရင်းများ ပြင်ဆင်ရန်")
if not df.empty:
    for i, row in df.iterrows():
        with st.expander(f"👤 {row['Customer']} | 🔢 {row['Number']} | 💰 {row['Amount']}"):
            with st.form(f"edit_form_{i}"):
                e_name = st.text_input("အမည်ပြင်ရန်", value=row['Customer'])
                e_num = st.text_input("ဂဏန်းပြင်ရန်", value=row['Number'], max_chars=2)
                e_amt = st.number_input("ပမာဏပြင်ရန်", value=int(row['Amount']))
                if st.form_submit_button("💾 ပြင်ဆင်မှုသိမ်းမည်"):
                    try:
                        requests.post(script_url, json={
                            "action": "update", "row_index": int(i)+2,
                            "Customer": e_name, "Number": str(e_num).zfill(2), "Amount": int(e_amt)
                        })
                        st.success("✅ ပြင်ဆင်ပြီးပါပြီ။ ဇယားကို Update လုပ်နေသည်...")
                        time.sleep(2) # Google Sheet update ဖြစ်ချိန်ကို စောင့်ပေးခြင်း
                        st.rerun()
                    except:
                        st.error("❌ ပြင်မရပါ။ Apps Script URL ကို စစ်ဆေးပါ။")

# --- ၉။ အရောင်းဇယားနှင့် ရှာဖွေခြင်း ---
st.divider()
st.subheader("📊 အရောင်းဇယား")
search_name = st.text_input("🔎 နာမည်ဖြင့်ရှာရန်")
filtered_df = df[df['Customer'].str.contains(search_name, case=False, na=False)] if search_name else df
st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# အကုန်ဖျက်ရန်
if st.button("🔥 စာရင်းအားလုံးဖျက်မည်"):
    try:
        requests.post(script_url, json={"action": "clear_all"})
        st.warning("ဖျက်ပြီးပါပြီ။")
        time.sleep(2)
        st.rerun()
    except:
        st.error("❌ ဖျက်မရပါ။")
