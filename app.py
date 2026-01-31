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
MAX_NUMBER_LIMIT = 50000  # ဂဏန်းတစ်ကွက်ကို ၅သောင်းကျပ်

# =========================
# User Database
# =========================
USERS_DATABASE = {
    "admin": {
        "password": "1632022",
        "sheet_url": "",
        "script_url": "",
        "za_rate": 80
    }
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
    st.session_state.number_limits_cache = {}  # Cache for number limits

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
    
    # Add User Section
    with st.container(border=True):
        st.markdown("### ➕ အကောင့်အသစ်ထည့်ရန်")
        
        with st.form("add_user_form"):
            admin_user = st.text_input("Admin Username")
            admin_pass = st.text_input("Admin Password", type="password")
            new_user = st.text_input("အကောင့်အသစ် Username")
            new_pass = st.text_input("အကောင့်အသစ် Password", type="password")
            confirm_pass = st.text_input("Password ထပ်ရိုက်ပါ", type="password")
            
            if st.form_submit_button("အကောင့်ထည့်မည်", type="secondary"):
                if admin_user == "admin" and admin_pass == "1632022":
                    if new_user and new_pass and confirm_pass:
                        if new_pass == confirm_pass:
                            if new_user not in USERS_DATABASE:
                                USERS_DATABASE[new_user] = {
                                    "password": new_pass,
                                    "sheet_url": "",
                                    "script_url": "",
                                    "za_rate": 80
                                }
                                st.success(f"✅ {new_user} အကောင့်ထည့်ပြီးပါပြီ")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("❌ Username ရှိပြီးသားဖြစ်နေပါသည်")
                        else:
                            st.error("❌ Password များမတူပါ")
                    else:
                        st.error("❌ အကောင့်အချက်အလက်များ ဖြည့်ပါ")
                else:
                    st.error("❌ Admin credentials မှားနေပါသည်")
    
    st.stop()

# =========================
# Main Application
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
    
    # Debug mode
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
                help="ဒေတာသိမ်းမည့် Google Sheet link"
            )
            
            script_url = st.text_input(
                "🔄 Apps Script URL", 
                value=user_data.get("script_url", ""),
                placeholder="https://script.google.com/macros/s/.../exec",
                help="ဒေတာလက်ခံမည့် Apps Script Web App link"
            )
            
            if sheet_url != user_data.get("sheet_url", ""):
                user_data["sheet_url"] = sheet_url
                USERS_DATABASE[user]["sheet_url"] = sheet_url
                st.success("✅ Sheet URL saved!")
            
            if script_url != user_data.get("script_url", ""):
                user_data["script_url"] = script_url
                USERS_DATABASE[user]["script_url"] = script_url
                st.success("✅ Script URL saved!")
    
    st.divider()
    
    # Settings
    st.markdown("### ⚡ Settings")
    
    za_rate = st.number_input(
        "💰 ဇ (အဆ)", 
        value=user_data.get("za_rate", 80), 
        min_value=1, 
        step=1,
        help="ပေါက်ငွေတွက်ချက်ရာတွင် အမြတ်အဆ"
    )
    
    # Display current limit
    st.info(f"**🎯 ဂဏန်းအလိုက် Limit:** {MAX_NUMBER_LIMIT:,} ကျပ်")
    st.caption("(ဂဏန်းတစ်ကွက်ကို မြန်မာငွေ ၅သောင်းကျပ် အထိသာ လက်ခံပါသည်)")
    
    if za_rate != user_data.get("za_rate", 80):
        user_data["za_rate"] = za_rate
        USERS_DATABASE[user]["za_rate"] = za_rate
    
    st.divider()
    
    # Check specific number
    st.markdown("### 🔍 ဂဏန်းစစ်ဆေးရန်")
    check_number = st.text_input("ဂဏန်း", max_chars=2, key="check_number", label_visibility="collapsed")
    
    if check_number:
        check_number = check_number.zfill(2)
        if st.button("စစ်ဆေးမည်", use_container_width=True):
            st.session_state.checking_number = check_number
    
    # Win number check
    st.markdown("### 🎲 ပေါက်ဂဏန်းစစ်")
    win_number = st.text_input("ပေါက်ဂဏန်း", max_chars=2, key="win_number", label_visibility="collapsed")
    
    st.divider()
    
    # System info
    st.markdown("### ℹ️ System Info")
    st.caption(f"📅 ရက်စွဲ: {TODAY}")
    st.caption(f"💰 ဇအဆ: {za_rate}")
    st.caption(f"🎯 ဂဏန်း Limit: {MAX_NUMBER_LIMIT:,} ကျပ်")
    
    if st.session_state.last_refresh:
        last_refresh_time = st.session_state.last_refresh.strftime("%I:%M:%S %p")
        st.caption(f"🕐 Last update: {last_refresh_time}")
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.session_state.last_refresh = datetime.now()
        st.session_state.number_limits_cache = {}
        st.rerun()
    
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.user_data = None
        st.session_state.number_limits_cache = {}
        st.rerun()

