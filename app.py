import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time
import re

# --- ၁။ Page Setup ---
st.set_page_config(page_title="2D Agent Pro", layout="wide", page_icon="💰")

# --- ၂။ Link Persistence (Link တွေ မပျောက်အောင် Cache လုပ်ထားခြင်း) ---
if "links" not in st.session_state:
    st.session_state["links"] = {"sheet": "", "script": ""}

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
                st.rerun()
            else:
                st.error("❌ Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
    st.stop()

# --- ၅။ Sidebar (Link များ သိမ်းဆည်းခြင်း) ---
st.sidebar.title(f"👋 {st.session_state['username']}")
with st.sidebar.expander("🛠 Software Setup"):
    in_sheet = st.text_input("Google Sheet URL", value=st.session_state["links"]["sheet"])
    in_script = st.text_input("Apps Script URL", value=st.session_state["links"]["script"])
    if st.button("✅ Save Links"):
        st.session_state["links"]["sheet"] = in_sheet
        st.session_state["links"]["script"] = in_script
        st.success("သိမ်းဆည်းပြီးပါပြီ။")
        st.rerun()

sheet_url = st.session_state["links"]["sheet"]
script_url = st.session_state["links"]["script"]

if st.sidebar.button("🚪 Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

if not sheet_url or not script_url:
    st.warning("💡 Sidebar ရှိ Setup တွင် Link များကို အရင်ထည့်ပေးပါ။")
    st.stop()

# --- ၆။ Data Loading (Cache အမှားရှင်းရန် Cachebuster သုံးခြင်း) ---
def get_csv_url(url):
    m = re.search(r"/d/([^/]*)", url)
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv" if m else None

try:
    csv_url = get_csv_url(sheet_url)
    # cachebuster ထည့်လိုက်ခြင်းဖြင့် ဒေတာအသစ်ကို အမြဲဆွဲပါမည်
    df = pd.read_csv(f"{csv_url}&cachebuster={int(time.time())}")
    df.columns = df.columns.str.strip()
    df['Number'] = df['Number'].astype(str).str.zfill(2)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
except Exception:
    st.error("❌ ဒေတာဆွဲမရပါ။ Link ပြန်စစ်ပါ။")
    st.stop()

# --- ၇။ Main Dashboard ---
st.title("📊 2D အရောင်းစာရင်း")
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

# --- ၈။ ပြင်ဆင်ခြင်း (တစ်ခုချင်းစီပြင်တာ သေချာပေါက် အလုပ်လုပ်စေရန်) ---
st.divider()
st.subheader("⚙️ စာရင်းများ ပြင်ဆင်ရန်")

if not df.empty:
    for i, row in df.iterrows():
        # Syntax Error fix: bracket သေချာပိတ်သည်
        actual_row = int(i) + 2
        with st.expander(f"👤 {row['Customer']} | 🔢 {row['Number']} | 💰 {row['Amount']} Ks"):
            with st.form(f"edit_form_{i}"):
                e_name = st.text_input("အမည်ပြင်ရန်", value=row['Customer'])
                e_num = st.text_input("ဂဏန်းပြင်ရန်", value=row['Number'], max_chars=2)
                e_amt = st.number_input("ပမာဏပြင်ရန်", value=int(row['Amount']))
                
                if st.form_submit_button("💾 သိမ်းဆည်းမည်"):
                    try:
                        res = requests.post(script_url, json={
                            "action": "update", "row_index": actual_row,
                            "Customer": e_name, "Number": str(e_num).zfill(2), "Amount": int(e_amt)
                        })
                        if res.status_code == 200:
                            st.success("✅ ပြင်ဆင်ပြီးပါပြီ။ ခဏစောင့်ပါ...")
                            # Sheet ဘက်မှာ update ဖြစ်ချိန်ကို စောင့်ပေးခြင်း
                            time.sleep(2) 
                            st.rerun()
                        else:
                            st.error("❌ Apps Script URL ကို စစ်ဆေးပါ။")
                    except:
                        st.error("❌ ပြင်မရပါ။")

# --- ၉။ အရောင်းဇယား ---
st.divider()
st.subheader("📊 အရောင်းဇယား")
st.dataframe(df, use_container_width=True, hide_index=True)

if st.button("🔥 စာရင်းအားလုံးဖျက်မည်"):
    try:
        requests.post(script_url, json={"action": "clear_all"})
        st.warning("ဖျက်ပြီးပါပြီ။")
        time.sleep(2)
        st.rerun()
    except:
        st.error("❌ ဖျက်မရပါ။")
