import streamlit as st
import requests
import psycopg2
import pandas as pd

# --- DB Connection ---
def get_db_connection():
    return psycopg2.connect(
        host="expensetracker.postgres.database.azure.com",
        database="postgres",
        user="expenseadmin",
        password="goodjoe@K",
        port="5432",
        sslmode="require"
    )

# --- Auth Functions ---
def register_user(username, password, name):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password_hash, full_name) VALUES (%s, %s, %s)",
            (username, password, name) # Using simple password for now; use bcrypt later!
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Registration failed: {e}")
        return False

def check_login(username, password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE username = %s AND password_hash = %s", (username, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

# --- UI LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # Toggle between Login and Register
    choice = st.radio("Select Action", ["Login", "Register"], horizontal=True)

    if choice == "Register":
        with st.form("reg_form"):
            st.subheader("Create New Account")
            new_name = st.text_input("Full Name")
            new_user = st.text_input("Choose Username")
            new_pw = st.text_input("Choose Password", type="password")
            reg_submit = st.form_submit_button("Sign Up")
            
            if reg_submit:
                if register_user(new_user, new_pw, new_name):
                    st.success("Account created! You can now Login.")

    else:
        with st.form("login_form"):
            st.subheader("Login to Macha Tracker")
            u_id = st.text_input("Username")
            u_pw = st.text_input("Password", type="password")
            login_submit = st.form_submit_button("Login")
            
            if login_submit:
                user_exists = check_login(u_id, u_pw)
                if user_exists:
                    st.session_state.logged_in = True
                    st.session_state.user_id = u_id
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")

else:
    # --- Main Dashboard ---
    st.sidebar.info(f"User: {st.session_state.user_id}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
    
    st.title("🚀 Macha's Expense Dashboard")
    # ... Rest of your Upload and Chart logic here ...
    # 2. UPLOAD TO N8N
    uploaded_file = st.file_uploader("Upload Receipt", type=['png', 'jpg', 'pdf'])
    if uploaded_file and st.button("Process with AI"):
        webhook_url = "https://praga.app.n8n.cloud/webhook-test/receipt-upload"
        files = {
            'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
        }
        payload = {
            'user_id': st.session_state.user_id
        }
        
        
        with st.spinner("AI analyzing..."):
            res = requests.post(webhook_url, files=files, data=data)
            if res.status_code == 200:
                st.success("Transaction Saved!")
            else:
                st.error("N8N Connection Failed")

    # 3. SHOW RECENT DATA FROM AZURE
    st.markdown("### Your Recent Expenses")
    conn = get_db_connection()
    if conn:
        query = f"SELECT date, merchant, amount, category FROM transactions WHERE user_id = '{st.session_state.user_id}' ORDER BY date DESC"
        df = pd.read_sql(query, conn)
        st.dataframe(df, use_container_width=True)
        conn.close()