import streamlit as st
import requests
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

load_dotenv()

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ExpenseFlow",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

:root {
    --bg:        #0a0a0f;
    --surface:   #111118;
    --border:    #1e1e2e;
    --accent:    #7c3aed;
    --accent2:   #06b6d4;
    --accent3:   #f59e0b;
    --text:      #e2e8f0;
    --muted:     #64748b;
    --success:   #10b981;
    --danger:    #ef4444;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
}

[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

/* Hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* Headings */
h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    letter-spacing: -0.02em;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 1.2rem !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    color: var(--accent2) !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'DM Mono', monospace !important;
    color: var(--muted) !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* Buttons */
.stButton > button {
    background: var(--accent) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: #6d28d9 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(124,58,237,0.4) !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stRadio > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
    font-family: 'DM Mono', monospace !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 2px dashed var(--border) !important;
    border-radius: 12px !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}

/* Divider */
hr {
    border-color: var(--border) !important;
}

/* Sidebar elements */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--muted) !important;
    width: 100%;
}
[data-testid="stSidebar"] .stButton > button:hover {
    border-color: var(--danger) !important;
    color: var(--danger) !important;
    background: transparent !important;
    box-shadow: none !important;
}

/* Success/Error messages */
.stSuccess {
    background: rgba(16,185,129,0.1) !important;
    border: 1px solid rgba(16,185,129,0.3) !important;
    border-radius: 8px !important;
}
.stError {
    background: rgba(239,68,68,0.1) !important;
    border: 1px solid rgba(239,68,68,0.3) !important;
    border-radius: 8px !important;
}

/* Spinner */
.stSpinner > div {
    border-top-color: var(--accent) !important;
}

/* Card component */
.macha-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

.macha-tag {
    display: inline-block;
    background: rgba(124,58,237,0.15);
    color: #a78bfa;
    border: 1px solid rgba(124,58,237,0.3);
    border-radius: 999px;
    font-size: 0.7rem;
    padding: 2px 10px;
    font-family: 'DM Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.1;
}

.hero-sub {
    font-family: 'DM Mono', monospace;
    color: var(--muted);
    font-size: 0.8rem;
    letter-spacing: 0.05em;
}

.login-container {
    max-width: 420px;
    margin: 4rem auto;
}

.stat-row {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border);
}

