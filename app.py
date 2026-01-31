import streamlit as st
import pandas as pd
import hashlib

# ==================== Session State Initialization ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = ''
if 'current_user' not in st.session_state:
    st.session_state.current_user = ''
if 'users_db' not in st.session_state:
    # Simple user database (in real app, use proper database)
    st.session_state.users_db = {
        'admin': {
            'password': hashlib.sha256('admin123'.encode()).hexdigest(),
            'role': 'admin',
            'name': 'စီမံခန့်ခွဲသူ'
        },
        'user1': {
            'password': hashlib.sha256('user123'.encode()).hexdigest(),
            'role': 'user',
            'name': 'အသုံးပြုသူ၁'
        }
    }
if 'number_limits_cache' not in st.session_state:
    st.session_state.number_limits_cache = {}

# ==================== Helper Functions ====================
def authenticate(username, password):
    """အသုံးပြုသူအတည်ပြုခြင်း"""
    if username in st.session_state.users_db:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if st.session_state.users_db[username]['password'] == hashed_password:
            return True, st.session_state.users_db[username]['role']
    return False, None

def add_user(username, password, role, name):
    """အသုံးပြုသူအသစ်ထည့်ခြင်း"""
    if username in st.session_state.users_db:
        return False, "အသုံးပြုသူအမည်ရှိပြီးသားဖြစ်နေပါသည်။"
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    st.session_state.users_db[username] = {
        'password': hashed_password,
        'role': role,
        'name': name
    }
    return True, "အကောင့်အသစ်ထည့်သွင်းပြီးပါပြီ။"

def logout():
    """ထွက်ခွာခြင်း"""
    st.session_state.logged_in = False
    st.session_state.user_role = ''
    st.session_state.current_user = ''

# ==================== Page Configuration ====================
st.set_page_config(
    page_title="အကောင့်စီမံခန့်ခွဲမှုစနစ်",
    page_icon="🔐",
    layout="wide"
)

