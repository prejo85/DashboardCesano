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
# 2. FUNZIONI DI FORMATTAZIONE VALUTA ED ESPRESSIONI ITALIANE (PURO PYTHON)
# -----------------------------------------------------------------------------
def fmt_valuta_interi(valore):
    return f"€ {int(round(valore)):,}".replace(',', '.')

def fmt_valuta_decimali(valore):
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
# 4. INTERFACCIA CARICAMENTO NELLA SIDEBAR LATERALE
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
# BLOCCO 1: CONFIGURAZIONE FILTRI E TITOLI DINAMICI
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

        # Pulizia della stringa dello store per mostrare solo il nome dopo il codice numerico
        nome_store_pulito = selected_store.split(" - ")[-1] if " - " in str(selected_store) else selected_store

        if selected_area == "--- TOTALE STORE ---":
            dati_vista = df_filtrato_store.copy()
            titolo_vista = f"Visualizzazione: TOTALE STORE {nome_store_pulito}"
        elif selected_reparto == "--- TOTALE AREA ---":
            dati_vista = df_filtrato_area.copy()
            titolo_vista = f"Visualizzazione: TOTALE AREA {selected_area} ({nome_store_pulito})"
        else:
            dati_vista = df_filtrato_area[df_filtrato_area.iloc[:, 4] == selected_reparto]
            titolo_vista = f"Visualizzazione REPARTO: {selected_reparto} ({nome_store_pulito})"
    else:
        dati_vista = pd.DataFrame()
        st.error("Il file Mensilizzazione non ha colonne sufficienti per la mappatura gerarchica.")
