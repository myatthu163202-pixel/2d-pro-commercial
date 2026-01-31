import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests, time, re

# =========================
# Page Setup
# =========================
st.set_page_config(
    page_title="2D Agent Pro",
    page_icon="💰",
    layout="wide"
)

# =========================
# Time & Limit Setup
# =========================
MM_TZ = timezone(timedelta(hours=6, minutes=30))  
TODAY = datetime.now(MM_TZ).strftime("%Y-%m-%d")
NUMBER_LIMIT = 50000   

# =========================
# User Storage
# =========================
@st.cache_resource
def storage():
    return {
        "admin": {
            "sheet": "",
            "script": "",
            "show_links": False
        }
    }

DB = storage()

# =========================
# Login System
# =========================
USERS = {"admin": "123456"}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USERS and USERS[u] == p:
            st.session_state.login = True
            st.session_state.user = u
            st.rerun()
        else:
            st.error("❌ Username သို့မဟုတ် Password မှားနေပါသည်")
    st.stop()

user = st.session_state.user

# =========================
# Sidebar
# =========================
st.sidebar.title(f"👤 {user}")

toggle_text = "🔓 Link ပြရန်" if not DB[user]["show_links"] else "🔒 Link ဖွက်ရန်"
if st.sidebar.button(toggle_text):
    DB[user]["show_links"] = not DB[user]["show_links"]
    st.rerun()

if DB[user]["show_links"]:
    with st.sidebar.container(border=True):
        st.markdown("### ⚙️ System Links")
        sheet = st.text_input("Google Sheet URL", value=DB[user]["sheet"])
        script = st.text_input("Apps Script URL", value=DB[user]["script"])
        DB[user]["sheet"] = sheet
        DB[user]["script"] = script
        st.caption("🔒 Link များကို အလိုအလျောက် သိမ်းထားပါသည်")

sheet = DB[user]["sheet"]
script = DB[user]["script"]

st.sidebar.divider()
win_number = st.sidebar.text_input("🎯 ပေါက်ဂဏန်းစစ်", max_chars=2)
za_rate = st.sidebar.number_input("💰 ဇ (အဆ)", value=80)

if st.sidebar.button("Logout"):
    st.session_state.login = False
    st.rerun()

if not sheet or not script:
    st.warning("⚠️ Sidebar ရှိ Link များကို အရင်ထည့်ပါ")
    st.stop()

# =========================
# Load Google Sheet
# =========================
def csv_url(url):
    try:
        m = re.search(r"/d/([^/]+)", url)
        return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv"
    except:
        return ""

try:
    # URL မှာ cache မငြိအောင် timestamp ထည့်ထားသည်
    full_url = csv_url(sheet) + f"&t={int(time.time())}"
    df = pd.read_csv(full_url)
    df.columns = df.columns.str.strip()

    for c in ["Date","Time","Customer","Number","Amount","Receipt"]:
        if c not in df.columns:
            df[c] = ""

    df["Number"] = df["Number"].astype(str).str.zfill(2)
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    
    # ပြင်တဲ့အခါမှာ Sheet ရဲ့ Row အစစ်ကို သိဖို့ index ကို သိမ်းထားမယ်
    df['sheet_row'] = df.index + 2 
    today_df = df[df["Date"] == TODAY]

except Exception as e:
    st.error(f"❌ Sheet ချိတ်ဆက်မှု အမှားအယွင်းရှိနေပါသည်")
    st.stop()

# =========================
# Dashboard
# =========================
st.title("💰 2D Agent Dashboard")
total_today = today_df['Amount'].sum()
st.metric("📊 ဒီနေ့စုစုပေါင်းရောင်းငွေ", f"{total_today:,.0f} ကျပ်")