# Get user settings
sheet = user_data.get("sheet_url", "")
script = user_data.get("script_url", "")
ZA_RATE = user_data.get("za_rate", 80)

# =========================
# Debug Functions
# =========================
def debug_log(message, data=None):
    if st.session_state.debug_mode:
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.markdown(f"`[{timestamp}] {message}`")
        if data is not None:
            st.json(data)

# =========================
# Check Number Limit
# =========================
def check_number_limit(number):
    """Check how much is remaining for a specific number"""
    try:
        if not script:
            return None
        
        payload = {"action": "check_limit", "number": number}
        response = requests.post(script, json=payload, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "limit_info":
                return result
        return None
    except:
        return None

# =========================
# Load Google Sheet
# =========================
def csv_url(url):
    try:
        m = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
        if m:
            file_id = m.group(1)
            return f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv"
        return ""
    except:
        return ""

def load_sheet_data():
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
        
        df.columns = df.columns.str.strip()
        
        required_columns = ["Date", "Time", "Customer", "Number", "Amount", "Receipt"]
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""
        
        df["Number"] = df["Number"].astype(str).str.zfill(2)
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
        
        df['sheet_row'] = df.index + 2
        
        today_df = df[df["Date"] == TODAY].copy()
        
        # Calculate limits for all numbers
        if not today_df.empty:
            number_totals = today_df.groupby('Number')['Amount'].sum()
            for num, total in number_totals.items():
                st.session_state.number_limits_cache[num] = {
                    'current_total': total,
                    'remaining': MAX_NUMBER_LIMIT - total,
                    'max_limit': MAX_NUMBER_LIMIT
                }
        
        return df, today_df
        
    except Exception as e:
        st.error(f"❌ Sheet ချိတ်ဆက်မှု အမှားအယွင်းရှိနေပါသည်")
        debug_log(f"Error details: {str(e)}")
        return None, None

# Load data
df, today_df = load_sheet_data()

if df is None or today_df is None:
    st.warning("📋 ဒေတာမရှိသေးပါ / Setup မပြည့်စုံသေးပါ")
    st.stop()

# =========================
# Dashboard with Limits
# =========================
st.title(f"💰 2D Agent Pro - {user}")

# Stats row with limit info
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_today = today_df['Amount'].sum()
    st.metric("📊 ဒီနေ့စုစုပေါင်း", f"{total_today:,.0f} ကျပ်")
with col2:
    total_transactions = len(today_df)
    st.metric("🔄 ဒီနေ့လုပ်ဆောင်ချက်", f"{total_transactions}")
with col3:
    if not today_df.empty:
        # Find numbers at or near limit
        numbers_near_limit = []
        for num in today_df['Number'].unique():
            total = today_df[today_df['Number'] == num]['Amount'].sum()
            if total >= MAX_NUMBER_LIMIT * 0.8:  # 80% or more
                numbers_near_limit.append(f"{num} ({total:,.0f})")
        
        if numbers_near_limit:
            display_text = f"{len(numbers_near_limit)} ဂဏန်း"
            st.metric("⚠️ Limit နီးကပ်ဂဏန်း", display_text, delta="သတိ")
        else:
            st.metric("✅ Limit အကုန်ဂဏန်း", "0")
with col4:
    if not today_df.empty:
        # Calculate how many numbers have reached limit
        numbers_at_limit = 0
        for num in today_df['Number'].unique():
            total = today_df[today_df['Number'] == num]['Amount'].sum()
            if total >= MAX_NUMBER_LIMIT:
                numbers_at_limit += 1
        
        total_unique_numbers = len(today_df['Number'].unique())
        st.metric("🔴 Limit ပြည့်ဂဏန်း", f"{numbers_at_limit}/{total_unique_numbers}")

# Check specific number if requested
if hasattr(st.session_state, 'checking_number'):
    check_number = st.session_state.checking_number
    limit_info = check_number_limit(check_number)
    
    if limit_info:
        with st.container(border=True):
            st.markdown(f"### 🔍 ဂဏန်း {check_number} စစ်ဆေးချက်")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                current_total = limit_info.get('current_total', 0)
                st.metric("💰 လက်ရှိစုစုပေါင်း", f"{current_total:,.0f} ကျပ်")
            with col2:
                remaining = limit_info.get('remaining', MAX_NUMBER_LIMIT)
                st.metric("✅ ထပ်ထည့်နိုင်သောငွေ", f"{remaining:,.0f} ကျပ်")
            with col3:
                max_limit = limit_info.get('max_limit', MAX_NUMBER_LIMIT)
                st.metric("🎯 အများဆုံးပမာဏ", f"{max_limit:,.0f} ကျပ်")
            
            # Progress bar
            progress = min(current_total / max_limit, 1.0)
            st.progress(progress)
            st.caption(f"Limit ရဲ့ {progress*100:.1f}% ရောက်ရှိနေပါသည်")
            
            if current_total >= max_limit:
                st.error(f"❌ ဂဏန်း {check_number} သည် Limit ပြည့်သွားပါပြီ")
            elif remaining < 1000:
                st.warning(f"⚠️ ဂဏန်း {check_number} အတွက် {remaining:,} ကျပ် သာကျန်ပါသည်")
            else:
                st.success(f"✅ ဂဏန်း {check_number} အတွက် {remaining:,} ကျပ် ကျန်ပါသည်")
    
    # Clear the checking state
    st.session_state.pop('checking_number', None)

st.divider()

# =========================
# New Entry with Limit Check
# =========================
with st.expander("📝 စာရင်းအသစ်ထည့်ရန်", expanded=True):
    with st.form("new_entry", clear_on_submit=True, border=True):
        st.markdown("### အချက်အလက်အသစ်ထည့်ပါ")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("👤 ထိုးသူအမည်", placeholder="ဉာဏ်လင်း")
        with c2:
            number_input = st.text_input("🔢 ထိုးမည့်ဂဏန်း", placeholder="12", max_chars=2, key="new_number")
        with c3:
            amount = st.number_input("💰 ပိုက်ဆံပမာဏ", min_value=100, step=100, value=1000, key="new_amount")
        
        # Real-time limit check
        if number_input:
            number = number_input.zfill(2)
            
            # Get current total for this number
            current_total = 0
            if number in st.session_state.number_limits_cache:
                current_total = st.session_state.number_limits_cache[number]['current_total']
            else:
                # Check from today's data
                number_data = today_df[today_df["Number"] == number]
                if not number_data.empty:
                    current_total = number_data["Amount"].sum()
                    st.session_state.number_limits_cache[number] = {
                        'current_total': current_total,
                        'remaining': MAX_NUMBER_LIMIT - current_total,
                        'max_limit': MAX_NUMBER_LIMIT
                    }
            
            remaining = MAX_NUMBER_LIMIT - current_total
            new_total = current_total + amount
            
            # Display limit info
            limit_col1, limit_col2, limit_col3 = st.columns(3)
            with limit_col1:
                st.metric("လက်ရှိစုစုပေါင်း", f"{current_total:,.0f} ကျပ်")
            with limit_col2:
                st.metric("ထပ်ထည့်နိုင်", f"{remaining:,.0f} ကျပ်")
            with limit_col3:
                st.metric("အများဆုံး", f"{MAX_NUMBER_LIMIT:,} ကျပ်")
            
            # Progress bar
            progress = min(new_total / MAX_NUMBER_LIMIT, 1.0)
            color = "red" if new_total > MAX_NUMBER_LIMIT else "orange" if progress > 0.8 else "green"
            st.progress(progress)
            
            # Warning messages
            if new_total > MAX_NUMBER_LIMIT:
                st.error(f"❌ ဂဏန်း {number} သည် Limit {MAX_NUMBER_LIMIT:,} ကျပ် ကျော်သွားမည်")
                st.error(f"ထပ်ထည့်နိုင်သောငွေ: {remaining:,} ကျပ်")
            elif new_total == MAX_NUMBER_LIMIT:
                st.warning(f"⚠️ ဂဏန်း {number} သည် Limit ပြည့်သွားမည်")
            elif progress > 0.9:
                st.warning(f"⚠️ ဂဏန်း {number} သည် Limit နီးကပ်နေပါသည်")
            elif remaining < 5000:
                st.info(f"ℹ️ ဂဏန်း {number} အတွက် {remaining:,} ကျပ် သာကျန်ပါသည်")
        
        submit = st.form_submit_button("💾 သိမ်းမည်", type="primary", use_container_width=True)
        
        if submit:
            if not name or not number_input:
                st.error("❌ ထိုးသူအမည်နှင့် ဂဏန်းထည့်ပါ")
            else:
                number = number_input.zfill(2)
                
                # Final check before sending
                current_total = 0
                if number in st.session_state.number_limits_cache:
                    current_total = st.session_state.number_limits_cache[number]['current_total']
                else:
                    number_data = today_df[today_df["Number"] == number]
                    if not number_data.empty:
                        current_total = number_data["Amount"].sum()
                
                new_total = current_total + amount
                
                if new_total > MAX_NUMBER_LIMIT:
                    remaining = MAX_NUMBER_LIMIT - current_total
                    st.error(f"❌ ဂဏန်း {number} သည် Limit {MAX_NUMBER_LIMIT:,} ကျပ် ကျော်နေပါပြီ")
                    st.error(f"ထပ်ထည့်နိုင်သောငွေ: {remaining:,} ကျပ်")
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
                                if result.get("status") == "limit_exceeded":
                                    st.error(f"❌ {result.get('message', 'Limit ကျော်နေပါသည်')}")
                                else:
                                    st.success(f"✅ {result.get('message', 'သိမ်းပြီးပါပြီ')}")
                                    time.sleep(1)
                                    st.session_state.last_refresh = datetime.now()
                                    st.session_state.number_limits_cache = {}
                                    st.rerun()
                            else:
                                result = resp.json() if resp.text else {}
                                if result.get("status") == "limit_exceeded":
                                    st.error(f"❌ {result.get('message', 'Limit ကျော်နေပါသည်')}")
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
# Edit Records with Limit Check
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
                
                # Check limit before update
                nu = nu.zfill(2) if nu else r.Number
                
                if nu != r.Number or am != r.Amount:
                    # Calculate current totals
                    current_total_excluding = today_df[
                        (today_df["Number"] == nu) & 
                        (today_df.index != i)
                    ]["Amount"].sum()
                    
                    new_total = current_total_excluding + am
                    
                    if new_total > MAX_NUMBER_LIMIT:
                        remaining = MAX_NUMBER_LIMIT - current_total_excluding
                        st.error(f"❌ ဂဏန်း {nu} အတွက် {remaining:,} ကျပ် သာကျန်ပါသည်")
                
                if st.form_submit_button("🔄 ပြင်မည်", use_container_width=True):
                    nu = nu.zfill(2)
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
                result = resp.json()
                if result.get("status") == "limit_exceeded":
                    st.error(f"❌ {result.get('message', 'Limit ကျော်နေပါသည်')}")
                else:
                    st.success("✅ ပြင်ပြီးပါပြီ")
                    time.sleep(1)
                    st.session_state.last_refresh = datetime.now()
                    st.session_state.number_limits_cache = {}
                    st.rerun()
            else:
                result = resp.json() if resp.text else {}
                if result.get("status") == "limit_exceeded":
                    st.error(f"❌ {result.get('message', 'Limit ကျော်နေပါသည်')}")
                else:
                    st.error(f"❌ Update failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        st.error(f"❌ Update error: {str(e)}")

st.divider()

# =========================
# Table with Limit Indicators
# =========================
st.subheader("📋 ဒီနေ့စာရင်းဇယား (Limit ဖော်ပြချက်နှင့်)")

# Add limit status to dataframe
def get_limit_status(number, amount):
    total = today_df[today_df["Number"] == number]["Amount"].sum()
    if total >= MAX_NUMBER_LIMIT:
        return "🔴 Limit ပြည့်"
    elif total >= MAX_NUMBER_LIMIT * 0.9:
        return "🟡 Limit နီးပြီ"
    elif total >= MAX_NUMBER_LIMIT * 0.7:
        return "🟠 Limit 70%"
    else:
        return "🟢 ကျန်ရှိ"

if not today_df.empty:
    today_df["Limit_Status"] = today_df.apply(
        lambda row: get_limit_status(row["Number"], row["Amount"]), axis=1
    )

search_col1, search_col2 = st.columns([3, 1])
with search_col1:
    search = st.text_input("🔍 နာမည်ဖြင့်ရှာရန်", placeholder="ထိုးသူအမည်ရိုက်ထည့်ပါ...")
with search_col2:
    sort_by = st.selectbox("အစဉ်လိုက်စီရန်", ["Time", "Amount", "Number", "Limit_Status"])

view_df = today_df.drop(columns=['sheet_row']).copy()

if search:
    view_df = view_df[view_df["Customer"].str.contains(search, case=False, na=False)]

if sort_by == "Amount":
    view_df = view_df.sort_values(by="Amount", ascending=False)
elif sort_by == "Number":
    view_df = view_df.sort_values(by="Number")
elif sort_by == "Customer":
    view_df = view_df.sort_values(by="Customer")
elif sort_by == "Limit_Status":
    view_df = view_df.sort_values(by="Limit_Status", ascending=False)
else:
    view_df = view_df.sort_values(by="Time", ascending=False)

# Display limit summary
if not today_df.empty:
    numbers_at_limit = []
    numbers_near_limit = []
    
    for num in today_df['Number'].unique():
        total = today_df[today_df["Number"] == num]["Amount"].sum()
        if total >= MAX_NUMBER_LIMIT:
            numbers_at_limit.append(f"{num} ({total:,.0f})")
        elif total >= MAX_NUMBER_LIMIT * 0.8:
            numbers_near_limit.append(f"{num} ({total:,.0f})")
    
    if numbers_at_limit or numbers_near_limit:
        with st.container(border=True):
            st.markdown("### ⚠️ Limit သတိပေးချက်များ")
            
            if numbers_at_limit:
                st.error(f"**🔴 Limit ပြည့်သွားသောဂဏန်းများ:** {', '.join(numbers_at_limit)}")
            
            if numbers_near_limit:
                st.warning(f"**🟡 Limit နီးကပ်နေသောဂဏန်းများ:** {', '.join(numbers_near_limit)}")

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
            "Receipt": st.column_config.TextColumn("ရက်စဘွယ်"),
            "Limit_Status": st.column_config.TextColumn("Limit အခြေအနေ")
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
                csv_data = view_df.drop(columns=['Limit_Status']).to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "💾 CSV ဒေါင်းလုဒ်",
                    csv_data,
                    f"2d_data_{TODAY}_{user}.csv",
                    "text/csv",
                    use_container_width=True
                )
            else:
                excel_data = view_df.drop(columns=['Limit_Status']).to_excel(index=False, engine='openpyxl')
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
                        st.success(f"✅ {result.get('message', 'အောင်မြင်စွာဖျက်ပြီးပါပြီ')}")
                        
                        st.balloons()
                        time.sleep(2)
                        st.session_state.last_refresh = datetime.now()
                        st.session_state.number_limits_cache = {}
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
# Footer
# =========================
st.divider()
footer_col1, footer_col2, footer_col3 = st.columns(3)
with footer_col1:
    st.caption(f"👤 User: {user}")
    st.caption(f"🕐 Last update: {datetime.now(MM_TZ).strftime('%I:%M:%S %p')}")
with footer_col2:
    st.caption(f"📅 Date: {TODAY}")
    st.caption(f"🎯 Number Limit: {MAX_NUMBER_LIMIT:,} ကျပ်")
with footer_col3:
    st.caption("💻 2D Agent Pro v3.0")
    st.caption(f"💰 Za Rate: {ZA_RATE}")
