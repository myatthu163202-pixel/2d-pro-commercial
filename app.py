import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests, time, re

# ================= PAGE SETUP =================
st.set_page_config("2D Agent Pro", "💰", layout="wide")

MM_TZ = timezone(timedelta(hours=6, minutes=30))
TODAY = datetime.now(MM_TZ).strftime("%Y-%m-%d")
NUMBER_LIMIT = 50000   

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

# ================= SIDEBAR (WITH HIDE/SHOW LINKS) =================
st.sidebar.title(f"👤 {user}")

# Link များကို ဖျောက်ထားရန်/ပြရန် expander သုံးထားသည်
with st.sidebar.expander("⚙️ Settings (Links)"):
    sheet = st.text_input("Google Sheet URL", DB[user]["sheet"])
    script = st.text_input("Apps Script URL", DB[user]["script"])

    if st.button("💾 Save Links"):
        DB[user]["sheet"] = sheet
        DB[user]["script"] = script
        st.success("သိမ်းပြီး")
        time.sleep(1)
        st.rerun()

st.sidebar.divider()
win = st.sidebar.text_input("🎯 ပေါက်ဂဏန်း", max_chars=2)
za = st.sidebar.number_input("💰 ဇ (အဆ)", value=80)

if st.sidebar.button("Logout"):
    st.session_state.login = False
    st.rerun()

if not sheet or not script:
    st.warning("Sidebar ရှိ Settings တွင် Sheet / Script Link ထည့်ပါ")
    st.stop()

# ================= LOAD SHEET =================
def csv_url(url):
    try:
        m = re.search(r"/d/([^/]+)", url)
        return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv"
    except:
        return ""

try:
    df = pd.read_csv(csv_url(sheet) + f"&t={int(time.time())}", header=0)
    df.columns = df.columns.str.strip()
    for c in ["Date","Time","Customer","Number","Amount","Receipt"]:
        if c not in df.columns:
            df[c] = ""
    df["Number"] = df["Number"].astype(str).str.zfill(2)
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    today_df = df[df["Date"] == TODAY]
except:
    st.error("Sheet URL မှားနေပါသည် သို့မဟုတ် Access မရှိပါ")
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
            if num and name:
                num = num.zfill(2)
                used_amount = today_df[today_df["Number"] == num]["Amount"].sum()
                if used_amount + amt > NUMBER_LIMIT:
                    st.error(f"❌ {num} သည် Limit ပြည့်နေပြီ!")
                else:
                    receipt = f"R-{TODAY}-{len(today_df)+1:04d}"
                    payload = {
                        "action": "insert",
                        "Date": TODAY,
                        "Time": datetime.now(MM_TZ).strftime("%I:%M %p"),
                        "Customer": name,
                        "Number": num,
                        "Amount": int(amt),
                        "Receipt": receipt
                    }
                    requests.post(script, json=payload)
                    st.success("✔️ သိမ်းပြီး")
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("အချက်အလက်အကုန်ဖြည့်ပါ")

# ================= WIN CHECK =================
if win:
    w = today_df[today_df["Number"] == win.zfill(2)]
    if not w.empty:
        w["လျော်ကြေး"] = w["Amount"] * za
        st.success(f"🎉 ပေါက်ဂဏန်း {win} တွေ့ရှိမှု")
        st.table(w[["Customer","Number","Amount","လျော်ကြေး"]])

# ================= TABLE & SEARCH =================
st.subheader("📋 ဒီနေ့စာရင်းဇယား")
search = st.text_input("🔍 နာမည်ဖြင့်ရှာရန်")
view = today_df
if search:
    view = view[view["Customer"].str.contains(search, case=False, na=False)]

st.dataframe(view, use_container_width=True, hide_index=True)

# ================= EXPORT & CLEAR =================
col_dl, col_clr = st.columns([1, 1])

with col_dl:
    csv_data = view.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ CSV ဒေါင်းလုဒ်ဆွဲရန်", csv_data, "today_2d.csv", "text/csv")

with col_clr:
    # အကုန်ဖျက်ရန် Double Check လုပ်ခြင်း
    confirm = st.checkbox("⚠️ စာရင်းအားလုံးဖျက်ရန် သေချာပါသည်")
    if st.button("🔥 ဒီနေ့စာရင်း အကုန်ဖျက်မည်", disabled=not confirm):
        requests.post(script, json={"action":"clear_today","date":TODAY})
        st.warning("ဖျက်ပြီးပါပြီ")
        time.sleep(1)
        st.rerun()
