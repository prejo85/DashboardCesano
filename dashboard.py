import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO

# Configurazione iniziale della pagina Streamlit
st.set_page_config(page_title="Dashboard Commerciale Avanzata", layout="wide", page_icon="📊")

st.title("📊 Dashboard Commerciale Integrata")
st.markdown("### Analisi Multilivello: Store, Reparti, Clienti e Indicatori di Performance")
@st.cache_data
def load_and_clean_data(file_reparti, file_ctg, file_sellout, file_indispensabili, file_mensile):
    """
    Carica i file sorgente eliminando le righe di intestazione/filtro 
    e normalizza i formati numerici italiani (es. 1.256,52 o stringhe con spazi).
    """
    def clean_df(file_path, skip_rows=0):
        # Legge il file gestendo il separatore punto e virgola
        df = pd.read_csv(file_path, sep=";", skiprows=skip_rows, skip_blank_lines=True)
        # Rimuove righe di commento o filtri se presenti all'inizio
        df = df[df.iloc[:, 0].notna() & ~df.iloc[:, 0].astype(str).str.contains("Report Filter|View Filter|^$|bmplreparti", case=False)]
        return df

    def parse_numeric(series):
        # Normalizza i numeri in formato stringa italiano (es. 7.136,81 -> 7136.81)
        series_clean = series.astype(str).str.replace(r'\s+', '', regex=True) # Rimuove spazi vuoti
        series_clean = series_clean.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        return pd.to_numeric(series_clean, errors='coerce').fillna(0)

    # Caricamento e pulizia righe iniziali di metadati
    df_rep = clean_df(file_reparti, skip_rows=6)
    df_ctg = clean_df(file_ctg, skip_rows=6)
    df_sel = clean_df(file_sellout, skip_rows=5)
    df_ind = clean_df(file_indispensabili, skip_rows=5)
    df_men = clean_df(file_mensile, skip_rows=5)

    # Pulizia colonne numeriche per il file bmplreparti e ctg
    for col in ["Sales TT", "Sales TT PY Custom Cal", "Front Margin", "Front Margin PY Custom Cal"]:
        if col in df_rep.columns: df_rep[col] = parse_numeric(df_rep[col])
        if col in df_ctg.columns: df_ctg[col] = parse_numeric(df_ctg[col])
    
    # Pulizia colonne file sellout
    if "Sales TT" in df_sel.columns: df_sel["Sales TT"] = parse_numeric(df_sel["Sales TT"])
    if "Front Margin" in df_sel.columns: df_sel["Front Margin"] = parse_numeric(df_sel["Front Margin"])
        
    # Pulizia colonne file indispensabili
    for col in ["DA - Sales TT", "DA - Sales TT PY Custom Cal", "DA - #Colli", "DA - #Colli PY Custom Cal"]:
        if col in df_ind.columns: df_ind[col] = parse_numeric(df_ind[col])

    # Pulizia colonne file mensilizzazione
    for col in ["DA - Sales TT", "DA - Sales TT PY Custom Cal", "DA - Front Margin", "DA - Front Margin PY Custom Cal", "DA - #Colli", "DA - Stock Days", "DA - Stock Days PY Custom Cal", "DA - Avg Stock", "DA - Shrinkage NNBP"]:
        if col in df_men.columns: df_men[col] = parse_numeric(df_men[col])

    return df_rep, df_ctg, df_sel, df_ind, df_men
# Pannello laterale per il caricamento file
st.sidebar.header("📁 Caricamento File Sorgente")
st.sidebar.markdown("Carica i 5 file estratti per generare la dashboard aggiornata.")

u_rep = st.sidebar.file_uploader("1. File BMPL Reparti (.csv)", type="csv")
u_ctg = st.sidebar.file_uploader("2. File CTG (.csv)", type="csv")
u_sel = u_sel_file = st.sidebar.file_uploader("3. File Free Analysis Sellout (.csv)", type="csv")
u_ind = st.sidebar.file_uploader("4. File Indispensabili (.csv)", type="csv")
u_men = st.sidebar.file_uploader("5. File Mensilizzazione (.csv)", type="csv")

# Blocco se mancano i file
if not (u_rep and u_ctg and u_sel and u_ind and u_men):
    st.info("💡 Per iniziare, carica tutti e 5 i file richiesti nel pannello laterale sinistro.")
    st.stop()

# Elaborazione dei dati caricati
df_rep, df_ctg, df_sel, df_ind, df_men = load_and_clean_data(u_rep, u_ctg, u_sel, u_ind, u_men)

# Creazione delle due schede principali della dashboard
tab1, tab2 = st.tabs(["🏬 Vista Store e Performance Reparti", "👥 Analisi Profilazione Clienti (Sellout)"])
with tab1:
    st.header("🏬 Monitoraggio Gerarchico Store & Performance Mix")
    
    # Filtri dinamici concatenati
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        lista_store = sorted(df_men["Store"].unique())
        selected_store = st.selectbox("Seleziona Store:", lista_store)
    with col_f2:
        df_filtrato_men = df_men[df_men["Store"] == selected_store]
        lista_aree = sorted(df_filtrato_men["Sales Area Deparment"].unique())
        selected_area = st.selectbox("Seleziona Area di Vendita:", lista_aree)
    with col_f3:
        df_filtrato_men = df_filtrato_men[df_filtrato_men["Sales Area Deparment"] == selected_area]
        lista_reparti = sorted(df_filtrato_men["Sales Department"].unique())
        selected_reparto = st.selectbox("Seleziona Reparto:", lista_reparti)

    # Applicazione filtro finale per estrarre la riga del reparto specifico
    dati_mensili_reparto = df_filtrato_men[df_filtrato_men["Sales Department"] == selected_reparto]

    if not dati_mensili_reparto.empty:
        row = dati_mensili_reparto.iloc[0]
        st.markdown(f"### 🎯 KPI Mensilizzazione - Reparto: **{selected_reparto}**")
        
        # Layout metriche principali in card
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Sales TT", f"€ {row['DA - Sales TT']:,.2f}", f"vs PY: € {row['DA - Sales TT PY Custom Cal']:,.2f}")
        m2.metric("Front Margin", f"€ {row['DA - Front Margin']:,.2f}", f"{row['DA - %Front Margin']:.2f}%" if isinstance(row['DA - %Front Margin'], (int, float)) else str(row['DA - %Front Margin']))
        m3.metric("Stock Days", f"{row['DA - Stock Days']:.1f} Giorni", f"Avg Stock: € {row['DA - Avg Stock']:,.2f}")
        m4.metric("Shrinkage NNBP (Sfrido)", f"€ {row['DA - Shrinkage NNBP']:,.2f}")
        
        # Grafico Gauge per i giorni di giacenza
        st.markdown("#### 📦 Efficienza Stock e Rotazioni")
        fig_stock = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = row['DA - Stock Days'],
            domain = {'x': 'y': [0, 1]},
            title = {'text': "Giorni di Giacenza (Giacenza Media / Vendite)"},
            delta = {'reference': row['DA - Stock Days PY Custom Cal'], 'inverse': True},
            gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "royalblue"}}
        ))
        fig_stock.update_layout(height=250, margin=dict(t=30, b=0, l=30, r=30))
        st.plotly_chart(fig_stock, use_container_width=True)
    else:
        st.warning("Nessun dato corrispondente trovato nel file Mensilizzazione per lo Store/Reparto selezionato.")

    st.markdown("---")
    st.subheader("🔗 Indicatori di Reparto Integrati (File Esterni)")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("#### 📈 Indicatori BMPL Reparti")
        match_bmpl = df_rep[df_rep["Sales Department"].astype(str).str.contains(selected_reparto[:3], na=False)]
        if not match_bmpl.empty:
            st.dataframe(match_bmpl[["F/NF", "Sales Department", "Sales TT", "Front Margin", "# Colli"]], use_container_width=True, hide_index=True)
        else:
            st.caption("Nessuna corrispondenza BMPL trovata per questo reparto.")

    with col_c2:
        st.markdown("#### 📌 Monitoraggio Articoli Indispensabili (Focus Reparto)")
        match_indisp = df_ind[df_ind["Sales Department"].astype(str).str.contains(selected_reparto[:3], na=False)]
        if not match_indisp.empty:
            st.dataframe(match_indisp[["G2", "Article", "DA - Sales TT", "DA - #Colli"]], use_container_width=True, hide_index=True)
        else:
            st.caption("Nessun articolo indispensabile censito per questo reparto.")

    st.markdown("---")
    st.subheader("👥 Vista Canale e Categoria Cliente (Dati Report CTG)")
    
    dati_ctg_filtrati = df_ctg[df_ctg["Sales Department"].astype(str).str.contains(selected_reparto[:3], na=False)]
    if not dati_ctg_filtrati.empty:
        pivot_ctg = dati_ctg_filtrati.groupby(["Channel Detail", "Customer Category", "CTG"])[["Sales TT", "# Visits", "Sales per Visit"]].sum().reset_index()
        fig_ctg_bar = px.bar(pivot_ctg, x="Customer Category", y="Sales TT", color="CTG", barmode="group", title="Fatturato per Canale/Categoria Cliente nel Reparto")
        st.plotly_chart(fig_ctg_bar, use_container_width=True)
        st.dataframe(pivot_ctg.sort_values(by="Sales TT", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Nessun dato di profilazione canali/clienti (CTG) disponibile per il reparto selezionato.")
with tab2:
    st.header("👥 Analisi Granulare del Portafoglio Clienti (Sellout)")
    st.markdown("Esplorazione approfondita delle vendite per singolo Cliente basata sull'intero file *Free Analysis Sellout*.")

    # Filtri di scheda per raffinare la ricerca clienti
    col_s1, col_f_cust, col_s2 = st.columns(3)
    with col_s1:
        tipo_gestione = st.multiselect("Filtra per Tipo Gestione:", options=sorted(df_sel["Tipo Gestione"].dropna().unique()))
    with col_f_cust:
        ricerca_cliente = st.text_input("🔍 Cerca per Ragione Sociale / Codice Cliente:")
    with col_s2:
        mpro_club = st.multiselect("Filtra per Stato MPRO Club:", options=sorted(df_sel["MPRO Club"].dropna().unique()))

    # Filtrazione condizionale del dataframe Sellout
    df_sel_filtrato = df_sel.copy()
    if tipo_gestione:
        df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["Tipo Gestione"].isin(tipo_gestione)]
    if mpro_club:
        df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["MPRO Club"].isin(mpro_club)]
    if ricerca_cliente:
        df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["Customer"].astype(str).str.contains(ricerca_cliente, case=False, na=False)]

    # Sezione Grafici e Performance Macro Clienti
    c_g1, c_g2 = st.columns(2)
    with c_g1:
        df_v_sales = df_sel_filtrato.groupby("Venditore")["Sales TT"].sum().reset_index().sort_values(by="Sales TT", ascending=False).head(10)
        fig_v_sales = px.bar(df_v_sales, x="Sales TT", y="Venditore", orientation="h", title="Top 10 Venditori per Fatturato Sviluppato (Sellout)", color="Sales TT", color_continuous_scale="Blugrn")
        st.plotly_chart(fig_v_sales, use_container_width=True)
    with c_g2:
        df_cat_sales = df_sel_filtrato.groupby("Customer Category")["Sales TT"].sum().reset_index()
        fig_cat_sales = px.pie(df_cat_sales, values="Sales TT", names="Customer Category", title="Fatturato per Macrocategoria Cliente", hole=0.3)
        st.plotly_chart(fig_cat_sales, use_container_width=True)

    # Classifica e griglia analitica finale Clienti
    st.markdown("### 📋 Elenco Analitico Clienti (Ordinati per Fatturato Decrescente)")
    df_customer_pivoted = df_sel_filtrato.groupby(["Customer", "Customer Category", "Venditore", "MPRO Club"]).agg({
        "Sales TT": "sum",
        "Front Margin": "sum",
        "# Visit": "sum"
    }).reset_index().sort_values(by="Sales TT", ascending=False)
    
    # Formattazione per la visualizzazione tabellare pulita
    df_customer_pivoted["Sales TT"] = df_customer_pivoted["Sales TT"].map('€ {:,.2f}'.format)
    df_customer_pivoted["Front Margin"] = df_customer_pivoted["Front Margin"].map('€ {:,.2f}'.format)
    
    st.dataframe(df_customer_pivoted, use_container_width=True, hide_index=True)
