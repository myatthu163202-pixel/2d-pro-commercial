import streamlit as st
import pandas as pd
import hashlib
import time
from datetime import datetime, timedelta
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import re
import os

# ==================== CONFIGURATION ====================
MYANMAR_TZ = pytz.timezone('Asia/Yangon')
PRICE_PER_NUMBER = 50000

# ==================== SESSION STATE INITIALIZATION ====================
def init_session_state():
    # Authentication states
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = ''
    if 'current_user' not in st.session_state:
        st.session_state.current_user = ''
    
    # 2D App states
    if 'sheet_url' not in st.session_state:
        st.session_state.sheet_url = ''
    if 'user_configs' not in st.session_state:
        st.session_state.user_configs = {}
    if 'today_entries' not in st.session_state:
        st.session_state.today_entries = {}
    if 'google_sheets' not in st.session_state:
        st.session_state.google_sheets = {}
    if 'last_reset_date' not in st.session_state:
        st.session_state.last_reset_date = datetime.now(MYANMAR_TZ).strftime('%Y-%m-%d')
    if 'hidden_sections' not in st.session_state:
        st.session_state.hidden_sections = {}
    
    # User Management states (from previous panel)
    if 'users_db' not in st.session_state:
        init_users_database()
    if 'number_limits_cache' not in st.session_state:
        st.session_state.number_limits_cache = {}
    if 'activity_log' not in st.session_state:
        st.session_state.activity_log = []
    if 'current_page' not in st.session_state:
        st.session_state.current_page = '🏠 ပင်မစာမျက်နှာ'
    
    # Initialize user-specific data
    if st.session_state.current_user:
        init_user_data()

