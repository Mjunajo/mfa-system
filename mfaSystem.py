import streamlit as st
import pyotp
import sqlite3
import bcrypt
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
import base64

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'register'
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            password TEXT,
            totp_secret TEXT,
            is_verified BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def save_user(username, email, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        totp_secret = pyotp.random_base32()
        hashed_pw = hash_password(password)
        c.execute(
            'INSERT INTO users (username, email, password, totp_secret) VALUES (?, ?, ?, ?)',
            (username, email, hashed_pw, totp_secret)
        )
        conn.commit()
        return totp_secret
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    return user

def generate_qr(username, secret):
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(username, issuer_name="MFA System")
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Initialize database
init_db()

# App header
st.set_page_config(page_title="Secure MFA System", layout="centered")

# Custom CSS for styling
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 4px;
    }
    .stTextInput>div>div>input {
        background-color: white;
    }
    .error-msg {
        color: #ff0000;
        padding: 10px;
        border-radius: 4px;
        margin: 10px 0;
    }
    .success-msg {
        color: #4CAF50;
        padding: 10px;
        border-radius: 4px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Main title
st.title("🔐 Secure MFA System")
st.markdown("---")

# Tab selection
tabs = ["Register", "Login", "Verify TOTP"]
selected_tab = st.radio("", tabs, horizontal=True, key="tabs")

if selected_tab == "Register":
    st.subheader("Register New Account")
    
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Register")
        
        if submit_button:
            if username and email and password:
                totp_secret = save_user(username, email, password)
                if totp_secret:
                    qr_code = generate_qr(username, totp_secret)
                    st.success("Registration successful! Scan this QR code with your authenticator app.")
                    st.markdown(f'<img src="data:image/png;base64,{qr_code}" style="width:200px">', unsafe_allow_html=True)
                    st.code(totp_secret, language=None)
                    st.info("Please save this secret key as backup!")
                else:
                    st.error("Username or email already exists!")
            else:
                st.error("Please fill in all fields!")

elif selected_tab == "Login":
    st.subheader("Login to Your Account")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if username and password:
                user = get_user(username)
                if user and verify_password(password, user[2]):
                    st.session_state.user = username
                    st.success("Login successful! Please verify your TOTP code.")
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password!")
            else:
                st.error("Please fill in all fields!")

elif selected_tab == "Verify TOTP":
    if st.session_state.user:
        st.subheader("Verify TOTP Code")
        
        with st.form("totp_form"):
            totp_code = st.text_input("Enter TOTP Code")
            submit_button = st.form_submit_button("Verify")
            
            if submit_button:
                if totp_code:
                    user = get_user(st.session_state.user)
                    if user:
                        totp = pyotp.TOTP(user[3])
                        if totp.verify(totp_code):
                            st.success("TOTP verification successful! You are now fully authenticated.")
                            st.session_state.logged_in = True
                        else:
                            st.error("Invalid TOTP code!")
                    else:
                        st.error("User not found!")
                else:
                    st.error("Please enter TOTP code!")
    else:
        st.warning("Please login first!")

# Show logged in state
if st.session_state.logged_in:
    st.sidebar.success(f"Logged in as: {st.session_state.user}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.experimental_rerun()
