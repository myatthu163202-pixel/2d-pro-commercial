import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests, time, re

# ================= PAGE SETUP =================
st.set_page_config("2D Agent Pro", "💰", layout="wide")

MM_TZ = timezone(timedelta(hours=6, minutes=30))
TODAY = datetime.now(MM_TZ).strftime("%Y-%m-%d")
NUMBER_LIMIT = 50000   # ဂဏန်းတစ်လုံး ၅သောင်းကန့်သတ်

# ================= USER STORAGE =================
@st.cache_resource
def storage():
    return {
        "admin": {"sheet": "", "script": ""}
    }

DB = storage()

# ================= LOGIN =================
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
            st.error("Login မအောင်မြင်ပါ")
    st.stop()

user = st.session_state.user

# ================= SIDEBAR =================
st.sidebar.title(f"👤 {user}")

# 🔒 Hide / Show Links
with st.sidebar.expander("⚙️ Sheet / Script Settings"):
    sheet = st.text_input("Google Sheet URL", value=DB[user]["sheet"])
    script = st.text_input("Apps Script URL", value=DB[user]["script"])

    # 🔥 AUTO SAVE (Button မလို)
    DB[user]["sheet"] = sheet
    DB[user]["script"] = script

st.sidebar.caption("🔒 Link များကို အလိုအလျောက် သိမ်းထားပါသည်")

st.sidebar.divider()
win = st.sidebar.text_input("🎯 ပေါက်ဂဏန်း", max_chars=2)
za = st.sidebar.number_input("💰 ဇ (အဆ)", value=80)

if st.sidebar.button("Logout"):
    st.session_state.login = False
    st.rerun()

if not sheet or not script:
    st.warning("⚠️ Sidebar ထဲတွင် Sheet / Script URL ထည့်ပါ")
    st.stop()

# ================= LOAD SHEET =================
def csv_url(url):
    m = re.search(r"/d/([^/]+)", url)
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv"

try:
    df = pd.read_csv(csv_url(sheet) + f"&t={int(time.time())}")
    df.columns = df.columns.str.strip()

    for c in ["Date","Time","Customer","Number","Amount","Receipt"]:
        if c not in df.columns:
            df[c] = ""

    df["Number"] = df["Number"].astype(str).str.zfill(2)
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)

    today_df = df[df["Date"] == TODAY]

except:
    st.error("❌ Sheet URL မှားနေပါသည် သို့မဟုတ် Access မရှိပါ")
    st.stop()

# ================= DASHBOARD =================
st.title("💰 2D Agent Dashboard")
st.metric("📊 ဒီနေ့စုစုပေါင်း", f"{today_df['Amount'].sum():,.0f} Ks")

# ================= NEW ENTRY =================
with st.expander("📝 စာရင်းအသစ်ထည့်ရန်", expanded=True):
    with st.form("new_entry", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("ထိုးသူအမည်")
        num = c2.text_input("ထိုးမည်ဂဏန်း", max_chars=2)
        amt = c3.number_input("ပိုက်ဆံပမာဏ", min_value=100, step=100)

        if st.form_submit_button("သိမ်းမည်"):
            if not name or not num:
                st.warning("အချက်အလက်အကုန်ဖြည့်ပါ")
            else:
                num = num.zfill(2)
                used = today_df[today_df["Number"] == num]["Amount"].sum()

                if used + amt > NUMBER_LIMIT:
                    st.error(f"❌ {num} သည် ၅သောင်း Limit ပြည့်နေပါပြီ")
                else:
                    payload = {
                        "action": "insert",
                        "Date": TODAY,
                        "Time": datetime.now(MM_TZ).strftime("%I:%M %p"),
                        "Customer": name,
                        "Number": num,
                        "Amount": int(amt),
                        "Receipt": f"R-{TODAY}-{int(time.time())}"
                    }
                    requests.post(script, json=payload)
                    st.success("✔️ သိမ်းပြီး")
                    time.sleep(1)
                    st.rerun()

# ================= WIN CHECK =================
if win:
    w = today_df[today_df["Number"] == win.zfill(2)]
    if not w.empty:
        w = w.copy()
        w["လျော်ကြေး"] = w["Amount"] * za
        st.success(f"🎉 ပေါက်ဂဏန်း {win}")
        st.table(w[["Customer","Number","Amount","လျော်ကြေး"]])

# ================= TABLE =================
st.subheader("📋 ဒီနေ့စာရင်းဇယား")
search = st.text_input("🔍 နာမည်ဖြင့်ရှာရန်")
view = today_df

if search:
    view = view[view["Customer"].str.contains(search, case=False, na=False)]

st.dataframe(view, use_container_width=True, hide_index=True)

# ================= EXPORT & CLEAR =================
col1, col2 = st.columns(2)

with col1:
    csv = view.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ CSV ဒေါင်းလုဒ်", csv, "today_2d.csv", "text/csv")

with col2:
    confirm = st.checkbox("⚠️ ဒီနေ့စာရင်းကို ဖျက်မည်ဟု သေချာပါသည်")

    if st.button("🔥 ဒီနေ့စာရင်း အကုန်ဖျက်", disabled=not confirm):
        # Sheet ထဲက တကယ်ဖျက်
        requests.post(script, json={
            "action": "clear_today",
            "date": TODAY
        })

        # 🔥 App Cache ဖျက်
        st.cache_data.clear()

        st.success("✔️ Sheet + App နှစ်ဖက်လုံး ဖျက်ပြီးပါပြီ")
        time.sleep(1)
        st.rerun()
