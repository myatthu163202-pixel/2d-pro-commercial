import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time
import re

# --- ၁။ Page Setup ---
st.set_page_config(page_title="2D Agent Pro", layout="wide", page_icon="💰")

# --- ၂။ User Database (အကောင့်တစ်ခုနှင့်တစ်ခု Sheet မတူအောင်ခွဲထားခြင်း) ---
USERS = {"admin": "123456", "thiri": "163202"}

# --- ၃။ Storage (Refresh လုပ်လည်း Link မပျောက်စေရန်) ---
if "user_storage" not in st.session_state:
    st.session_state["user_storage"] = {u: {"sheet": "", "script": ""} for u in USERS}

# --- ၄။ Login စနစ် ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>🔐 Member Login</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        if st.button("Login", use_container_width=True):
            if u in USERS and USERS[u] == p:
                st.session_state["logged_in"] = True
                st.session_state["username"] = u
                st.rerun()
            else:
                st.error("❌ Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
    st.stop()

curr_user = st.session_state["username"]
user_links = st.session_state["user_storage"][curr_user]

# --- ၅။ Sidebar (Link တစ်ခါထည့်ရုံဖြင့် မှတ်ထားပေးမည့်စနစ်) ---
st.sidebar.title(f"👋 {curr_user}")
with st.sidebar.expander("🛠 Software Setup", expanded=False):
    # သိမ်းထားတဲ့ Link ကို ပြန်ပြပေးခြင်းဖြင့် Refresh လုပ်လည်း ထပ်ထည့်စရာမလိုတော့ပါ
    in_sheet = st.text_input("Google Sheet URL", value=user_links["sheet"])
