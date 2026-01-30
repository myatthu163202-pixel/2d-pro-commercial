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

# --- ၃။ လင့်ခ်များကို ဤနေရာတွင် အသေထည့်ပါ (ဒါမှ တစ်ခါထည့်ရင် ထပ်မတောင်းမှာ) ---
# ဒီမျက်တောင်ဖွင့်ပိတ်ထဲမှာ မင်းရဲ့ လင့်ခ်အစစ်တွေကို ကူးထည့်လိုက်ပါ
DEFAULT_SHEET_URL = "YOUR_SHEET_URL" 
DEFAULT_SCRIPT_URL = "YOUR_SCRIPT_URL"

# --- ၄။ Login စနစ် ---
def check_password():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        st.markdown("<h2 style='text-align: center;'>🔐 Member Login</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
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
    # --- Sidebar Section ---
    st.sidebar.title(f"👋 မင်္ဂလာပါ {st.session_state['username']}")
    
    # Setup ကို Expander ထဲမှာပဲ ထားပေးထားပါတယ်
    with st.sidebar.expander("🛠 Software Setup (Link များ)", expanded=False):
        # value=DEFAULT_SHEET_URL ကြောင့် အမြဲတမ်း မှတ်နေမှာပါ
        user_sheet_url = st.text_input("Google Sheet URL", value=DEFAULT_SHEET_URL)
        user_script_url = st.text_input("Apps Script URL", value=DEFAULT_SCRIPT_URL)

    if not user_sheet_url or not user_script_url or user_sheet_url == "YOUR_SHEET_URL":
        st.info("💡 GitHub ကုဒ်ထဲတွင် လင့်ခ်များကို အရင်ဆုံး အစားထိုးထည့်ပေးပါ။")
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
        st.error("❌ ချိတ်ဆက်မှု မှားယွင်းနေပါသည်။")
        st.stop()

    # --- ၅။ Dashboard (မင်းကြိုက်တဲ့ Layout အတိုင်း) ---
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
                k2.metric("💸 လျော်ကြေး", f"{total_out:
