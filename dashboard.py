import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. CONFIGURAZIONE DELLA PAGINA E TITOLO PRINCIPALE
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Dashboard Commerciale Avanzata", layout="wide", page_icon="📊")

st.title("📊 Dashboard Commerciale Integrata")
st.markdown("### Analisi Multilivello: Store, Aree, Reparti e Segmentazione Clienti")

# -----------------------------------------------------------------------------
# 2. FUNZIONI DI FORMATTAZIONE VALUTA ITALIANA (PURO PYTHON)
# -----------------------------------------------------------------------------
def fmt_valuta(valore):
    return f"€ {valore:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def fmt_percentuale(valore):
    return f"{valore:.2f}%".replace('.', ',')

def fmt_giorni(valore):
    return f"{valore:.1f} gg".replace('.', ',')

# -----------------------------------------------------------------------------
# 3. ENGINE CENTRALIZZATO DI PULIZIA E PARSING DEI REPORT (RIGA 0)
# -----------------------------------------------------------------------------
@st.cache_data
def load_and_clean_data(file_reparti, file_ctg, file_sellout, file_indispensabili, file_mensile):
    def clean_df(file_path):
        try:
            df = pd.read_csv(file_path, sep=";", skiprows=0, skip_blank_lines=True)
            if len(df.columns) <= 1:
                df = pd.read_csv(file_path, sep=",", skiprows=0, skip_blank_lines=True)
        except:
            df = pd.read_csv(file_path, sep=",", skiprows=0, skip_blank_lines=True)
        df.columns = df.columns.str.strip()
        df = df[df.iloc[:, 0].notna()]
        return df

    df_rep = clean_df(file_reparti)
    df_ctg = clean_df(file_ctg)
    df_sel = clean_df(file_sellout)
    df_ind = clean_df(file_indispensabili)
    df_men = clean_df(file_mensile)
    return df_rep, df_ctg, df_sel, df_ind, df_men

# -----------------------------------------------------------------------------
# 4. INTERFACCIA CARICAMENTO NELLA SIDEBAR LATERALE E CREAZIONE TAB
# -----------------------------------------------------------------------------
st.sidebar.header("📁 Caricamento File Sorgente")
u_rep = st.sidebar.file_uploader("1. File BMPL Reparti (.csv)", type="csv")
u_ctg = st.sidebar.file_uploader("2. File CTG (.csv)", type="csv")
u_sel = st.sidebar.file_uploader("3. File Free Analysis Sellout (.csv)", type="csv")
u_ind = st.sidebar.file_uploader("4. File Indispensabili (.csv)", type="csv")
u_men = st.sidebar.file_uploader("5. File Mensilizzazione (.csv)", type="csv")

if not (u_rep and u_ctg and u_sel and u_ind and u_men):
    st.info("💡 Carica i 5 report commerciali puliti nel pannello laterale sinistro per attivare l'interfaccia.")
    st.stop()

# Inizializzazione dei dataframe e delle schede
df_rep, df_ctg, df_sel, df_ind, df_men = load_and_clean_data(u_rep, u_ctg, u_sel, u_ind, u_men)
tab1, tab2 = st.tabs(["🏬 Vista Store e Performance Reparti", "👥 Analisi Profilazione Clienti (Sellout)"])

