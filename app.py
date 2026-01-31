import streamlit as st
import pandas as pd
import hashlib
import re
from datetime import datetime

# ==================== Session State Initialization ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = ''
if 'current_user' not in st.session_state:
    st.session_state.current_user = ''
if 'users_db' not in st.session_state:
    # User database with hashed passwords
    st.session_state.users_db = {
        'admin': {
            'password': hashlib.sha256('admin123'.encode()).hexdigest(),
            'role': 'admin',
            'name': 'စီမံခန့်ခွဲသူ',
            'email': 'admin@company.com',
            'created_at': '2024-01-01',
            'last_login': '2024-01-15'
        },
        'user1': {
            'password': hashlib.sha256('user123'.encode()).hexdigest(),
            'role': 'user',
            'name': 'ဦးကျော်ကျော်',
            'email': 'kyawkyaw@email.com',
            'created_at': '2024-01-05',
            'last_login': '2024-01-14'
        },
        'user2': {
            'password': hashlib.sha256('user456'.encode()).hexdigest(),
            'role': 'user',
            'name': 'ဒေါ်မြမြ',
            'email': 'myamya@email.com',
            'created_at': '2024-01-10',
            'last_login': '2024-01-13'
        }
    }
if 'number_limits_cache' not in st.session_state:
    st.session_state.number_limits_cache = {}
if 'activity_log' not in st.session_state:
    st.session_state.activity_log = []

# ==================== Helper Functions ====================
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

