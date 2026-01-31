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
NUMBER_LIMIT = 50000

# =========================
# User Management Functions
# =========================
def hash_password(password):
    """Hash password for security"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from session state or initialize"""
    if "users" not in st.session_state:
        # Default admin user (can be changed)
        st.session_state.users = {
            "admin": {
                "password_hash": hash_password("admin123"),  # Change this!
                "sheet": "",
                "script": "",
                "show_links": False,
                "za_rate": 80,
                "number_limit": 50000
            }
        }
    return st.session_state.users

def save_user(username, password, sheet="", script=""):
    """Save new user or update existing user"""
    users = load_users()
    users[username] = {
        "password_hash": hash_password(password),
        "sheet": sheet,
        "script": script,
        "show_links": False,
        "za_rate": 80,
        "number_limit": 50000
    }
    st.session_state.users = users
    return True

def delete_user(username):
    """Delete a user"""
    if username in st.session_state.users:
        del st.session_state.users[username]
        return True
    return False

# Initialize users
users_db = load_users()

# =========================
# Login System
# =========================
if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.user = None
    st.session_state.last_refresh = None
    st.session_state.script_debug = False

if not st.session_state.login:
    # Login Page
    st.title("🔐 2D Agent Pro - Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("### အကောင့်ဝင်ရန်")
            
            tab_login, tab_register = st.tabs(["🔐 အကောင့်ဝင်", "📝 အကောင့်အသစ်"])
            
            with tab_login:
                username = st.text_input("👤 Username", key="login_username")
                password = st.text_input("🔒 Password", type="password", key="login_password")
                
                if st.button("🚀 Login", type="primary", use_container_width=True):
                    if username in users_db:
                        stored_hash = users_db[username]["password_hash"]
                        if hash_password(password) == stored_hash:
                            st.session_state.login = True
                            st.session_state.user = username
                            st.session_state.last_refresh = datetime.now()
                            st.rerun()
                        else:
                            st.error("❌ Password မှားနေပါသည်")
                    else:
                        st.error("❌ Username မရှိပါ")
            
            with tab_register:
                st.info("👑 Admin မှသာ အကောင့်အသစ်ဖန်တီးနိုင်ပါသည်")
                
                # Only allow admin to create new accounts
                admin_username = st.text_input("Admin Username", key="admin_user")
                admin_password = st.text_input("Admin Password", type="password", key="admin_pass")
                
                new_username = st.text_input("အကောင့်အသစ် Username", key="new_user")
                new_password = st.text_input("အကောင့်အသစ် Password", type="password", key="new_pass")
                
                if st.button("➕ အကောင့်အသစ်ဖန်တီးမည်", use_container_width=True):
                    # Verify admin credentials
                    if admin_username in users_db and admin_password:
                        stored_admin_hash = users_db[admin_username]["password_hash"]
                        if hash_password(admin_password) == stored_admin_hash:
                            if new_username and new_password:
                                if new_username not in users_db:
                                    save_user(new_username, new_password)
                                    st.success(f"✅ {new_username} အကောင့်ဖန်တီးပြီးပါပြီ")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ Username ရှိပြီးသားဖြစ်နေပါသည်")
                            else:
                                st.error("❌ Username နှင့် Password ထည့်ပါ")
                        else:
                            st.error("❌ Admin Password မှားနေပါသည်")
                    else:
                        st.error("❌ Admin credentials မှားနေပါသည်")
    
    st.divider()
    
    # User list (admin only view)
    with st.expander("👥 ရှိပြီးသားအကောင့်များ"):
        if users_db:
            user_list = list(users_db.keys())
            cols = 3
            rows = (len(user_list) + cols - 1) // cols
            
            for i in range(rows):
                col_list = st.columns(cols)
                for j in range(cols):
                    idx = i * cols + j
                    if idx < len(user_list):
                        with col_list[j]:
                            st.text(f"👤 {user_list[idx]}")
        else:
            st.info("📭 အကောင့်မရှိသေးပါ")
    
    st.stop()

user = st.session_state.user
current_user_data = users_db[user]

# =========================
# Admin Management Page
# =========================
if user == "admin":
    with st.sidebar.expander("👑 Admin Management", expanded=False):
        st.markdown("### အကောင့်များစီမံခန့်ခွဲမှု")
        
        # List all users
        st.markdown("#### 👥 အကောင့်များ")
        for username in list(users_db.keys()):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.text(f"👤 {username}")
            with col2:
                if username != "admin":
                    if st.button("🗑️", key=f"del_{username}"):
                        if delete_user(username):
                            st.success(f"✅ {username} ဖျက်ပြီးပါပြီ")
                            time.sleep(1)
                            st.rerun()
            st.divider()
        
        # Change admin password
        st.markdown("#### 🔑 Admin Password ပြောင်းရန်")
        old_pass = st.text_input("လက်ရှိ Password", type="password", key="old_admin_pass")
        new_pass = st.text_input("Password အသစ်", type="password", key="new_admin_pass")
        confirm_pass = st.text_input("Password အသစ် ထပ်ရိုက်ပါ", type="password", key="confirm_admin_pass")
        
        if st.button("🔄 Password ပြောင်းမည်", use_container_width=True):
            if hash_password(old_pass) == current_user_data["password_hash"]:
                if new_pass and new_pass == confirm_pass:
                    save_user("admin", new_pass, current_user_data["sheet"], current_user_data["script"])
                    st.success("✅ Password ပြောင်းပြီးပါပြီ")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Password အသစ်များ မတူပါ")
            else:
                st.error("❌ လက်ရှိ Password မှားနေပါသည်")

# =========================
# Sidebar
# =========================
with st.sidebar:
    st.title(f"👤 {user}")
    st.divider()
    
    # Debug mode toggle
    debug_mode = st.checkbox("🐛 Debug Mode", value=st.session_state.script_debug)
    if debug_mode != st.session_state.script_debug:
        st.session_state.script_debug = debug_mode
        st.rerun()
    
    # User-specific settings
    st.markdown("### ⚙️ User Settings")
    
    toggle_text = "🔓 Link ပြရန်" if not current_user_data["show_links"] else "🔒 Link ဖွက်ရန်"
    if st.button(toggle_text, use_container_width=True):
        current_user_data["show_links"] = not current_user_data["show_links"]
        st.rerun()
    
    if current_user_data["show_links"]:
        with st.container(border=True):
            st.markdown("#### 🔗 System Links")
            
            sheet = st.text_input(
                "📊 Google Sheet URL", 
                value=current_user_data["sheet"],
                placeholder="https://docs.google.com/spreadsheets/d/...",
                help="ဒေတာသိမ်းမည့် Google Sheet link",
                key=f"sheet_{user}"
            )
            
            script = st.text_input(
                "🔄 Apps Script URL", 
                value=current_user_data["script"],
                placeholder="https://script.google.com/macros/s/.../exec",
                help="ဒေတာလက်ခံမည့် Apps Script Web App link",
                key=f"script_{user}"
            )
            
            if sheet != current_user_data["sheet"] or script != current_user_data["script"]:
                current_user_data["sheet"] = sheet
                current_user_data["script"] = script
                # Update in users database
                users_db[user] = current_user_data
                st.success("✅ Links saved!")
            
            if script:
                try:
                    test_response = requests.get(script, timeout=5)
                    if test_response.status_code == 200:
                        st.success("✅ Script connected")
                    else:
                        st.warning(f"⚠️ Script responded with {test_response.status_code}")
                except:
                    st.error("❌ Cannot connect to script")
    
    st.divider()
    
    # User preferences
    st.markdown("### ⚡ User Preferences")
    za_rate = st.number_input(
        "💰 ဇ (အဆ)", 
        value=current_user_data.get("za_rate", 80), 
        min_value=1, 
        step=1,
        key=f"za_rate_{user}"
    )
    
    number_limit = st.number_input(
        "🎯 ဂဏန်း Limit", 
        value=current_user_data.get("number_limit", 50000), 
        min_value=1000, 
        step=1000,
        key=f"limit_{user}"
    )
    
    # Save preferences
    if za_rate != current_user_data.get("za_rate", 80) or number_limit != current_user_data.get("number_limit", 50000):
        current_user_data["za_rate"] = za_rate
        current_user_data["number_limit"] = number_limit
        users_db[user] = current_user_data
    
    st.divider()
    
    # Win number check
    st.markdown("### 🎲 ပေါက်ဂဏန်းစစ်")
    win_number = st.text_input("ပေါက်ဂဏန်း", max_chars=2, key=f"win_number_{user}", label_visibility="collapsed")
    
    st.divider()
    
    # System info
    st.markdown("### ℹ️ System Info")
    last_refresh_time = st.session_state.last_refresh.strftime("%I:%M:%S %p") if st.session_state.last_refresh else "Never"
    st.caption(f"Last refresh: {last_refresh_time}")
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.session_state.last_refresh = datetime.now()
        st.rerun()
    
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        st.session_state.login = False
        st.session_state.user = None
        st.rerun()

# Use user-specific settings
sheet = current_user_data["sheet"]
script = current_user_data["script"]
NUMBER_LIMIT = current_user_data.get("number_limit", 50000)

# =========================
# Debug Functions
# =========================
def debug_log(message, data=None):
    """Log debug messages if debug mode is enabled"""
    if st.session_state.script_debug:
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
        
        # Add timestamp to prevent caching
        full_url = f"{csv_url_str}&t={int(time.time())}"
        debug_log(f"Loading data from: {full_url}")
        
        # Read CSV
        df = pd.read_csv(full_url)
        debug_log(f"Raw data loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Clean column names
        df.columns = df.columns.str.strip()
        debug_log("Columns after cleaning:", list(df.columns))
        
        # Ensure required columns exist
        required_columns = ["Date", "Time", "Customer", "Number", "Amount", "Receipt"]
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""
                debug_log(f"Added missing column: {col}")
        
        # Format data
        df["Number"] = df["Number"].astype(str).str.zfill(2)
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
        
        # Store original sheet row number (for updates)
        df['sheet_row'] = df.index + 2
        
        # Filter today's data
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
    st.warning("📋 ဒေတာမရှိသေးပါ")
    
    # Show sample data structure
    with st.expander("📁 Expected Sheet Structure"):
        st.markdown("""
        | Date | Time | Customer | Number | Amount | Receipt |
        |------|------|----------|--------|--------|---------|
        | 2024-01-20 | 10:30 AM | John | 12 | 1000 | R-2024-01-20-0001 |
        | 2024-01-20 | 11:00 AM | Mary | 45 | 2000 | R-2024-01-20-0002 |
        
        **Note:** Column names must be exactly as shown above.
        """)
    st.stop()

# =========================
# Dashboard
# =========================
st.title(f"💰 2D Agent Pro Dashboard - {user}")

# Stats row
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_today = today_df['Amount'].sum()
    st.metric("📊 ဒီနေ့စုစုပေါင်း", f"{total_today:,.0f} ကျပ်")
with col2:
    total_transactions = len(today_df)
    st.metric("🔄 ဒီနေ့လုပ်ဆောင်ချက်များ", f"{total_transactions}")
with col3:
    avg_amount = total_today / total_transactions if total_transactions > 0 else 0
    st.metric("📈 ပျမ်းမျှထိုးငွေ", f"{avg_amount:,.0f} ကျပ်")
with col4:
    if not today_df.empty:
        popular_num = today_df.groupby('Number')['Amount'].sum().idxmax()
        popular_amount = today_df.groupby('Number')['Amount'].sum().max()
        st.metric("🔥 လူကြိုက်အများဆုံးဂဏန်း", f"{popular_num} ({popular_amount:,.0f} ကျပ်)")

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
        
        # Check limit for the selected number
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
        winners["လျော်ကြေး"] = winners["Amount"] * za_rate
        total_payout = winners["လျော်ကြေး"].sum()
        
        st.success(f"🎉 ပေါက်သူများ (ဂဏန်း: {win_number}) - စုစုပေါင်းလျော်ကြေး: {total_payout:,.0f} ကျပ်")
        
        # Display in a nice table
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
                    
                    # Check if changing number would exceed limit
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

# Search and filter
search_col1, search_col2 = st.columns([3, 1])
with search_col1:
    search = st.text_input("🔍 နာမည်ဖြင့်ရှာရန်", placeholder="ထိုးသူအမည်ရိုက်ထည့်ပါ...")
with search_col2:
    sort_by = st.selectbox("အစဉ်လိုက်စီရန်", ["Time", "Amount", "Number", "Customer"])

# Prepare data for display
view_df = today_df.drop(columns=['sheet_row']).copy()

# Apply search filter
if search:
    view_df = view_df[view_df["Customer"].str.contains(search, case=False, na=False)]

# Sort data
if sort_by == "Amount":
    view_df = view_df.sort_values(by="Amount", ascending=False)
elif sort_by == "Number":
    view_df = view_df.sort_values(by="Number")
elif sort_by == "Customer":
    view_df = view_df.sort_values(by="Customer")
else:  # Time
    view_df = view_df.sort_values(by="Time", ascending=False)

# Display summary
st.caption(f"📊 စုစုပေါင်း {len(view_df)} ခု | စုစုပေါင်းငွေ: {view_df['Amount'].sum():,.0f} ကျပ်")

# Display data table
if not view_df.empty:
    # Format the display
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
        
        # Export options
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
        ဒီခလုတ်ကို နှိပ်လိုက်ရင် ဒီနေ့စာရင်းအားလုံး **အပြီးအပိုင် ပျက်သွားမည်**။
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
                        
                        # Show notification
                        st.balloons()
                        
                        # Wait and refresh
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
if st.session_state.script_debug:
    with st.expander("🐛 Debug Information", expanded=False):
        st.subheader("System Information")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current User", user)
            st.metric("Script URL", script[:50] + "..." if len(script) > 50 else script)
        with col2:
            st.metric("Number Limit", f"{NUMBER_LIMIT:,}")
            st.metric("Sheet URL", sheet[:50] + "..." if len(sheet) > 50 else sheet)
        
        st.subheader("Data Preview")
        tab1, tab2, tab3 = st.tabs(["Today's Data", "All Data", "Raw Info"])
        
        with tab1:
            st.dataframe(today_df, use_container_width=True)
            st.json(today_df.to_dict(orient='records')[:5] if not today_df.empty else {})
        
        with tab2:
            st.dataframe(df, use_container_width=True)
        
        with tab3:
            st.code(f"""
            System Time (MM): {datetime.now(MM_TZ).strftime("%Y-%m-%d %I:%M:%S %p")}
            Today String: {TODAY}
            Data Shape: {df.shape if df is not None else 'N/A'}
            Today Data Shape: {today_df.shape if today_df is not None else 'N/A'}
            Session User: {user}
            Total Users: {len(users_db)}
            """)

# =========================
# Footer
# =========================
st.divider()
footer_col1, footer_col2, footer_col3 = st.columns(3)
with footer_col1:
    st.caption(f"👤 User: {user}")
    st.caption(f"🕐 Last updated: {datetime.now(MM_TZ).strftime('%I:%M:%S %p')}")
with footer_col2:
    st.caption(f"📅 Date: {TODAY}")
    st.caption(f"🎯 Limit: {NUMBER_LIMIT:,} ကျပ်")
with footer_col3:
    st.caption("💻 2D Agent Pro v2.0")
    st.caption(f"💰 Za Rate: {za_rate}")
