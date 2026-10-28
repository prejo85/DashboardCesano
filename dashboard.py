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
# BLOCCO 2: ENGINE DI CALCOLO COMMERCIALE E ROTAZIONE MEDIA SUL PERIODO
# =============================================================================
    if not dati_vista.empty:
        st.markdown(f"### 🎯 {titolo_vista}")
        
        # --- PARSER AD ALTA PRECISIONE PER FORMATI EUROPEI E INTERI CON PUNTI ---
        def parse_to_numeric_series(dataframe, col_index, is_stock=False):
            if len(dataframe.columns) > col_index:
                s = dataframe.iloc[:, col_index].astype(str).str.replace(r'\s+', '', regex=True)
                s = s.replace(['-', '--', 'nan', 'NaN', ''], '0')
                
                if is_stock:
                    # Per la colonna Stock (es. 149.108 o 1.004.906) rimuoviamo tutti i punti prima della conversione
                    s = s.str.replace('.', '', regex=False)
                else:
                    # Per le altre colonne commerciali (es. 7.772,75)
                    if s.str.count(r'\.').max() > 1:
                        s = s.str.replace('.', '', regex=False)
                    elif s.str.contains(r'\.').any() and s.str.contains(',').any():
                        s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    elif s.str.contains(',').any() and not s.str.contains(r'\.').any():
                        s = s.str.replace(',', '.', regex=False)
                        
                return pd.to_numeric(s, errors='coerce').fillna(0.0)
            return pd.Series(dtype=float, index=dataframe.index)

        # Creazione colonne numeriche d'appoggio nel subset filtrato corrente
        df_calc = dati_vista.copy()
        df_calc['Sales_TY_Num'] = parse_to_numeric_series(df_calc, 5)   # Colonna 5: DA - Sales TT
        df_calc['Sales_PY_Num'] = parse_to_numeric_series(df_calc, 6)   # Colonna 6: DA - Sales TT PY Custom Cal
        df_calc['Margin_TY_Num'] = parse_to_numeric_series(df_calc, 11) # Colonna 11: DA - Front Margin
        df_calc['Margin_PY_Num'] = parse_to_numeric_series(df_calc, 12) # Colonna 12: DA - Front Margin PY Custom Cal
        df_calc['Stock_TY_Num'] = parse_to_numeric_series(df_calc, 13, is_stock=True)  # Colonna 13: DA - Avg Stock (Forzato Intero)
        df_calc['Shrink_TY_Num'] = parse_to_numeric_series(df_calc, 16) # Colonna 16: DA - Shrinkage NNBP
        df_calc['Shrink_PY_Num'] = parse_to_numeric_series(df_calc, 17) # Colonna 17: DA - Shrinkage NNBP PY Custom Cal

        # Aggregazioni volumetriche totali del periodo selezionato
        sales_tot = float(df_calc['Sales_TY_Num'].sum())
        sales_py_tot = float(df_calc['Sales_PY_Num'].sum())
        margin_tot = float(df_calc['Margin_TY_Num'].sum())
        margin_py_tot = float(df_calc['Margin_PY_Num'].sum())
        shrink_tot = float(df_calc['Shrink_TY_Num'].sum())
        shrink_py_tot = float(df_calc['Shrink_PY_Num'].sum())
        avg_stock_tot = float(df_calc['Stock_TY_Num'].sum())

        # Calcolo incidenze percentuali progressive
        margin_on_sales = (margin_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        shrink_on_sales = (shrink_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        margin_on_sales_py = (margin_py_tot / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
        shrink_on_sales_py = (shrink_py_tot / sales_py_tot * 100) if sales_py_tot != 0 else 0.0

        # Delta classici e scostamenti in punti percentuali
        delta_sales_pct = ((sales_tot - sales_py_tot) / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
        delta_margin_pp = margin_on_sales - margin_on_sales_py
        delta_shrink_pp = shrink_on_sales - shrink_on_sales_py

        # --- ENGINE DI CALCOLO GENERALE DEGLI STOCK DAYS SU TUTTI I GIORNI DISPONIBILI ---
        # Raggruppiamo i valori sommandoli giorno per giorno (Colonna 0: Data)
        df_giornaliero = df_calc.groupby(df_calc.iloc[:, 0]).agg({
            'Stock_TY_Num': 'sum',
            'Sales_TY_Num': 'sum',
            'Sales_PY_Num': 'sum'
        }).reset_index()

        # Calcolo del rapporto Stock / Sales per ogni singola giornata della selezione
        df_giornaliero['Days_TY'] = df_giornaliero.apply(
            lambda r: r['Stock_TY_Num'] / r['Sales_TY_Num'] if r['Sales_TY_Num'] > 0 else 0.0, axis=1
        )
        df_giornaliero['Days_PY'] = df_giornaliero.apply(
            lambda r: r['Stock_TY_Num'] / r['Sales_PY_Num'] if r['Sales_PY_Num'] > 0 else 0.0, axis=1
        )

        # Consideriamo per la media solo le giornate con vendite attive
        giorni_validi_ty = df_giornaliero[df_giornaliero['Days_TY'] > 0]
        giorni_validi_py = df_giornaliero[df_giornaliero['Days_PY'] > 0]

        # Calcolo finale delle medie del periodo selezionato
        val_stock_days = float(giorni_validi_ty['Days_TY'].mean()) if not giorni_validi_ty.empty else 0.0
        val_stock_days_py = float(giorni_validi_py['Days_PY'].mean()) if not giorni_validi_py.empty else 0.0
        delta_stock_pct = ((val_stock_days - val_stock_days_py) / val_stock_days_py * 100) if val_stock_days_py != 0 else 0.0

        # --- ENGINE DI CALCOLO INTERNO: AVG STOCK DELL'ULTIMO GIORNO CRONOLOGICO (PROTETTO) ---
        val_avg_stock_ultimo_giorno = 0.0
        try:
            # Usiamo format='mixed' per digerire automaticamente anni a 2 o 4 cifre (%y o %Y)
            df_calc['Date_Parsed'] = pd.to_datetime(df_calc.iloc[:, 0].astype(str).str.strip(), format='mixed', errors='coerce')
            df_date_valide = df_calc[df_calc['Date_Parsed'].notna()]
            
            if not df_date_valide.empty:
                # Isola la data cronologicamente più recente della selezione corrente
                ultima_data_assoluta = df_date_valide['Date_Parsed'].max()
                df_ultimo_giorno_stock = df_date_valide[df_date_valide['Date_Parsed'] == ultima_data_assoluta]
                
                # Somma i valori delle giacenze per i reparti inclusi nel filtro attivo
                val_avg_stock_ultimo_giorno = float(df_ultimo_giorno_stock['Stock_TY_Num'].sum())
        except:
            pass

        # =============================================================================
        # BLOCCO 3 AGGIORNATO: INTEGRAZIONE DINAMICA CROSS-REPORT (PRECISION ENGINE)
        # =============================================================================
        st.markdown("<br>---", unsafe_allow_html=True)
        st.subheader("🔗 Indicatori di Performance Cross-Report (BMPL & Indispensabili)")

        import re

        # 1. Estrazione dinamica e pulita dei codici reparto unici filtrati (es. {'110', '190'}) tramite Regex
        reparti_mensilizzazione = dati_vista.iloc[:, 4].dropna().astype(str).str.strip()
        codici_target = set()
        for r in reparti_mensilizzazione:
            match = re.search(r'\d+', r)
            if match:
                codici_target.add(match.group())

        # Funzione di utilità locale per generare i mini blocchi KPI nativi
        def render_mini_kpi(label, current_val, py_val, is_currency=True):
            delta_pct = ((current_val - py_val) / py_val * 100) if py_val != 0 else 0.0
            val_str = fmt_valuta_interi(current_val) if is_currency else f"{int(round(current_val)):,}".replace(',', '.')
            py_str = fmt_valuta_interi(py_val) if is_currency else f"{int(round(py_val)):,}".replace(',', '.')
            
            st.metric(
                label=label,
                value=val_str,
                delta=f"{delta_pct:+.2f}% vs PY",
                help=f"Valore Anno Precedente (PY): {py_str}"
            )

        col_c1, col_c2 = st.columns(2)
        
        # --- PANNELLO 1: REPORT BMPL REPARTI (ALLINEAMENTO STRUTTURALE ALL'ECCEL) ---
        with col_c1:
            st.markdown("#### 📈 Sintesi Report BMPL Reparti")
            col_rep_bmpl = [c for c in df_rep.columns if 'department' in c.lower() or 'reparto' in c.lower()]
            
            if col_rep_bmpl and not dati_vista.empty and len(codici_target) > 0:
                col_bmpl_nome = col_rep_bmpl[0]
                
                # Creiamo una copia per ripulire i codici reparto estratti da BMPL usando lo stesso motore Regex
                df_rep_clean = df_rep.copy()
                df_rep_clean['Codice_Reparto_BMPL'] = df_rep_clean[col_bmpl_nome].astype(str).apply(
                    lambda x: re.search(r'\d+', x).group() if re.search(r'\d+', x) else ''
                )
                
                # Filtriamo il file BMPL legandolo unicamente alle chiavi attive del filtro iniziale
                match_bmpl = df_rep_clean[df_rep_clean['Codice_Reparto_BMPL'].isin(codici_target)]
                
                if not match_bmpl.empty:
                    def parse_bmpl_clean(dataframe, col_name):
                        if col_name in dataframe.columns:
                            s = dataframe[col_name].astype(str).str.replace(r'\s+', '', regex=True)
                            s = s.replace(['-', '--', 'nan', 'NaN', ''], '0')
                            s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                            return pd.to_numeric(s, errors='coerce').fillna(0.0)
                        return pd.Series(0.0, index=dataframe.index)

                    # Calcolo aggregati dinamici sulle sole righe corrispondenti
                    bmpl_sales = float(parse_bmpl_clean(match_bmpl, 'Sales TT').sum())
                    bmpl_sales_py = float(parse_bmpl_clean(match_bmpl, 'Sales TT PY Custom Cal').sum())
                    bmpl_margin = float(parse_bmpl_clean(match_bmpl, 'Front Margin').sum())
                    bmpl_margin_py = float(parse_bmpl_clean(match_bmpl, 'Front Margin PY Custom Cal').sum())
                    bmpl_colli = float(parse_bmpl_clean(match_bmpl, '# Colli').sum())
                    bmpl_colli_py = float(parse_bmpl_clean(match_bmpl, '# Colli PY Custom Cal').sum())
                    
                    margin_pct_ty = (bmpl_margin / bmpl_sales * 100) if bmpl_sales != 0 else 0.0
                    margin_pct_py = (bmpl_margin_py / bmpl_sales_py * 100) if bmpl_sales_py != 0 else 0.0
                    delta_margin_bmpl_pp = margin_pct_ty - margin_pct_py
                    
                    delta_sales_bmpl = ((bmpl_sales - bmpl_sales_py) / bmpl_sales_py * 100) if bmpl_sales_py != 0 else 0.0
                    delta_colli_bmpl = ((bmpl_colli - bmpl_colli_py) / bmpl_colli_py * 100) if bmpl_colli_py != 0 else 0.0

                    # Renderizzazione delle tre card simmetriche per il file BMPL
                    sub_col1, sub_col2, sub_col3 = st.columns(3)
                    with sub_col1: 
                        st.metric(label="Sales TT (BMPL)", value=fmt_valuta_interi(bmpl_sales), delta=f"{delta_sales_bmpl:+.2f}% vs PY")
                    with sub_col2: 
                        st.metric(label="Front Margin % (BMPL)", value=fmt_percentuale(margin_pct_ty), delta=f"{delta_margin_bmpl_pp:+.2f} pp vs PY")
                    with sub_col3: 
                        st.metric(label="Volume Colli (BMPL)", value=f"{int(round(bmpl_colli)):,}".replace(',', '.'), delta=f"{delta_colli_bmpl:+.2f}% vs PY")
                else:
                    st.caption("⚠️ Nessun reparto del file BMPL corrisponde ai filtri attivi della Mensilizzazione.")
            else:
                st.caption("🔍 Seleziona uno Store o un'Area per visualizzare i dati storici del report BMPL.")

        # --- PANNELLO 2: REPORT ARTICOLI INDISPENSABILI ---
        with col_c2:
            st.markdown("#### 📌 Sintesi Articoli Indispensabili nel Mix")
            col_rep_ind = [c for c in df_ind.columns if 'department' in c.lower() or 'reparto' in c.lower()]
            
            if col_rep_ind and len(codici_target) > 0:
                col_ind_nome = col_rep_ind[0]
                df_ind_clean = df_ind.copy()
                df_ind_clean['Codice_Reparto_IND'] = df_ind_clean[col_ind_nome].astype(str).apply(
                    lambda x: re.search(r'\d+', x).group() if re.search(r'\d+', x) else ''
                )
                match_indisp = df_ind_clean[df_ind_clean['Codice_Reparto_IND'].isin(codici_target)]
                
                if not match_indisp.empty:
                    ind_sales = float(parse_to_numeric_series(match_indisp, df_ind.columns.get_loc('DA - Sales TT') if 'DA - Sales TT' in df_ind.columns else 0).sum())
                    ind_sales_py = float(parse_to_numeric_series(match_indisp, df_ind.columns.get_loc('DA - Sales TT PY Custom Cal') if 'DA - Sales TT PY Custom Cal' in df_ind.columns else 0).sum())
                    ind_colli = float(parse_to_numeric_series(match_indisp, df_ind.columns.get_loc('DA - #Colli') if 'DA - #Colli' in df_ind.columns else 0).sum())
                    ind_colli_py = float(parse_to_numeric_series(match_indisp, df_ind.columns.get_loc('DA - #Colli PY Custom Cal') if 'DA - #Colli PY Custom Cal' in df_ind.columns else 0).sum())
                    n_articoli = match_indisp[df_ind.columns[0]].nunique()
                    
                    sub_ind1, sub_ind2 = st.columns(2)
                    with sub_ind1: render_mini_kpi("Sales (Indispensabili)", ind_sales, ind_sales_py)
                    with sub_ind2: render_mini_kpi("Volume Colli (Indisp.)", ind_colli, ind_colli_py, is_currency=False)
                    st.info(f"🎯 **{n_articoli}** Articoli Indispensabili filtrati ed elaborati nel mix corrente.")
                else:
                    st.caption("⚠️ Nessun articolo indispensabile trovato per questa selezione.")
            else:
                st.caption("🔍 Seleziona un'area o un reparto per agganciare gli articoli indispensabili.")
 
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