def authenticate(username, password):
    """အသုံးပြုသူအတည်ပြုခြင်း"""
    if username in st.session_state.users_db:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if st.session_state.users_db[username]['password'] == hashed_password:
            # Update last login
            st.session_state.users_db[username]['last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_activity("Login", f"User: {username}")
            return True, st.session_state.users_db[username]['role']
    return False, None

def add_user(username, password, role, name, email=""):
    """အသုံးပြုသူအသစ်ထည့်ခြင်း"""
    # Validation
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
    
    # Add user
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

def update_user(username, **kwargs):
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

def delete_user(username):
    """အသုံးပြုသူဖျက်ခြင်း"""
    if username in st.session_state.users_db:
        if username == st.session_state.current_user:
            return False, "မိမိကိုယ်တိုင်ဖျက်ရန်မဖြစ်နိုင်ပါ။"
        
        del st.session_state.users_db[username]
        log_activity("Delete User", f"Deleted: {username}")
        return True, f"အကောင့် '{username}' ဖျက်ပြီးပါပြီ။"
    return False, "အသုံးပြုသူမတွေ့ပါ။"

def logout():
    """ထွက်ခွာခြင်း"""
    log_activity("Logout", f"User: {st.session_state.current_user}")
    st.session_state.logged_in = False
    st.session_state.user_role = ''
    st.session_state.current_user = ''

# ==================== Page Configuration ====================
st.set_page_config(
    page_title="အကောင့်စီမံခန့်ခွဲမှုစနစ်",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Custom CSS ====================
st.markdown("""
<style>
/* Main styles */
.main-header {
    font-size: 2.5rem;
    color: #1E3A8A;
    text-align: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 3px solid #3B82F6;
}
.sub-header {
    font-size: 1.8rem;
    color: #1E40AF;
    margin-bottom: 1.5rem;
    padding-left: 10px;
    border-left: 5px solid #3B82F6;
}
.section-header {
    font-size: 1.4rem;
    color: #374151;
    margin: 1.5rem 0 1rem 0;
}

/* Box styles */
.info-box {
    background-color: #F0F9FF;
    padding: 1.2rem;
    border-radius: 10px;
    border: 1px solid #BFDBFE;
    margin: 1rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.success-box {
    background-color: #D1FAE5;
    padding: 1.2rem;
    border-radius: 10px;
    border: 1px solid #A7F3D0;
    margin: 1rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.warning-box {
    background-color: #FEF3C7;
    padding: 1.2rem;
    border-radius: 10px;
    border: 1px solid #FDE68A;
    margin: 1rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.error-box {
    background-color: #FEE2E2;
    padding: 1.2rem;
    border-radius: 10px;
    border: 1px solid #FECACA;
    margin: 1rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

/* Button styles */
.stButton > button {
    transition: all 0.3s ease;
    border-radius: 8px;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

/* Form styles */
.stTextInput > div > div > input {
    border-radius: 8px;
}
.stSelectbox > div > div > select {
    border-radius: 8px;
}

/* Table styles */
.dataframe {
    border-radius: 10px;
    overflow: hidden;
}
.dataframe th {
    background-color: #3B82F6 !important;
    color: white !important;
}

/* Sidebar styles */
[data-testid="stSidebar"] {
    background-color: #F8FAFC;
}
[data-testid="stSidebar"] .sidebar-content {
    padding: 2rem 1rem;
}

/* Card styles */
.user-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 15px;
    margin: 1rem 0;
    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

/* Responsive design */
@media (max-width: 768px) {
    .main-header {
        font-size: 2rem;
    }
}
</style>
""", unsafe_allow_html=True)

# ==================== Main Application ====================
def main():
    # ==================== LOGIN PAGE ====================
    if not st.session_state.logged_in:
        render_login_page()
        return
    
    # ==================== LOGGED IN PAGES ====================
    # Sidebar
    render_sidebar()
    
    # Main content based on user role
    if st.session_state.user_role == 'admin':
        render_admin_dashboard()
    else:
        render_user_dashboard()

# ==================== Login Page ====================
def render_login_page():
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown('<h1 class="main-header">🔐 အကောင့်စီမံခန့်ခွဲမှုစနစ်</h1>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("### လုပ်ငန်းစနစ်သို့ ကြိုဆိုပါသည်")
            st.write("ကျေးဇူးပြု၍ အကောင့်ဝင်ရောက်ပါ။")
            st.markdown('</div>', unsafe_allow_html=True)
            
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("👤 **အသုံးပြုသူအမည်**", 
                                       placeholder="သင့်အသုံးပြုသူအမည်ထည့်ပါ",
                                       key="login_username")
                
                password = st.text_input("🔒 **စကားဝှက်**", 
                                       type="password",
                                       placeholder="သင့်စကားဝှက်ထည့်ပါ",
                                       key="login_password")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    login_button = st.form_submit_button("🚀 **ဝင်ရောက်မည်**", 
                                                       use_container_width=True,
                                                       type="primary")
                with col_btn2:
                    clear_button = st.form_submit_button("🗑️ **ရှင်းလင်းမည်**",
                                                        use_container_width=True)
                
                if login_button:
                    if username and password:
                        authenticated, role = authenticate(username, password)
                        if authenticated:
                            st.session_state.logged_in = True
                            st.session_state.user_role = role
                            st.session_state.current_user = username
                            st.success(f"✅ **{username}** အနေနဲ့ ဝင်ရောက်ပြီးပါပြီ။")
                            st.rerun()
                        else:
                            st.error("❌ အသုံးပြုသူအမည် သို့မဟုတ် စကားဝှက် မှားယွင်းနေပါသည်။")
                    else:
                        st.warning("⚠ ကျေးဇူးပြု၍ အသုံးပြုသူအမည်နှင့် စကားဝှက်ထည့်ပါ။")
                
                if clear_button:
                    st.rerun()
            
            # Demo credentials
            with st.expander("📋 သက်သေခံအချက်အလက်များ"):
                col_demo1, col_demo2 = st.columns(2)
                with col_demo1:
                    st.markdown("**👑 Admin Account:**")
                    st.code("အသုံးပြုသူအမည်: admin\nစကားဝှက်: admin123")
                with col_demo2:
                    st.markdown("**👤 User Account:**")
                    st.code("အသုံးပြုသူအမည်: user1\nစကားဝှက်: user123")
            
            st.markdown("---")
            st.caption("© 2024 အကောင့်စီမံခန့်ခွဲမှုစနစ် - ဗားရှင်း 1.0")

# ==================== Sidebar ====================
def render_sidebar():
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
        
        st.divider()
        
        # Navigation
        st.markdown("### 🗺️ လမ်းညွှန်မှု")
        
        if st.session_state.user_role == 'admin':
            page = st.radio(
                "စာမျက်နှာရွေးချယ်ရန်",
                ["🏠 ပင်မစာမျက်နှာ", "👥 အကောင့်စီမံခန့်ခွဲမှု", "📊 အချက်အလက်များ", "⚙️ ဆက်တင်များ"],
                index=0
            )
            st.session_state.current_page = page
        
        st.divider()
        
        # Quick stats
        st.markdown("### 📈 အချက်အလက်အကျဉ်း")
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("စုစုပေါင်းအကောင့်", len(st.session_state.users_db))
        with col_stat2:
            active_admins = sum(1 for u in st.session_state.users_db.values() if u['role'] == 'admin')
            st.metric("Admin များ", active_admins)
        
        st.divider()
        
        # Logout button
        if st.button("🚪 **ထွက်ခွာမည်**", use_container_width=True, type="secondary"):
            logout()
            st.rerun()

# ==================== User Dashboard ====================
def render_user_dashboard():
    user_info = st.session_state.users_db[st.session_state.current_user]
    
    st.markdown(f'<h1 class="main-header">👋 ကြိုဆိုပါတယ် {user_info["name"]}!</h1>', unsafe_allow_html=True)
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # Welcome message
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("### သင့်အကောင့်သို့ ကြိုဆိုပါသည်")
        st.write(f"**အသုံးပြုသူအမည်:** `{st.session_state.current_user}`")
        st.write(f"**အခန်းကဏ္ဍ:** `{user_info['role']}`")
        st.write(f"**အကောင့်ဖွင့်သည့်ရက်:** `{user_info['created_at']}`")
        
        if user_info.get('email'):
            st.write(f"**အီးမေးလ်:** `{user_info['email']}`")
        
        st.markdown("---")
        st.write("**လုပ်ဆောင်နိုင်သည်များ:**")
        st.write("✅ သင့်အချက်အလက်များကြည့်ရှုခြင်း")
        st.write("✅ လုပ်ဆောင်ချက်မှတ်တမ်းကြည့်ရှုခြင်း")
        st.write("❌ အကောင့်အသစ်ထည့်သွင်းခြင်း (Admin များအတွက်သာ)")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Activity log (last 5 activities)
        st.markdown('<h3 class="section-header">📝 လတ်တလောလုပ်ဆောင်ချက်များ</h3>', unsafe_allow_html=True)
        
        user_activities = [log for log in st.session_state.activity_log 
                          if log['user'] == st.session_state.current_user][-5:]
        
        if user_activities:
            for activity in reversed(user_activities):
                with st.container():
                    st.markdown(f"""
                    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 4px solid #4f46e5;">
                    <strong>{activity['action']}</strong><br>
                    <small>{activity['timestamp']}</small><br>
                    <small>{activity['details']}</small>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("မည်သည့်လုပ်ဆောင်ချက်မှမရှိသေးပါ။")
    
    with col_right:
        # Important notice
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("### ⚠ သတိပြုရန်")
        st.write("""
        အကောင့်အသစ်ထည့်သွင်းခွင့်သည် **Admin** များအတွက်သာဖြစ်ပါသည်။
        
        လိုအပ်ပါက သက်ဆိုင်ရာ Admin ထံ တောင်းဆိုပါ။
        
        **အရေးပေါ်အခြေအနေ:**
        - အကောင့်ပြဿနာရှိပါက Admin ကိုအကြောင်းကြားပါ
        - စကားဝှက်မေ့သွားပါက Reset လုပ်ရန်လိုအပ်ပါသည်
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Cache info
        st.markdown('<h3 class="section-header">💾 Cache အချက်အလက်</h3>', unsafe_allow_html=True)
        
        cache_size = len(st.session_state.number_limits_cache)
        st.metric("Cache အရွယ်အစား", f"{cache_size} items")
        
        if st.button("🔍 Cache အချက်အလက်များကြည့်ရှုရန်"):
            if st.session_state.number_limits_cache:
                st.write(st.session_state.number_limits_cache)
            else:
                st.info("Cache ထဲတွင် အချက်အလက်မရှိပါ။")

# ==================== Admin Dashboard ====================
def render_admin_dashboard():
    # Get current page from session state
    current_page = st.session_state.get('current_page', '🏠 ပင်မစာမျက်နှာ')
    
    if current_page == "🏠 ပင်မစာမျက်နှာ":
        render_admin_home()
    elif current_page == "👥 အကောင့်စီမံခန့်ခွဲမှု":
        render_user_management()
    elif current_page == "📊 အချက်အလက်များ":
        render_statistics()
    elif current_page == "⚙️ ဆက်တင်များ":
        render_settings()

def render_admin_home():
    st.markdown('<h1 class="main-header">⚙️ Admin Panel - စီမံခန့်ခွဲမှုဗဟို</h1>', unsafe_allow_html=True)
    
    # Quick stats cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("စုစုပေါင်းအကောင့်", len(st.session_state.users_db))
    with col2:
        admin_count = sum(1 for u in st.session_state.users_db.values() if u['role'] == 'admin')
        st.metric("Admin အကောင့်", admin_count)
    with col3:
        user_count = sum(1 for u in st.session_state.users_db.values() if u['role'] == 'user')
        st.metric("User အကောင့်", user_count)
    with col4:
        today = datetime.now().strftime("%Y-%m-%d")
        today_logins = sum(1 for u in st.session_state.users_db.values() 
                          if u['last_login'].startswith(today))
        st.metric("ယနေ့ဝင်ရောက်သူ", today_logins)
    
    st.divider()
    
    # Quick actions
    st.markdown('<h3 class="sub-header">🚀 အမြန်လုပ်ဆောင်ချက်များ</h3>', unsafe_allow_html=True)
    
    col_act1, col_act2, col_act3 = st.columns(3)
    
    with col_act1:
        if st.button("👤 အကောင့်အသစ်ထည့်ရန်", use_container_width=True):
            st.session_state.current_page = "👥 အကောင့်စီမံခန့်ခွဲမှု"
            st.rerun()
    
    with col_act2:
        if st.button("📊 အချက်အလက်များကြည့်ရန်", use_container_width=True):
            st.session_state.current_page = "📊 အချက်အလက်များ"
            st.rerun()
    
    with col_act3:
        if st.button("📝 လုပ်ဆောင်ချက်မှတ်တမ်း", use_container_width=True):
            view_activity_log()
    
    st.divider()
    
    # Recent activities
    st.markdown('<h3 class="sub-header">📝 နောက်ဆုံးလုပ်ဆောင်ချက်များ</h3>', unsafe_allow_html=True)
    
    recent_activities = st.session_state.activity_log[-10:]
    if recent_activities:
        for activity in reversed(recent_activities):
            col_icon, col_content = st.columns([0.1, 0.9])
            with col_icon:
                if "Login" in activity['action']:
                    st.write("🔐")
                elif "Add" in activity['action']:
                    st.write("➕")
                elif "Update" in activity['action']:
                    st.write("✏️")
                elif "Delete" in activity['action']:
                    st.write("🗑️")
                else:
                    st.write("📝")
            
            with col_content:
                st.markdown(f"""
                **{activity['action']}** - *{activity['user']}*
                <br><small>{activity['timestamp']}</small>
                <br><small>{activity['details']}</small>
                """, unsafe_allow_html=True)
            st.divider()
    else:
        st.info("မည်သည့်လုပ်ဆောင်ချက်မှမရှိသေးပါ။")

# ==================== USER MANAGEMENT PAGE ====================
def render_user_management():
    st.markdown('<h1 class="main-header">👥 အကောင့်စီမံခန့်ခွဲမှု</h1>', unsafe_allow_html=True)
    
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
    """အကောင့်အသစ်ထည့်သွင်းရန် form"""
    st.markdown('<h3 class="section-header">အကောင့်အသစ်ထည့်သွင်းရန်</h3>', unsafe_allow_html=True)
    
    # Important instruction
    st.markdown("""
    <div class="info-box">
    <h4>⚠ မှတ်ချက်</h4>
    <p>ကျေးဇူးပြု၍ အောက်ပါအချက်အလက်များကိုဖြည့်ပြီး <b>"အကောင့်အသစ်ထည့်သွင်းမည်"</b> ခလုတ်ကိုနှိပ်ပါ။</p>
    <p><b>Enter ခလုတ်နှိပ်၍ မပို့ပါနှင့်။</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main form - ဒီနေရာမှာ form submit button ကိုသေချာထည့်ထားပါတယ်
    with st.form("add_user_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input(
                "အသုံးပြုသူအမည် *",
                placeholder="john_doe",
                help="အင်္ဂလိပ်အက္ခရာ၊ နံပါတ်နှင့် underscore သာ (အနည်းဆုံး ၃ လုံး)",
                key="new_username"
            )
            
            new_password = st.text_input(
                "စကားဝှက် *",
                type="password",
                placeholder="အနည်းဆုံး ၆ လုံး",
                help="အနည်းဆုံးစာလုံး ၆ လုံးပါဝင်ရမည်",
                key="new_password"
            )
        
        with col2:
            new_name = st.text_input(
                "အမည်အပြည့်အစုံ *",
                placeholder="ဦးကျော်ကျော်",
                help="အပြည့်အစုံအမည်ထည့်ပါ",
                key="new_fullname"
            )
            
            new_role = st.selectbox(
                "အခန်းကဏ္ဍ *",
                ["user", "admin"],
                help="User သို့မဟုတ် Admin အခန်းကဏ္ဍ",
                key="new_role"
            )
        
        new_email = st.text_input(
            "အီးမေးလ်",
            placeholder="example@gmail.com",
            help="Optional - အီးမေးလ်လိပ်စာ",
            key="new_email"
        )
        
        # Requirements
        st.markdown("""
        <div class="warning-box">
        <h5>✅ လိုအပ်ချက်များ:</h5>
        <ul>
        <li>အသုံးပြုသူအမည် - အနည်းဆုံး ၃ လုံး</li>
        <li>စကားဝှက် - အနည်းဆုံး ၆ လုံး</li>
        <li>အမည်အပြည့်အစုံ - မဖြစ်မနေထည့်ရန်</li>
        <li>* ပါသောနေရာများ - မဖြစ်မနေဖြည့်ရန်</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # FORM SUBMIT BUTTON - ဒီနေရာကအရေးကြီးပါတယ်
        col_submit1, col_submit2 = st.columns([3, 1])
        with col_submit1:
            submitted = st.form_submit_button(
                "✅ **အကောင့်အသစ်ထည့်သွင်းမည်** (ဤခလုတ်ကိုနှိပ်ပါ)",
                use_container_width=True,
                type="primary"
            )
        with col_submit2:
            st.form_submit_button(
                "🗑️ **ရှင်းလင်းမည်**",
                use_container_width=True,
                type="secondary"
            )
        
        if submitted:
            # Validation
            if not all([new_username, new_password, new_name, new_role]):
                st.error("❌ ကျေးဇူးပြု၍ လိုအပ်သောအချက်အလက်အားလုံးကို ဖြည့်စွက်ပါ။")
                return
            
            if len(new_username) < 3:
                st.error("❌ အသုံးပြုသူအမည်သည် အနည်းဆုံး ၃ လုံးပါဝင်ရမည်။")
                return
            
            if len(new_password) < 6:
                st.error("❌ စကားဝှက်သည် အနည်းဆုံး ၆ လုံးပါဝင်ရမည်။")
                return
            
            if not re.match("^[a-zA-Z0-9_]+$", new_username):
                st.error("❌ အသုံးပြုသူအမည်တွင် အင်္ဂလိပ်အက္ခရာ၊ နံပါတ်နှင့် underscore သာပါဝင်နိုင်သည်။")
                return
            
            # Add user
            success, message = add_user(new_username, new_password, new_role, new_name, new_email)
            
            if success:
                st.markdown(f'<div class="success-box"><h4>✅ အောင်မြင်ပါသည်!</h4><p>{message}</p></div>', unsafe_allow_html=True)
                st.balloons()
                
                # Show new user info
                with st.expander("🆕 အသစ်ထည့်သွင်းထားသောအကောင့်အချက်အလက်"):
                    new_user = st.session_state.users_db[new_username]
                    st.json({
                        "အသုံးပြုသူအမည်": new_username,
                        "အမည်": new_user['name'],
                        "အခန်းကဏ္ဍ": new_user['role'],
                        "အီးမေးလ်": new_user['email'],
                        "ဖန်တီးသည့်ရက်": new_user['created_at']
                    })
            else:
                st.error(f"❌ {message}")

def render_user_list():
    """အကောင့်များစာရင်းပြသခြင်း"""
    st.markdown('<h3 class="section-header">အကောင့်များစာရင်း</h3>', unsafe_allow_html=True)
    
    # Search and filter
    col_search, col_filter, col_refresh = st.columns([2, 1, 1])
    
    with col_search:
        search_term = st.text_input("🔍 ရှာဖွေရန်", placeholder="အမည် သို့မဟုတ် အသုံးပြုသူအမည်ဖြင့်ရှာပါ")
    
    with col_filter:
        role_filter = st.selectbox("အခန်းကဏ္ဍရွေးချယ်ရန်", ["အားလုံး", "admin", "user"])
    
    with col_refresh:
        if st.button("🔄 ပြန်လည်စတင်မည်", use_container_width=True):
            st.rerun()
    
    # Display users in table
    users_list = []
    for username, details in st.session_state.users_db.items():
        # Apply filters
        if search_term and search_term.lower() not in username.lower() and search_term.lower() not in details['name'].lower():
            continue
        
        if role_filter != "အားလုံး" and details['role'] != role_filter:
            continue
        
        users_list.append({
            'အသုံးပြုသူအမည်': username,
            'အမည်': details['name'],
            'အခန်းကဏ္ဍ': details['role'],
            'အီးမေးလ်': details.get('email', 'N/A'),
            'အကောင့်ဖွင့်သည့်ရက်': details['created_at'],
            'နောက်ဆုံးဝင်ရောက်ချိန်': details['last_login']
        })
    
    if users_list:
        df = pd.DataFrame(users_list)
        
        # Style the dataframe
        def highlight_admin(row):
            if row['အခန်းကဏ္ဍ'] == 'admin':
                return ['background-color: #d4edda'] * len(row)
            return [''] * len(row)
        
        styled_df = df.style.apply(highlight_admin, axis=1)
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Statistics
        st.markdown("### 📊 စာရင်းဇယား")
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            st.metric("စုစုပေါင်းအကောင့်", len(users_list))
        with col_stat2:
            admin_count = sum(1 for u in users_list if u['အခန်းကဏ္ဍ'] == 'admin')
            st.metric("Admin အကောင့်", admin_count)
        with col_stat3:
            user_count = sum(1 for u in users_list if u['အခန်းကဏ္ဍ'] == 'user')
            st.metric("User အကောင့်", user_count)
        
        # Export option
        if st.button("📥 CSV ဖိုင်ထုတ်ယူရန်"):
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="💾 CSV ဖိုင်ဒေါင်းလုတ်လုပ်ရန်",
                data=csv,
                file_name=f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("ရှာဖွေမှုနှင့်ကိုက်ညီသော အကောင့်များမတွေ့ရှိပါ။")

def render_edit_user():
    """အကောင့်ပြင်ဆင်ခြင်း"""
    st.markdown('<h3 class="section-header">အကောင့်အချက်အလက်ပြင်ဆင်ခြင်း</h3>', unsafe_allow_html=True)
    
    # Select user to edit
    user_options = list(st.session_state.users_db.keys())
    selected_user = st.selectbox("ပြင်ဆင်လိုသောအကောင့်ရွေးချယ်ရန်", user_options)
    
    if selected_user:
        user_info = st.session_state.users_db[selected_user]
        
        with st.form("edit_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                edit_name = st.text_input(
                    "အမည်အပြည့်အစုံ *",
                    value=user_info['name'],
                    key="edit_name"
                )
                
                edit_role = st.selectbox(
                    "အခန်းကဏ္ဍ *",
                    ["user", "admin"],
                    index=0 if user_info['role'] == 'user' else 1,
                    key="edit_role"
                )
            
            with col2:
                edit_email = st.text_input(
                    "အီးမေးလ်",
                    value=user_info.get('email', ''),
                    key="edit_email"
                )
                
                new_password = st.text_input(
                    "စကားဝှက် အသစ် (မထည့်လျှင်ပြီးခဲ့သည့်အတိုင်းထားမည်)",
                    type="password",
                    placeholder="စကားဝှက်အသစ်ထည့်ပါ",
                    key="edit_password"
                )
            
            st.markdown("""
            <div class="info-box">
            <p><b>မှတ်ချက်:</b> စကားဝှက်ကွက်လပ်ထားခဲ့လျှင် လက်ရှိစကားဝှက်အတိုင်းထားမည်။</p>
            </div>
            """, unsafe_allow_html=True)
            
            col_edit1, col_edit2 = st.columns([3, 1])
            with col_edit1:
                submitted = st.form_submit_button(
                    "💾 **အချက်အလက်များသိမ်းဆည်းမည်**",
                    use_container_width=True,
                    type="primary"
                )
            
            if submitted:
                update_data = {
                    'name': edit_name,
                    'role': edit_role,
                    'email': edit_email
                }
                
                if new_password:
                    update_data['password'] = new_password
                
                success, message = update_user(selected_user, **update_data)
                
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

def render_delete_user():
    """အကောင့်ဖျက်ခြင်း"""
    st.markdown('<h3 class="section-header">အကောင့်ဖျက်ခြင်း</h3>', unsafe_allow_html=True)
    
    # Warning message
    st.markdown("""
    <div class="error-box">
    <h4>⚠ သတိပေးချက်</h4>
    <p>အကောင့်ဖျက်ခြင်းသည် <b>ပြန်လည်ရယူ၍မရသော လုပ်ဆောင်ချက်ဖြစ်ပါသည်။</b></p>
    <p>ဖျက်မည့်အကောင့်၏ အချက်အလက်အားလုံးပျက်စီးသွားမည်ဖြစ်ပါသည်။</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Select user to delete (exclude current user)
    deletable_users = [u for u in st.session_state.users_db.keys() 
                      if u != st.session_state.current_user]
    
    if deletable_users:
        selected_user = st.selectbox("ဖျက်လိုသောအကောင့်ရွေးချယ်ရန်", deletable_users)
        
        if selected_user:
            user_info = st.session_state.users_db[selected_user]
            
            # Show user info
            st.markdown("### ဖျက်မည့်အကောင့်၏အချက်အလက်များ")
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                st.write(f"**အသုံးပြုသူအမည်:** {selected_user}")
                st.write(f"**အမည်:** {user_info['name']}")
                st.write(f"**အခန်းကဏ္ဍ:** {user_info['role']}")
            
            with col_info2:
                st.write(f"**အကောင့်ဖွင့်သည့်ရက်:** {user_info['created_at']}")
                st.write(f"**နောက်ဆုံးဝင်ရောက်ချိန်:** {user_info['last_login']}")
                if user_info.get('email'):
                    st.write(f"**အီးမေးလ်:** {user_info['email']}")
            
            # Confirmation
            st.divider()
            confirm_text = st.text_input(
                "အတည်ပြုခြင်း: အကောင့်ဖျက်ရန် သေချာပါသလား? ဖျက်မည်ဆိုလျှင် အောက်ပါအတိုင်းရေးပါ",
                placeholder="ကျွန်ုပ်အကောင့်ဖျက်ရန်သဘောတူပါသည်"
            )
            
            col_del1, col_del2 = st.columns(2)
            
            with col_del1:
                if st.button("🗑️ **အကောင့်ဖျက်မည်**", 
                           type="primary",
                           disabled=confirm_text != "ကျွန်ုပ်အကောင့်ဖျက်ရန်သဘောတူပါသည်",
                           use_container_width=True):
                    success, message = delete_user(selected_user)
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
            
            with col_del2:
                if st.button("❌ လုပ်ဆောင်ချက်ပယ်ဖျက်မည်", use_container_width=True):
                    st.rerun()
    else:
        st.info("ဖျက်နိုင်သောအကောင့်များမရှိပါ။")

# ==================== Statistics Page ====================
def render_statistics():
    st.markdown('<h1 class="main-header">📊 အချက်အလက်များနှင့် အစီရင်ခံစာများ</h1>', unsafe_allow_html=True)
    
    tab_stat1, tab_stat2, tab_stat3 = st.tabs(["📈 စာရင်းဇယားများ", "📅 လုပ်ဆောင်ချက်မှတ်တမ်း", "🔍 Cache စီမံခန့်ခွဲမှု"])
    
    with tab_stat1:
        render_user_statistics()
    
    with tab_stat2:
        view_activity_log()
    
    with tab_stat3:
        manage_cache()

def render_user_statistics():
    """အသုံးပြုသူစာရင်းဇယားများ"""
    # Calculate statistics
    total_users = len(st.session_state.users_db)
    admin_count = sum(1 for u in st.session_state.users_db.values() if u['role'] == 'admin')
    user_count = total_users - admin_count
    
    # Monthly signups (simulated)
    months = ["ဇန်နဝါရီ", "ဖေဖော်ဝါရီ", "မတ်", "ဧပြီ", "မေ", "ဇွန်"]
    signups = [5, 8, 12, 10, 15, 18]  # Example data
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("စုစုပေါင်းအကောင့်", total_users)
    with col2:
        st.metric("Admin အကောင့်", admin_count)
    with col3:
        st.metric("User အကောင့်", user_count)
    with col4:
        active_today = sum(1 for u in st.session_state.users_db.values() 
                          if u['last_login'].startswith(datetime.now().strftime("%Y-%m-%d")))
        st.metric("ယနေ့အသုံးပြုသူ", active_today)
    
    st.divider()
    
    # Charts
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("### 👥 အခန်းကဏ္ဍအလိုက်ခွဲခြားမှု")
        role_data = pd.DataFrame({
            'အခန်းကဏ္ဍ': ['Admin', 'User'],
            'အရေအတွက်': [admin_count, user_count]
        })
        st.bar_chart(role_data.set_index('အခန်းကဏ္ဍ'))
    
    with col_chart2:
        st.markdown("### 📅 လစဉ်အကောင့်တိုးပွားမှု")
        monthly_data = pd.DataFrame({
            'လ': months,
            'အရေအတွက်': signups
        })
        st.line_chart(monthly_data.set_index('လ'))
    
    st.divider()
    
    # User activity heatmap (simulated)
    st.markdown("### 📅 လုပ်ဆောင်မှုအချိန်ဇယား")
    days = ["တနင်္လာ", "အင်္ဂါ", "ဗုဒ္ဓဟူး", "ကြာသပတေး", "သောကြာ", "စနေ", "တနင်္ဂနွေ"]
    hours = [f"{i}:00" for i in range(8, 20)]
    
    # Simulate activity data
    import random
    activity_data = [[random.randint(0, 10) for _ in range(7)] for _ in range(12)]
    
    activity_df = pd.DataFrame(activity_data, index=hours, columns=days)
    
    st.dataframe(activity_df.style.background_gradient(cmap='YlOrRd'), use_container_width=True)
    
    st.caption("အရောင်ရင့်လေလေ လုပ်ဆောင်မှုများလေလေ")

def view_activity_log():
    """လုပ်ဆောင်ချက်မှတ်တမ်းကြည့်ရှုခြင်း"""
    st.markdown('<h3 class="section-header">လုပ်ဆောင်ချက်မှတ်တမ်း</h3>', unsafe_allow_html=True)
    
    if st.session_state.activity_log:
        # Filter options
        col_filter1, col_filter2, col_filter3 = st.columns(3)
        
        with col_filter1:
            user_filter = st.multiselect(
                "အသုံးပြုသူအလိုက်စစ်ထုတ်ခြင်း",
                options=list(set(log['user'] for log in st.session_state.activity_log)),
                default=[]
            )
        
        with col_filter2:
            action_filter = st.multiselect(
                "လုပ်ဆောင်ချက်အလိုက်စစ်ထုတ်ခြင်း",
                options=list(set(log['action'] for log in st.session_state.activity_log)),
                default=[]
            )
        
        with col_filter3:
            date_filter = st.date_input(
                "ရက်စွဲအလိုက်စစ်ထုတ်ခြင်း",
                value=[]
            )
        
        # Filter logs
        filtered_logs = st.session_state.activity_log
        
        if user_filter:
            filtered_logs = [log for log in filtered_logs if log['user'] in user_filter]
        
        if action_filter:
            filtered_logs = [log for log in filtered_logs if log['action'] in action_filter]
        
        if date_filter:
            date_str = date_filter.strftime("%Y-%m-%d")
            filtered_logs = [log for log in filtered_logs if log['timestamp'].startswith(date_str)]
        
        # Display logs
        for log in reversed(filtered_logs):
            with st.container():
                # Determine color based on action
                if "Login" in log['action']:
                    border_color = "#10B981"  # Green
                    icon = "🔐"
                elif "Add" in log['action']:
                    border_color = "#3B82F6"  # Blue
                    icon = "➕"
                elif "Update" in log['action']:
                    border_color = "#F59E0B"  # Yellow
                    icon = "✏️"
                elif "Delete" in log['action']:
                    border_color = "#EF4444"  # Red
                    icon = "🗑️"
                else:
                    border_color = "#6B7280"  # Gray
                    icon = "📝"
                
                st.markdown(f"""
                <div style="
                    background-color: white;
                    padding: 12px;
                    border-radius: 8px;
                    border-left: 5px solid {border_color};
                    margin: 8px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                ">
                    <div style="display: flex; align-items: center; margin-bottom: 5px;">
                        <span style="font-size: 20px; margin-right: 10px;">{icon}</span>
                        <strong style="font-size: 16px;">{log['action']}</strong>
                        <span style="margin-left: auto; color: #6B7280; font-size: 12px;">{log['timestamp']}</span>
                    </div>
                    <div style="color: #4B5563; font-size: 14px;">
                        <strong>အသုံးပြုသူ:</strong> {log['user']}
                        {f"<br><strong>အသေးစိတ်:</strong> {log['details']}" if log['details'] else ""}
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

def manage_cache():
    """Cache စီမံခန့်ခွဲမှု"""
    st.markdown('<h3 class="section-header">Cache စီမံခန့်ခွဲမှု</h3>', unsafe_allow_html=True)
    
    col_manage1, col_manage2 = st.columns([2, 1])
    
    with col_manage1:
        # Cache operations
        st.markdown("### Cache လုပ်ဆောင်ချက်များ")
        
        with st.form("cache_management_form"):
            cache_key = st.text_input("Cache Key", placeholder="key", key="cache_key")
            cache_value = st.text_input("Cache Value", placeholder="value", key="cache_value")
            
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
        # Cache status
        st.markdown("### Cache အခြေအနေ")
        
        cache_size = len(st.session_state.number_limits_cache)
        st.metric("Cache အရွယ်အစား", f"{cache_size} items")
        
        if st.button("🔍 Cache အကြောင်းကြည့်ရှုရန်"):
            if st.session_state.number_limits_cache:
                st.write(st.session_state.number_limits_cache)
            else:
                st.info("Cache ထဲတွင် အချက်အလက်မရှိပါ။")
        
        st.divider()
        
        # Cache statistics
        st.markdown("#### Cache စာရင်းဇယား")
        if cache_size > 0:
            keys = list(st.session_state.number_limits_cache.keys())
            values = list(st.session_state.number_limits_cache.values())
            
            avg_length = sum(len(str(v)) for v in values) / cache_size if cache_size > 0 else 0
            
            st.write(f"**Key များ:** {', '.join(keys[:5])}{'...' if len(keys) > 5 else ''}")
            st.write(f"**ပျမ်းမျှတန်ဖိုးအရွယ်အစား:** {avg_length:.1f} စာလုံး")
            
            # Export cache
            if st.button("📤 Cache ထုတ်ယူရန်"):
                cache_df = pd.DataFrame(
                    list(st.session_state.number_limits_cache.items()),
                    columns=['Key', 'Value']
                )
                csv = cache_df.to_csv(index=False, encoding='utf-8-sig')
                
                st.download_button(
                    label="💾 Cache ဒေါင်းလုတ်လုပ်ရန်",
                    data=csv,
                    file_name=f"cache_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

# ==================== Settings Page ====================
def render_settings():
    st.markdown('<h1 class="main-header">⚙️ စနစ်ဆက်တင်များ</h1>', unsafe_allow_html=True)
    
    tab_set1, tab_set2, tab_set3 = st.tabs(["🔧 အထွေထွေဆက်တင်များ", "🔐 လုံခြုံရေးဆက်တင်များ", "📋 စနစ်အချက်အလက်"])
    
    with tab_set1:
        render_general_settings()
    
    with tab_set2:
        render_security_settings()
    
    with tab_set3:
        render_system_info()

def render_general_settings():
    """အထွေထွေဆက်တင်များ"""
    st.markdown("### 🔧 အထွေထွေဆက်တင်များ")
    
    with st.form("general_settings_form"):
        # Theme settings
        st.markdown("#### 🎨 UI Theme")
        theme = st.selectbox("Theme ရွေးချယ်ရန်", ["Light", "Dark", "Auto"])
        
        # Language settings
        st.markdown("#### 🌐 ဘာသာစကား")
        language = st.selectbox("ဘာသာစကားရွေးချယ်ရန်", ["မြန်မာ", "အင်္ဂလိပ်"])
        
        # Notification settings
        st.markdown("#### 🔔 အသိပေးချက်များ")
        col_notif1, col_notif2 = st.columns(2)
        
        with col_notif1:
            email_notifications = st.checkbox("အီးမေးလ်အသိပေးချက်များ", value=True)
            login_alerts = st.checkbox("ဝင်ရောက်မှုသတိပေးချက်များ", value=True)
        
        with col_notif2:
            error_alerts = st.checkbox("အမှားအယွင်းသတိပေးချက်များ", value=True)
            update_notifications = st.checkbox("အပ်ဒိတ်အသိပေးချက်များ", value=True)
        
        # Data settings
        st.markdown("#### 💾 ဒေတာစီမံခန့်ခွဲမှု")
        auto_backup = st.checkbox("အလိုအလျောက် Backup လုပ်မည်", value=True)
        backup_frequency = st.selectbox("Backup ကြိမ်နှုန်း", ["နေ့စဉ်", "အပတ်စဉ်", "လစဉ်"])
        
        col_save, col_reset = st.columns(2)
        with col_save:
            save_settings = st.form_submit_button("💾 ဆက်တင်များသိမ်းဆည်းမည်", use_container_width=True)
        with col_reset:
            reset_settings = st.form_submit_button("🔄 မူလအတိုင်းပြန်ထားမည်", use_container_width=True)
        
        if save_settings:
            st.success("✅ ဆက်တင်များသိမ်းဆည်းပြီးပါပြီ။")
            log_activity("Settings", "Updated general settings")
        
        if reset_settings:
            st.info("🔄 ဆက်တင်များမူလအတိုင်းပြန်လည်ထားရှိပါမည်။")

def render_security_settings():
    """လုံခြုံရေးဆက်တင်များ"""
    st.markdown("### 🔐 လုံခြုံရေးဆက်တင်များ")
    
    # Password policy
    st.markdown("#### 🔒 စကားဝှက်စည်းမျဉ်းများ")
    
    with st.form("security_settings_form"):
        min_password_length = st.slider("အနည်းဆုံးစကားဝှက်အရှည်", 6, 20, 8)
        require_uppercase = st.checkbox("အကြီးအသေးစာလုံးပါဝင်ရန်", value=True)
        require_numbers = st.checkbox("နံပါတ်ပါဝင်ရန်", value=True)
        require_special = st.checkbox("အထူးသင်္ကေတပါဝင်ရန်", value=False)
        
        # Session settings
        st.markdown("#### ⏱️ Session ဆက်တင်များ")
        session_timeout = st.slider("Session အချိန်ကုန်ဆုံးမှု (မိနစ်)", 15, 240, 60)
        max_login_attempts = st.slider("အများဆုံးဝင်ရောက်ခွင့်ကြိုးစားမှု", 3, 10, 5)
        
        # Security features
        st.markdown("#### 🛡️ အပိုလုံခြုံရေးစနစ်များ")
        two_factor_auth = st.checkbox("၂-ဆင့်အတည်ပြုခြင်း", value=False)
        ip_whitelist = st.checkbox("IP Whitelist သုံးရန်", value=False)
        login_notifications = st.checkbox("ဝင်ရောက်မှုအသိပေးချက်များ", value=True)
        
        col_sec1, col_sec2 = st.columns(2)
        with col_sec1:
            save_security = st.form_submit_button("💾 လုံခြုံရေးဆက်တင်များသိမ်းမည်", use_container_width=True)
        with col_sec2:
            test_security = st.form_submit_button("🧪 လုံခြုံရေးစစ်ဆေးမှုပြုလုပ်မည်", use_container_width=True)
        
        if save_security:
            st.success("✅ လုံခြုံရေးဆက်တင်များသိမ်းဆည်းပြီးပါပြီ။")
            log_activity("Security", "Updated security settings")
        
        if test_security:
            st.info("🔒 လုံခြုံရေးစစ်ဆေးမှုပြုလုပ်နေပါသည်...")
            
            # Simulate security test
            import time
            progress_bar = st.progress(0)
            
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            st.success("✅ လုံခြုံရေးစစ်ဆေးမှု အောင်မြင်ပါသည်။")

def render_system_info():
    """စနစ်အချက်အလက်"""
    st.markdown("### 📋 စနစ်အချက်အလက်")
    
    # System information cards
    col_sys1, col_sys2, col_sys3 = st.columns(3)
    
    with col_sys1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 20px; border-radius: 10px; text-align: center;">
            <h3>🏢 စနစ်</h3>
            <p style="font-size: 24px; margin: 10px 0;">User Management</p>
            <p>ဗားရှင်း 1.0.0</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_sys2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    color: white; padding: 20px; border-radius: 10px; text-align: center;">
            <h3>📊 ဒေတာ</h3>
            <p style="font-size: 24px; margin: 10px 0;">{}</p>
            <p>စုစုပေါင်းအကောင့်</p>
        </div>
        """.format(len(st.session_state.users_db)), unsafe_allow_html=True)
    
    with col_sys3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    color: white; padding: 20px; border-radius: 10px; text-align: center;">
            <h3>📈 လုပ်ဆောင်မှု</h3>
            <p style="font-size: 24px; margin: 10px 0;">{}</p>
            <p>လုပ်ဆောင်ချက်မှတ်တမ်း</p>
        </div>
        """.format(len(st.session_state.activity_log)), unsafe_allow_html=True)
    
    st.divider()
    
    # Detailed system info
    st.markdown("#### 🖥️ နည်းပညာအချက်အလက်")
    
    col_detail1, col_detail2 = st.columns(2)
    
    with col_detail1:
        st.markdown("""
        **ဆော့ဖ်ဝဲအချက်အလက်:**
        - **အမည်:** အကောင့်စီမံခန့်ခွဲမှုစနစ်
        - **ဗားရှင်း:** 1.0.0
        - **ဖွံ့ဖြိုးမှု:** Streamlit
        - **ဘာသာစကား:** Python 3.8+
        
        **ဒေတာဘေ့စ်:**
        - **အမျိုးအစား:** In-memory Session
        - **အကောင့်အရေအတွက်:** {}
        - **Cache အရွယ်အစား:** {} items
        """.format(len(st.session_state.users_db), len(st.session_state.number_limits_cache)))
    
    with col_detail2:
        st.markdown("""
        **လုံခြုံရေးစနစ်:**
        - **စကားဝှက် Hashing:** SHA-256
        - **Session စီမံခန့်ခွဲမှု:** Streamlit Session State
        - **လုပ်ဆောင်ချက်မှတ်တမ်း:** ပြည့်စုံ
        
        **ပံ့ပိုးမှုများ:**
        - **Multi-role Access:** Admin/User
        - **ဒေတာထုတ်ယူမှု:** CSV Export
        - **Cache စီမံခန့်ခွဲမှု:** ပြည့်စုံ
        """)
    
    st.divider()
    
    # System maintenance
    st.markdown("#### 🔧 စနစ်ထိန်းသိမ်းမှု")
    
    col_maint1, col_maint2, col_maint3 = st.columns(3)
    
    with col_maint1:
        if st.button("🔄 Cache ရှင်းလင်းရန်", use_container_width=True):
            st.session_state.number_limits_cache = {}
            st.success("✅ Cache ရှင်းလင်းပြီးပါပြီ။")
            log_activity("System", "Cleared cache")
            st.rerun()
    
    with col_maint2:
        if st.button("📊 Activity Log ရှင်းလင်းရန်", use_container_width=True):
            st.session_state.activity_log = []
            st.success("✅ Activity Log ရှင်းလင်းပြီးပါပြီ။")
            log_activity("System", "Cleared activity log")
            st.rerun()
    
    with col_maint3:
        if st.button("📥 စနစ်အချက်အလက်ထုတ်ယူရန်", use_container_width=True):
            # Create system report
            system_report = {
                "system_info": {
                    "name": "User Management System",
                    "version": "1.0.0",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "user_stats": {
                    "total_users": len(st.session_state.users_db),
                    "admin_count": sum(1 for u in st.session_state.users_db.values() if u['role'] == 'admin'),
                    "user_count": sum(1 for u in st.session_state.users_db.values() if u['role'] == 'user')
                },
                "activity_stats": {
                    "total_activities": len(st.session_state.activity_log),
                    "cache_size": len(st.session_state.number_limits_cache)
                }
            }
            
            # Convert to JSON for download
            import json
            report_json = json.dumps(system_report, indent=2, ensure_ascii=False)
            
            st.download_button(
                label="💾 System Report ဒေါင်းလုတ်လုပ်ရန်",
                data=report_json,
                file_name=f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

# ==================== RUN APPLICATION ====================
if __name__ == "__main__":
    main()