def init_users_database():
    """Initialize user database with both admin and agent roles"""
    st.session_state.users_db = {
        'admin': {
            'password': hashlib.sha256('admin123'.encode()).hexdigest(),
            'role': 'admin',
            'name': 'စီမံခန့်ခွဲသူ',
            'email': 'admin@company.com',
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'last_login': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        'agent1': {
            'password': hashlib.sha256('agent123'.encode()).hexdigest(),
            'role': 'agent',
            'name': 'အေဂျင့်တစ်',
            'email': 'agent1@company.com',
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'last_login': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        'user1': {
            'password': hashlib.sha256('user123'.encode()).hexdigest(),
            'role': 'user',
            'name': 'ဦးကျော်ကျော်',
            'email': 'user1@company.com',
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'last_login': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    }

def init_user_data():
    """Initialize user-specific data"""
    if st.session_state.current_user not in st.session_state.today_entries:
        st.session_state.today_entries[st.session_state.current_user] = []
    if st.session_state.current_user not in st.session_state.user_configs:
        st.session_state.user_configs[st.session_state.current_user] = {
            'sheet_url': '',
            'script_url': ''
        }

# ==================== 2D APP HELPER FUNCTIONS ====================
def get_myanmar_time():
    """မြန်မာစံတော်ချိန်ရယူခြင်း"""
    return datetime.now(MYANMAR_TZ)

def format_myanmar_time(dt=None):
    """မြန်မာစံတော်ချိန်ဖော်ပြခြင်း"""
    if dt is None:
        dt = get_myanmar_time()
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def get_today_date():
    """ယနေ့ရက်စွဲရယူခြင်း"""
    return get_myanmar_time().strftime('%Y-%m-%d')

def validate_number(number_str):
    """ဂဏန်းစစ်ဆေးခြင်း"""
    if not re.match(r'^\d{2,3}$', number_str):
        return False, "ဂဏန်းသည် ၂ လုံး သို့မဟုတ် ၃ လုံးဖြစ်ရမည်"
    
    if len(number_str) == 2:
        if not (0 <= int(number_str) <= 99):
            return False, "2D ဂဏန်းသည် 00 မှ 99 အတွင်းဖြစ်ရမည်"
    elif len(number_str) == 3:
        if not (0 <= int(number_str) <= 999):
            return False, "3D ဂဏန်းသည် 000 မှ 999 အတွင်းဖြစ်ရမည်"
    
    return True, ""

def validate_name(name):
    """နာမည်စစ်ဆေးခြင်း"""
    if not name or len(name.strip()) < 2:
        return False, "နာမည်အနည်းဆုံး ၂ လုံးထည့်ပါ"
    return True, ""

def calculate_amount(number_str, quantity):
    """စုစုပေါင်းပမာဏတွက်ချက်ခြင်း"""
    return PRICE_PER_NUMBER * quantity

def connect_to_google_sheets(sheet_url, credentials_json=None):
    """Google Sheets နှင့်ချိတ်ဆက်ခြင်း"""
    try:
        if not sheet_url:
            return None, "Sheet URL ထည့်ပါ"
        
        if sheet_url in st.session_state.google_sheets:
            return st.session_state.google_sheets[sheet_url], "ချိတ်ဆက်ပြီးသား"
        
        scope = ["https://spreadsheets.google.com/feeds", 
                "https://www.googleapis.com/auth/drive"]
        
        if credentials_json:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                credentials_json, scope)
        else:
            try:
                creds_dict = json.loads(st.secrets["google_credentials"])
                creds = ServiceAccountCredentials.from_json_keyfile_dict(
                    creds_dict, scope)
            except:
                class MockSheet:
                    def worksheet(self, title):
                        class MockWorksheet:
                            def append_row(self, row):
                                print(f"Mock append: {row}")
                                return True
                        return MockWorksheet()
                
                mock_sheet = MockSheet()
                st.session_state.google_sheets[sheet_url] = mock_sheet
                return mock_sheet, "Demo mode"
        
        client = gspread.authorize(creds)
        sheet = client.open_by_url(sheet_url)
        st.session_state.google_sheets[sheet_url] = sheet
        return sheet, "ချိတ်ဆက်ပြီးပါပြီ"
    except Exception as e:
        return None, f"ချိတ်ဆက်မှုမအောင်မြင်ပါ: {str(e)}"

def save_to_google_sheets(entry_data, sheet_url, script_url=""):
    """Google Sheets သို့သိမ်းဆည်းခြင်း"""
    try:
        sheet, message = connect_to_google_sheets(sheet_url)
        if not sheet:
            return False, message
        
        today = get_today_date()
        try:
            worksheet = sheet.worksheet(today)
        except:
            worksheet = sheet.add_worksheet(title=today, rows="1000", cols="10")
            headers = ["အချိန်", "ထိုးသူအမည်", "ထိုးမည့်ဂဏန်း", "အရေအတွက်", 
                      "ပမာဏ", "ပေါက်ဂဏန်း", "အခြေအနေ", "မှတ်ချက်"]
            worksheet.append_row(headers)
        
        row = [
            entry_data['time'],
            entry_data['name'],
            entry_data['number'],
            entry_data['quantity'],
            entry_data['amount'],
            entry_data.get('winning_number', ''),
            entry_data.get('status', 'စောင့်ဆိုင်းနေ'),
            entry_data.get('note', '')
        ]
        
        worksheet.append_row(row)
        
        if script_url:
            try:
                import requests
                requests.post(script_url, json=entry_data, timeout=5)
            except:
                pass
        
        return True, "Google Sheets သို့သိမ်းဆည်းပြီးပါပြီ"
    except Exception as e:
        return False, f"သိမ်းဆည်းမှုမအောင်မြင်ပါ: {str(e)}"

def check_daily_reset():
    """နေ့စဉ်ဒေတာပြန်လည်စတင်ခြင်းစစ်ဆေးခြင်း"""
    today = get_today_date()
    
    if st.session_state.last_reset_date != today:
        for user in st.session_state.today_entries:
            st.session_state.today_entries[user] = []
        st.session_state.hidden_sections = {}
        st.session_state.last_reset_date = today
        st.rerun()

# ==================== USER MANAGEMENT FUNCTIONS (From Panel) ====================
def log_activity(action, details=""):
    """လုပ်ဆောင်ချက်မှတ်တမ်းထားရှိခြင်း"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = st.session_state.current_user if st.session_state.logged_in else "Guest"
    st.session_state.activity_log.append({
        'timestamp': timestamp,
        'user': user,
        'action': action,
        'details': details
    })

def authenticate_user(username, password):
    """အသုံးပြုသူအတည်ပြုခြင်း"""
    if username in st.session_state.users_db:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if st.session_state.users_db[username]['password'] == hashed_password:
            st.session_state.users_db[username]['last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_activity("Login", f"User: {username}")
            return True, st.session_state.users_db[username]['role']
    return False, None

def add_new_user(username, password, role, name, email=""):
    """အသုံးပြုသူအသစ်ထည့်ခြင်း"""
    if not username or not password or not role or not name:
        return False, "လိုအပ်သောအချက်အလက်များကိုဖြည့်စွက်ပါ။"
    
    if len(username) < 3:
        return False, "အသုံးပြုသူအမည်သည် အနည်းဆုံး ၃ လုံးပါဝင်ရမည်။"
    
    if len(password) < 6:
        return False, "စကားဝှက်သည် အနည်းဆုံး ၆ လုံးပါဝင်ရမည်။"
    
    if not re.match("^[a-zA-Z0-9_]+$", username):
        return False, "အသုံးပြုသူအမည်တွင် အင်္ဂလိပ်အက္ခရာ၊ နံပါတ်နှင့် underscore သာပါဝင်နိုင်သည်။"
    
    if username in st.session_state.users_db:
        return False, "အသုံးပြုသူအမည်ရှိပြီးသားဖြစ်နေပါသည်။"
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    st.session_state.users_db[username] = {
        'password': hashed_password,
        'role': role,
        'name': name,
        'email': email,
        'created_at': datetime.now().strftime("%Y-%m-%d"),
        'last_login': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    log_activity("Add User", f"New user: {username} ({role})")
    return True, f"အကောင့် '{username}' အောင်မြင်စွာထည့်သွင်းပြီးပါပြီ။"

def update_user_info(username, **kwargs):
    """အသုံးပြုသူအချက်အလက်ပြင်ဆင်ခြင်း"""
    if username in st.session_state.users_db:
        for key, value in kwargs.items():
            if key == 'password' and value:
                st.session_state.users_db[username][key] = hashlib.sha256(value.encode()).hexdigest()
            elif value:
                st.session_state.users_db[username][key] = value
        
        log_activity("Update User", f"Updated: {username}")
        return True, "အချက်အလက်ပြင်ဆင်ပြီးပါပြီ။"
    return False, "အသုံးပြုသူမတွေ့ပါ။"

def delete_user_account(username):
    """အသုံးပြုသူဖျက်ခြင်း"""
    if username in st.session_state.users_db:
        if username == st.session_state.current_user:
            return False, "မိမိကိုယ်တိုင်ဖျက်ရန်မဖြစ်နိုင်ပါ။"
        
        del st.session_state.users_db[username]
        log_activity("Delete User", f"Deleted: {username}")
        return True, f"အကောင့် '{username}' ဖျက်ပြီးပါပြီ။"
    return False, "အသုံးပြုသူမတွေ့ပါ။"

# ==================== MAIN APP ====================
def main():
    # Initialize session state
    init_session_state()
    
    # Check daily reset for 2D app
    check_daily_reset()
    
    # Set page config
    st.set_page_config(
        page_title="2D စနစ် & အကောင့်မန်နေဂျာ",
        page_icon="🎰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #3B82F6;
    }
    .sub-title {
        font-size: 1.8rem;
        color: #1E40AF;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #F0F9FF;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #BFDBFE;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #FEF3C7;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #FDE68A;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #D1FAE5;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #A7F3D0;
        margin: 1rem 0;
    }
    .user-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    .hide-button {
        background-color: #6B7280 !important;
        color: white !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ==================== LOGIN PAGE ====================
    if not st.session_state.logged_in:
        render_login_page()
        return
    
    # ==================== LOGGED IN ====================
    render_sidebar()
    
    # Check current page from navigation
    current_page = st.session_state.get('current_page', '🏠 ပင်မစာမျက်နှာ')
    
    if current_page == "🏠 ပင်မစာမျက်နှာ":
        render_home_page()
    elif current_page == "🎰 2D ထိုးစနစ်":
        render_2d_system()
    elif current_page == "👥 အကောင့်စီမံခန့်ခွဲမှု":
        render_user_management()
    elif current_page == "📊 အစီရင်ခံစာများ":
        render_reports_page()
    elif current_page == "⚙️ ဆက်တင်များ":
        render_settings_page()

# ==================== LOGIN PAGE ====================
def render_login_page():
    """Login page ပြသခြင်း"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<h1 class="main-title">🎰 2D စနစ် & အကောင့်မန်နေဂျာ</h1>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("### 🔐 အကောင့်ဝင်ရောက်ရန်")
            st.write("ကျေးဇူးပြု၍ သင့်အကောင့်ဖြင့် ဝင်ရောက်ပါ။")
            st.markdown('</div>', unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("👤 **အသုံးပြုသူအမည်**", 
                                       placeholder="သင့်အသုံးပြုသူအမည်ထည့်ပါ")
                
                password = st.text_input("🔒 **စကားဝှက်**", 
                                       type="password",
                                       placeholder="သင့်စကားဝှက်ထည့်ပါ")
                
                login_button = st.form_submit_button("🚀 **ဝင်ရောက်မည်**", 
                                                   use_container_width=True)
                
                if login_button:
                    if username and password:
                        authenticated, role = authenticate_user(username, password)
                        if authenticated:
                            st.session_state.logged_in = True
                            st.session_state.user_role = role
                            st.session_state.current_user = username
                            
                            # Initialize user data
                            init_user_data()
                            
                            st.success(f"✅ **{username}** အနေနဲ့ ဝင်ရောက်ပြီးပါပြီ။")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ အသုံးပြုသူအမည် သို့မဟုတ် စကားဝှက် မှားယွင်းနေပါသည်။")
                    else:
                        st.warning("⚠ ကျေးဇူးပြု၍ အသုံးပြုသူအမည်နှင့် စကားဝှက်ထည့်ပါ။")
            
            # Demo credentials
            with st.expander("📋 သက်သေခံအချက်အလက်များ"):
                col_demo1, col_demo2, col_demo3 = st.columns(3)
                with col_demo1:
                    st.markdown("**👑 Admin:**")
                    st.code("User: admin\nPass: admin123")
                with col_demo2:
                    st.markdown("**🎰 Agent:**")
                    st.code("User: agent1\nPass: agent123")
                with col_demo3:
                    st.markdown("**👤 User:**")
                    st.code("User: user1\nPass: user123")

# ==================== SIDEBAR ====================
def render_sidebar():
    """Sidebar ပြသခြင်း"""
    with st.sidebar:
        # User info card
        user_info = st.session_state.users_db[st.session_state.current_user]
        st.markdown(f"""
        <div class="user-card">
            <h3>👤 {user_info['name']}</h3>
            <p><strong>အခန်းကဏ္ဍ:</strong> {user_info['role'].upper()}</p>
            <p><strong>အသုံးပြုသူ:</strong> {st.session_state.current_user}</p>
            <p><strong>နောက်ဆုံးဝင်ရောက်ချိန်:</strong><br>{user_info['last_login']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Myanmar time
        current_time = format_myanmar_time()
        st.markdown(f"""
        <div class="info-box">
            <p><strong>မြန်မာစံတော်ချိန်:</strong></p>
            <h3 style="text-align: center; color: #1E40AF;">{current_time.split()[1]}</h3>
            <p style="text-align: center;">{current_time.split()[0]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Navigation - Different for different roles
        st.markdown("### 🗺️ လမ်းညွှန်မှု")
        
        if st.session_state.user_role == 'admin':
            page_options = [
                "🏠 ပင်မစာမျက်နှာ",
                "🎰 2D ထိုးစနစ်", 
                "👥 အကောင့်စီမံခန့်ခွဲမှု",
                "📊 အစီရင်ခံစာများ",
                "⚙️ ဆက်တင်များ"
            ]
        elif st.session_state.user_role == 'agent':
            page_options = [
                "🏠 ပင်မစာမျက်နှာ",
                "🎰 2D ထိုးစနစ်",
                "📊 အစီရင်ခံစာများ",
                "⚙️ ဆက်တင်များ"
            ]
        else:  # user
            page_options = [
                "🏠 ပင်မစာမျက်နှာ",
                "📊 အစီရင်ခံစာများ",
                "⚙️ ဆက်တင်များ"
            ]
        
        selected_page = st.radio("စာမျက်နှာရွေးချယ်ရန်", page_options)
        st.session_state.current_page = selected_page
        
        st.divider()
        
        # Quick stats
        st.markdown("### 📈 အချက်အလက်အကျဉ်း")
        
        if st.session_state.user_role in ['admin', 'agent']:
            today_entries = st.session_state.today_entries.get(st.session_state.current_user, [])
            total_amount = sum(entry['amount'] for entry in today_entries)
            
            col_stat1, col_stat2 = st.columns(2)
            with col_stat1:
                st.metric("ယနေ့အရေအတွက်", len(today_entries))
            with col_stat2:
                st.metric("ယနေ့ပမာဏ", f"{total_amount:,} Ks")
        else:
            st.metric("စုစုပေါင်းအကောင့်", len(st.session_state.users_db))
        
        st.divider()
        
        # Logout button
        if st.button("🚪 **ထွက်ခွာမည်**", use_container_width=True):
            log_activity("Logout", f"User: {st.session_state.current_user}")
            st.session_state.logged_in = False
            st.session_state.user_role = ''
            st.session_state.current_user = ''
            st.rerun()

# ==================== HOME PAGE ====================
def render_home_page():
    """Home dashboard"""
    st.markdown('<h1 class="main-title">🏠 ပင်မစာမျက်နှာ</h1>', unsafe_allow_html=True)
    
    user_info = st.session_state.users_db[st.session_state.current_user]
    
    # Welcome message
    col_welcome, col_stats = st.columns([2, 1])
    
    with col_welcome:
        st.markdown(f"""
        <div class="info-box">
            <h2>👋 ကြိုဆိုပါတယ် {user_info['name']}!</h2>
            <p><strong>အခန်းကဏ္ဍ:</strong> {user_info['role']}</p>
            <p><strong>အကောင့်ဖွင့်သည့်ရက်:</strong> {user_info['created_at']}</p>
            <p><strong>နောက်ဆုံးဝင်ရောက်ချိန်:</strong> {user_info['last_login']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick actions based on role
        st.markdown("### 🚀 အမြန်လုပ်ဆောင်ချက်များ")
        
        if st.session_state.user_role in ['admin', 'agent']:
            col_act1, col_act2, col_act3 = st.columns(3)
            
            with col_act1:
                if st.button("🎯 2D ထိုးရန်", use_container_width=True):
                    st.session_state.current_page = "🎰 2D ထိုးစနစ်"
                    st.rerun()
            
            with col_act2:
                if st.button("📋 စာရင်းကြည့်ရန်", use_container_width=True):
                    st.session_state.current_page = "🎰 2D ထိုးစနစ်"
                    st.rerun()
            
            with col_act3:
                if st.button("📊 အစီရင်ခံစာ", use_container_width=True):
                    st.session_state.current_page = "📊 အစီရင်ခံစာများ"
                    st.rerun()
        
        if st.session_state.user_role == 'admin':
            col_admin1, col_admin2 = st.columns(2)
            
            with col_admin1:
                if st.button("👥 အေဂျင့်မန်နေဂျာ", use_container_width=True):
                    st.session_state.current_page = "👥 အကောင့်စီမံခန့်ခွဲမှု"
                    st.rerun()
            
            with col_admin2:
                if st.button("⚙️ ဆက်တင်များ", use_container_width=True):
                    st.session_state.current_page = "⚙️ ဆက်တင်များ"
                    st.rerun()
    
    with col_stats:
        # System stats
        st.markdown("### 📊 စနစ်အချက်အလက်")
        
        total_users = len(st.session_state.users_db)
        admin_count = sum(1 for u in st.session_state.users_db.values() if u['role'] == 'admin')
        agent_count = sum(1 for u in st.session_state.users_db.values() if u['role'] == 'agent')
        user_count = sum(1 for u in st.session_state.users_db.values() if u['role'] == 'user')
        
        st.metric("စုစုပေါင်းအသုံးပြုသူ", total_users)
        st.metric("Admin များ", admin_count)
        st.metric("အေဂျင့်များ", agent_count)
        st.metric("User များ", user_count)
        
        # Activity log preview
        st.markdown("### 📝 နောက်ဆုံးလုပ်ဆောင်ချက်များ")
        recent_activities = st.session_state.activity_log[-5:]
        
        if recent_activities:
            for activity in reversed(recent_activities):
                st.caption(f"{activity['timestamp']} - {activity['user']}: {activity['action']}")
        else:
            st.info("မည်သည့်လုပ်ဆောင်ချက်မှမရှိသေးပါ။")

# ==================== 2D SYSTEM ====================
def render_2d_system():
    """2D Betting System"""
    
    # Check if user is agent or admin
    if st.session_state.user_role not in ['admin', 'agent']:
        st.error("⚠️ ဤစနစ်ကို အသုံးပြုခွင့်မရှိပါ။ Admin သို့မဟုတ် Agent များသာအသုံးပြုနိုင်ပါသည်။")
        return
    
    # Check if user has configured sheet URL
    user_config = st.session_state.user_configs.get(st.session_state.current_user, {})
    
    if not user_config.get('sheet_url'):
        render_sheet_configuration()
        return
    
    # Create tabs for 2D system
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 ဂဏန်းထည့်ရန်", "📋 ယနေ့စာရင်း", "⚙️ 2D ဆက်တင်များ", "📊 2D အစီရင်ခံစာ"])
    
    with tab1:
        render_2d_entry_form()
    
    with tab2:
        render_2d_today_entries()
    
    with tab3:
        render_2d_settings()
    
    with tab4:
        render_2d_reports()

def render_sheet_configuration():
    """Sheet configuration for 2D system"""
    st.markdown('<h1 class="main-title">🎰 2D ထိုးစနစ်</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <h3>📋 Google Sheets ချိတ်ဆက်ရန်</h3>
    <p>2D ထိုးစနစ်ကိုအသုံးပြုရန် ကျေးဇူးပြု၍ သင့်ရဲ့ Google Sheets URL ကိုထည့်ပါ။</p>
    <p>ဒေတာများကို ဒီ Sheet ထဲသို့အလိုအလျောက်သိမ်းဆည်းပေးပါမည်။</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("sheet_config_form"):
        sheet_url = st.text_input(
            "Google Sheets URL *",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="သင့်ရဲ့ Google Sheets လင့်ကိုထည့်ပါ"
        )
        
        script_url = st.text_input(
            "Google Apps Script URL (Optional)",
            placeholder="https://script.google.com/...",
            help="Auto-update အတွက် Apps Script URL"
        )
        
        # Test connection
        test_col1, test_col2 = st.columns([1, 3])
        with test_col1:
            test_connection = st.form_submit_button("🔗 ချိတ်ဆက်စမ်းသပ်မည်")
        
        if test_connection and sheet_url:
            with st.spinner("ချိတ်ဆက်စမ်းသပ်နေပါသည်..."):
                sheet, message = connect_to_google_sheets(sheet_url)
                if sheet:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
        
        # Save configuration
        save_config = st.form_submit_button("💾 သိမ်းဆည်းမည်", use_container_width=True)
        
        if save_config and sheet_url:
            st.session_state.user_configs[st.session_state.current_user] = {
                'sheet_url': sheet_url,
                'script_url': script_url
            }
            
            sheet, message = connect_to_google_sheets(sheet_url)
            if sheet:
                st.success(f"✅ ဆက်တင်များသိမ်းဆည်းပြီး Google Sheets ချိတ်ဆက်ပြီးပါပြီ။")
                st.balloons()
                time.sleep(2)
                st.rerun()
            else:
                st.error(f"❌ ဆက်တင်များသိမ်းဆည်းပြီးသော်လည်း {message}")

def render_2d_entry_form():
    """2D number entry form"""
    st.markdown('<h2 class="sub-title">🎯 ဂဏန်းထည့်သွင်းရန်</h2>', unsafe_allow_html=True)
    
    # Hide/show toggle
    col_hide, col_info = st.columns([1, 3])
    with col_hide:
        if st.button("🙈 ဖျောက်မည်", key="hide_2d_form"):
            st.session_state.hidden_sections['2d_form'] = True
            st.rerun()
    
    if st.session_state.hidden_sections.get('2d_form', False):
        if st.button("👁️ ပြမည်", key="show_2d_form"):
            st.session_state.hidden_sections['2d_form'] = False
            st.rerun()
        return
    
    with st.form("number_entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            better_name = st.text_input(
                "ထိုးသူအမည် *",
                placeholder="ဥပမာ - ကိုကျော်မင်း"
            )
            
            number = st.text_input(
                "ထိုးမည့်ဂဏန်း *",
                placeholder="ဥပမာ - 55 (2D) သို့မဟုတ် 123 (3D)"
            )
            
            winning_number = st.text_input(
                "ပေါက်ဂဏန်း (Optional)",
                placeholder="ထွက်သောဂဏန်း"
            )
        
        with col2:
            quantity = st.number_input(
                "အရေအတွက် *",
                min_value=1,
                max_value=100,
                value=1
            )
            
            amount = 0
            if number and quantity:
                is_valid, _ = validate_number(number)
                if is_valid:
                    amount = calculate_amount(number, quantity)
            
            st.markdown(f"""
            <div style="background-color: #F0F9FF; padding: 1rem; border-radius: 10px;">
                <p><strong>တွက်ချက်ထားသောပမာဏ:</strong></p>
                <h2 style="color: #1E40AF; text-align: center;">{amount:,} Ks</h2>
                <p style="text-align: center; font-size: 0.9rem; color: #6B7280;">
                (ဂဏန်းတစ်လုံးလျှင် {PRICE_PER_NUMBER:,} Ks)
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            note = st.text_area(
                "မှတ်ချက် (Optional)",
                placeholder="အထူးမှတ်ချက်ရှိပါကထည့်ပါ",
                height=50
            )
        
        submitted = st.form_submit_button(
            "✅ **ဂဏန်းထည့်သွင်းမည်**",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            errors = []
            
            is_name_valid, name_error = validate_name(better_name)
            if not is_name_valid:
                errors.append(name_error)
            
            is_number_valid, number_error = validate_number(number)
            if not is_number_valid:
                errors.append(number_error)
            
            if quantity <= 0:
                errors.append("အရေအတွက်သည် ၁ ထက်ကြီးရမည်")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                entry = {
                    'id': len(st.session_state.today_entries.get(st.session_state.current_user, [])) + 1,
                    'time': format_myanmar_time(),
                    'name': better_name,
                    'number': number,
                    'quantity': quantity,
                    'amount': amount,
                    'winning_number': winning_number if winning_number else '',
                    'status': 'စောင့်ဆိုင်းနေ',
                    'note': note if note else ''
                }
                
                if st.session_state.current_user not in st.session_state.today_entries:
                    st.session_state.today_entries[st.session_state.current_user] = []
                
                st.session_state.today_entries[st.session_state.current_user].append(entry)
                
                user_config = st.session_state.user_configs.get(st.session_state.current_user, {})
                sheet_url = user_config.get('sheet_url', '')
                script_url = user_config.get('script_url', '')
                
                if sheet_url:
                    success, message = save_to_google_sheets(entry, sheet_url, script_url)
                    if success:
                        st.success(f"✅ ဂဏန်းထည့်သွင်းပြီး Google Sheets သို့သိမ်းဆည်းပြီးပါပြီ။")
                    else:
                        st.warning(f"⚠️ ဂဏန်းထည့်သွင်းပြီးသော်လည်း {message}")
                else:
                    st.success("✅ ဂဏန်းထည့်သွင်းပြီးပါပြီ။")
                
                st.balloons()

def render_2d_today_entries():
    """Today's 2D entries"""
    st.markdown('<h2 class="sub-title">📋 ယနေ့ထည့်သွင်းထားသောဂဏန်းများ</h2>', unsafe_allow_html=True)
    
    # Hide/show toggle
    if st.button("🙈 ဤကဏ္ဍကိုဖျောက်မည်", key="hide_today_2d"):
        st.session_state.hidden_sections['today_2d'] = True
        st.rerun()
    
    if st.session_state.hidden_sections.get('today_2d', False):
        if st.button("👁️ ဤကဏ္ဍကိုပြမည်", key="show_today_2d"):
            st.session_state.hidden_sections['today_2d'] = False
            st.rerun()
        return
    
    today_entries = st.session_state.today_entries.get(st.session_state.current_user, [])
    
    if not today_entries:
        st.info("ယနေ့အတွက် မည်သည့်ဂဏန်းမှမထည့်ရသေးပါ။")
        return
    
    # Summary
    total_quantity = sum(entry['quantity'] for entry in today_entries)
    total_amount = sum(entry['amount'] for entry in today_entries)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("စုစုပေါင်းအရေအတွက်", len(today_entries))
    with col2:
        st.metric("စုစုပေါင်းထိုးခြင်းအရေအတွက်", total_quantity)
    with col3:
        st.metric("စုစုပေါင်းပမာဏ", f"{total_amount:,} Ks")
    
    st.divider()
    
    # Edit/Delete
    st.markdown("### ✏️ စာရင်းပြင်ဆင်ခြင်း/ဖျက်ခြင်း")
    
    for i, entry in enumerate(today_entries):
        with st.expander(f"#{i+1} - {entry['name']} ({entry['number']}) - {entry['amount']:,} Ks"):
            col_info, col_actions = st.columns([3, 1])
            
            with col_info:
                st.write(f"**အချိန်:** {entry['time']}")
                st.write(f"**ထိုးသူအမည်:** {entry['name']}")
                st.write(f"**ဂဏန်း:** {entry['number']}")
                st.write(f"**အရေအတွက်:** {entry['quantity']}")
                st.write(f"**ပမာဏ:** {entry['amount']:,} Ks")
                if entry['winning_number']:
                    st.write(f"**ပေါက်ဂဏန်း:** {entry['winning_number']}")
                st.write(f"**အခြေအနေ:** {entry['status']}")
                if entry['note']:
                    st.write(f"**မှတ်ချက်:** {entry['note']}")
            
            with col_actions:
                if st.button("✏️", key=f"edit_2d_{i}"):
                    st.session_state.editing_2d_entry = i
                    st.rerun()
                
                if st.button("🗑️", key=f"delete_2d_{i}"):
                    today_entries.pop(i)
                    st.success("စာရင်းဖျက်ပြီးပါပြီ။")
                    time.sleep(1)
                    st.rerun()
    
    # Edit form
    if 'editing_2d_entry' in st.session_state:
        entry_index = st.session_state.editing_2d_entry
        if entry_index < len(today_entries):
            entry = today_entries[entry_index]
            
            st.markdown("---")
            st.markdown("### ✏️ စာရင်းပြင်ဆင်ခြင်း")
            
            with st.form(f"edit_2d_form_{entry_index}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    edited_name = st.text_input("ထိုးသူအမည်", value=entry['name'])
                    edited_number = st.text_input("ဂဏန်း", value=entry['number'])
                    edited_winning = st.text_input("ပေါက်ဂဏန်း", value=entry.get('winning_number', ''))
                
                with col2:
                    edited_quantity = st.number_input("အရေအတွက်", 
                                                     min_value=1, 
                                                     value=entry['quantity'])
                    edited_status = st.selectbox(
                        "အခြေအနေ",
                        ["စောင့်ဆိုင်းနေ", "ထိုးပြီး", "ပေါက်ပြီး", "မပေါက်ပါ"],
                        index=["စောင့်ဆိုင်းနေ", "ထိုးပြီး", "ပေါက်ပြီး", "မပေါက်ပါ"]
                            .index(entry['status'])
                    )
                    edited_note = st.text_area("မှတ်ချက်", value=entry.get('note', ''))
                
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.form_submit_button("💾 သိမ်းဆည်းမည်"):
                        today_entries[entry_index]['name'] = edited_name
                        today_entries[entry_index]['number'] = edited_number
                        today_entries[entry_index]['quantity'] = edited_quantity
                        today_entries[entry_index]['amount'] = calculate_amount(edited_number, edited_quantity)
                        today_entries[entry_index]['winning_number'] = edited_winning
                        today_entries[entry_index]['status'] = edited_status
                        today_entries[entry_index]['note'] = edited_note
                        
                        user_config = st.session_state.user_configs.get(st.session_state.current_user, {})
                        sheet_url = user_config.get('sheet_url', '')
                        if sheet_url:
                            edited_entry = today_entries[entry_index].copy()
                            edited_entry['note'] = f"(ပြင်ဆင်ထား) {edited_note}"
                            save_to_google_sheets(edited_entry, sheet_url)
                        
                        del st.session_state.editing_2d_entry
                        st.success("စာရင်းပြင်ဆင်ပြီးပါပြီ။")
                        time.sleep(1)
                        st.rerun()
                
                with col_cancel:
                    if st.form_submit_button("❌ ပယ်ဖျက်မည်"):
                        del st.session_state.editing_2d_entry
                        st.rerun()

def render_2d_settings():
    """2D system settings"""
    st.markdown('<h2 class="sub-title">⚙️ 2D ဆက်တင်များ</h2>', unsafe_allow_html=True)
    
    user_config = st.session_state.user_configs.get(st.session_state.current_user, {})
    
    with st.form("2d_settings_form"):
        st.markdown("### 🔗 Google Sheets ဆက်တင်များ")
        
        current_sheet_url = st.text_input(
            "Google Sheets URL",
            value=user_config.get('sheet_url', ''),
            placeholder="https://docs.google.com/spreadsheets/d/..."
        )
        
        current_script_url = st.text_input(
            "Google Apps Script URL",
            value=user_config.get('script_url', ''),
            placeholder="https://script.google.com/..."
        )
        
        if st.form_submit_button("🔗 ချိတ်ဆက်စမ်းသပ်မည်"):
            if current_sheet_url:
                with st.spinner("ချိတ်ဆက်စမ်းသပ်နေပါသည်..."):
                    sheet, message = connect_to_google_sheets(current_sheet_url)
                    if sheet:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
            else:
                st.warning("Sheet URL ထည့်ပါ")
        
        if st.form_submit_button("💾 ဆက်တင်များသိမ်းဆည်းမည်"):
            st.session_state.user_configs[st.session_state.current_user] = {
                'sheet_url': current_sheet_url,
                'script_url': current_script_url
            }
            st.success("✅ ဆက်တင်များသိမ်းဆည်းပြီးပါပြီ။")
            st.rerun()
    
    st.divider()
    
    # Data management
    st.markdown("### 🗃️ ဒေတာစီမံခန့်ခွဲမှု")
    
    col_reset, col_export = st.columns(2)
    
    with col_reset:
        if st.button("🔄 ယနေ့စာရင်းအားလုံးဖျက်ရန်"):
            if st.checkbox("သေချာပါသလား?"):
                st.session_state.today_entries[st.session_state.current_user] = []
                st.success("ယနေ့စာရင်းအားလုံးဖျက်ပြီးပါပြီ။")
                time.sleep(1)
                st.rerun()
    
    with col_export:
        if st.button("📤 ယနေ့ဒေတာထုတ်ယူရန်"):
            today_entries = st.session_state.today_entries.get(st.session_state.current_user, [])
            if today_entries:
                df = pd.DataFrame(today_entries)
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                
                today_date = get_today_date()
                st.download_button(
                    label="💾 CSV ဖိုင်ဒေါင်းလုတ်လုပ်ရန်",
                    data=csv,
                    file_name=f"2d_entries_{st.session_state.current_user}_{today_date}.csv",
                    mime="text/csv"
                )
            else:
                st.info("ယနေ့အတွက် မည်သည့်ဒေတာမှမရှိသေးပါ။")

def render_2d_reports():
    """2D reports"""
    st.markdown('<h2 class="sub-title">📊 2D အစီရင်ခံစာ</h2>', unsafe_allow_html=True)
    
    # Date selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("စတင်ရက်", 
                                  value=datetime.now(MYANMAR_TZ).date())
    with col2:
        end_date = st.date_input("ပြီးဆုံးရက်", 
                                value=datetime.now(MYANMAR_TZ).date())
    
    # Report type
    report_type = st.selectbox(
        "အစီရင်ခံစာအမျိုးအစား",
        ["နေ့စဉ်အစီရင်ခံစာ", "ဂဏန်းအလိုက်အစီရင်ခံစာ", "ဘဏ္ဍာရေးအစီရင်ခံစာ"]
    )
    
    if st.button("📊 အစီရင်ခံစာထုတ်မည်"):
        today_entries = st.session_state.today_entries.get(st.session_state.current_user, [])
        
        if today_entries:
            df = pd.DataFrame(today_entries)
            
            # Summary stats
            total_entries = len(df)
            total_amount = df['amount'].sum()
            avg_per_entry = df['amount'].mean()
            
            col_sum1, col_sum2, col_sum3 = st.columns(3)
            with col_sum1:
                st.metric("စုစုပေါင်းအရေအတွက်", total_entries)
            with col_sum2:
                st.metric("စုစုပေါင်းပမာဏ", f"{total_amount:,} Ks")
            with col_sum3:
                st.metric("ပျမ်းမျှပမာဏ", f"{avg_per_entry:,.0f} Ks")
            
            # Top numbers
            st.markdown("### 🔝 အများဆုံးထိုးသောဂဏန်းများ")
            number_counts = df['number'].value_counts().head(10)
            st.bar_chart(number_counts)
            
            # Export option
            if st.button("📥 အစီရင်ခံစာထုတ်ယူရန်"):
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="💾 CSV အစီရင်ခံစာဒေါင်းလုတ်လုပ်ရန်",
                    data=csv,
                    file_name=f"2d_report_{st.session_state.current_user}_{get_today_date()}.csv",
                    mime="text/csv"
                )
        else:
            st.info("ယနေ့အတွက် မည်သည့်ဒေတာမှမရှိသေးပါ။")

# ==================== USER MANAGEMENT ====================
def render_user_management():
    """User management panel (admin only)"""
    if st.session_state.user_role != 'admin':
        st.error("⚠️ ဤစနစ်ကို Admin များသာအသုံးပြုနိုင်ပါသည်။")
        return
    
    st.markdown('<h1 class="main-title">👥 အကောင့်စီမံခန့်ခွဲမှု</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ အကောင့်အသစ်ထည့်ခြင်း", "📋 အကောင့်စာရင်း", "✏️ အကောင့်ပြင်ဆင်ခြင်း", "🗑️ အကောင့်ဖျက်ခြင်း"])
    
    with tab1:
        render_add_user_form()
    
    with tab2:
        render_user_list()
    
    with tab3:
        render_edit_user()
    
    with tab4:
        render_delete_user()

def render_add_user_form():
    """Add new user form"""
    st.markdown('<h3 class="sub-title">အကောင့်အသစ်ထည့်သွင်းရန်</h3>', unsafe_allow_html=True)
    
    with st.form("add_user_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input(
                "အသုံးပြုသူအမည် *",
                placeholder="john_doe",
                help="အင်္ဂလိပ်အက္ခရာ၊ နံပါတ်နှင့် underscore သာ"
            )
            
            new_password = st.text_input(
                "စကားဝှက် *",
                type="password",
                placeholder="အနည်းဆုံး ၆ လုံး"
            )
        
        with col2:
            new_name = st.text_input(
                "အမည်အပြည့်အစုံ *",
                placeholder="ဦးကျော်ကျော်"
            )
            
            new_role = st.selectbox(
                "အခန်းကဏ္ဍ *",
                ["user", "agent", "admin"],
                help="User, Agent, သို့မဟုတ် Admin"
            )
        
        new_email = st.text_input(
            "အီးမေးလ်",
            placeholder="example@gmail.com",
            help="Optional"
        )
        
        submitted = st.form_submit_button(
            "✅ **အကောင့်အသစ်ထည့်သွင်းမည်**",
            use_container_width=True
        )
        
        if submitted:
            success, message = add_new_user(new_username, new_password, new_role, new_name, new_email)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

def render_user_list():
    """User list display"""
    st.markdown('<h3 class="sub-title">အကောင့်များစာရင်း</h3>', unsafe_allow_html=True)
    
    users_list = []
    for username, details in st.session_state.users_db.items():
        # Get 2D stats for agents
        today_count = 0
        today_amount = 0
        if details['role'] in ['admin', 'agent']:
            today_entries = st.session_state.today_entries.get(username, [])
            today_count = len(today_entries)
            today_amount = sum(entry['amount'] for entry in today_entries)
        
        users_list.append({
            'အသုံးပြုသူအမည်': username,
            'အမည်': details['name'],
            'အခန်းကဏ္ဍ': details['role'],
            'အီးမေးလ်': details.get('email', 'N/A'),
            'အကောင့်ဖွင့်သည့်ရက်': details['created_at'],
            'ယနေ့ 2D အရေအတွက်': today_count if details['role'] in ['admin', 'agent'] else 'N/A',
            'ယနေ့ 2D ပမာဏ': f"{today_amount:,} Ks" if details['role'] in ['admin', 'agent'] else 'N/A'
        })
    
    if users_list:
        df = pd.DataFrame(users_list)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("မည်သည့်အကောင့်မှမရှိသေးပါ။")

def render_edit_user():
    """Edit user form"""
    st.markdown('<h3 class="sub-title">အကောင့်အချက်အလက်ပြင်ဆင်ခြင်း</h3>', unsafe_allow_html=True)
    
    user_options = list(st.session_state.users_db.keys())
    selected_user = st.selectbox("ပြင်ဆင်လိုသောအကောင့်ရွေးချယ်ရန်", user_options)
    
    if selected_user:
        user_info = st.session_state.users_db[selected_user]
        
        with st.form("edit_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                edit_name = st.text_input(
                    "အမည်အပြည့်အစုံ *",
                    value=user_info['name']
                )
                
                edit_role = st.selectbox(
                    "အခန်းကဏ္ဍ *",
                    ["user", "agent", "admin"],
                    index=["user", "agent", "admin"].index(user_info['role'])
                )
            
            with col2:
                edit_email = st.text_input(
                    "အီးမေးလ်",
                    value=user_info.get('email', '')
                )
                
                new_password = st.text_input(
                    "စကားဝှက် အသစ် (မထည့်လျှင်ပြီးခဲ့သည့်အတိုင်းထားမည်)",
                    type="password",
                    placeholder="စကားဝှက်အသစ်ထည့်ပါ"
                )
            
            submitted = st.form_submit_button(
                "💾 **အချက်အလက်များသိမ်းဆည်းမည်**",
                use_container_width=True
            )
            
            if submitted:
                update_data = {
                    'name': edit_name,
                    'role': edit_role,
                    'email': edit_email
                }
                
                if new_password:
                    update_data['password'] = new_password
                
                success, message = update_user_info(selected_user, **update_data)
                
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

def render_delete_user():
    """Delete user form"""
    st.markdown('<h3 class="sub-title">အကောင့်ဖျက်ခြင်း</h3>', unsafe_allow_html=True)
    
    deletable_users = [u for u in st.session_state.users_db.keys() 
                      if u != st.session_state.current_user]
    
    if deletable_users:
        selected_user = st.selectbox("ဖျက်လိုသောအကောင့်ရွေးချယ်ရန်", deletable_users)
        
        if selected_user:
            user_info = st.session_state.users_db[selected_user]
            
            st.markdown("### ဖျက်မည့်အကောင့်၏အချက်အလက်များ")
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                st.write(f"**အသုံးပြုသူအမည်:** {selected_user}")
                st.write(f"**အမည်:** {user_info['name']}")
                st.write(f"**အခန်းကဏ္ဍ:** {user_info['role']}")
            
            with col_info2:
                st.write(f"**အကောင့်ဖွင့်သည့်ရက်:** {user_info['created_at']}")
                if user_info.get('email'):
                    st.write(f"**အီးမေးလ်:** {user_info['email']}")
            
            confirm_text = st.text_input(
                "အတည်ပြုခြင်း: အကောင့်ဖျက်ရန် သေချာပါသလား? ဖျက်မည်ဆိုလျှင် အောက်ပါအတိုင်းရေးပါ",
                placeholder="ကျွန်ုပ်အကောင့်ဖျက်ရန်သဘောတူပါသည်"
            )
            
            col_del1, col_del2 = st.columns(2)
            
            with col_del1:
                if st.button("🗑️ **အကောင့်ဖျက်မည်**", 
                           disabled=confirm_text != "ကျွန်ုပ်အကောင့်ဖျက်ရန်သဘောတူပါသည်",
                           use_container_width=True):
                    success, message = delete_user_account(selected_user)
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
            
            with col_del2:
                if st.button("❌ လုပ်ဆောင်ချက်ပယ်ဖျက်မည်", use_container_width=True):
                    st.rerun()
    else:
        st.info("ဖျက်နိုင်သောအကောင့်များမရှိပါ။")

# ==================== REPORTS PAGE ====================
def render_reports_page():
    """Reports page"""
    st.markdown('<h1 class="main-title">📊 အစီရင်ခံစာများ</h1>', unsafe_allow_html=True)
    
    if st.session_state.user_role == 'admin':
        tab1, tab2, tab3 = st.tabs(["📈 စာရင်းဇယားများ", "📅 လုပ်ဆောင်ချက်မှတ်တမ်း", "🔍 Cache စီမံခန့်ခွဲမှု"])
        
        with tab1:
            render_system_statistics()
        
        with tab2:
            render_activity_log()
        
        with tab3:
            render_cache_management()
    else:
        st.info("📊 အစီရင်ခံစာများကို Admin များသာကြည့်ရှုနိုင်ပါသည်။")

def render_system_statistics():
    """System statistics"""
    # User statistics
    total_users = len(st.session_state.users_db)
    admin_count = sum(1 for u in st.session_state.users_db.values() if u['role'] == 'admin')
    agent_count = sum(1 for u in st.session_state.users_db.values() if u['role'] == 'agent')
    user_count = sum(1 for u in st.session_state.users_db.values() if u['role'] == 'user')
    
    # 2D statistics
    total_2d_entries = 0
    total_2d_amount = 0
    for entries in st.session_state.today_entries.values():
        total_2d_entries += len(entries)
        total_2d_amount += sum(entry['amount'] for entry in entries)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("စုစုပေါင်းအသုံးပြုသူ", total_users)
    with col2:
        st.metric("Admin များ", admin_count)
    with col3:
        st.metric("အေဂျင့်များ", agent_count)
    with col4:
        st.metric("ယနေ့ 2D အရေအတွက်", total_2d_entries)
    
    st.divider()
    
    # Activity summary
    st.markdown("### 📈 လုပ်ဆောင်မှုအကျဉ်းချုပ်")
    
    activity_df = pd.DataFrame(st.session_state.activity_log)
    if not activity_df.empty:
        st.dataframe(activity_df, use_container_width=True)
    else:
        st.info("မည်သည့်လုပ်ဆောင်ချက်မှတ်တမ်းမှမရှိသေးပါ။")

def render_activity_log():
    """Activity log viewer"""
    st.markdown('<h3 class="sub-title">လုပ်ဆောင်ချက်မှတ်တမ်း</h3>', unsafe_allow_html=True)
    
    if st.session_state.activity_log:
        # Filter options
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            user_filter = st.multiselect(
                "အသုံးပြုသူအလိုက်စစ်ထုတ်ခြင်း",
                options=list(set(log['user'] for log in st.session_state.activity_log))
            )
        
        with col_filter2:
            action_filter = st.multiselect(
                "လုပ်ဆောင်ချက်အလိုက်စစ်ထုတ်ခြင်း",
                options=list(set(log['action'] for log in st.session_state.activity_log))
            )
        
        # Filter logs
        filtered_logs = st.session_state.activity_log
        
        if user_filter:
            filtered_logs = [log for log in filtered_logs if log['user'] in user_filter]
        
        if action_filter:
            filtered_logs = [log for log in filtered_logs if log['action'] in action_filter]
        
        # Display logs
        for log in reversed(filtered_logs):
            with st.container():
                st.markdown(f"""
                <div style="
                    background-color: white;
                    padding: 12px;
                    border-radius: 8px;
                    border-left: 5px solid #3B82F6;
                    margin: 8px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                ">
                    <strong>{log['action']}</strong>
                    <div style="color: #6B7280; font-size: 12px;">
                        {log['timestamp']} - {log['user']}
                        {f"<br>{log['details']}" if log['details'] else ""}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Export option
        if st.button("📥 မှတ်တမ်းများထုတ်ယူရန်"):
            log_df = pd.DataFrame(filtered_logs)
            csv = log_df.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                label="💾 CSV ဖိုင်ဒေါင်းလုတ်လုပ်ရန်",
                data=csv,
                file_name=f"activity_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("လုပ်ဆောင်ချက်မှတ်တမ်းများမရှိသေးပါ။")

def render_cache_management():
    """Cache management"""
    st.markdown('<h3 class="sub-title">Cache စီမံခန့်ခွဲမှု</h3>', unsafe_allow_html=True)
    
    col_manage1, col_manage2 = st.columns([2, 1])
    
    with col_manage1:
        st.markdown("### Cache လုပ်ဆောင်ချက်များ")
        
        with st.form("cache_management_form"):
            cache_key = st.text_input("Cache Key", placeholder="key")
            cache_value = st.text_input("Cache Value", placeholder="value")
            
            col_ops1, col_ops2, col_ops3 = st.columns(3)
            
            with col_ops1:
                add_cache = st.form_submit_button("➕ Cache ထည့်မည်", use_container_width=True)
            
            with col_ops2:
                remove_cache = st.form_submit_button("➖ Cache ဖယ်ရှားမည်", use_container_width=True)
            
            with col_ops3:
                clear_cache = st.form_submit_button("🧹 Cache အားလုံးဖယ်ရှားမည်", use_container_width=True)
            
            if add_cache:
                if cache_key and cache_value:
                    st.session_state.number_limits_cache[cache_key] = cache_value
                    st.success(f"✅ Cache ထည့်သွင်းပြီးပါပြီ: `{cache_key}` = `{cache_value}`")
                    log_activity("Cache Operation", f"Added: {cache_key}")
                    st.rerun()
                else:
                    st.warning("⚠ Key နှင့် Value ထည့်ပါ")
            
            if remove_cache:
                if cache_key in st.session_state.number_limits_cache:
                    del st.session_state.number_limits_cache[cache_key]
                    st.success(f"✅ Cache ဖယ်ရှားပြီးပါပြီ: `{cache_key}`")
                    log_activity("Cache Operation", f"Removed: {cache_key}")
                    st.rerun()
                else:
                    st.warning("⚠ Key မတွေ့ပါ")
            
            if clear_cache:
                st.session_state.number_limits_cache = {}
                st.success("✅ Cache အားလုံးဖယ်ရှားပြီးပါပြီ။")
                log_activity("Cache Operation", "Cleared all cache")
                st.rerun()
    
    with col_manage2:
        st.markdown("### Cache အခြေအနေ")
        
        cache_size = len(st.session_state.number_limits_cache)
        st.metric("Cache အရွယ်အစား", f"{cache_size} items")
        
        if st.button("🔍 Cache အကြောင်းကြည့်ရှုရန်"):
            if st.session_state.number_limits_cache:
                st.write(st.session_state.number_limits_cache)
            else:
                st.info("Cache ထဲတွင် အချက်အလက်မရှိပါ။")

# ==================== SETTINGS PAGE ====================
def render_settings_page():
    """Settings page"""
    st.markdown('<h1 class="main-title">⚙️ ဆက်တင်များ</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔧 အထွေထွေဆက်တင်များ", "📋 စနစ်အချက်အလက်"])
    
    with tab1:
        render_general_settings()
    
    with tab2:
        render_system_info()

def render_general_settings():
    """General settings"""
    st.markdown("### 🔧 အထွေထွေဆက်တင်များ")
    
    with st.form("general_settings_form"):
        # Theme settings
        st.markdown("#### 🎨 UI Theme")
        theme = st.selectbox("Theme ရွေးချယ်ရန်", ["Light", "Dark", "Auto"])
        
        # Language settings
        st.markdown("#### 🌐 ဘာသာစကား")
        language = st.selectbox("ဘာသာစကားရွေးချယ်ရန်", ["မြန်မာ", "အင်္ဂလိပ်"])
        
        # Data settings
        st.markdown("#### 💾 ဒေတာစီမံခန့်ခွဲမှု")
        auto_backup = st.checkbox("အလိုအလျောက် Backup လုပ်မည်", value=True)
        backup_frequency = st.selectbox("Backup ကြိမ်နှုန်း", ["နေ့စဉ်", "အပတ်စဉ်", "လစဉ်"])
        
        col_save, col_reset = st.columns(2)
        with col_save:
            save_settings = st.form_submit_button("💾 ဆက်တင်များသိမ်းဆည်းမည်", use_container_width=True)
        
        if save_settings:
            st.success("✅ ဆက်တင်များသိမ်းဆည်းပြီးပါပြီ။")
            log_activity("Settings", "Updated general settings")

def render_system_info():
    """System information"""
    st.markdown("### 📋 စနစ်အချက်အလက်")
    
    # System information cards
    col_sys1, col_sys2, col_sys3 = st.columns(3)
    
    with col_sys1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 20px; border-radius: 10px; text-align: center;">
            <h3>🏢 စနစ်</h3>
            <p style="font-size: 24px; margin: 10px 0;">2D & အကောင့်မန်နေဂျာ</p>
            <p>ဗားရှင်း 1.0.0</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_sys2:
        total_users = len(st.session_state.users_db)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    color: white; padding: 20px; border-radius: 10px; text-align: center;">
            <h3>📊 ဒေတာ</h3>
            <p style="font-size: 24px; margin: 10px 0;">{total_users}</p>
            <p>စုစုပေါင်းအသုံးပြုသူ</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_sys3:
        activity_count = len(st.session_state.activity_log)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    color: white; padding: 20px; border-radius: 10px; text-align: center;">
            <h3>📈 လုပ်ဆောင်မှု</h3>
            <p style="font-size: 24px; margin: 10px 0;">{activity_count}</p>
            <p>လုပ်ဆောင်ချက်မှတ်တမ်း</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Detailed system info
    st.markdown("#### 🖥️ နည်းပညာအချက်အလက်")
    
    col_detail1, col_detail2 = st.columns(2)
    
    with col_detail1:
        st.markdown("""
        **ဆော့ဖ်ဝဲအချက်အလက်:**
        - **အမည်:** 2D စနစ် & အကောင့်မန်နေဂျာ
        - **ဗားရှင်း:** 1.0.0
        - **ဖွံ့ဖြိုးမှု:** Streamlit
        - **ဘာသာစကား:** Python 3.8+
        
        **ဒေတာဘေ့စ်:**
        - **အမျိုးအစား:** In-memory Session
        - **အသုံးပြုသူအရေအတွက်:** {}
        - **Cache အရွယ်အစား:** {} items
        """.format(len(st.session_state.users_db), len(st.session_state.number_limits_cache)))
    
    with col_detail2:
        st.markdown("""
        **လုံခြုံရေးစနစ်:**
        - **စကားဝှက် Hashing:** SHA-256
        - **Session စီမံခန့်ခွဲမှု:** Streamlit Session State
        - **လုပ်ဆောင်ချက်မှတ်တမ်း:** ပြည့်စုံ
        
        **ပံ့ပိုးမှုများ:**
        - **Multi-role Access:** Admin/Agent/User
        - **Google Sheets Integration:** အလိုအလျောက်
        - **ဒေတာထုတ်ယူမှု:** CSV Export
        """)

# ==================== RUN APPLICATION ====================
if __name__ == "__main__":
    main()