# =========================
# New Entry
# =========================
with st.expander("📝 စာရင်းအသစ်ထည့်ရန်", expanded=True):
    with st.form("new_entry", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("ထိုးသူအမည်")
        number = c2.text_input("ထိုးမည်ဂဏန်း", max_chars=2)
        amount = c3.number_input("ပိုက်ဆံပမာဏ", min_value=100, step=100)

        if st.form_submit_button("သိမ်းမည်"):
            if not name or not number:
                st.warning("အချက်အလက်အပြည့်အစုံ ဖြည့်ပါ")
            else:
                number = number.zfill(2)
                used_amount = today_df[today_df["Number"] == number]["Amount"].sum()

                if used_amount + amount > NUMBER_LIMIT:
                    st.error(f"❌ ဂဏန်း {number} သည် Limit {NUMBER_LIMIT} ကျော်နေပါပြီ")
                else:
                    payload = {
                        "action": "insert",
                        "Date": TODAY,
                        "Time": datetime.now(MM_TZ).strftime("%I:%M %p"),
                        "Customer": name,
                        "Number": number,
                        "Amount": int(amount),
                        "Receipt": f"R-{TODAY}-{len(today_df)+1:04d}"
                    }
                    try:
                        resp = requests.post(script, json=payload)
                        st.success("✔️ သိမ်းပြီးပါပြီ")
                        time.sleep(1)
                        st.rerun()
                    except:
                        st.error("Script Link ချိတ်မရပါ")

# =========================
# Win Number Check
# =========================
if win_number:
    winners = today_df[today_df["Number"] == win_number.zfill(2)]
    if not winners.empty:
        winners["လျော်ကြေး"] = winners["Amount"] * za_rate
        st.success(f"🎉 ပေါက်သူများ (ဂဏန်း: {win_number})")
        st.table(winners[["Customer","Number","Amount","လျော်ကြေး"]])
    else:
        st.info("ဒီဂဏန်း ပေါက်သူမရှိပါ")

# =========================
# Edit Records
# =========================
st.subheader("✏️ ဒီနေ့စာရင်း ပြန်ပြင်ရန်")
for i, r in today_df.iterrows():
    with st.expander(f"{r.Customer} | {r.Number} | {r.Amount:,.0f} ကျပ်"):
        with st.form(f"edit_{i}"):
            en = st.text_input("အမည်", r.Customer)
            nu = st.text_input("ဂဏန်း", r.Number)
            am = st.number_input("ပမာဏ", value=int(r.Amount))
            if st.form_submit_button("ပြင်မည်"):
                requests.post(script, json={
                    "action": "update",
                    "row": int(r.sheet_row), # Sheet ထဲက Row အမှန်ကို ပို့ပေးခြင်း
                    "Customer": en,
                    "Number": nu.zfill(2),
                    "Amount": int(am)
                })
                st.success("✔️ ပြင်ပြီးပါပြီ")
                time.sleep(1)
                st.rerun()

# =========================
# Table & Search
# =========================
st.subheader("📋 ဒီနေ့စာရင်းဇယား")
search = st.text_input("🔍 နာမည်ဖြင့်ရှာရန်")
view_df = today_df.drop(columns=['sheet_row']) # User ကို Row index မပြရန်
if search:
    view_df = view_df[view_df["Customer"].str.contains(search, case=False, na=False)]

st.dataframe(view_df, use_container_width=True, hide_index=True)

# =========================
# Export & Clear Today
# =========================
col1, col2 = st.columns(2)
with col1:
    csv_data = view_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ CSV ဒေါင်းလုဒ်", csv_data, "today_2d.csv", "text/csv")

with col2:
    confirm = st.checkbox("⚠️ ဒီနေ့စာရင်းကို Sheet ထဲမှာပါ အပြီးဖျက်ရန် သေချာပါသည်")
    if st.button("🔥 ဒီနေ့စာရင်း အကုန်ဖျက်", disabled=not confirm):
        with st.spinner("ဖျက်နေသည်..."):
            requests.post(script, json={"action": "clear_today", "date": TODAY})
            st.warning("Sheet ထဲမှ ဒီနေ့စာရင်းအားလုံးကို ဖျက်လိုက်ပါပြီ")
            time.sleep(1)
            st.rerun()
