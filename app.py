import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time
import re

# --- ၁။ Page အပြင်အဆင် ---
st.set_page_config(page_title="2D Agent Pro", layout="wide", page_icon="💰")

# --- ၂။ VIP User စာရင်း ---
USERS = {"admin": "123456"}

# --- ၃။ Link များကို Refresh လုပ်သော်လည်း မှတ်မိနေစေရန် (Session သိမ်းခြင်း) ---
if "stored_links" not in st.session_state:
    st.session_state["stored_links"] = {"sheet": "", "script": ""}

# --- ၄။ Login စနစ် ---
def check_password():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if not st.session_state["logged_in"]:
        st.markdown("<h2 style='text-align: center;'>🔐 Member Login</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            u = st.text_input("Username", key="l_user")
            p = st.text_input("Password", type="password", key="l_pw")
            if st.button("Login", use_container_width=True):
                if u in USERS and USERS[u] == p:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = u
                    st.rerun()
                else:
                    st.error("❌ Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
        return False
    return True

if check_password():
    # --- Sidebar Section ---
    st.sidebar.title(f"👋 မင်္ဂလာပါ {st.session_state['username']}")
    
    # Software Setup (Refresh လုပ်လည်း မပျောက်အောင် value သတ်မှတ်ထားသည်)
    with st.sidebar.expander("🛠 Software Setup (Link များ)", expanded=True):
        in_sheet = st.text_input("Google Sheet URL", value=st.session_state["stored_links"]["sheet"])
        in_script = st.text_input("Apps Script URL", value=st.session
