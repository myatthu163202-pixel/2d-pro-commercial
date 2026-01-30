import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time
import re

# --- ၁။ Page အပြင်အဆင် ---
st.set_page_config(page_title="2D Agent Pro (Secure)", layout="wide", page_icon="💰")

# --- ၂။ VIP User စာရင်း ---
USERS = {
    "admin": "123456"
}

# --- ၃။ Login စနစ် ---
def check_password():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        st.markdown("<h2 style='text-align: center;'>🔐 Member Login</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            user = st.text_input("Username", key="login_user")
            pw = st.text_input("Password", type="password", key="login_pw")
            if st.button("Login", use_container_width=True):
                if user in USERS and USERS[user] == pw:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = user
                    st.rerun()
                else:
                    st.error("❌ Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
        return False
    return True

if check_password():
    # --- Sidebar Section (Link များကို Refresh လုပ်လည်း မှတ်မိနေစေရန်) ---
    st.sidebar.title(f"👋 မင်္ဂလာပါ {st.session_state['username']}")
    
    # Session ထဲမှာ Link တွေရှိမရှိ စစ်မယ်
    if "stored_sheet" not in st.session_state: st.session_state["stored_sheet"] = ""
    if "stored_script" not in st.session_state: st.session_state["stored_script"] = ""

    with st.sidebar.expander("🛠 Software Setup (Link များ)", expanded=True):
        user_sheet_url = st.text_input("Google Sheet URL", value=st.session_state["stored_sheet"])
        user_script_url = st.text_input("Apps Script URL", value=st.session_state["stored_script"])
        
        # ရိုက်ထည့်လိုက်တဲ့ Link တွေကို Session ထဲမှာ အမြဲမှတ်ထားမယ်
        st.session_state["stored_sheet"] = user_sheet_url
        st.session_state["stored_script"] = user_script_url

    if not user_sheet_url or not user_script_url:
        st.info("💡 Link များကို တစ်ခါပဲ ထည့်ပေးပါ။ Refresh လုပ်လည်း မှတ်မိနေပါလိမ့်မယ်။")
        st.stop()

    # URL မှ ID ကိုယူသည့် Function
    def get_csv_url(url):
        sheet_id_match = re.search(r"/d/([^/]*)", url)
        if sheet_id_match:
            sheet_id = sheet_id_match.group(1)
            return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        return None

    csv_clean_url = get_csv_url(user_sheet_url)

    # ဒေတာဆွဲယူခြင်း
    try:
        def load_data():
            url = f"{csv_clean_url}&cachebuster={int(time.time())}"
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

    # --- ၄။ Dashboard Layout (မင်းကြိုက်တဲ့အတိုင်း မပြောင်းပါ) ---
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
            num = st.text_input("ဂဏန်း (00-99)", max_chars=2)
            amt = st.number_input("ငွေပမာဏ", min_value=100, step=100)
            if st.form_submit_button("✅ သိမ်းဆည်းမည်"):
                if name and num:
                    tz_mm = timezone(timedelta(hours=6, minutes=30))
                    now_mm = datetime.now(tz_mm).strftime("%I:%M %p")
                    payload = {"action": "insert", "Customer": name.strip(), "Number": str(num).zfill(2), "Amount": int(amt), "Time": now_mm}
                    requests.post(user_script_url, json=payload)
                    st.success("စာရင်းသွင်းပြီးပါပြီ။")
                    time.sleep(1)
                    st.rerun()

    with c2:
        st.subheader("📊 အရောင်းဇယား")
        if st.button("🔄 Refresh Data"):
            st.rerun()
            
        if not df.empty:
            search = st.text_input("🔎 နာမည်ဖြင့်ရှာရန်")
            view_df = df[df['Customer'].str.contains(search, case=False, na=False)] if search else df
            st.dataframe(view_df, use_container_width=True, hide_index=True)

            if win_num:
                winners = df[df['Number'] == win_num].copy()
                total_out = winners['Amount'].sum() * za_rate
                balance = total_in - total_out
                st.divider()
                st.subheader("📈 ရလဒ်အကျဉ်းချုပ်")
                k1, k2, k3 = st.columns(3)
                k1.metric("🏆 ပေါက်သူ", f"{len(winners)} ဦး")
                k2.metric("💸 လျော်ကြေး", f"{total_out:,.0f} Ks")
                k3.metric("💹 အမြတ်/အရှုံး", f"{balance:,.0f} Ks", delta=float(balance))
                
                if not winners.empty:
                    winners['လျော်ရမည့်ငွေ'] = winners['Amount'] * za_rate
                    st.table(winners[['Customer', 'Number', 'Amount', 'လျော်ရမည့်ငွေ']])

    if not df.empty:
        st.divider()
        with st.expander("🗑 စာရင်းဖျက်ရန်"):
            for i in range(len(df)-1, -1, -1):
                r = df.iloc[i]
                col_x, col_y = st.columns([4, 1])
                col_x.write(f"👤 {r['Customer']} | 🔢 {r['Number']} | 💵 {r['Amount']} Ks")
                if col_y.button("ဖျက်", key=f"del_{i}"):
                    requests.post(user_script_url, json={"action": "delete", "row_index": i + 1})
                    st.rerun()

    st.sidebar.divider()
    if st.sidebar.button("⚠️ စာရင်းအားလုံးဖျက်မည်"):
        requests.post(user_script_url, json={"action": "clear_all"})
        time.sleep(1)
        st.rerun()
