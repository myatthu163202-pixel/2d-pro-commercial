import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests, time, re

# ------------------ PAGE SETUP ------------------
st.set_page_config("2D Agent Pro", "💰", layout="wide")

MM_TZ = timezone(timedelta(hours=6, minutes=30))
TODAY = datetime.now(MM_TZ).strftime("%Y-%m-%d")

# ------------------ LINK STORAGE ------------------
@st.cache_resource
def get_storage():
    return {
        "admin": {"sheet": "", "script": ""},
        "thiri": {"sheet": "", "script": ""}
    }

db = get_storage()

# ------------------ LOGIN ------------------
USERS = {"admin": "123456", "thiri": "163202"}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Agent Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USERS and USERS[u] == p:
            st.session_state.login = True
            st.session_state.user = u
            st.rerun()
        else:
            st.error("❌ Login မအောင်မြင်ပါ")
    st.stop()

user = st.session_state.user

# ------------------ SIDEBAR ------------------
st.sidebar.title(f"👤 {user}")

sheet = st.sidebar.text_input("Google Sheet URL", value=db[user]["sheet"])
script = st.sidebar.text_input("Apps Script URL", value=db[user]["script"])

if st.sidebar.button("💾 Save"):
    db[user]["sheet"] = sheet
    db[user]["script"] = script
    st.success("Saved")
    time.sleep(1)
    st.rerun()

st.sidebar.divider()
win_num = st.sidebar.text_input("🎯 ပေါက်ဂဏန်း", max_chars=2)
za = st.sidebar.number_input("💰 ဇ (အဆ)", value=80)

if st.sidebar.button("Logout"):
    st.session_state.login = False
    st.rerun()

if not sheet or not script:
    st.warning("Link မပြည့်စုံပါ")
    st.stop()

# ------------------ LOAD DATA ------------------
def csv_url(url):
    m = re.search(r"/d/([^/]+)", url)
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv"

try:
    df = pd.read_csv(csv_url(sheet) + f"&t={int(time.time())}")
except:
    st.error("Sheet မဖတ်နိုင်ပါ")
    st.stop()

df.fillna("", inplace=True)
df["Number"] = df["Number"].astype(str).str.zfill(2)
df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)

today_df = df[df["Date"] == TODAY]

# ------------------ DASHBOARD ------------------
st.title("💰 2D Agent Dashboard")
st.metric("📊 ဒီနေ့စုစုပေါင်း", f"{today_df['Amount'].sum():,.0f} Ks")

# ------------------ NEW ENTRY ------------------
with st.expander("➕ စာရင်းအသစ်"):
    with st.form("new"):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("ထိုးသူအမည်")
        num = c2.text_input("ဂဏန်း", max_chars=2)
        amt = c3.number_input("ပမာဏ", min_value=100, step=100)
        if st.form_submit_button("သိမ်း"):
            if name and num:
                # DUPLICATE CHECK
                dup = today_df[
                    (today_df["Customer"] == name) &
                    (today_df["Number"] == num.zfill(2))
                ]
                if not dup.empty:
                    st.error("⚠️ ဒီနာမည် ဒီဂဏန်း ရှိပြီးသား")
                else:
                    payload = {
                        "action": "insert",
                        "Date": TODAY,
                        "Time": datetime.now(MM_TZ).strftime("%I:%M %p"),
                        "Customer": name,
                        "Number": num.zfill(2),
                        "Amount": int(amt)
                    }
                    requests.post(script, json=payload)
                    st.success("✔️ သိမ်းပြီး")
                    time.sleep(1)
                    st.rerun()

# ------------------ WIN CHECK ------------------
if win_num:
    win = today_df[today_df["Number"] == win_num.zfill(2)]
    if not win.empty:
        win["လျော်ကြေး"] = win["Amount"] * za
        st.success("🎉 ပေါက်သူများ")
        st.table(win[["Customer", "Number", "Amount", "လျော်ကြေး"]])

# ------------------ EDIT ------------------
st.subheader("✏️ ဒီနေ့စာရင်းပြင်ရန်")
for i, r in today_df.iterrows():
    with st.expander(f"{r.Customer} | {r.Number} | {r.Amount}"):
        with st.form(f"e{i}"):
            en = st.text_input("နာမည်", r.Customer)
            nu = st.text_input("ဂဏန်း", r.Number)
            am = st.number_input("ပမာဏ", value=int(r.Amount))
            if st.form_submit_button("Update"):
                requests.post(script, json={
                    "action": "update",
                    "row": i + 2,
                    "Customer": en,
                    "Number": nu.zfill(2),
                    "Amount": int(am)
                })
                st.success("Updated")
                time.sleep(1)
                st.rerun()

# ------------------ TABLE ------------------
st.subheader("📋 ဒီနေ့စာရင်း")
search = st.text_input("🔍 နာမည်စစ်")
view = today_df
if search:
    view = view[view["Customer"].str.contains(search, case=False)]

st.dataframe(view, use_container_width=True, hide_index=True)

# ------------------ CLEAR TODAY ------------------
st.divider()
if st.button("🔥 ဒီနေ့စာရင်း အကုန်ဖျက်"):
    requests.post(script, json={"action": "clear_today", "date": TODAY})
    st.warning("ဒီနေ့စာရင်း ဖျက်ပြီး")
    time.sleep(1)
    st.rerun()
