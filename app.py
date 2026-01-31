import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests, time, re, json, hashlib

# =========================
# Page Setup
# =========================
st.set_page_config(
    page_title="2D Agent Pro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Time & Limit Setup
# =========================
MM_TZ = timezone(timedelta(hours=6, minutes=30))  
TODAY = datetime.now(MM_TZ).strftime("%Y-%m-%d")

# =========================
# User Database (Hardcoded)
# =========================
USERS_DATABASE = {
    "admin": {
        "password": "1632022",  # Admin password
        "sheet_url": "",
        "script_url": "",
        "number_limit": 50000,
        "za_rate": 80
    }
    # Add more users here in format:
    # "username": {
    #     "password": "password123",
    #     "sheet_url": "",
    #     "script_url": "",
    #     "number_limit": 50000,
    #     "za_rate": 80
    # }
}

# =========================
# Session State Setup
# =========================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.user_data = None
    st.session_state.debug_mode = False
    st.session_state.last_refresh = None
    st.session_state.show_links = True

# =========================
# Login Page
# =========================
if not st.session_state.authenticated:
    st.title("🔐 2D Agent Pro - Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("### အကောင့်ဝင်ရန်")
            
            username = st.text_input("👤 Username", key="login_username")
            password = st.text_input("🔒 Password", type="password", key="login_password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🚀 Login", type="primary", use_container_width=True):
                    if username in USERS_DATABASE:
                        if USERS_DATABASE[username]["password"] == password:
                            st.session_state.authenticated = True
                            st.session_state.current_user = username
                            st.session_state.user_data = USERS_DATABASE[username].copy()
                            st.session_state.last_refresh = datetime.now()
                            st.rerun()
                        else:
                            st.error("❌ Password မှားနေပါသည်")
                    else:
                        st.error("❌ Username မရှိပါ")
            
            with col_btn2:
                if st.button("➕ Add User", use_container_width=True):
                    st.switch_page("?add_user=true") if "add_user" not in st.query_params else None
    
    # User Management Section (Visible to all)
    with st.container(border=True):
        st.markdown("### 👥 အကောင့်များ")
        
        # Add new user form
        if st.query_params.get("add_user") == "true":
            st.markdown("#### အကောင့်အသစ်ထည့်ရန်")
            
            admin_user = st.text_input("Admin Username", key="admin_user_add")
            admin_pass = st.text_input("Admin Password", type="password", key="admin_pass_add")
            new_user = st.text_input("အကောင့်အသစ် Username", key="new_user_add")
            new_pass = st.text_input("အကောင့်အသစ် Password", type="password", key="new_pass_add")
            
            if st.button("အကောင့်ထည့်မည်", type="primary"):
                # Verify admin credentials
                if admin_user == "admin" and admin_pass == "1632022":
                    if new_user and new_pass:
                        if new_user not in USERS_DATABASE:
                            # Update the users database
                            USERS_DATABASE[new_user] = {
                                "password": new_pass,
                                "sheet_url": "",
                                "script_url": "",
                                "number_limit": 50000,
                                "za_rate": 80
                            }
                            st.success(f"✅ {new_user} အကောင့်ထည့်ပြီးပါပြီ")
                            time.sleep(2)
                            st.query_params.clear()
                            st.rerun()
                        else:
                            st.error("❌ Username ရှိပြီးသားဖြစ်နေပါသည်")
                    else:
                        st.error("❌ Username နှင့် Password ထည့်ပါ")
                else:
                    st.error("❌ Admin credentials မှားနေပါသည်")
            
            if st.button("မထည့်တော့ပါ", type="secondary"):
                st.query_params.clear()
                st.rerun()
        else:
            # Show existing users
            if USERS_DATABASE:
                user_list = list(USERS_DATABASE.keys())
                cols = 3
                rows = (len(user_list) + cols - 1) // cols
                
                for i in range(rows):
                    col_list = st.columns(cols)
                    for j in range(cols):
                        idx = i * cols + j
                        if idx < len(user_list):
                            username = user_list[idx]
                            with col_list[j]:
                                st.text(f"👤 {username}")
                                if username != "admin":
                                    if st.button(f"🗑️", key=f"del_{username}"):
                                        # Only admin can delete
                                        st.warning(f"{username} ကိုဖျက်ရန် admin ဝင်ရောက်ပါ")
            else:
                st.info("📭 အကောင့်မရှိသေးပါ")
            
            if st.button("➕ Add New User", type="secondary"):
                st.query_params["add_user"] = "true"
                st.rerun()
    
    st.stop()

# =========================
# Main Application (After Login)
# =========================
user = st.session_state.current_user
user_data = st.session_state.user_data

# =========================
# Sidebar
# =========================
with st.sidebar:
    st.title(f"👤 {user}")
    
    if user == "admin":
        st.success("👑 Admin Account")
    else:
        st.info("👤 User Account")
    
    st.divider()
    
    # Debug mode toggle
    debug_mode = st.checkbox("🐛 Debug Mode", value=st.session_state.debug_mode)
    if debug_mode != st.session_state.debug_mode:
        st.session_state.debug_mode = debug_mode
        st.rerun()
    
    # Link management
    toggle_text = "🔒 Link ဖွက်ရန်" if st.session_state.show_links else "🔓 Link ပြရန်"
    if st.button(toggle_text, use_container_width=True):
        st.session_state.show_links = not st.session_state.show_links
        st.rerun()
    
    if st.session_state.show_links:
        with st.container(border=True):
            st.markdown("#### 🔗 System Links")
            
            sheet_url = st.text_input(
                "📊 Google Sheet URL", 
                value=user_data.get("sheet_url", ""),
                placeholder="https://docs.google.com/spreadsheets/d/...",
                help="ဒေတာသိမ်းမည့် Google Sheet link",
                key=f"sheet_{user}"
            )
            
            script_url = st.text_input(
                "🔄 Apps Script URL", 
                value=user_data.get("script_url", ""),
                placeholder="https://script.google.com/macros/s/.../exec",
                help="ဒေတာလက်ခံမည့် Apps Script Web App link",
                key=f"script_{user}"
            )
            
            if sheet_url != user_data.get("sheet_url", ""):
                user_data["sheet_url"] = sheet_url
                USERS_DATABASE[user]["sheet_url"] = sheet_url
                st.success("✅ Sheet URL saved!")
            
            if script_url != user_data.get("script_url", ""):
                user_data["script_url"] = script_url
                USERS_DATABASE[user]["script_url"] = script_url
                st.success("✅ Script URL saved!")
            
            if script_url:
                try:
                    test_response = requests.get(script_url, timeout=5)
                    if test_response.status_code == 200:
                        st.success("✅ Script connected")
                    else:
                        st.warning(f"⚠️ Script responded with {test_response.status_code}")
                except:
                    st.error("❌ Cannot connect to script")
    
    st.divider()
    
    # User settings
    st.markdown("### ⚡ Settings")
    
    number_limit = st.number_input(
        "🎯 ဂဏန်း Limit", 
        value=user_data.get("number_limit", 50000), 
        min_value=1000, 
        step=1000,
        help="ဂဏန်းတစ်ခုချင်းစီအတွက် အများဆုံးထိုးနိုင်သောပမာဏ",
        key=f"limit_{user}"
    )
    
    za_rate = st.number_input(
        "💰 ဇ (အဆ)", 
        value=user_data.get("za_rate", 80), 
        min_value=1, 
        step=1,
        help="ပေါက်ငွေတွက်ချက်ရာတွင် အမြတ်အဆ",
        key=f"za_rate_{user}"
    )
    
    # Save settings
    if number_limit != user_data.get("number_limit", 50000):
        user_data["number_limit"] = number_limit
        USERS_DATABASE[user]["number_limit"] = number_limit
    
    if za_rate != user_data.get("za_rate", 80):
        user_data["za_rate"] = za_rate
        USERS_DATABASE[user]["za_rate"] = za_rate
    
    st.divider()
    
    # Win number check
    st.markdown("### 🎲 ပေါက်ဂဏန်းစစ်")
    win_number = st.text_input("ပေါက်ဂဏန်း", max_chars=2, label_visibility="collapsed")
    
    st.divider()
    
    # System info
    st.markdown("### ℹ️ System Info")
    st.caption(f"📅 ရက်စွဲ: {TODAY}")
    st.caption(f"🎯 Limit: {number_limit:,} ကျပ်")
    st.caption(f"💰 ဇအဆ: {za_rate}")
    
    if st.session_state.last_refresh:
        last_refresh_time = st.session_state.last_refresh.strftime("%I:%M:%S %p")
        st.caption(f"🕐 Last update: {last_refresh_time}")
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.session_state.last_refresh = datetime.now()
        st.rerun()
    
    # Admin features
    if user == "admin":
        st.divider()
        st.markdown("### 👑 Admin Tools")
        if st.button("👥 Manage Users", use_container_width=True):
            st.session_state.authenticated = False
            st.query_params.clear()
            st.rerun()
    
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.user_data = None
        st.rerun()

# Get user settings
sheet = user_data.get("sheet_url", "")
script = user_data.get("script_url", "")
NUMBER_LIMIT = user_data.get("number_limit", 50000)
ZA_RATE = user_data.get("za_rate", 80)

# =========================
# Debug Functions
# =========================
def debug_log(message, data=None):
    """Log debug messages if debug mode is enabled"""
    if st.session_state.debug_mode:
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.markdown(f"`[{timestamp}] {message}`")
        if data is not None:
            st.json(data)

# =========================
# Load Google Sheet
# =========================
def csv_url(url):
    """Convert Google Sheet URL to CSV export URL"""
    try:
        m = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
        if m:
            file_id = m.group(1)
            return f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv"
        return ""
    except Exception as e:
        debug_log(f"Error parsing sheet URL: {str(e)}")
        return ""

def load_sheet_data():
    """Load data from Google Sheet"""
    try:
        if not sheet:
            st.error("⚠️ Google Sheet URL မထည့်ရသေးပါ")
            return None, None
        
        csv_url_str = csv_url(sheet)
        if not csv_url_str:
            st.error("❌ Google Sheet URL မှားယွင်းနေပါသည်")
            return None, None
        
        full_url = f"{csv_url_str}&t={int(time.time())}"
        debug_log(f"Loading data from: {full_url}")
        
        df = pd.read_csv(full_url)
        debug_log(f"Raw data loaded: {len(df)} rows, {len(df.columns)} columns")
        
        df.columns = df.columns.str.strip()
        debug_log("Columns after cleaning:", list(df.columns))
        
        required_columns = ["Date", "Time", "Customer", "Number", "Amount", "Receipt"]
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""
                debug_log(f"Added missing column: {col}")
        
        df["Number"] = df["Number"].astype(str).str.zfill(2)
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
        
        df['sheet_row'] = df.index + 2
        
        today_df = df[df["Date"] == TODAY].copy()
        
        debug_log(f"Data processing complete - Total rows: {len(df)}, Today's rows: {len(today_df)}")
        
        return df, today_df
        
    except Exception as e:
        st.error(f"❌ Sheet ချိတ်ဆက်မှု အမှားအယွင်းရှိနေပါသည်: {str(e)}")
        debug_log(f"Error details: {str(e)}")
        return None, None

# Load data
df, today_df = load_sheet_data()

if df is None or today_df is None:
    st.warning("📋 ဒေတာမရှိသေးပါ / Setup မပြည့်စုံသေးပါ")
    
    with st.expander("🔧 Setup Instructions", expanded=True):
        st.markdown("""
        ### 📝 Setup လုပ်ရန်
        
        1. Sidebar မှာ **"Link ပြရန်"** ကိုနှိပ်ပါ
        2. Google Sheet URL နှင့် Apps Script URL ထည့်ပါ
        3. Save လုပ်ပါ
        
        **Sample Data Structure:**
        | Date | Time | Customer | Number | Amount | Receipt |
        |------|------|----------|--------|--------|---------|
        | 2024-01-20 | 10:30 AM | ဉာဏ်လင်း | 12 | 1000 | R-2024-01-20-0001 |
        """)
    st.stop()

# =========================
# Dashboard
# =========================
st.title(f"💰 2D Agent Pro - {user}")

# Stats row
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_today = today_df['Amount'].sum()
    st.metric("📊 ဒီနေ့စုစုပေါင်း", f"{total_today:,.0f} ကျပ်")
with col2:
    total_transactions = len(today_df)
    st.metric("🔄 ဒီနေ့လုပ်ဆောင်ချက်", f"{total_transactions}")
with col3:
    avg_amount = total_today / total_transactions if total_transactions > 0 else 0
    st.metric("📈 ပျမ်းမျှထိုးငွေ", f"{avg_amount:,.0f} ကျပ်")
with col4:
    if not today_df.empty:
        popular_num = today_df.groupby('Number')['Amount'].sum().idxmax()
        popular_amount = today_df.groupby('Number')['Amount'].sum().max()
        st.metric("🔥 လူကြိုက်အများဆုံး", f"{popular_num} ({popular_amount:,.0f})")

st.divider()

# =========================
# New Entry
# =========================
with st.expander("📝 စာရင်းအသစ်ထည့်ရန်", expanded=True):
    with st.form("new_entry", clear_on_submit=True, border=True):
        st.markdown("### အချက်အလက်အသစ်ထည့်ပါ")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("👤 ထိုးသူအမည်", placeholder="ဉာဏ်လင်း")
        with c2:
            number = st.text_input("🔢 ထိုးမည့်ဂဏန်း", placeholder="12", max_chars=2)
        with c3:
            amount = st.number_input("💰 ပိုက်ဆံပမာဏ", min_value=100, step=100, value=1000)
        
        if number:
            number = number.zfill(2)
            used_amount = today_df[today_df["Number"] == number]["Amount"].sum()
            remaining = NUMBER_LIMIT - used_amount
            
            if remaining <= 0:
                st.error(f"❌ ဂဏန်း {number} သည် Limit ပြည့်သွားပါပြီ")
            elif amount > remaining:
                st.warning(f"⚠️ ဂဏန်း {number} အတွက် {remaining:,} ကျပ် သာကျန်ပါသည်")
            else:
                st.success(f"✅ ဂဏန်း {number} အတွက် {remaining:,.0f} ကျပ် ကျန်ပါသည်")
        
        submit = st.form_submit_button("💾 သိမ်းမည်", type="primary", use_container_width=True)
        
        if submit:
            if not name or not number:
                st.error("❌ ထိုးသူအမည်နှင့် ဂဏန်းထည့်ပါ")
            else:
                number = number.zfill(2)
                used_amount = today_df[today_df["Number"] == number]["Amount"].sum()
                
                if used_amount + amount > NUMBER_LIMIT:
                    st.error(f"❌ ဂဏန်း {number} သည် Limit {NUMBER_LIMIT:,} ကျပ် ကျော်နေပါပြီ")
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
                    
                    debug_log("Sending insert request:", payload)
                    
                    try:
                        with st.spinner("🔄 သိမ်းနေသည်..."):
                            resp = requests.post(script, json=payload, timeout=10)
                            debug_log(f"Response status: {resp.status_code}")
                            debug_log(f"Response body: {resp.text}")
                            
                            if resp.status_code == 200:
                                result = resp.json()
                                st.success(f"✅ {result.get('status', 'သိမ်းပြီးပါပြီ')}")
                                time.sleep(1)
                                st.session_state.last_refresh = datetime.now()
                                st.rerun()
                            else:
                                st.error(f"❌ အမှားအယွင်း: {resp.status_code} - {resp.text}")
                    except requests.exceptions.Timeout:
                        st.error("⏱️ Request timeout. Script က response မပြန်ပါ")
                    except requests.exceptions.ConnectionError:
                        st.error("🔌 Connection error. Script URL ကို ပြန်စစ်ပါ")
                    except Exception as e:
                        st.error(f"❌ မမျှော်လင့်သောအမှား: {str(e)}")

# =========================
# Win Number Check
# =========================
if win_number and win_number.strip():
    win_number = win_number.zfill(2)
    winners = today_df[today_df["Number"] == win_number].copy()
    
    if not winners.empty:
        winners["လျော်ကြေး"] = winners["Amount"] * ZA_RATE
        total_payout = winners["လျော်ကြေး"].sum()
        
        st.success(f"🎉 ပေါက်သူများ (ဂဏန်း: {win_number}) - စုစုပေါင်းလျော်ကြေး: {total_payout:,.0f} ကျပ်")
        
        display_df = winners[["Customer", "Number", "Amount", "လျော်ကြေး"]].copy()
        display_df["Amount"] = display_df["Amount"].apply(lambda x: f"{x:,.0f}")
        display_df["လျော်ကြေး"] = display_df["လျော်ကြေး"].apply(lambda x: f"{x:,.0f}")
        
        st.dataframe(
            display_df,
            column_config={
                "Customer": "အမည်",
                "Number": "ဂဏန်း",
                "Amount": "ထိုးငွေ",
                "လျော်ကြေး": "လျော်ကြေး"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info(f"ℹ️ ဂဏန်း {win_number} ပေါက်သူမရှိပါ")

st.divider()

# =========================
# Edit Records
# =========================
st.subheader("✏️ ဒီနေ့စာရင်းများ ပြန်ပြင်ရန်")

if today_df.empty:
    st.info("📭 ဒီနေ့စာရင်းမရှိသေးပါ")
else:
    for i, r in today_df.iterrows():
        with st.expander(f"**{r.Customer}** | ဂဏန်း: {r.Number} | ငွေပမာဏ: {r.Amount:,.0f} ကျပ် | အချိန်: {r.Time}"):
            with st.form(f"edit_{i}", border=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    en = st.text_input("👤 အမည်", value=r.Customer, key=f"name_{i}")
                with col2:
                    nu = st.text_input("🔢 ဂဏန်း", value=r.Number, max_chars=2, key=f"num_{i}")
                with col3:
                    am = st.number_input("💰 ပမာဏ", value=int(r.Amount), min_value=100, step=100, key=f"amt_{i}")
                
                if st.form_submit_button("🔄 ပြင်မည်", use_container_width=True):
                    nu = nu.zfill(2)
                    
                    if nu != r.Number:
                        used_amount = today_df[today_df["Number"] == nu]["Amount"].sum()
                        if used_amount + am > NUMBER_LIMIT:
                            st.error(f"❌ ဂဏန်း {nu} သည် Limit ကျော်သွားမည်")
                        else:
                            update_record(r.sheet_row, en, nu, am)
                    else:
                        update_record(r.sheet_row, en, nu, am)

def update_record(row, customer, number, amount):
    """Update a record in the Google Sheet"""
    payload = {
        "action": "update",
        "row": int(row),
        "Customer": customer,
        "Number": number,
        "Amount": int(amount)
    }
    
    debug_log("Sending update request:", payload)
    
    try:
        with st.spinner("ပြင်နေသည်..."):
            resp = requests.post(script, json=payload, timeout=10)
            debug_log(f"Update response: {resp.status_code} - {resp.text}")
            
            if resp.status_code == 200:
                st.success("✅ ပြင်ပြီးပါပြီ")
                time.sleep(1)
                st.session_state.last_refresh = datetime.now()
                st.rerun()
            else:
                st.error(f"❌ Update failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        st.error(f"❌ Update error: {str(e)}")

st.divider()

# =========================
# Table & Search
# =========================
st.subheader("📋 ဒီနေ့စာရင်းဇယား")

search_col1, search_col2 = st.columns([3, 1])
with search_col1:
    search = st.text_input("🔍 နာမည်ဖြင့်ရှာရန်", placeholder="ထိုးသူအမည်ရိုက်ထည့်ပါ...")
with search_col2:
    sort_by = st.selectbox("အစဉ်လိုက်စီရန်", ["Time", "Amount", "Number", "Customer"])

view_df = today_df.drop(columns=['sheet_row']).copy()

if search:
    view_df = view_df[view_df["Customer"].str.contains(search, case=False, na=False)]

if sort_by == "Amount":
    view_df = view_df.sort_values(by="Amount", ascending=False)
elif sort_by == "Number":
    view_df = view_df.sort_values(by="Number")
elif sort_by == "Customer":
    view_df = view_df.sort_values(by="Customer")
else:
    view_df = view_df.sort_values(by="Time", ascending=False)

st.caption(f"📊 စုစုပေါင်း {len(view_df)} ခု | စုစုပေါင်းငွေ: {view_df['Amount'].sum():,.0f} ကျပ်")

if not view_df.empty:
    display_df = view_df.copy()
    display_df["Amount"] = display_df["Amount"].apply(lambda x: f"{x:,.0f}")
    
    st.dataframe(
        display_df,
        column_config={
            "Date": st.column_config.TextColumn("ရက်စွဲ"),
            "Time": st.column_config.TextColumn("အချိန်"),
            "Customer": st.column_config.TextColumn("ထိုးသူ"),
            "Number": st.column_config.TextColumn("ဂဏန်း"),
            "Amount": st.column_config.TextColumn("ငွေပမာဏ"),
            "Receipt": st.column_config.TextColumn("ရက်စဘွယ်")
        },
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("🔍 ရှာတွေ့သော စာရင်းများမရှိပါ")

st.divider()

# =========================
# Export & Clear Today
# =========================
st.subheader("📤 Export & Management")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("### 📄 Data Export")
        
        export_format = st.radio("ဖိုင်အမျိုးအစား", ["CSV", "Excel"], horizontal=True)
        
        if not view_df.empty:
            if export_format == "CSV":
                csv_data = view_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "💾 CSV ဒေါင်းလုဒ်",
                    csv_data,
                    f"2d_data_{TODAY}_{user}.csv",
                    "text/csv",
                    use_container_width=True
                )
            else:
                excel_data = view_df.to_excel(index=False, engine='openpyxl')
                st.download_button(
                    "💾 Excel ဒေါင်းလုဒ်",
                    excel_data,
                    f"2d_data_{TODAY}_{user}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.warning("ဒေါင်းလုဒ်ရန် ဒေတာမရှိပါ")

with col2:
    with st.container(border=True):
        st.markdown("### 🗑️ Data Management")
        
        st.warning("""
        ⚠️ သတိပေးချက်:
        ဒီနေ့စာရင်းအားလုံး **အပြီးအပိုင် ပျက်သွားမည်**။
        မဖျက်ခင် ဒေါင်းလုဒ်ယူထားပါ။
        """)
        
        confirm = st.checkbox("ဖျက်ရန် သေချာပါသည်", key=f"delete_confirm_{user}")
        
        if st.button("🔥 ဒီနေ့စာရင်း အကုန်ဖျက်", 
                    disabled=not confirm or today_df.empty,
                    type="secondary",
                    use_container_width=True):
            
            with st.spinner("ဖျက်နေသည်..."):
                try:
                    payload = {"action": "clear_today", "date": TODAY}
                    debug_log("Sending clear_today request:", payload)
                    
                    response = requests.post(
                        script, 
                        json=payload,
                        timeout=30
                    )
                    
                    debug_log(f"Clear response: {response.status_code} - {response.text}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ {result.get('status', 'အောင်မြင်စွာဖျက်ပြီးပါပြီ')}")
                        
                        st.balloons()
                        time.sleep(2)
                        st.session_state.last_refresh = datetime.now()
                        st.rerun()
                    else:
                        st.error(f"❌ Error {response.status_code}: {response.text}")
                        
                except requests.exceptions.Timeout:
                    st.error("⏱️ Request timeout. Script က response မပြန်ပါ")
                except requests.exceptions.ConnectionError:
                    st.error("🔌 Connection error. Script URL ကို ပြန်စစ်ပါ")
                except Exception as e:
                    st.error(f"❌ အမှားအယွင်း: {str(e)}")

# =========================
# Debug Panel
# =========================
if st.session_state.debug_mode:
    with st.expander("🐛 Debug Information", expanded=False):
        st.subheader("System Information")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current User", user)
            st.metric("Number Limit", f"{NUMBER_LIMIT:,}")
        with col2:
            st.metric("Sheet URL", sheet[:50] + "..." if len(sheet) > 50 else sheet)
            st.metric("Script URL", script[:50] + "..." if len(script) > 50 else script)
        
        st.subheader("Data Preview")
        tab1, tab2 = st.tabs(["Today's Data", "All Data"])
        
        with tab1:
            st.dataframe(today_df, use_container_width=True)
        
        with tab2:
            st.dataframe(df, use_container_width=True)

# =========================
# Footer
# =========================
st.divider()
footer_col1, footer_col2, footer_col3 = st.columns(3)
with footer_col1:
    st.caption(f"👤 User: {user}")
    st.caption(f"🕐 Last update: {datetime.now(MM_TZ).strftime('%I:%M:%S %p')}")
with footer_col2:
    st.caption(f"📅 Date: {TODAY}")
    st.caption(f"🎯 Limit: {NUMBER_LIMIT:,} ကျပ်")
with footer_col3:
    st.caption("💻 2D Agent Pro v2.0")
    st.caption(f"💰 Za Rate: {ZA_RATE}")