# ==================== Main Application ====================
def main():
    # Custom CSS for better UI
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #1E40AF;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #F0F9FF;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #3B82F6;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #D1FAE5;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #10B981;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #FEF3C7;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #F59E0B;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ==================== LOGIN PAGE ====================
    if not st.session_state.logged_in:
        st.markdown('<h1 class="main-header">🔐 အကောင့်စီမံခန့်ခွဲမှုစနစ်</h1>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.container():
                st.markdown('<h3 class="sub-header">ဝင်ရောက်ရန်</h3>', unsafe_allow_html=True)
                
                with st.form("login_form"):
                    username = st.text_input("👤 အသုံးပြုသူအမည်", placeholder="သင့်အသုံးပြုသူအမည်ထည့်ပါ")
                    password = st.text_input("🔒 စကားဝှက်", type="password", placeholder="သင့်စကားဝှက်ထည့်ပါ")
                    
                    login_button = st.form_submit_button("🚀 ဝင်ရောက်မည်", use_container_width=True)
                    
                    if login_button:
                        if username and password:
                            authenticated, role = authenticate(username, password)
                            if authenticated:
                                st.session_state.logged_in = True
                                st.session_state.user_role = role
                                st.session_state.current_user = username
                                st.success(f"{username} အနေနဲ့ ဝင်ရောက်ပြီးပါပြီ။")
                                st.rerun()
                            else:
                                st.error("အသုံးပြုသူအမည် သို့မဟုတ် စကားဝှက် မှားယွင်းနေပါသည်။")
                        else:
                            st.warning("ကျေးဇူးပြု၍ အသုံးပြုသူအမည်နှင့် စကားဝှက်ထည့်ပါ။")
                
                # Demo credentials
                with st.expander("သက်သေခံအချက်အလက်များ"):
                    st.write("**Admin:**")
                    st.code("အသုံးပြုသူအမည်: admin\nစကားဝှက်: admin123")
                    st.write("**User:**")
                    st.code("အသုံးပြုသူအမည်: user1\nစကားဝှက်: user123")
        
        return
    
    # ==================== LOGGED IN PAGES ====================
    # Sidebar for navigation and user info
    with st.sidebar:
        st.markdown("### 👤 အသုံးပြုသူအချက်အလက်")
        st.write(f"**အမည်:** {st.session_state.users_db[st.session_state.current_user]['name']}")
        st.write(f"**အခန်းကဏ္ဍ:** {st.session_state.user_role}")
        st.write(f"**အသုံးပြုသူ:** {st.session_state.current_user}")
        
        st.divider()
        
        if st.button("🚪 ထွက်ခွာမည်", use_container_width=True):
            logout()
            st.rerun()
    
    # ==================== USER DASHBOARD ====================
    if st.session_state.user_role == 'user':
        st.markdown('<h1 class="main-header">👋 ကြိုဆိုပါတယ်!</h1>', unsafe_allow_html=True)
        
        user_info = st.session_state.users_db[st.session_state.current_user]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown(f"### မင်္ဂလာပါ {user_info['name']}!")
            st.write("သင်သည် **User** အခန်းကဏ္ဍဖြင့် ဝင်ရောက်ထားပါသည်။")
            st.write("အောက်ပါ feature များကို သုံးစွဲနိုင်ပါသည်။")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("### 📊 သင့်အချက်အလက်များ")
            user_data = {
                "အချက်အလက်": ["အသုံးပြုသူအမည်", "အမည်", "အခန်းကဏ္ဍ", "အကောင့်အမျိုးအစား"],
                "တန်ဖိုး": [
                    st.session_state.current_user,
                    user_info['name'],
                    user_info['role'],
                    "သာမန်အသုံးပြုသူ"
                ]
            }
            st.dataframe(pd.DataFrame(user_data), use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown('<div class="warning-box">', unsafe_allow_html=True)
            st.markdown("### ⚠ သတိပြုရန်")
            st.write("အကောင့်အသစ်ထည့်သွင်းခွင့်သည် **Admin** များအတွက်သာဖြစ်ပါသည်။")
            st.write("လိုအပ်ပါက admin ထံ တောင်းဆိုပါ။")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Cache demonstration for user
            st.markdown("### 💾 Cache အချက်အလက်")
            cache_size = len(st.session_state.number_limits_cache)
            st.metric("Cache အရွယ်အစား", f"{cache_size} items")
            
            if st.button("Cache ကိုကြည့်ရှုမည်"):
                if st.session_state.number_limits_cache:
                    st.write(st.session_state.number_limits_cache)
                else:
                    st.info("Cache ထဲတွင် အချက်အလက်မရှိပါ။")
    
    # ==================== ADMIN DASHBOARD ====================
    elif st.session_state.user_role == 'admin':
        st.markdown('<h1 class="main-header">⚙️ Admin Panel - စီမံခန့်ခွဲမှုဗဟို</h1>', unsafe_allow_html=True)
        
        # Tabs for different admin functions
        tab1, tab2, tab3 = st.tabs(["👥 အကောင့်ထည့်သွင်းခြင်း", "📋 အကောင့်စာရင်း", "⚡ Cache စီမံခန့်ခွဲမှု"])
        
        with tab1:
            st.markdown('<h3 class="sub-header">အကောင့်အသစ်ထည့်သွင်းရန်</h3>', unsafe_allow_html=True)
            
            with st.form("add_account_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_username = st.text_input("အသုံးပြုသူအမည် *", help="အနည်းဆုံး ၃ လုံးပါဝင်ရန်")
                    new_password = st.text_input("စကားဝှက် *", type="password", help="အနည်းဆုံး ၆ လုံးပါဝင်ရန်")
                
                with col2:
                    new_name = st.text_input("အမည် *")
                    new_role = st.selectbox("အခန်းကဏ္ဍ *", ["user", "admin"])
                
                st.markdown("**မှတ်ချက်:** * ပြထားသောနေရာများကို ဖြည့်စွက်ရန်လိုအပ်သည်။")
                
                # SUBMIT BUTTON - အရေးကြီးပါသည်!
                submitted = st.form_submit_button("✅ အကောင့်အသစ်ထည့်သွင်းမည်", use_container_width=True)
                
                if submitted:
                    if not all([new_username, new_password, new_name]):
                        st.error("ကျေးဇူးပြု၍ လိုအပ်သောအချက်အလက်အားလုံးကို ဖြည့်စွက်ပါ။")
                    elif len(new_username) < 3:
                        st.error("အသုံးပြုသူအမည်သည် အနည်းဆုံး ၃ လုံးပါဝင်ရမည်။")
                    elif len(new_password) < 6:
                        st.error("စကားဝှက်သည် အနည်းဆုံး ၆ လုံးပါဝင်ရမည်။")
                    else:
                        success, message = add_user(new_username, new_password, new_role, new_name)
                        if success:
                            st.markdown(f'<div class="success-box">{message}</div>', unsafe_allow_html=True)
                            st.balloons()
                        else:
                            st.error(message)
        
        with tab2:
            st.markdown('<h3 class="sub-header">အကောင့်များစာရင်း</h3>', unsafe_allow_html=True)
            
            # Display all users in a table
            users_list = []
            for username, details in st.session_state.users_db.items():
                users_list.append({
                    'အသုံးပြုသူအမည်': username,
                    'အမည်': details['name'],
                    'အခန်းကဏ္ဍ': details['role'],
                    'အကောင့်အမျိုးအစား': 'Admin' if details['role'] == 'admin' else 'User'
                })
            
            if users_list:
                df = pd.DataFrame(users_list)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("စုစုပေါင်းအကောင့်", len(users_list))
                with col2:
                    admin_count = sum(1 for u in users_list if u['အခန်းကဏ္ဍ'] == 'admin')
                    st.metric("Admin အကောင့်", admin_count)
                with col3:
                    user_count = sum(1 for u in users_list if u['အခန်းကဏ္ဍ'] == 'user')
                    st.metric("User အကောင့်", user_count)
            else:
                st.info("အကောင့်များမတွေ့ရှိပါ။")
        
        with tab3:
            st.markdown('<h3 class="sub-header">Cache စီမံခန့်ခွဲမှု</h3>', unsafe_allow_html=True)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Cache operations
                st.write("### Cache လုပ်ဆောင်ချက်များ")
                
                cache_key = st.text_input("Cache Key", placeholder="key")
                cache_value = st.text_input("Cache Value", placeholder="value")
                
                col_add, col_clear, col_view = st.columns(3)
                
                with col_add:
                    if st.button("➕ Cache ထည့်မည်", use_container_width=True):
                        if cache_key and cache_value:
                            st.session_state.number_limits_cache[cache_key] = cache_value
                            st.success(f"Cache ထည့်သွင်းပြီးပါပြီ: {cache_key}")
                            st.rerun()
                        else:
                            st.warning("Key နှင့် Value ထည့်ပါ")
                
                with col_clear:
                    if st.button("🗑️ Cache ဖယ်ရှားမည်", use_container_width=True):
                        if cache_key in st.session_state.number_limits_cache:
                            del st.session_state.number_limits_cache[cache_key]
                            st.success(f"Cache ဖယ်ရှားပြီးပါပြီ: {cache_key}")
                            st.rerun()
                        else:
                            st.warning("Key မတွေ့ပါ")
                
                with col_view:
                    if st.button("👁️ Cache ကြည့်မည်", use_container_width=True):
                        if st.session_state.number_limits_cache:
                            st.write(st.session_state.number_limits_cache)
                        else:
                            st.info("Cache ထဲတွင် အချက်အလက်မရှိပါ။")
            
            with col2:
                st.write("### Cache စာရင်း")
                if st.session_state.number_limits_cache:
                    for key, value in st.session_state.number_limits_cache.items():
                        st.code(f"{key}: {value}")
                    st.write(f"**စုစုပေါင်း:** {len(st.session_state.number_limits_cache)} items")
                else:
                    st.info("Cache ထဲတွင် အချက်အလက်မရှိပါ။")
                
                if st.button("🧹 Cache အားလုံးဖယ်ရှားမည်", use_container_width=True):
                    st.session_state.number_limits_cache = {}
                    st.success("Cache အားလုံးဖယ်ရှားပြီးပါပြီ။")
                    st.rerun()

# ==================== RUN APP ====================
if __name__ == "__main__":
    main()
