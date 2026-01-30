import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time
import re

# --- ၁။ Page အပြင်အဆင် ---
st.set_page_config(page_title="2D Agent Pro", layout="wide", page_icon="💰")

# --- ၂။ User စာရင်း ---
USERS = {"admin": "123456", "thiri": "163202"}

# --- ၃။ Storage (Refresh လုပ်လည်း Link တွေမပျောက်အောင်) ---
if "user_storage" not in st.session_state:
    st.session_state["user_storage"] = {u: {"sheet": "", "script": ""} for u in USERS}

# --- ၄။ Login စနစ် ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>🔐 Member Login</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        u = st.text_input("Username", key="l_user")
        p = st.text_input("Password", type="password", key="l_pass")
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
with st.sidebar.expander("🛠 Software Setup", expanded=True):
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

if not sheet_url or not script_url:
    st.warning("💡 အပေါ်က Setup တွင် Link များကို အရင်ထည့်ပေးပါ။")
    st.stop()

# --- ၆။ Data Loading (Syntax Error များကို ဒီမှာ အကုန်ပြင်ထားသည်) ---
def get_csv_url(url):
    m = re.search(r"/d/([^/]*)", url)
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv" if m else None

try:
    csv_url = get_csv_url(sheet_url)
    # image_65826f.png နှင့် image_6514b3.png ပါ Error များကို ဤနေရာတွင် ပြင်ဆင်ထားသည်
    df = pd.read_csv(f"{csv_url}&cachebuster={int(time.time())}")
    df.columns = df.columns.str.strip()
    df['Number'] = df['Number'].astype(str).str.zfill(2)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
except Exception:
    st.error("❌ ဒေတာဆွဲမရပါ။ Link ပြန်စစ်ပါ။")
    st.stop()

# --- ၇။ Dashboard (image_651592.png UI အတိုင်း) ---
st.title(f"💰 {curr_user}'s 2D Agent Pro")
total_in = df['Amount'].sum() if not df.empty else 0
st.write(f"စုစုပေါင်းရောင်းရငွေ")
st.header(f"{total_in:,.0f} Ks")

# စာရင်းသွင်းရန် Form
with st.expander("📝 စာရင်းအသစ်သွင်းရန်"):
    with st.form("entry_form", clear_on_submit=True):
        name = st.text_input("နာမည်")
        num = st.text_input("ဂဏန်း (၂ လုံး)", max_chars=2)
        amt = st.number_input("ငွေပမာဏ", min_value=100, step=100)
        if st.form_submit_button("✅ သိမ်းဆည်းမည်"):
            if name and num:
                now = datetime.now(timezone(timedelta(hours=6, minutes=30))).strftime("%I:%M %p")
                requests.post(script_url, json={"action": "insert", "Customer": name, "Number": str(num).zfill(2), "Amount": int(amt), "Time": now})
                st.success("သွင်းပြီးပါပြီ။")
                time.sleep(1)
                st.rerun()

# --- ၈။ တစ်ခုချင်းဖျက်ရန်အပိုင်း (အဓိကပြင်ဆင်ချက်) ---
st.subheader("📊 အရောင်းစာရင်း (တစ်ခုချင်းဖျက်ရန်)")
if not df.empty:
    for i, row in df.iterrows():
        col_text, col_del = st.columns([4, 1])
        col_text.write(f"👤 {row['Customer']} | 🔢 {row['Number']} | 💵 {int(row['Amount'])} Ks")
        
        # image_6590d9.png ပါ "ဖျက်" ခလုတ် logic
        if col_del.button("🗑 ဖျက်", key=f"del_{i}"):
            # Header Row ပါသဖြင့် Row Index ကို +2 လုပ်ခြင်း
            target_row = int(i) + 2
            try:
                resp = requests.post(script_url, json={"action": "delete", "row_index": target_row})
                if resp.status_code == 200:
                    st.success("ဖျက်ပြီးပါပြီ။")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Apps Script Error!")
            except Exception:
                st.error("❌ ချိတ်ဆက်မှု Error!")

# Logout
if st.sidebar.button("🚪 Logout"):
    st.session_state["logged_in"] = False
    st.rerun()