# =============================================================================
# BLOCCO 2: ENGINE DI CALCOLO COMMERCIALE E CALCOLO STOCK DAYS
# =============================================================================
    if not dati_vista.empty:
        st.markdown(f"### 🎯 {titolo_vista}")
        
        # --- PARSER AD ALTA PRECISIONE PER FORMATI EUROPEI COMPLESSI ---
        def parse_to_numeric_series(dataframe, col_index):
            if len(dataframe.columns) > col_index:
                s = dataframe.iloc[:, col_index].astype(str).str.replace(r'\s+', '', regex=True)
                s = s.replace(['-', '--', 'nan', 'NaN', ''], '0')
                if s.str.count(r'\.').max() > 1:
                    s = s.str.replace('.', '', regex=False)
                elif s.str.contains(r'\.').any() and s.str.contains(',').any():
                    s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                elif s.str.contains(',').any() and not s.str.contains(r'\.').any():
                    s = s.str.replace(',', '.', regex=False)
                return pd.to_numeric(s, errors='coerce').fillna(0.0)
            return pd.Series(dtype=float, index=dataframe.index)

        # Estrazione colonne numeriche d'appoggio nel subset filtrato corrente
        df_calc = dati_vista.copy()
        df_calc['Sales_TY_Num'] = parse_to_numeric_series(df_calc, 5)   # Colonna 5: DA - Sales TT
        df_calc['Sales_PY_Num'] = parse_to_numeric_series(df_calc, 6)   # Colonna 6: DA - Sales TT PY Custom Cal
        df_calc['Margin_TY_Num'] = parse_to_numeric_series(df_calc, 11) # Colonna 11: DA - Front Margin
        df_calc['Margin_PY_Num'] = parse_to_numeric_series(df_calc, 12) # Colonna 12: DA - Front Margin PY Custom Cal
        df_calc['Stock_TY_Num'] = parse_to_numeric_series(df_calc, 13)  # Colonna 13: DA - Avg Stock
        df_calc['Stock_Days_TY'] = parse_to_numeric_series(df_calc, 14) # Colonna 14: DA - Stock Days
        df_calc['Stock_Days_PY'] = parse_to_numeric_series(df_calc, 15) # Colonna 15: DA - Stock Days PY Custom Cal
        df_calc['Shrink_TY_Num'] = parse_to_numeric_series(df_calc, 16)  # Colonna 16: DA - Shrinkage NNBP
        df_calc['Shrink_PY_Num'] = parse_to_numeric_series(df_calc, 17)  # Colonna 17: DA - Shrinkage NNBP PY Custom Cal

        # Aggregazioni volumetriche totali del periodo selezionato
        sales_tot = float(df_calc['Sales_TY_Num'].sum())
        sales_py_tot = float(df_calc['Sales_PY_Num'].sum())
        margin_tot = float(df_calc['Margin_TY_Num'].sum())
        margin_py_tot = float(df_calc['Margin_PY_Num'].sum())
        shrink_tot = float(df_calc['Shrink_TY_Num'].sum())
        shrink_py_tot = float(df_calc['Shrink_PY_Num'].sum())
        avg_stock_tot = float(df_calc['Stock_TY_Num'].sum())

        # Calcolo incidenze percentuali correnti (TY) e passate (PY)
        margin_on_sales = (margin_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        shrink_on_sales = (shrink_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        margin_on_sales_py = (margin_py_tot / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
        shrink_on_sales_py = (shrink_py_tot / sales_py_tot * 100) if sales_py_tot != 0 else 0.0

        # Variazioni classiche (Delta %)
        delta_sales_pct = ((sales_tot - sales_py_tot) / sales_py_tot * 100) if sales_py_tot != 0 else 0.0

        # Calcolo scostamenti in Punti Percentuali (Sottrazione diretta pp)
        delta_margin_pp = margin_on_sales - margin_on_sales_py
        delta_shrink_pp = shrink_on_sales - shrink_on_sales_py

        # --- ALGORITMO DI CALCOLO STOCK DAYS SU MATRICE GIORNALIERA AGGREGATA ---
        df_giornaliero = df_calc.groupby(df_calc.iloc[:, 0]).agg({
            'Stock_TY_Num': 'sum',
            'Sales_TY_Num': 'sum',
            'Sales_PY_Num': 'sum'
        }).reset_index()

        # Divisione analitica giornaliera: Stock del giorno / Vendite del giorno
        df_giornaliero['Days_TY'] = df_giornaliero.apply(
            lambda r: r['Stock_TY_Num'] / r['Sales_TY_Num'] if r['Sales_TY_Num'] > 0 else 0.0, axis=1
        )
        df_giornaliero['Days_PY'] = df_giornaliero.apply(
            lambda r: r['Stock_TY_Num'] / r['Sales_PY_Num'] if r['Sales_PY_Num'] > 0 else 0.0, axis=1
        )

        # Filtro di protezione: escludiamo dalla media le giornate senza attività
        giorni_attivi_ty = df_giornaliero[df_giornaliero['Days_TY'] > 0]
        giorni_attivi_py = df_giornaliero[df_giornaliero['Days_PY'] > 0]

        val_stock_days = float(giorni_attivi_ty['Days_TY'].mean()) if not giorni_attivi_ty.empty else 0.0
        val_stock_days_py = float(giorni_attivi_py['Days_PY'].mean()) if not giorni_attivi_py.empty else 0.0
        delta_stock_pct = ((val_stock_days - val_stock_days_py) / val_stock_days_py * 100) if val_stock_days_py != 0 else 0.0
# =============================================================================
# BLOCCO 3: FORMATTAZIONE EUROPEA E VISUALIZZAZIONE KPI CARDS
# =============================================================================
        # Funzioni di localizzazione e arrotondamento stringhe
        def fmt_valuta_interi(valore):
            return f"€ {int(round(valore)):,}".replace(',', '.')

        def fmt_valuta_decimali(valore):
            return f"€ {valore:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        def fmt_percentuale(valore):
            return f"{valore:.2f}%".replace('.', ',')

        def fmt_giorni(valore):
            return f"{valore:.1f} gg".replace('.', ',')

        # Rendering a quattro colonne in puro Python
        st.markdown("#### 📊 Indicatori Chiave di Performance")
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            st.metric(
                label="💰 Sales TT", 
                value=fmt_valuta_interi(sales_tot), 
                delta=f"{delta_sales_pct:+.2f}% vs PY",
                help=f"Fatturato anno precedente: {fmt_valuta_interi(sales_py_tot)}"
            )
        with m2:
            st.metric(
                label="📈 Front Margin %", 
                value=fmt_percentuale(margin_on_sales), 
                delta=f"{delta_margin_pp:+.2f} pp vs PY",
                help=f"Margine PY: {fmt_percentuale(margin_on_sales_py)} | Valore: {fmt_valuta_decimali(margin_tot)}"
            )
        with m3:
            st.metric(
                label="📦 Stock Days", 
                value=fmt_giorni(val_stock_days), 
                delta=f"{delta_stock_pct:+.2f}% vs PY", 
                delta_color="inverse",
                help=f"Giacenza PY: {fmt_giorni(val_stock_days_py)}"
            )
        with m4:
            st.metric(
                label="📉 Shrinkage (Sfrido)", 
                value=fmt_percentuale(shrink_on_sales), 
                delta=f"{delta_shrink_pp:+.2f} pp vs PY",
                delta_color="inverse",
                help=f"Sfrido PY: {fmt_percentuale(shrink_on_sales_py)} | Valore: {fmt_valuta_decimali(shrink_tot)}"
            )

        st.markdown("<br>#### 📦 Dettaglio Giacenze e Rotazioni", unsafe_allow_html=True)
        df_stock_kpi = pd.DataFrame({
            "Metrica": ["Giorni di Giacenza Correnti (Ponderati)", "Giorni di Giacenza Anno Prec. (PY)", "Stock Medio Corrente Complessivo"],
            "Valore": [fmt_giorni(val_stock_days), fmt_giorni(val_stock_days_py), fmt_valuta_interi(avg_stock_tot)]
        })
        st.dataframe(df_stock_kpi, use_container_width=True, hide_index=True)
    else:
        st.warning("Nessun record corrispondente rilevato all'interno dei filtri correnti.")

# =============================================================================
# SCHEDA 2: ANALISI PORTAFOGLIO FORZA VENDITE E CLIENTI
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

    def parse_sellout_col(series):
        s = series.astype(str).str.replace(r'\s+', '', regex=True)
        s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        return pd.to_numeric(s, errors='coerce').fillna(0.0)

    sellout_sales_tot = float(parse_sellout_col(df_sel_filtrato["Sales TT"]).sum()) if "Sales TT" in df_sel_filtrato.columns else 0.0
    sellout_margin_tot = float(parse_sellout_col(df_sel_filtrato["Front Margin"]).sum()) if "Front Margin" in df_sel_filtrato.columns else 0.0
    sellout_visits_tot = float(parse_sellout_col(df_sel_filtrato["# Visit"]).sum()) if "# Visit" in df_sel_filtrato.columns else 0.0
    sellout_margin_pct = (sellout_margin_tot / sellout_sales_tot * 100) if sellout_sales_tot != 0 else 0.0

    st.markdown("##### 📊 Indicatori Chiave del Portafoglio Selezionato")
    ms1, ms2, ms3 = st.columns(3)
    with ms1:
        st.metric(label="💼 Fatturato Portafoglio (Sellout)", value=fmt_valuta_interi(sellout_sales_tot))
    with ms2:
        st.metric(label="🎯 Front Margin % Realizzato", value=fmt_percentuale(sellout_margin_pct), help=f"Valore assoluto: {fmt_valuta_decimali(sellout_margin_tot)}")
    with ms3:
        st.metric(label="👣 Volume Totale Visite", value=f"{int(sellout_visits_tot):,}".replace(',', '.'))

    st.markdown("<br>### 📋 Elenco Analitico Clienti (Ordinati per Fatturato Decrescente)")
    raggruppamento_cols = [c for c in ["Customer", "Customer Category", "Venditore", "MPRO Club"] if c in df_sel_filtrato.columns]
    
    if raggruppamento_cols:
        agg_dict = {"Sales TT": "sum"}
        if "Front Margin" in df_sel_filtrato.columns: agg_dict["Front Margin"] = "sum"
        if "# Visit" in df_sel_filtrato.columns: agg_dict["# Visit"] = "sum"
        
        df_customer_pivoted = df_sel_filtrato.groupby(raggruppamento_cols).agg(agg_dict).reset_index().sort_values(by="Sales TT", ascending=False)
        
        df_customer_pivoted["Sales TT"] = df_customer_pivoted["Sales TT"].map(fmt_valuta_interi)
        if "Front Margin" in df_customer_pivoted.columns:
            df_customer_pivoted["Front Margin"] = df_customer_pivoted["Front Margin"].map(fmt_valuta_decimali)
        if "# Visit" in df_customer_pivoted.columns:
            df_customer_pivoted["# Visit"] = df_customer_pivoted["# Visit"].map('{:,.0f}'.format)

        st.dataframe(df_customer_pivoted, use_container_width=True, hide_index=True)