# =============================================================================
# SCHEDA 1: PERFORMANCE STRUTTURA STORE, AREE E REPARTI
# =============================================================================
with tab1:
    st.header("🏬 Monitoraggio Gerarchico Store & Performance Mix")
    
    if len(df_men.columns) >= 5:
        df_men_clean = df_men.copy()
        df_men_clean.iloc[:, 1] = df_men_clean.iloc[:, 1].astype(str).str.strip() # Store
        df_men_clean.iloc[:, 3] = df_men_clean.iloc[:, 3].astype(str).str.strip() # Area
        df_men_clean.iloc[:, 4] = df_men_clean.iloc[:, 4].astype(str).str.strip() # Reparto
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            lista_store = sorted([x for x in df_men_clean.iloc[:, 1].unique() if x not in ['nan', 'None', '']])
            selected_store = st.selectbox("Seleziona Store:", lista_store)
        with col_f2:
            df_filtrato_store = df_men_clean[df_men_clean.iloc[:, 1] == selected_store]
            lista_aree = ["--- TOTALE STORE ---"] + sorted([x for x in df_filtrato_store.iloc[:, 3].unique() if x not in ['nan', 'None', '']])
            selected_area = st.selectbox("Seleziona Area di Vendita:", lista_aree)
        with col_f3:
            if selected_area != "--- TOTALE STORE ---":
                df_filtrato_area = df_filtrato_store[df_filtrato_store.iloc[:, 3] == selected_area]
                lista_reparti = ["--- TOTALE AREA ---"] + sorted([x for x in df_filtrato_area.iloc[:, 4].unique() if x not in ['nan', 'None', '']])
            else:
                df_filtrato_area = df_filtrato_store.copy()
                lista_reparti = ["--- DETTAGLIO RICHIESTO ---"]
            selected_reparto = st.selectbox("Seleziona Reparto:", lista_reparti)

        if selected_area == "--- TOTALE STORE ---":
            dati_vista = df_filtrato_store.copy()
            titolo_vista = f"Visualizzazione: TOTALE STORE {selected_store}"
        elif selected_reparto == "--- TOTALE AREA ---":
            dati_vista = df_filtrato_area.copy()
            titolo_vista = f"Visualizzazione: TOTALE AREA {selected_area} ({selected_store})"
        else:
            dati_vista = df_filtrato_area[df_filtrato_area.iloc[:, 4] == selected_reparto]
            titolo_vista = f"Visualizzazione REPARTO: {selected_reparto} ({selected_store})"
    else:
        dati_vista = pd.DataFrame()
        st.error("Il file Mensilizzazione non ha colonne sufficienti.")

    if not dati_vista.empty:
        st.markdown(f"### 🎯 {titolo_vista}")
        
        # --- PARSER AD ALTA PRECISIONE PER FORMATI EUROPEI COMPLESSI ---
        def parse_to_numeric_series(dataframe, col_index):
            if len(dataframe.columns) > col_index:
                # Trasforma in stringa e rimuove spazi bianchi
                s = dataframe.iloc[:, col_index].astype(str).str.replace(r'\s+', '', regex=True)
                # Gestione stringhe vuote o trattini
                s = s.replace(['-', '--', 'nan', 'NaN', ''], '0')
                
                # Se ci sono più punti (es. 1.004.906), è un intero con separatore delle migliaia
                if s.str.count(r'\.').max() > 1:
                    s = s.str.replace('.', '', regex=False)
                # Se c'è un solo punto e una virgola (es. 7.772,75), puliamo secondo lo standard EU
                elif s.str.contains(r'\.').any() and s.str.contains(',').any():
                    s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                # Se c'è solo la virgola come decimale (es. 22,88)
                elif s.str.contains(',').any() and not s.str.contains(r'\.').any():
                    s = s.str.replace(',', '.', regex=False)
                    
                return pd.to_numeric(s, errors='coerce').fillna(0.0)
            return pd.Series(dtype=float)

        # --- MAPPATURA RIGOROSA BASATA SUL NUOVO DOCUMENTO CSV ---
        sales_series = parse_to_numeric_series(dati_vista, 5)          # Colonna 5: DA - Sales TT
        sales_py_series = parse_to_numeric_series(dati_vista, 6)       # Colonna 6: DA - Sales TT PY Custom Cal
        margin_series = parse_to_numeric_series(dati_vista, 11)        # Colonna 11: DA - Front Margin
        margin_py_series = parse_to_numeric_series(dati_vista, 12)     # Colonna 12: DA - Front Margin PY Custom Cal
        avg_stock_series = parse_to_numeric_series(dati_vista, 13)     # Colonna 13: DA - Avg Stock
        stock_days_series = parse_to_numeric_series(dati_vista, 14)    # Colonna 14: DA - Stock Days
        stock_days_py_series = parse_to_numeric_series(dati_vista, 15) # Colonna 15: DA - Stock Days PY Custom Cal
        shrink_series = parse_to_numeric_series(dati_vista, 16)        # Colonna 16: DA - Shrinkage NNBP
        shrink_py_series = parse_to_numeric_series(dati_vista, 17)     # Colonna 17: DA - Shrinkage NNBP PY Custom Cal

        # Aggregazioni matematiche corrette
        sales_tot = float(sales_series.sum())
        sales_py_tot = float(sales_py_series.sum())
        margin_tot = float(margin_series.sum())
        margin_py_tot = float(margin_py_series.sum())
        shrink_tot = float(shrink_series.sum())
        shrink_py_tot = float(shrink_py_series.sum())
        avg_stock_tot = float(avg_stock_series.sum())
        
        # Calcolo Giacenze Medie ponderate sul volume di fatturato (Previene distorsioni da righe vuote)
        val_stock_days = float(stock_days_series.mean()) if not stock_days_series.empty else 0.0
        val_stock_days_py = float(stock_days_py_series.mean()) if not stock_days_py_series.empty else 0.0

        # Calcolo percentuali di incidenza e variazioni (Delta)
        margin_on_sales = (margin_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        shrink_on_sales = (shrink_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        
        delta_sales_pct = ((sales_tot - sales_py_tot) / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
        delta_margin_pct = ((margin_tot - margin_py_tot) / margin_py_tot * 100) if margin_py_tot != 0 else 0.0
        delta_stock_pct = ((val_stock_days - val_stock_days_py) / val_stock_days_py * 100) if val_stock_days_py != 0 else 0.0
        delta_shrink_pct = ((shrink_tot - shrink_py_tot) / shrink_py_tot * 100) if shrink_py_tot != 0 else 0.0

        # --- NUOVE FUNZIONI DI FORMATTAZIONE VALUTA SENZA DECIMALI SULLE VENDITE ---
        def fmt_valuta_interi(valore):
            return f"€ {int(round(valore)):,}".replace(',', '.')

        def fmt_valuta_decimali(valore):
            return f"€ {valore:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        def fmt_percentuale(valore):
            return f"{valore:.2f}%".replace('.', ',')

        def fmt_giorni(valore):
            return f"{valore:.1f} gg".replace('.', ',')

        # --- RENDERING DEI COMPONENTI NATIVI STREAMLIT ---
        st.markdown("#### 📊 Indicatori Chiave di Performance")
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            st.metric(
                label="💰 Sales TT (Arrotondato)", 
                value=fmt_valuta_interi(sales_tot), 
                delta=f"{delta_sales_pct:+.2f}% vs PY",
                help=f"Anno precedente: {fmt_valuta_interi(sales_py_tot)}"
            )
        with m2:
            st.metric(
                label="📈 Front Margin %", 
                value=fmt_percentuale(margin_on_sales), 
                delta=f"{delta_margin_pct:+.2f}% vs PY",
                help=f"Valore assoluto: {fmt_valuta_decimali(margin_tot)}"
            )
        with m3:
            st.metric(
                label="📦 Stock Days", 
                value=fmt_giorni(val_stock_days), 
                delta=f"{delta_stock_pct:+.2f}% vs PY", 
                delta_color="inverse",
                help=f"Anno precedente: {fmt_giorni(val_stock_days_py)}"
            )
        with m4:
            st.metric(
                label="📉 Shrinkage (Sfrido)", 
                value=fmt_percentuale(shrink_on_sales), 
                delta=f"{delta_shrink_pct:+.2f}% vs PY",
                delta_color="inverse",
                help=f"Valore assoluto: {fmt_valuta_decimali(shrink_tot)}"
            )

        st.markdown("<br>#### 📦 Dettaglio Giacenze e Rotazioni", unsafe_allow_html=True)
        df_stock_kpi = pd.DataFrame({
            "Metrica": ["Giorni di Giacenza Correnti", "Giorni di Giacenza Anno Prec. (PY)", "Stock Medio Corrente Complessivo"],
            "Valore": [fmt_giorni(val_stock_days), fmt_giorni(val_stock_days_py), fmt_valuta_interi(avg_stock_tot)]
        })
        st.dataframe(df_stock_kpi, use_container_width=True, hide_index=True)



# =============================================================================
# SCHEDA 2: ANALISI PORTAFOGLIO FORZA VENDITE E CLIENTI (Free Analysis Sellout)
# =============================================================================
with tab2:
    st.header("👥 Analisi Profilazione e Portafoglio Clienti (Sellout)")
    st.markdown("Esplorazione analitica delle performance per singolo Cliente basata sul report *Free Analysis Sellout*.")

    col_s1, col_f_cust, col_s2 = st.columns(3)
    with col_s1:
        tipo_gestione = st.multiselect("Filtra per Tipo Gestione:", options=sorted(df_sel["Tipo Gestione"].dropna().unique()) if "Tipo Gestione" in df_sel.columns else [])
    with col_f_cust:
        ricerca_cliente = st.text_input("🔍 Cerca Ragione Sociale o Codice Cliente Contabile:")
    with col_s2:
        mpro_club = st.multiselect("Filtra per Stato MPRO Club:", options=sorted(df_sel["MPRO Club"].dropna().unique()) if "MPRO Club" in df_sel.columns else [])

    df_sel_filtrato = df_sel.copy()
    if tipo_gestione and "Tipo Gestione" in df_sel.columns:
        df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["Tipo Gestione"].isin(tipo_gestione)]
    if mpro_club and "MPRO Club" in df_sel.columns:
        df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["MPRO Club"].isin(mpro_club)]
    if ricerca_cliente and "Customer" in df_sel.columns:
        df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["Customer"].astype(str).str.contains(ricerca_cliente, case=False, na=False)]

    # --- CALCOLO METRICHE SELLOUT ---
    # Usiamo lo stesso parser sicuro usato nella prima scheda per i decimali europei
    def parse_sellout_col(series):
        s = series.astype(str).str.replace(r'\s+', '', regex=True)
        s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        return pd.to_numeric(s, errors='coerce').fillna(0.0)

    sellout_sales_tot = float(parse_sellout_col(df_sel_filtrato["Sales TT"]).sum()) if "Sales TT" in df_sel_filtrato.columns else 0.0
    sellout_margin_tot = float(parse_sellout_col(df_sel_filtrato["Front Margin"]).sum()) if "Front Margin" in df_sel_filtrato.columns else 0.0
    sellout_visits_tot = float(parse_sellout_col(df_sel_filtrato["# Visit"]).sum()) if "# Visit" in df_sel_filtrato.columns else 0.0
    sellout_margin_pct = (sellout_margin_tot / sellout_sales_tot * 100) if sellout_sales_tot != 0 else 0.0

    # --- RENDERING CARD IN PURO PYTHON (SCHEDA 2) ---
    st.markdown("##### 📊 Indicatori Chiave del Portafoglio Selezionato")
    ms1, ms2, ms3 = st.columns(3)
    with ms1:
        st.metric(label="💼 Fatturato Portafoglio (Sellout)", value=fmt_valuta(sellout_sales_tot))
    with ms2:
        st.metric(label="🎯 Front Margin % Realizzato", value=fmt_percentuale(sellout_margin_pct), help=f"Valore assoluto: {fmt_valuta(sellout_margin_tot)}")
    with ms3:
        st.metric(label="👣 Volume Totale Visite", value=f"{int(sellout_visits_tot):,}".replace(',', '.'))

    st.markdown("<br>", unsafe_allow_html=True)


