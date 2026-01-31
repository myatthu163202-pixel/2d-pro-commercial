import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests, time, re

# ================= PAGE SETUP =================
st.set_page_config("2D Agent Pro", "💰", layout="wide")

MM_TZ = timezone(timedelta(hours=6, minutes=30))
TODAY = datetime.now(MM_TZ).strftime("%Y-%m-%d")
NUMBER_LIMIT = 50000   # ⭐ ဂဏန်းတစ်ခု အများဆုံး ၅သောင်း ⭐

# ================= USER STORAGE =================
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
            st.error("❌ Login မအောင်မြင်ပါ")
    st.stop()

user = st.session_state.user

# ================= SIDEBAR =================
st.sidebar.title(f"👤 {user}")

toggle_label = "🔓 Link ပြရန်" if not DB[user]["show_links"] else "🔒 Link ဖွက်ရန်"
if st.sidebar.button(toggle_label):
    DB[user]["show_links"] = not DB[user]["show_links"]
    st.rerun()

if DB[user]["show_links"]:
    with st.sidebar.container(border=True):
        st.markdown("### ⚙️ System Links")

        sheet = st.text_input(
            "Google Sheet URL",
            value=DB[user]["sheet"]
        )

        script = st.text_input(
            "Apps Script URL",
            value=DB[user]["script"]
        )

        # 🔥 Auto Save
        DB[user]["sheet"] = sheet
        DB[user]["script"] = script

        st.caption("🔒 Link များကို အလိုအလျောက် သိမ်းထားပါသည်")

sheet = DB[user]["sheet"]
script = DB[user]["script"]

st.sidebar.divider()
win = st.sidebar.text_input("🎯 ပေါက်ဂဏန်း", max_chars=2)
za = st.sidebar.number_input("💰 ဇ (အဆ)", value=80)

if st.sidebar.button("Logout"):
    st.session_state.login = False
    st.rerun()

if not sheet or not script:
    st.warning("⚠️ Link များကို အရင်ထည့်ပါ")
    st.stop()

# ================= LOAD SHEET =================
def csv_url(url):
    m = re.search(r"/d/([^/]+)", url)
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv"

df = pd.read_csv(csv_url(sheet) + f"&t={int(time.time())}")
df.columns = df.columns.str.strip()

for c in ["Date","Time","Customer","Number","Amount","Receipt"]:
    if c not in df.columns:
        df[c] = ""

df["Number"] = df["Number"].astype(str).str.zfill(2)
df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)

today_df = df[df["Date"] == TODAY]

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
            num = num.zfill(2)
            used = today_df[today_df["Number"] == num]["Amount"].sum()

            if used + amt > NUMBER_LIMIT:
                st.error(
                    f"❌ ဂဏန်း {num} သည် ဒီနေ့ {used:,.0f} ကျပ်ရှိပြီးသားပါ။\n"
                    f"အများဆုံး {NUMBER_LIMIT:,.0f} ကျပ်သာ ခွင့်ပြုထားပါသည်။"
                )
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
                st.success("✔️ စာရင်းသွင်းပြီးပါပြီ")
                time.sleep(1)
                st.rerun()

# ================= WIN CHECK =================
if win:
    winners = today_df[today_df["Number"] == win.zfill(2)]
    if not winners.empty:
        winners["လျော်ကြေး"] = winners["Amount"] * za
        st.success("🎉 ပေါက်သူများ")
        st.table(winners[["Customer","Number","Amount","လျော်ကြေး"]])

# ================= EDIT =================
st.subheader("✏️ ဒီနေ့စာရင်း ပြန်ပြင်ရန်")
for i, r in today_df.iterrows():
    with st.expander(f"{r.Customer} | {r.Number} | {r.Amount:,.0f}"):
        with st.form(f"edit_{i}"):
            en = st.text_input("အမည်", r.Customer)
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
                st.success("ပြင်ပြီးပါပြီ")
                time.sleep(1)
                st.rerun()

# ================= TABLE =================
st.subheader("📋 ဒီနေ့စာရင်းဇယား")
search = st.text_input("🔍 နာမည်စစ်ရန်")
view = today_df
if search:
    view = view[view["Customer"].str.contains(search, case=False, na=False)]

st.dataframe(view, use_container_width=True, hide_index=True)

# ================= EXPORT =================
csv_data = view.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ ဒီနေ့စာရင်း CSV ဒေါင်း", csv_data, "today_2d.csv", "text/csv")

# ================= CLEAR TODAY =================
st.divider()
if st.button("🔥 ဒီနေ့စာရင်း အကုန်ဖျက်"):
    requests.post(script, json={"action": "clear_today", "date": TODAY})
    st.warning("ဒီနေ့စာရင်းအားလုံး ဖျက်ပြီးပါပြီ")
    time.sleep(1)
    st.rerun()