.category-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 6px;
}
</style>
""", unsafe_allow_html=True)

# ── DB Connection ──────────────────────────────────────────────────────────────
def get_db_connection():
    try:
        return psycopg2.connect(
            host=os.getenv('AZURE_HOST'),
            database=os.getenv('AZURE_DATABASE'),
            user=os.getenv('AZURE_USER'),
            password=os.getenv('AZURE_PASSWORD'),
            port=os.getenv('AZURE_PORT', '5432'),
            sslmode=os.getenv('AZURE_SSLMODE', 'require')
        )
    except Exception as e:
        st.error(f"DB connection failed: {e}")
        return None

# ── Auth ───────────────────────────────────────────────────────────────────────
def register_user(username, password, name):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password_hash, full_name) VALUES (%s, %s, %s)",
            (username, password, name)
        )
        conn.commit()
        cur.close(); conn.close()
        return True
    except Exception as e:
        st.error(f"Registration failed: {e}")
        return False

def check_login(username, password):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT username, full_name FROM users WHERE username = %s AND password_hash = %s",
            (username, password)
        )
        user = cur.fetchone()
        cur.close(); conn.close()
        return user
    except Exception as e:
        st.error(f"Login error: {e}")
        return None

# ── Session Init ───────────────────────────────────────────────────────────────
for key, val in [('logged_in', False), ('user_id', None), ('full_name', None), ('active_tab', 'dashboard')]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── Category Colors ────────────────────────────────────────────────────────────
CAT_COLORS = {
    'Food': '#f59e0b', 'Transport': '#06b6d4', 'Shopping': '#8b5cf6',
    'Entertainment': '#ec4899', 'Health': '#10b981', 'Other': '#64748b',
    'Dining': '#f97316', 'Travel': '#3b82f6', 'Utilities': '#6366f1',
}
def cat_color(cat):
    return CAT_COLORS.get(cat, '#7c3aed')

# ══════════════════════════════════════════════════════════════════════════════
# AUTH PAGES
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:

    st.markdown("""
    <div style="text-align:center; padding: 3rem 0 1rem;">
        <div class="hero-title">💸 ExpenseFlow</div>
        <div class="hero-sub" style="margin-top:0.5rem;">AI-powered expense intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        choice = st.radio("", ["Login", "Register"], horizontal=True, label_visibility="collapsed")
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        if choice == "Register":
            with st.form("reg_form"):
                new_name = st.text_input("Full Name", placeholder="Pragadeesh K")
                new_user = st.text_input("Username", placeholder="username")
                new_pw   = st.text_input("Password", type="password", placeholder="••••••••")
                if st.form_submit_button("Create Account →", use_container_width=True):
                    if register_user(new_user, new_pw, new_name):
                        st.success("✅ Account created! Login now.")
        else:
            with st.form("login_form"):
                u_id = st.text_input("Username", placeholder="username")
                u_pw = st.text_input("Password", type="password", placeholder="••••••••")
                if st.form_submit_button("Login →", use_container_width=True):
                    user = check_login(u_id, u_pw)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_id   = user[0]
                        st.session_state.full_name = user[1] or user[0]
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
else:
    uid = st.session_state.user_id

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 1rem 0 1.5rem;">
            <div style="font-family:'Syne',sans-serif; font-weight:800; font-size:1.3rem; color:white;">
                💸 ExpenseFlow
            </div>
            <div style="font-size:0.7rem; color:var(--muted); margin-top:4px; font-family:'DM Mono',monospace;">
                @{uid}
            </div>
        </div>
        <hr style="margin-bottom:1.5rem;">
        """, unsafe_allow_html=True)

        nav = st.radio("", ["📊 Dashboard", "📤 Upload Receipt", "📋 Transactions"], label_visibility="collapsed")
        st.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)

        if st.button("Logout"):
            for key in ['logged_in', 'user_id', 'full_name']:
                st.session_state[key] = False if key == 'logged_in' else None
            st.rerun()

    # ── Load Data ──────────────────────────────────────────────────────────────
    @st.cache_data(ttl=30)
    def load_data(user_id):
        conn = get_db_connection()
        if not conn:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        try:
            df = pd.read_sql(
                "SELECT date, merchant, amount, currency, category FROM transactions WHERE user_id = %s ORDER BY date DESC",
                conn, params=(user_id,)
            )
            df_cat = pd.read_sql(
                "SELECT category, SUM(amount) as total, COUNT(*) as count FROM transactions WHERE user_id = %s GROUP BY category ORDER BY total DESC",
                conn, params=(user_id,)
            )
            df_trend = pd.read_sql(
                "SELECT TO_CHAR(date,'YYYY-MM') as month, SUM(amount) as total FROM transactions WHERE user_id = %s GROUP BY month ORDER BY month",
                conn, params=(user_id,)
            )
            conn.close()
            return df, df_cat, df_trend
        except Exception as e:
            st.error(f"Data load error: {e}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df, df_cat, df_trend = load_data(uid)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB: DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    if nav == "📊 Dashboard":
        st.markdown(f"""
        <div style="margin-bottom:2rem;">
            <div class="hero-title">Dashboard</div>
            <div class="hero-sub">Welcome back, {st.session_state.full_name or uid}</div>
        </div>
        """, unsafe_allow_html=True)

        # KPI row
        total_spend  = df['amount'].astype(float).sum() if not df.empty else 0
        total_txns   = len(df)
        avg_txn      = total_spend / total_txns if total_txns else 0
        top_category = df_cat.iloc[0]['category'] if not df_cat.empty else "—"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Spent",       f"${total_spend:,.0f}")
        c2.metric("Transactions",      total_txns)
        c3.metric("Avg per Transaction", f"${avg_txn:,.0f}")
        c4.metric("Top Category",      top_category)

        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

        if not df.empty:
            col_l, col_r = st.columns([1.2, 1])

            # Donut Chart
            with col_l:
                st.markdown("<div class='macha-card'>", unsafe_allow_html=True)
                st.markdown("<div style='font-family:Syne,sans-serif;font-weight:700;margin-bottom:1rem;'>Spend by Category</div>", unsafe_allow_html=True)
                colors = [cat_color(c) for c in df_cat['category']]
                fig_donut = go.Figure(go.Pie(
                    labels=df_cat['category'],
                    values=df_cat['total'],
                    hole=0.6,
                    marker=dict(colors=colors, line=dict(color='#0a0a0f', width=2)),
                    textfont=dict(family='DM Mono', color='white', size=11),
                    hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>"
                ))
                fig_donut.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='DM Mono', color='#e2e8f0'),
                    legend=dict(font=dict(family='DM Mono', size=11), bgcolor='rgba(0,0,0,0)'),
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=280,
                    showlegend=True
                )
                st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
                st.markdown("</div>", unsafe_allow_html=True)

            # Category breakdown list
            with col_r:
                st.markdown("<div class='macha-card'>", unsafe_allow_html=True)
                st.markdown("<div style='font-family:Syne,sans-serif;font-weight:700;margin-bottom:1rem;'>Breakdown</div>", unsafe_allow_html=True)
                for _, row in df_cat.iterrows():
                    pct = (float(row['total']) / total_spend * 100) if total_spend else 0
                    color = cat_color(row['category'])
                    st.markdown(f"""
                    <div class="stat-row">
                        <span class="category-dot" style="background:{color}"></span>
                        <span style="flex:1;font-size:0.85rem;">{row['category']}</span>
                        <span style="color:{color};font-weight:600;font-size:0.85rem;">₹{float(row['total']):,.0f}</span>
                        <span style="color:var(--muted);font-size:0.75rem;margin-left:8px;">{pct:.0f}%</span>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # Monthly trend
            if not df_trend.empty and len(df_trend) > 1:
                st.markdown("<div class='macha-card'>", unsafe_allow_html=True)
                st.markdown("<div style='font-family:Syne,sans-serif;font-weight:700;margin-bottom:1rem;'>Monthly Trend</div>", unsafe_allow_html=True)
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(
                    x=df_trend['month'], y=df_trend['total'],
                    mode='lines+markers',
                    line=dict(color='#7c3aed', width=2.5),
                    marker=dict(color='#06b6d4', size=7, line=dict(color='#0a0a0f', width=2)),
                    fill='tozeroy',
                    fillcolor='rgba(124,58,237,0.08)',
                    hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>"
                ))
                fig_trend.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='DM Mono', color='#64748b', size=11),
                    xaxis=dict(gridcolor='#1e1e2e', showline=False),
                    yaxis=dict(gridcolor='#1e1e2e', showline=False),
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=220,
                    showlegend=False
                )
                st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
                st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.markdown("""
            <div class="macha-card" style="text-align:center; padding:3rem; color:var(--muted);">
                <div style="font-size:3rem; margin-bottom:1rem;">🧾</div>
                <div style="font-family:'Syne',sans-serif; font-size:1.1rem; color:var(--text);">No transactions yet</div>
                <div style="margin-top:0.5rem; font-size:0.8rem;">Upload a receipt to get started</div>
            </div>
            """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB: UPLOAD
    # ══════════════════════════════════════════════════════════════════════════
    elif nav == "📤 Upload Receipt":
        st.markdown("""
        <div style="margin-bottom:2rem;">
            <div class="hero-title">Upload Receipt</div>
            <div class="hero-sub">Let AI extract & categorize your expenses</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1.5, 1])
        with col1:
            st.markdown("<div class='macha-card'>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "Drop your receipt here",
                type=['png', 'jpg', 'jpeg', 'pdf'],
                label_visibility="visible"
            )

            if uploaded_file:
                st.markdown(f"""
                <div style="margin: 1rem 0; padding: 0.75rem 1rem; background:rgba(6,182,212,0.08); border:1px solid rgba(6,182,212,0.2); border-radius:8px; font-size:0.8rem;">
                    📎 <strong>{uploaded_file.name}</strong> &nbsp;·&nbsp; {uploaded_file.size / 1024:.1f} KB
                </div>
                """, unsafe_allow_html=True)

                if st.button("⚡ Analyze with AI", use_container_width=True):
                    webhook_url = os.getenv('N8N_WEBHOOK_URL', 'https://praga.app.n8n.cloud/webhook-test/receipt-upload')
                    file_bytes = uploaded_file.getvalue()
                    files   = {'file': (uploaded_file.name, file_bytes, uploaded_file.type)}
                    payload = {'user_id': str(uid)}

                    with st.spinner("AI is reading your receipt..."):
                        try:
                            res = requests.post(webhook_url, files=files, data=payload, timeout=30)
                            if res.status_code == 200:
                                st.success("✅ Transaction saved successfully!")
                                st.cache_data.clear()
                                st.balloons()
                            else:
                                st.error(f"Error {res.status_code}: {res.text}")
                        except requests.exceptions.Timeout:
                            st.error("Request timed out. Try again.")
                        except Exception as e:
                            st.error(f"Connection Error: {e}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="macha-card">
                <div style="font-family:'Syne',sans-serif;font-weight:700;margin-bottom:1.2rem;">How it works</div>
                <div class="stat-row">
                    <span style="color:#7c3aed;margin-right:10px;font-size:1.1rem;">1.</span>
                    <span style="font-size:0.82rem;">Upload photo of receipt or bill</span>
                </div>
                <div class="stat-row">
                    <span style="color:#06b6d4;margin-right:10px;font-size:1.1rem;">2.</span>
                    <span style="font-size:0.82rem;">AI extracts merchant, amount & date</span>
                </div>
                <div class="stat-row">
                    <span style="color:#f59e0b;margin-right:10px;font-size:1.1rem;">3.</span>
                    <span style="font-size:0.82rem;">Auto-categorized & stored in your DB</span>
                </div>
                <div class="stat-row" style="border:none;">
                    <span style="color:#10b981;margin-right:10px;font-size:1.1rem;">4.</span>
                    <span style="font-size:0.82rem;">Dashboard updates instantly</span>
                </div>
                <div style="margin-top:1.5rem; padding:0.75rem; background:rgba(124,58,237,0.08); border-radius:8px; font-size:0.75rem; color:var(--muted);">
                    Supports JPG, PNG, PDF · Max 10MB
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB: TRANSACTIONS
    # ══════════════════════════════════════════════════════════════════════════
    elif nav == "📋 Transactions":
        st.markdown("""
        <div style="margin-bottom:2rem;">
            <div class="hero-title">Transactions</div>
            <div class="hero-sub">Full history of your expenses</div>
        </div>
        """, unsafe_allow_html=True)

        if not df.empty:
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                categories = ['All'] + sorted(df['category'].dropna().unique().tolist())
                filter_cat = st.selectbox("Category", categories)
            with col2:
                sort_by = st.selectbox("Sort by", ["Date ↓", "Date ↑", "Amount ↓", "Amount ↑"])
            with col3:
                search = st.text_input("Search merchant", placeholder="e.g. Swiggy")

            # Apply filters
            df_view = df.copy()
            df_view['amount'] = df_view['amount'].astype(float)

            if filter_cat != 'All':
                df_view = df_view[df_view['category'] == filter_cat]
            if search:
                df_view = df_view[df_view['merchant'].str.contains(search, case=False, na=False)]

            sort_map = {
                "Date ↓": ('date', False), "Date ↑": ('date', True),
                "Amount ↓": ('amount', False), "Amount ↑": ('amount', True)
            }
            col_s, asc = sort_map[sort_by]
            df_view = df_view.sort_values(col_s, ascending=asc)

            # Summary strip
            st.markdown(f"""
            <div style="display:flex;gap:2rem;padding:0.75rem 0;margin-bottom:1rem;border-bottom:1px solid var(--border);font-size:0.8rem;color:var(--muted);">
                <span>{len(df_view)} transactions</span>
                <span>Total: <strong style="color:var(--accent2);">₹{df_view['amount'].sum():,.0f}</strong></span>
            </div>
            """, unsafe_allow_html=True)

            # Table with colored categories
            st.dataframe(
                df_view.rename(columns={
                    'date': 'Date', 'merchant': 'Merchant',
                    'amount': 'Amount (₹)', 'currency': 'Currency', 'category': 'Category'
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Amount (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                    "Date": st.column_config.DateColumn(format="DD MMM YYYY"),
                }
            )
        else:
            st.markdown("""
            <div class="macha-card" style="text-align:center; padding:3rem; color:var(--muted);">
                <div style="font-size:3rem; margin-bottom:1rem;">📭</div>
                <div style="font-family:'Syne',sans-serif; font-size:1.1rem; color:var(--text);">No transactions found</div>
            </div>
            """, unsafe_allow_html=True)