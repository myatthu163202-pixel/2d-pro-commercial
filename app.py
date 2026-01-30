# --- ၆။ Data Loading (ဇယားမှာ အသစ်ပေါ်အောင် Cache ဖျက်ပြီး ဆွဲခိုင်းခြင်း) ---
def get_csv_url(url):
    m = re.search(r"/d/([^/]*)", url)
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv" if m else None

try:
    csv_url = get_csv_url(sheet_url)
    # cachebuster ထည့်ထားတဲ့အတွက် Browser က ဒေတာအဟောင်းကို မသုံးတော့ဘဲ အသစ်ကိုပဲ အမြဲဆွဲပါမယ်
    df = pd.read_csv(f"{csv_url}&cachebuster={int(time.time())}")
    df.columns = df.columns.str.strip()
    df['Number'] = df['Number'].astype(str).str.zfill(2)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
except Exception as e:
    # f-string syntax error များကို ဤနေရာတွင် ပြင်ထားသည်
    st.error(f"❌ ဒေတာဆွဲမရပါ။ Link ပြန်စစ်ပါ။")
    st.stop()

# --- ၉။ ပြင်ဆင်ခြင်း (ဒေတာပြင်ပြီးနောက် ဇယားကို ၂ စက္ကန့်စောင့်ပြီး Update လုပ်ခိုင်းခြင်း) ---
with col_edit:
    st.subheader("⚙️ တစ်ခုချင်းစီ ပြင်ဆင်ရန် (မဖျက်ပါ)")
    if not df.empty:
        for i, row in df.iterrows():
            with st.expander(f"👤 {row['Customer']} | 🔢 {row['Number']}"):
                with st.form(f"edit_{i}"):
                    e_name = st.text_input("အမည်ပြင်ရန်", value=row['Customer'])
                    e_num = st.text_input("ဂဏန်းပြင်ရန်", value=row['Number'], max_chars=2)
                    e_amt = st.number_input("ပမာဏပြင်ရန်", value=int(row['Amount']))
                    if st.form_submit_button("💾 သိမ်းဆည်းမည်"):
                        try:
                            # Google Apps Script ထံသို့ ပြင်ဆင်ရန် ပို့ခြင်း
                            requests.post(script_url, json={
                                "action": "update", "row_index": int(i)+2,
                                "Customer": e_name, "Number": str(e_num).zfill(2), "Amount": int(e_amt)
                            })
                            # အောက်က စာသားပေါ်ပြီးလျှင် ဇယားမှာ ချက်ချင်း Update ဖြစ်သွားပါလိမ့်မည်
                            st.success("✅ ပြင်ဆင်ပြီးပါပြီ။ ဇယားကို Update လုပ်နေသည်...")
                            # Google Sheet ထဲမှာ ဒေတာသွားပြင်ချိန်ကို ၂ စက္ကန့် စောင့်ပေးခြင်း
                            time.sleep(2) 
                            st.rerun()
                        except Exception:
                            st.error("❌ ပြင်မရပါ။")
