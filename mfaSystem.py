# app.py
import streamlit as st
from database import create_user, get_user, verify_user
from notifications import generate_otp, send_email_otp, send_sms_otp
from auth import verify_password, store_otp, verify_otp

# Page configuration
st.set_page_config(page_title="Secure MFA System", layout="centered")

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #1a1a1a;
        color: white;
        border: none;
        padding: 15px 24px;
        border-radius: 8px;
        font-weight: 600;
    }
    .stTextInput>div>div>input {
        background-color: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        padding: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# App header
st.title("🔐 Secure MFA System")
st.markdown("---")

# Navigation
tabs = ["Register", "Login", "Verify"]
selected_tab = st.radio("", tabs, horizontal=True)

if selected_tab == "Register":
    st.subheader("Create New Account")
    
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        phone = st.text_input("Phone Number (with country code)", value="+91")
        password = st.text_input("Password", type="password")
        mfa_preference = st.selectbox(
            "Preferred MFA Method",
            ["email", "phone"]
        )
        submit = st.form_submit_button("Register")
        
        if submit:
            if username and email and password:
                try:
                    create_user(username, email, phone, password, mfa_preference)
                    st.success("Registration successful! Please login.")
                except Exception as e:
                    st.error(f"Registration failed: {str(e)}")

elif selected_tab == "Login":
    st.subheader("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            user = get_user(username)
            if user and verify_password(password, user['password']):
                otp = generate_otp()
                store_otp(username, otp)
                
                if user['mfa_preference'] == 'email':
                    if send_email_otp(user['email'], otp):
                        st.success("OTP sent to your email!")
                        st.session_state.user = username
                else:
                    if send_sms_otp(user['phone'], otp):
                        st.success("OTP sent to your phone!")
                        st.session_state.user = username
            else:
                st.error("Invalid username or password!")

elif selected_tab == "Verify":
    if st.session_state.user:
        st.subheader("Verify OTP")
        
        with st.form("verify_form"):
            otp = st.text_input("Enter OTP")
            submit = st.form_submit_button("Verify")
            
            if submit:
                if verify_otp(st.session_state.user, otp):
                    verify_user(st.session_state.user)
                    st.session_state.authenticated = True
                    st.success("Successfully verified!")
                else:
                    st.error("Invalid or expired OTP!")
    else:
        st.warning("Please login first!")

# Show authenticated state
if st.session_state.authenticated:
    st.sidebar.success(f"Logged in as: {st.session_state.user}")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.experimental_rerun()
