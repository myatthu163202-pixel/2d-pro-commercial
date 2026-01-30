import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time
import re

st.set_page_config(page_title="2D Agent Pro (Commercial)", layout="wide")

st.sidebar.title("🛠 Software Setup")
with st.sidebar.expander("🔗 လင့်များ ချိတ်ဆက်ရန်", expanded=True):
    user_sheet_url = st.text_input("1. Google Sheet URL")
    user_script_url = st.text_input("2. Apps Script URL")

if not user_sheet_url or not user_script_url:
    st.info("👋 မင်္ဂလာပါ။ စတင်ရန် Sidebar တွင် လင့်များ ထည့်ပေးပါ။")
    st.stop()

# --- Sheet Link ကို Clean လုပ်ပေးသည့်အပိုင်း ---
def get_csv_url(url):
    # Sheet ID ကိုပဲ ဆွဲထုတ်ပြီး CSV Link ပြန်ဆောက်ပေးခြင်း
    sheet_id_match = re.search(r"/d/([^/]*)", url)
    if sheet_id_match:
        sheet_id = sheet_id_match.group(1)
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    return None

csv_clean_url = get_csv_url(user_sheet_url)

if not csv_clean_url:
    st.error("❌ Google Sheet URL ပုံစံ မှားယွင်းနေပါသည်။")
    st.stop()

# ဒေတာဆွဲယူခြင်း
try:
    def load_data():
        res = requests.get(f"{csv_clean_url}&cache={time.time()}")
        data = pd.read_csv(csv_clean_url)
        if not data.empty:
            data.columns = data.columns.str.strip()
            data['Number'] = data['Number'].astype(str).str.zfill(2)
            data['Amount'] = pd.to_numeric(data['Amount'], errors='coerce').fillna(0)
        return data
    df = load_data()
except Exception as e:
    st.error(f"❌ ချိတ်ဆက်၍မရပါ။ Sheet ကို 'Anyone with the link' ပေးထားပါသလား ပြန်စစ်ပါ။")
    st.stop()

# --- မင်းသဘောကျသော Dashboard Layout (အရင်အတိုင်း) ---
st.title("💰 2D Agent Pro Dashboard")

st.sidebar.header("⚙️ Admin Settings")
win_num = st.sidebar.text_input("🎰 ပေါက်ဂဏန်း", max_chars=2)
za_rate = st.sidebar.number_input("💰 ဇ (အဆ)", value=80)

total_in = df['Amount'].sum() if not df.empty else 0
st.info(f"💵 စုစုပေါင်းရောင်းရငွေ: {total_in:,.0f} Ks")

c1, c2 = st.columns([1, 2])

with c1:
    st.subheader("📝 စာရင်းသွင်းရန်")
    with st.form("entry_form", clear_on_submit=True):
        name = st.text_input("နာမည်")
        num = st.text_input("ဂဏန်း", max_chars=2)
        amt = st.number_input("ငွေပမာဏ", min_value=100, step=100)
        if st.form_submit_button("✅ သိမ်းဆည်းမည်"):
            if name and num:
                tz_mm = timezone(timedelta(hours=6, minutes=30))
                now_mm = datetime.now(tz_mm).strftime("%I:%M %p")
                payload = {"action": "insert", "Customer": name.strip(), "Number": str(num).zfill(2), "Amount": int(amt), "Time": now_mm}
                requests.post(user_script_url, json=payload)
                st.success("သိမ်းပြီးပါပြီ။")
                time.sleep(1)
                st.rerun()

with c2:
    st.subheader("📊 အရောင်းဇယား")
    if st.button("🔄 Refresh"):
        st.rerun()
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        if win_num:
            winners = df[df['Number'] == win_num].copy()
            total_out = winners['Amount'].sum() * za_rate
            balance = total_in - total_out
            st.divider()
            k1, k2, k3 = st.columns(3)
            k1.metric("🏆 ပေါက်သူ", f"{len(winners)} ဦး")
            k2.metric("💸 လျော်ကြေး", f"{total_out:,.0f} Ks")
            k3.metric("💹 အမြတ်/အရှုံး", f"{balance:,.0f} Ks", delta=balance)
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
