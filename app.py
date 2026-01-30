import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time
import re

# --- ၁။ Page အပြင်အဆင် ---
st.set_page_config(page_title="2D Agent Pro", layout="wide", page_icon="💰")

# --- ၂။ VIP User စာရင်း ---
USERS = {
        "admin": "123456",
        "thiri": "163202",
        }

# --- ၃။ Link များကို Browser Memory တွင် အသေသတ်မှတ်ထားမည့်စနစ် ---
# ဤနည်းလမ်းသည် Refresh နှိပ်သော်လည်း Link များ လုံးဝမပျောက်စေရန် အာမခံသည်
@st.cache_resource
def get_stored_config():
    return {"sheet": "", "script": ""}

config = get_stored_config()

# --- ၄။ Login စနစ် ---
def check_password():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if not st.session_state["logged_in"]:
        st.markdown("<h2 style='text-align: center;'>🔐 Member Login</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            u = st.text_input("Username", key="l_user")
            p = st.text_input("Password", type="password", key="l_pw")
            if st.button("Login", use_container_width=True):
                if u in USERS and USERS[u] == p:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = u
                    st.rerun()
                else:
                    st.error("❌ Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
        return False
    return True

if check_password():
    # --- Sidebar Section ---
    st.sidebar.title(f"👋 မင်္ဂလာပါ {st.session_state['username']}")
    
    with st.sidebar.expander("🛠 Software Setup (Link များ)", expanded=True):
        in_sheet = st.text_input("Google Sheet URL", value=config["sheet"])
        in_script = st.text_input("Apps Script URL", value=config["script"])
        
        if st.button("✅ Link များမှတ်ထားမည်"):
            config["sheet"] = in_sheet
            config["script"] = in_script
            st.success("မှတ်သားပြီးပါပြီ။ Refresh လုပ်လည်း မပျောက်တော့ပါ။")
            st.rerun()

    sheet_url = config["sheet"]
    script_url = config["script"]

    if not sheet_url or not script_url:
        st.warning("💡 အပေါ်က Setup တွင် Link များကို အရင်ဆုံး တစ်ခါထည့်ပေးပါ။")
        st.stop()

    def get_csv_url(url):
        m = re.search(r"/d/([^/]*)", url)
        return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv" if m else None

    csv_url = get_csv_url(sheet_url)

    try:
        def load_data():
            url = f"{csv_url}&cachebuster={int(time.time())}"
            data = pd.read_csv(url)
            if not data.empty:
                data.columns = data.columns.str.strip()
                data['Number'] = data['Number'].astype(str).str.zfill(2)
                data['Amount'] = pd.to_numeric(data['Amount'], errors='coerce').fillna(0)
            return data
        df = load_data()
    except:
        st.error("❌ Link ချိတ်ဆက်မှု မှားယွင်းနေပါသည်။")
        st.stop()

    # --- ၅။ Dashboard Layout (မင်းကြိုက်သည့်အတိုင်း အပြည့်အစုံ) ---
    st.title("💰 2D Agent Pro Dashboard")
    
    st.sidebar.header("⚙️ Admin Settings")
    win_num = st.sidebar.text_input("🎰 ပေါက်ဂဏန်း", max_chars=2)
    za_rate = st.sidebar.number_input("💰 ဇ (အဆ)", value=80)
    
    if st.sidebar.button("🚪 Log out"):
        st.session_state["logged_in"] = False
        st.rerun()

    total_in = df['Amount'].sum() if not df.empty else 0
    st.success(f"💵 စုစုပေါင်းရောင်းရငွေ: {total_in:,.0f} Ks")

    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("📝 စာရင်းသွင်းရန်")
        with st.form("entry_form", clear_on_submit=True):
            name = st.text_input("နာမည်")
            num = st.text_input("ဂဏန်း", max_chars=2)
            amt = st.number_input("ငွေပမာဏ", min_value=100, step=100)
            if st.form_submit_button("✅ သိမ်းဆည်းမည်"):
                if name and num:
                    now = datetime.now(timezone(timedelta(hours=6, minutes=30))).strftime("%I:%M %p")
                    requests.post(script_url, json={"action": "insert", "Customer": name.strip(), "Number": str(num).zfill(2), "Amount": int(amt), "Time": now})
                    st.success("စာရင်းသွင်းပြီးပါပြီ။")
                    time.sleep(1)
                    st.rerun()

    with c2:
        st.subheader("📊 အရောင်းဇယား")
        if st.button("🔄 Refresh Data"): st.rerun()
        if not df.empty:
            search = st.text_input("🔎 နာမည်ဖြင့်ရှာရန်")
            view_df = df[df['Customer'].str.contains(search, case=False, na=False)] if search else df
            st.dataframe(view_df, use_container_width=True, hide_index=True)
            
            if win_num:
                winners = df[df['Number'] == win_num].copy()
                total_out = winners['Amount'].sum() * za_rate
                st.divider()
                st.subheader("📈 ရလဒ်အကျဉ်းချုပ်")
                k1, k2, k3 = st.columns(3)
                k1.metric("🏆 ပေါက်သူ", f"{len(winners)} ဦး")
                k2.metric("💸 လျော်ကြေး", f"{total_out:,.0f} Ks")
                k3.metric("💹 အမြတ်/အရှုံး", f"{total_in - total_out:,.0f} Ks", delta=float(total_in - total_out))
                if not winners.empty:
                    winners['လျော်ရမည့်ငွေ'] = winners['Amount'] * za_rate
                    st.table(winners[['Customer', 'Number', 'Amount', 'လျော်ရမည့်ငွေ']])

    # --- ၆။ စာရင်းဖျက်သည့် အပိုင်းများ (မင်းကြိုက်တဲ့ Code အစုံပြန်ထည့်ပေးထားသည်) ---
    if not df.empty:
        st.divider()
        with st.expander("🗑 တစ်ဦးချင်းစာရင်းဖျက်ရန်"):
            for i in range(len(df)-1, -1, -1):
                r = df.iloc[i]
                col_x, col_y = st.columns([4, 1])
                col_x.write(f"👤 {r['Customer']} | 🔢 {r['Number']} | 💵 {r['Amount']} Ks")
                if col_y.button("ဖျက်", key=f"del_{i}"):
                    requests.post(script_url, json={"action": "delete", "row_index": i + 1})
                    st.rerun()

    st.sidebar.divider()
    if st.sidebar.button("⚠️ စာရင်းအားလုံးဖျက်မည်"):
        requests.post(script_url, json={"action": "clear_all"})
        time.sleep(1)
        st.rerun()
