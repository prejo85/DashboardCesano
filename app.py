import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# Configurazione della pagina Streamlit
st.set_page_config(page_title="Dashboard Commerciale Cesano", layout="wide", initial_sidebar_state="expanded")

st.title("📈 Dashboard Controllo Gestione - Ottobre 2026")
st.markdown("### Punto Vendita: *0011 - CESANO BOSCONE*")

# --- FUNZIONE DI PULIZIA AUTOMATICA PER I RECODR DEI TUOI REPORT ---
def load_clean_data(uploaded_file, search_keyword):
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        text_stream = io.StringIO(file_bytes.decode('utf-8', errors='ignore'))
        lines = text_stream.readlines()
        
        skip_rows = 0
        for i, line in enumerate(lines):
            if search_keyword in line:
                skip_rows = i
                break
                
        df = pd.read_csv(io.StringIO(file_bytes.decode('utf-8', errors='ignore')), skiprows=skip_rows)
        df = df.dropna(how='all').loc[:, ~df.columns.str.contains('^Unnamed')]
        
        for col in df.columns:
            if any(k in col for k in ['Sales', 'Margin', 'TT', 'Avg', 'Shrinkage', '#Colli', '# Colli', 'Visits']):
                df[col] = df[col].astype(str).str.replace(' ', '')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    return None

# --- BARRA LATERALE INTERATTIVA ---
st.sidebar.header("📁 Caricamento File Protetti")
st.sidebar.markdown("*I file caricati rimarranno solo nella memoria locale del tuo browser.*")
file_bmpl = st.sidebar.file_uploader("1. Report BMPL Reparti (Aggregato)", type=["csv"])
file_mensile = st.sidebar.file_uploader("2. Report Mensilizzazione (Giornaliero)", type=["csv"])
file_ctg = st.sidebar.file_uploader("3. Report CTG (Clienti)", type=["csv"])
file_articoli = st.sidebar.file_uploader("4. Report Indispensabili (Articoli)", type=["csv"])

# Controllo se l'utente ha inserito tutti i file richiesti
if file_bmpl and file_mensile and file_ctg and file_articoli:
    df_bmpl = load_clean_data(file_bmpl, 'Sales Department')
    df_mensile = load_clean_data(file_mensile, 'Date')
    df_ctg = load_clean_data(file_ctg, 'Sales Department')
    df_articoli = load_clean_data(file_articoli, 'Sales Area Deparment')
    
    # --- CALCOLO KPI GENERALI ---
    tot_sales = df_bmpl['Sales TT'].sum()
    tot_sales_py = df_bmpl['Sales TT PY Custom Cal'].sum()
    delta_sales = ((tot_sales - tot_sales_py) / tot_sales_py) * 100 if tot_sales_py != 0 else 0
    tot_margin = df_bmpl['Front Margin'].sum()
    margin_pct = (tot_margin / tot_sales) * 100 if tot_sales != 0 else 0

    # --- CREAZIONE DEI TAB NELL'INTERFACCIA UTENTE ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Performance Vendite", "📦 Logistica & Stock", "👥 Analisi Clienti", "🔥 Focus Articoli KVI"])

    with tab1:
        col1, col2, col3 = st.columns(3)
        col1.metric("Fatturato Totale", f"€ {tot_sales:,.2f}", f"{delta_sales:+.2f}% vs PY")
        col2.metric("Margine Commerciale", f"€ {tot_margin:,.2f}")
        col3.metric("Incidenza Margine", f"{margin_pct:.2f}%")
        st.markdown("---")
        
        st.subheader("Trend Vendite Giornaliere (Corrente vs Anno Precedente)")
        df_daily = df_mensile.groupby('Date')[['DA - Sales TT', 'DA - Sales TT PY Custom Cal']].sum().reset_index()
        df_daily['Date'] = pd.to_datetime(df_daily['Date'], dayfirst=True)
        df_daily = df_daily.sort_values('Date')
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=df_daily['Date'], y=df_daily['DA - Sales TT'], name='Fatturato 2026', line=dict(color='#00CC96', width=3)))
        fig_trend.add_trace(go.Scatter(x=df_daily['Date'], y=df_daily['DA - Sales TT PY Custom Cal'], name='Fatturato PY', line=dict(color='#636EFA', dash='dash')))
        fig_trend.update_layout(template="plotly_dark", height=350, margin=dict(l=20, r=20, t=10, b=10))
        st.plotly_chart(fig_trend, use_container_width=True)

        st.subheader("Fatturato e Margine Lordo per Reparto")
        fig_reparti = px.bar(df_bmpl.sort_values(by='Sales TT'), x='Sales TT', y='Sales Department', color='Front Margin', orientation='h', color_continuous_scale='Turbo', template='plotly_dark')
        st.plotly_chart(fig_reparti, use_container_width=True)

    with tab2:
        st.subheader("Giacenza Media vs Giorni di Rotazione Stock")
        df_logistica = df_mensile.groupby('Sales Department')[['DA - Avg Stock', 'DA - Stock Days']].mean().reset_index()
        fig_stock = px.scatter(df_logistica, x='DA - Stock Days', y='DA - Avg Stock', size='DA - Avg Stock', color='Sales Department', hover_name='Sales Department', size_max=35, template='plotly_dark')
        st.plotly_chart(fig_stock, use_container_width=True)

    with tab3:
        st.subheader("Composizione Target Clienti e Impatto delle Promozioni")
        df_clienti = df_ctg.groupby(['Customer Category'])['Sales TT'].sum().reset_index()
        df_promo = df_ctg.groupby(['Flag Promo'])['Sales TT'].sum().reset_index()
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.plotly_chart(px.pie(df_clienti, values='Sales TT', names='Customer Category', hole=.4, template='plotly_dark'), use_container_width=True)
        with col_c2:
            st.plotly_chart(px.bar(df_promo, x='Flag Promo', y='Sales TT', color='Flag Promo', template='plotly_dark'), use_container_width=True)

    with tab4:
        st.subheader("I 10 Articoli Indispensabili (KVI) più venduti")
        df_top_art = df_articoli.groupby('Article')['DA - Sales TT'].sum().reset_index().sort_values(by='DA - Sales TT', ascending=False).head(10)
        fig_art = px.bar(df_top_art, x='DA - Sales TT', y='Article', orientation='h', template='plotly_dark', color_discrete_sequence=['#AB63FA'])
        st.plotly_chart(fig_art, use_container_width=True)
else:
    st.info("👋 Benvenuto! Carica i quattro file CSV nella barra laterale sinistra per sbloccare i grafici analitici del punto vendita.")
    st.image("https://unsplash.com", caption="Pronto all'elaborazione dei dati di Cesano Boscone")
