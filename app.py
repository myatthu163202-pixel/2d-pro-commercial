import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests, time, re

# ------------------ PAGE SETUP ------------------
st.set_page_config(page_title="2D Agent Pro", layout="wide", page_icon="💰")

MM_TZ = timezone(timedelta(hours=6, minutes=30))
TODAY = datetime.now(MM_TZ).strftime("%Y-%m-%d")

# ------------------ LINK STORAGE ------------------
@st.cache_resource
def get_user_storage():
    return {"admin": {"sheet": "", "script": ""}}

user_db = get_user_storage()

# ------------------ LOGIN ------------------
USERS = {"admin": "123456"}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USERS and USERS[u] == p:
            st.session_state["logged_in"] = True
            st.session_state["user"] = u
            st.rerun()
        else:
            st.error("❌ Username or Password wrong")
    st.stop()

curr_user = st.session_state["user"]

# ------------------ SIDEBAR ------------------
st.sidebar.title(f"👋 {curr_user}")

in_sheet = st.sidebar.text_input("Google Sheet URL", value=user_db[curr_user]["sheet"])
in_script = st.sidebar.text_input("Apps Script URL", value=user_db[curr_user]["script"])

if st.sidebar.button("💾 Save Links"):
    user_db[curr_user]["sheet"] = in_sheet
    user_db[curr_user]["script"] = in_script
    st.success("Links Saved!")
    time.sleep(1)
    st.rerun()

sheet_url = user_db[curr_user]["sheet"]
script_url = user_db[curr_user]["script"]

st.sidebar.divider()
win_num = st.sidebar.text_input("🎰 Winning Number", max_chars=2)
za_rate = st.sidebar.number_input("💰 Rate (Za)", value=80)

if st.sidebar.button("🚪 Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

if not sheet_url or not script_url:
    st.warning("🔗 Enter both Sheet URL and Script URL")
    st.stop()

# ------------------ LOAD DATA ------------------
def get_csv_export(url):
    m = re.search(r"/d/([^/]*)", url)
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv"

try:
    csv_link = get_csv_export(sheet_url)
    df = pd.read_csv(csv_link + f"&t={int(time.time())}", header=0)
    df.columns = df.columns.str.strip()
    
    required_cols = ["Date","Time","Customer","Number","Amount"]
    for c in required_cols:
        if c not in df.columns:
            df[c] = ""
    
    df["Number"] = df["Number"].astype(str).str.zfill(2)
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
        
except Exception as e:
    st.error("❌ Cannot load data. Check Sheet URL.")
    st.stop()

today_df = df[df["Date"] == TODAY]

# ------------------ DASHBOARD ------------------
st.title(f"💰 {curr_user}'s 2D Dashboard")
total_in = today_df["Amount"].sum() if not today_df.empty else 0
st.metric("📊 Total (Today)", f"{total_in:,.0f} Ks")

# ------------------ NEW ENTRY ------------------
with st.expander("📝 New Entry"):
    with st.form("entry_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            f_name = st.text_input("Name")
        with col2:
            f_num = st.text_input("Number", max_chars=2)
        with col3:
            f_amt = st.number_input("Amount", min_value=100, step=100)
            
        if st.form_submit_button("✅ Save"):
            if not f_name or not f_num:
                st.error("❌ Name and Number required")
            else:
                dup = today_df[
                    (today_df["Customer"].str.lower() == f_name.lower()) &
                    (today_df["Number"] == f_num.zfill(2))
                ]
                if not dup.empty:
                    st.warning("⚠️ Duplicate found! Entry skipped.")
                else:
                    payload = {
                        "action": "insert",
                        "Date": TODAY,
                        "Time": datetime.now(MM_TZ).strftime("%I:%M %p"),
                        "Customer": f_name,
                        "Number": f_num.zfill(2),
                        "Amount": int(f_amt)
                    }
                    res = requests.post(script_url, json=payload)
                    if res.status_code == 200:
                        st.success("✔️ Saved!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Save failed")

# ------------------ WIN CHECK ------------------
if win_num:
    winners = today_df[today_df["Number"] == win_num.zfill(2)]
    if not winners.empty:
        winners["Payout"] = winners["Amount"] * za_rate
        st.success(f"🎉 Winners for {win_num.zfill(2)}")
        st.table(winners[["Customer","Number","Amount","Payout"]])

# ------------------ EDIT ENTRIES ------------------
st.divider()
st.subheader("✏️ Edit Today Entries")

for i, row in today_df.iterrows():
    row_idx = int(i) + 2
    with st.expander(f"{row['Customer']} | {row['Number']} | {row['Amount']}"):
        with st.form(f"edit_{i}"):
            en = st.text_input("Name", row["Customer"])
            nu = st.text_input("Number", row["Number"], max_chars=2)
            am = st.number_input("Amount", value=int(row["Amount"]))
            if st.form_submit_button("💾 Update"):
                payload = {
                    "action": "update",
                    "row": row_idx,
                    "Customer": en,
                    "Number": nu.zfill(2),
                    "Amount": int(am)
                }
                res = requests.post(script_url, json=payload)
                if res.status_code == 200:
                    st.success("Updated!")
                    time.s
