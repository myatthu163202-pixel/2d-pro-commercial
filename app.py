import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time

st.set_page_config(page_title="2D Agent Pro (Commercial)", layout="wide")

# --- Software Setup (ဝယ်သူက မိမိလင့်ကို မိမိထည့်ရန်) ---
st.sidebar.title("🛠 Software Setup")
with st.sidebar.expander("လင့်များ ချိတ်ဆက်ရန်", expanded=True):
    st.info("ဝယ်ယူထားသော ကုဒ်ကို အသုံးပြုရန် အောက်ပါလင့်များ ထည့်ပေးပါ။")
    user_sheet_url = st.text_input("1. Google Sheet URL", placeholder="https://docs.google.com/spreadsheets/d/...")
    user_script_url = st.text_input("2. Apps Script URL", placeholder="https://script.google.com/macros/s/...")

# လင့်မထည့်မချင်း App ကို ပေးမသုံးပါ
if not user_sheet_url or not user_script_url:
    st.markdown("### 👋 2D Agent Pro မှ ကြိုဆိုပါတယ်!\nစတင်အသုံးပြုရန် Sidebar တွင် လင့်များ အရင်ချိတ်ပေးပါ။")
    st.stop()

# ဒေတာဆွဲယူခြင်း
try:
    csv_url = user_sheet_url.replace('/edit', '/export?format=csv')
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
    st.error("❌ Link ချိတ်ဆက်မှု မှားယွင်းနေပါသည်။ Google Sheet ကို Anyone with the link ပေးထားပါသလား ပြန်စစ်ပါ။")
    st.stop()

# --- Dashboard Layout ---
st.title("💰 2D Agent Pro Dashboard")

st.sidebar.header("⚙️ Admin & Win Check")
win_num = st.sidebar.text_input("🎰 ပေါက်ဂဏန်းရိုက်ပါ", max_chars=2)
za_rate = st.sidebar.number_input("💰 ဇ (အဆ)", value=80)

total_in = df['Amount'].sum() if not df.empty else 0
st.info(f"💵 စုစုပေါင်းရောင်းရငွေ: {total_in:,.0f} Ks")

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
                
                payload = {
                    "action": "insert", "Customer": name.strip(), 
                    "Number": str(num).zfill(2), "Amount": int(amt), "Time": now_mm
                }
                requests.post(user_script_url, json=payload)
                st.success("သိမ်းပြီးပါပြီ။")
                time.sleep(1)
                st.rerun()

with c2:
    st.subheader("📊 အရောင်းဇယား")
    if st.button("🔄 Refresh"):
        st.rerun()
    search = st.text_input("🔎 နာမည်ဖြင့်ရှာရန်")

    if not df.empty:
        view_df = df[df['Customer'].str.contains(search, case=False, na=False)] if search else df
        st.dataframe(view_df, use_container_width=True, hide_index=True)

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
    st.subheader("🗑 စာရင်းဖျက်ရန်")
    with st.expander("တစ်ခုချင်းစီ ဖျက်ရန်"):
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
