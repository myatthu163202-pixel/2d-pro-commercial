import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time
import re

# --- ၁။ Page Setup ---
st.set_page_config(page_title="2D Agent Pro", layout="wide", page_icon="💰")

# --- ၂။ User List ---
USERS = {"admin": "123456", "thiri": "163202"}

# --- ၃။ Storage ---
if "user_storage" not in st.session_state:
    st.session_state["user_storage"] = {u: {"sheet": "", "script": ""} for u in USERS}

# --- ၄။ Login Logic ---
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

# Logged in values
curr_user = st.session_state["username"]
user_links = st.session_state["user_storage"][curr_user]

# --- Sidebar Setup ---
with st.sidebar.expander("🛠 Software Setup", expanded=False):
    in_sheet = st.text_input("Google Sheet URL", value=user_links["sheet"])
    in_script = st.text_input("Apps Script URL", value=user_links["script"])
    if st.button("✅ Save Links"):
        st.session_state["user_storage"][curr_user]["sheet"] = in_sheet
        st.session_state["user_storage"][curr_user]["script"] = in_script
        st.success("Saved!")
        time.sleep(1)
        st.rerun()

script_url = user_links["script"]
sheet_url = user_links["sheet"]

if not script_url or not sheet_url:
    st.warning("⚠️ Setup တွင် Link များအရင်ထည့်ပါ။")
    st.stop()

# Load Data
def get_csv_url(url):
    m = re.search(r"/d/([^/]*)", url)
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv" if m else None

try:
    df = pd.read_csv(get_csv_url(sheet_url))
    df.columns = df.columns.str.strip()
    df['Number'] = df['Number'].astype(str).str.zfill(2)
except:
    st.error("❌ ဒေတာဆွဲမရပါ။ Link မှန်မမှန်စစ်ပါ။")
    st.stop()

# --- Dashboard ---
st.title(f"💰 {curr_user}'s 2D Agent Pro")
total_amt = df['Amount'].sum() if not df.empty else 0
st.metric("စုစုပေါင်းရောင်းရငွေ", f"{total_amt:,.0f} Ks")

# View & Delete Section
if not df.empty:
    st.subheader("📊 အရောင်းစာရင်း (တစ်ခုချင်းဖျက်ရန်)")
    for i, row in df.iterrows():
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.write(f"👤 {row['Customer']} | 🔢 {row['Number']} | 💵 {row['Amount']} Ks")
        
        # တစ်ခုချင်းဖျက်ရန် ခလုတ် (ဒီအပိုင်းက အရေးကြီးဆုံး)
        if c3.button("🗑 ဖျက်", key=f"del_{i}"):
            target_row = i + 2  # Index 0 + Header 1 = Row 2
            try:
                # Apps Script ဆီ ပို့လိုက်ပြီ
                res = requests.post(script_url, json={"action": "delete", "row_index": target_row})
                if res.status_code == 200:
                    st.success("ဖျက်ပြီးပါပြီ။")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Apps Script Error!")
            except:
                st.error("ချိတ်ဆက်မှု Error!")

# Logout
if st.sidebar.button("🚪 Logout"):
    st.session_state["logged_in"] = False
    st.rerun()
