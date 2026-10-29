import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# -----------------------------------------------------------------------------
# 1. CONFIGURAZIONE DELLA PAGINA E TITOLO PRINCIPALE
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Dashboard Commerciale Avanzata", layout="wide", page_icon="📊")

st.title("📊 Dashboard Commerciale Integrata")
st.markdown("### Analisi Multilivello: Store, Aree, Reparti e Segmentazione Clienti")
# -----------------------------------------------------------------------------
# 2. FUNZIONI DI FORMATTAZIONE VALUTA E LOGICA DI PARSING CONTABILE ITALIANO
# -----------------------------------------------------------------------------
def fmt_valuta_interi(valore):
    return f"€ {int(round(valore)):,}".replace(',', '.')

def fmt_valuta_decimali(valore):
    return f"€ {valore:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def fmt_percentuale(valore):
    return f"{valore:.2f}%".replace('.', ',')

def fmt_giorni(valore):
    return f"{valore:.1f} gg".replace('.', ',')

def parse_universal_numeric(series_or_val):
    """
    Gestisce correttamente lo standard contabile italiano: punto per le migliaia e virgola per i decimali.
    Evita la decimazione delle cifre tonde (es. 5.000 interpretato come 5.0).
    """
    s = series_or_val.astype(str).str.replace(r'\s+', '', regex=True)
    s = s.replace(['-', '--', 'nan', 'NaN', 'None', ''], '0')
    
    def clean_string(x):
        if ',' in x and '.' in x:
            return x.replace('.', '').replace(',', '.')
        elif ',' in x:
            return x.replace(',', '.')
        elif '.' in x:
            return x.replace('.', '')
        return x

    s = s.apply(clean_string)
    return pd.to_numeric(s, errors='coerce').fillna(0.0)
# -----------------------------------------------------------------------------
# 3. ENGINE CENTRALIZZATO DI PULIZIA E PARSING DEI REPORT (RIGA 0)
# -----------------------------------------------------------------------------
def load_and_clean_data(file_reparti, file_ctg, file_sellout, file_indispensabili, file_mensile):
    def clean_df(file_path, is_sellout=False):
        if is_sellout:
            try:
                # Cerca dinamicamente dove inizia la riga di intestazione reale del file Sellout
                preview = pd.read_csv(file_path, sep=";", nrows=15, header=None)
                skip_rows = 0
                for idx, row in preview.iterrows():
                    row_str = str(row.values)
                    if "Store" in row_str and "Sales Department" in row_str:
                        skip_rows = idx
                        break
                file_path.seek(0)
                df = pd.read_csv(file_path, sep=";", skiprows=skip_rows, skip_blank_lines=True)
            except:
                file_path.seek(0)
                df = pd.read_csv(file_path, sep=";", skiprows=5, skip_blank_lines=True)
        else:
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
    df_sel = clean_df(file_sellout, is_sellout=True)
    df_ind = clean_df(file_indispensabili)
    df_men = clean_df(file_mensile)
    return df_rep, df_ctg, df_sel, df_ind, df_men
# -----------------------------------------------------------------------------
# 4. INTERFACCIA UNICA DI CARICAMENTO NELLA SIDEBAR LATERALE
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

# Inizializzazione controllata dei dataframe
df_rep, df_ctg, df_sel, df_ind, df_men = load_and_clean_data(u_rep, u_ctg, u_sel, u_ind, u_men)

# -----------------------------------------------------------------------------
# 5. FILTRI GERARCHICI IN ALTO CON LOGICA DI RESET
# -----------------------------------------------------------------------------
st.markdown("---")
col_f1, col_f2, col_f3, col_btn = st.columns([3, 3, 3, 1])

if "reset_clicked" not in st.session_state:
    st.session_state.reset_clicked = False

with col_btn:
    st.markdown("<div style='padding-top: 24px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.reset_clicked = True
        st.rerun()

if len(df_men.columns) >= 5:
    df_men_clean = df_men.copy()
    df_men_clean.iloc[:, 1] = df_men_clean.iloc[:, 1].astype(str).str.strip() 
    df_men_clean.iloc[:, 3] = df_men_clean.iloc[:, 3].astype(str).str.strip() 
    df_men_clean.iloc[:, 4] = df_men_clean.iloc[:, 4].astype(str).str.strip() 
    
    lista_store = sorted([x for x in df_men_clean.iloc[:, 1].unique() if x not in ['nan', 'None', '']])
    
    with col_f1:
        selected_store = st.selectbox("Seleziona Store:", lista_store, index=0 if st.session_state.reset_clicked else 0)
    
    df_filtrato_store = df_men_clean[df_men_clean.iloc[:, 1] == selected_store]
    lista_aree = ["--- TOTALE STORE ---"] + sorted([x for x in df_filtrato_store.iloc[:, 3].unique() if x not in ['nan', 'None', '']])
    
    with col_f2:
        selected_area = st.selectbox("Seleziona Area di Vendita:", lista_aree, index=0 if st.session_state.reset_clicked else 0)
    
    if selected_area != "--- TOTALE STORE ---":
        df_filtrato_area = df_filtrato_store[df_filtrato_store.iloc[:, 3] == selected_area]
        lista_reparti = ["--- TOTALE AREA ---"] + sorted([x for x in df_filtrato_area.iloc[:, 4].unique() if x not in ['nan', 'None', '']])
    else:
        df_filtrato_area = df_filtrato_store.copy()
        lista_reparti = ["--- DETTAGLIO RICHIESTO ---"]
        
    with col_f3:
        selected_reparto = st.selectbox("Seleziona Reparto:", lista_reparti, index=0 if st.session_state.reset_clicked else 0)

    st.session_state.reset_clicked = False
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

tab1, tab2 = st.tabs(["🏬 Vista Store e Performance Reparti", "👥 Analisi Profilazione Clienti (Sellout)"])
# =============================================================================
# TAB 1: VISUALIZZAZIONE DELLE VISTE GENERALI E PERFORMANCE INTEGRATE (Parte A)
# =============================================================================
with tab1:
    if not dati_vista.empty:
        st.markdown(f"### 🎯 {titolo_vista}")

        df_calc = dati_vista.copy()
        df_calc['Sales_TY_Num'] = parse_universal_numeric(df_calc.iloc[:, 5])   
        df_calc['Sales_PY_Num'] = parse_universal_numeric(df_calc.iloc[:, 6])   
        df_calc['Margin_TY_Num'] = parse_universal_numeric(df_calc.iloc[:, 11]) 
        df_calc['Margin_PY_Num'] = parse_universal_numeric(df_calc.iloc[:, 12]) 
        df_calc['Stock_TY_Num'] = parse_universal_numeric(df_calc.iloc[:, 13])  
        df_calc['Shrink_TY_Num'] = parse_universal_numeric(df_calc.iloc[:, 16]) 
        df_calc['Shrink_PY_Num'] = parse_universal_numeric(df_calc.iloc[:, 17]) 

        sales_tot = float(df_calc['Sales_TY_Num'].sum())
        sales_py_tot = float(df_calc['Sales_PY_Num'].sum())
        margin_tot = float(df_calc['Margin_TY_Num'].sum())
        margin_py_tot = float(df_calc['Margin_PY_Num'].sum())
        shrink_tot = float(df_calc['Shrink_TY_Num'].sum())
        shrink_py_tot = float(df_calc['Shrink_PY_Num'].sum())

        margin_on_sales = (margin_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        shrink_on_sales = (shrink_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        margin_on_sales_py = (margin_py_tot / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
        shrink_on_sales_py = (shrink_py_tot / sales_py_tot * 100) if sales_py_tot != 0 else 0.0

        delta_sales_pct = ((sales_tot - sales_py_tot) / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
        delta_margin_pp = margin_on_sales - margin_on_sales_py
        delta_shrink_pp = shrink_on_sales - shrink_on_sales_py

        df_giornaliero = df_calc.groupby(df_calc.iloc[:, 0]).agg({
            'Stock_TY_Num': 'sum',
            'Sales_TY_Num': 'sum',
            'Sales_PY_Num': 'sum'
        }).reset_index()

        df_giornaliero['Days_TY'] = df_giornaliero.apply(lambda r: r['Stock_TY_Num'] / r['Sales_TY_Num'] if r['Sales_TY_Num'] > 0 else 0.0, axis=1)
        df_giornaliero['Days_PY'] = df_giornaliero.apply(lambda r: r['Stock_TY_Num'] / r['Sales_PY_Num'] if r['Sales_PY_Num'] > 0 else 0.0, axis=1)

        giorni_validi_ty = df_giornaliero[df_giornaliero['Days_TY'] > 0]
        giorni_validi_py = df_giornaliero[df_giornaliero['Days_PY'] > 0]

        val_stock_days = float(giorni_validi_ty['Days_TY'].mean()) if not giorni_validi_ty.empty else 0.0
        val_stock_days_py = float(giorni_validi_py['Days_PY'].mean()) if not giorni_validi_py.empty else 0.0
        delta_stock_pct = ((val_stock_days - val_stock_days_py) / val_stock_days_py * 100) if val_stock_days_py != 0 else 0.0

        val_avg_stock_ultimo_giorno = 0.0
        try:
            df_calc['Date_Parsed'] = pd.to_datetime(df_calc.iloc[:, 0].astype(str).str.strip(), format='mixed', errors='coerce')
            df_date_valide = df_calc[df_calc['Date_Parsed'].notna()]
            if not df_date_valide.empty:
                ultima_data_assoluta = df_date_valide['Date_Parsed'].max()
                val_avg_stock_ultimo_giorno = float(df_date_valide[df_date_valide['Date_Parsed'] == ultima_data_assoluta]['Stock_TY_Num'].sum())
        except:
            pass

        reparti_mensilizzazione = dati_vista.iloc[:, 4].dropna().astype(str).str.strip()
        codici_target = set()
        for r in reparti_mensilizzazione:
            match = re.search(r'\d+', r)
            if match: codici_target.add(match.group())

        # Render delle metriche Streamlit in pagina
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1: st.metric(label="💰 Sales TT", value=fmt_valuta_interi(sales_tot), delta=f"{delta_sales_pct:+.2f}% vs PY")
        with m2: st.metric(label="📈 Front Margin %", value=fmt_percentuale(margin_on_sales), delta=f"{delta_margin_pp:+.2f} pp vs PY")
        with m3: st.metric(label="📦 Stock Days", value=fmt_giorni(val_stock_days), delta=f"{delta_stock_pct:+.2f}% vs PY", delta_color="inverse")
        with m4: st.metric(label="🏬 Avg Stock Last Day", value=fmt_valuta_interi(val_avg_stock_ultimo_giorno))
        with m5: st.metric(label="📉 Shrinkage (Sfrido)", value=fmt_percentuale(shrink_on_sales), delta=f"{delta_shrink_pp:+.2f} pp vs PY", delta_color="inverse")
        # -----------------------------------------------------------------------------
        # TAB 1: VISUALIZZAZIONE (Parte B - Cross Performance)
        # -----------------------------------------------------------------------------
        st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
        st.subheader("🔗 Indicatori di Performance Cross-Report (BMPL & Indispensabili)")
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.markdown("#### 📈 Sintesi Report BMPL Reparti")
            if not df_rep.empty:
                df_rep_pure = df_rep[df_rep.iloc[:, 0].astype(str).str.contains('FOOD', case=False, na=False)].copy()
                match_bmpl = df_rep_pure.copy()
                if selected_area != "--- TOTALE STORE ---" or (selected_reparto != "--- DETTAGLIO RICHIESTO ---" and selected_reparto != "--- TOTALE AREA ---"):
                    col_bmpl_rep = [c for c in df_rep_pure.columns if 'department' in c.lower() or 'reparto' in c.lower()]
                    if col_bmpl_rep and len(codici_target) > 0:
                        df_rep_pure['Codice_Reparto_BMPL'] = df_rep_pure[col_bmpl_rep[0]].astype(str).apply(
                            lambda x: re.search(r'\d+', str(x)).group() if re.search(r'\d+', str(x)) else ''
                        )
                        match_bmpl = df_rep_pure[df_rep_pure['Codice_Reparto_BMPL'].isin(codici_target)]

                if not match_bmpl.empty:
                    bmpl_sales = float(parse_universal_numeric(match_bmpl['Sales TT']).sum())
                    bmpl_sales_py = float(parse_universal_numeric(match_bmpl['Sales TT PY Custom Cal']).sum())
                    bmpl_margin = float(parse_universal_numeric(match_bmpl['Front Margin']).sum())
                    bmpl_margin_py = float(parse_universal_numeric(match_bmpl['Front Margin PY Custom Cal']).sum())
                    bmpl_colli = float(parse_universal_numeric(match_bmpl['# Colli']).sum())
                    bmpl_colli_py = float(parse_universal_numeric(match_bmpl['# Colli PY Custom Cal']).sum())
                    
                    margin_pct_ty = (bmpl_margin / bmpl_sales * 100) if bmpl_sales != 0 else 0.0
                    margin_pct_py = (bmpl_margin_py / bmpl_sales_py * 100) if bmpl_sales_py != 0 else 0.0
                    delta_margin_bmpl_pp = margin_pct_ty - margin_pct_py
                    delta_sales_bmpl = ((bmpl_sales - bmpl_sales_py) / bmpl_sales_py * 100) if bmpl_sales_py != 0 else 0.0
                    delta_colli_bmpl = ((bmpl_colli - bmpl_colli_py) / bmpl_colli_py * 100) if bmpl_colli_py != 0 else 0.0

                    sub_col1, sub_col2, sub_col3 = st.columns(3)
                    with sub_col1: st.metric(label="Sales TT (BMPL)", value=fmt_valuta_interi(bmpl_sales), delta=f"{delta_sales_bmpl:+.2f}% vs PY" if bmpl_sales_py != 0 else None)
                    with sub_col2: st.metric(label="Front Margin % (BMPL)", value=fmt_percentuale(margin_pct_ty), delta=f"{delta_margin_bmpl_pp:+.2f} pp vs PY")
                    with sub_col3: st.metric(label="Volume Colli (BMPL)", value=f"{int(round(bmpl_colli)):,}".replace(',', '.'), delta=f"{delta_colli_bmpl:+.2f}% vs PY" if bmpl_colli_py != 0 else None)

        with col_c2:
            st.markdown("#### 📌 Sintesi Articoli Indispensabili nel Mix")
            if not df_ind.empty:
                col_rep_ind = [c for c in df_ind.columns if 'department' in c.lower() or 'reparto' in c.lower()]
                match_indisp = pd.DataFrame()
                if col_rep_ind and len(codici_target) > 0:
                    df_ind['Codice_Reparto_IND'] = df_ind[col_rep_ind[0]].apply(lambda x: re.search(r'\d+', str(x)).group() if re.search(r'\d+', str(x)) else '')
                    match_indisp = df_ind[df_ind['Codice_Reparto_IND'].isin(codici_target)].copy()
                
                if not match_indisp.empty:
                    ind_sales = float(parse_universal_numeric(match_indisp.iloc[:, 5]).sum())       
                    ind_sales_py = float(parse_universal_numeric(match_indisp.iloc[:, 6]).sum())    
                    ind_colli = float(parse_universal_numeric(match_indisp.iloc[:, 7]).sum())       
                    ind_colli_py = float(parse_universal_numeric(match_indisp.iloc[:, 8]).sum())    
                    ind_shrink = float(parse_universal_numeric(match_indisp.iloc[:, 11]).sum())     

                    delta_sales_ind = ((ind_sales - ind_sales_py) / ind_sales_py * 100) if ind_sales_py != 0 else 0.0
                    delta_colli_ind = ((ind_colli - ind_colli_py) / ind_colli_py * 100) if ind_colli_py != 0 else 0.0

                    sub_ind1, sub_ind2, sub_ind3 = st.columns(3)
                    with sub_ind1: st.metric(label="Sales (Indispensabili)", value=fmt_valuta_interi(ind_sales), delta=f"{delta_sales_ind:+.2f}% vs PY")
                    with sub_ind2: st.metric(label="Volume Colli (Indisp.)", value=f"{int(round(ind_colli)):,}".replace(',', '.'), delta=f"{delta_colli_ind:+.2f}% vs PY")
                    with sub_ind3: st.metric(label="📉 Shrinkage (Indisp.)", value=fmt_valuta_interi(ind_shrink))
        # -----------------------------------------------------------------------------
        # TAB 1: VISUALIZZAZIONE (Parte C - Analisi Grafica Report CTG)
        # -----------------------------------------------------------------------------
        st.markdown("<br>---", unsafe_allow_html=True)
        st.subheader("📊 Analisi e Performance Mix Categorie e Canali (Report CTG)")
        if not df_ctg.empty:
            df_ctg_clean = df_ctg.copy()
            df_ctg_clean['Codice_Reparto_CTG'] = df_ctg_clean.iloc[:, 1].astype(str).apply(
                lambda x: re.search(r'\d+', str(x)).group() if re.search(r'\d+', str(x)) else ''
            )
            match_ctg = df_ctg_clean[df_ctg_clean['Codice_Reparto_CTG'].isin(codici_target)].copy() if len(codici_target) > 0 else df_ctg_clean.copy()
            
            if not match_ctg.empty:
                match_ctg['Sales_TY'] = parse_universal_numeric(match_ctg.iloc[:, 7])
                match_ctg['Visits_TY'] = parse_universal_numeric(match_ctg.iloc[:, 11])
                match_ctg['CTG_Label'] = match_ctg['CTG'].astype(str).str.strip().str.replace("'", "", regex=False).replace(['nan', 'None', ''], '-')
                match_ctg['Channel_Label'] = match_ctg['Channel Detail'].astype(str).str.strip()

                df_ctg_grouped = match_ctg.groupby('CTG_Label').agg({'Sales_TY': 'sum', 'Visits_TY': 'sum'}).reset_index()
                df_ctg_grouped = df_ctg_grouped[df_ctg_grouped['Sales_TY'] > 0].sort_values(by='Sales_TY', ascending=True)

                if not df_ctg_grouped.empty:
                    g1, g2 = st.columns(2)
                    with g1:
                        st.markdown("#### 💰 Volume di Fatturato per Categoria (Sales TT)")
                        fig_sales = px.bar(
                            df_ctg_grouped, x='Sales_TY', y='CTG_Label', orientation='h',
                            labels={'Sales_TY': 'Fatturato Corrente (€)', 'CTG_Label': 'Categoria CTG'},
                            template='plotly_dark', color='Sales_TY', color_continuous_scale='Blues'
                        )
                        fig_sales.update_layout(showlegend=False, coloraxis_showscale=False, height=400, margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig_sales, use_container_width=True)
                    with g2:
                        st.markdown("#### 👥 Frequenza e Mix dei Volumi delle Visite")
                        fig_visits = px.pie(df_ctg_grouped, values='Visits_TY', names='CTG_Label', template='plotly_dark', hole=0.4)
                        fig_visits.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig_visits, use_container_width=True)
                else:
                    st.caption("⚠️ I record del file CTG per la selezione corrente contengono volumi pari a zero o vuoti.")
            else:
                st.caption("⚠️ Nessun dato nel file CTG corrisponde ai reparti attivi nei filtri gerarchici.")
        else:
            st.info("Carica il file CTG nella barra laterale sinistra per sbloccare l'analisi grafica merceologica.")
# =============================================================================
# SCHEDA 2: ANALISI PORTAFOGLIO FORZA VENDITE E CLIENTI (Parte A - Filtri e Metrics)
# =============================================================================
with tab2:
    st.header("👥 Analisi Profilazione e Portafoglio Clienti (Sellout)")
    st.markdown("Esplorazione analitica delle performance per singolo Cliente basata sul report *Free Analysis Sellout*.")

    if not df_sel.empty:
        col_s1, col_f_cust, col_s2 = st.columns(3)
        with col_s1:
            options_gestione = sorted(df_sel["Tipo Gestione"].dropna().unique()) if "Tipo Gestione" in df_sel.columns else []
            tipo_gestione = st.multiselect("Filtra per Tipo Gestione:", options=options_gestione)
        with col_f_cust:
            ricerca_cliente = st.text_input("🔍 Cerca Ragione Sociale o Codice Cliente Contabile:")
        with col_s2:
            options_club = sorted(df_sel["MPRO Club"].dropna().unique()) if "MPRO Club" in df_sel.columns else []
            mpro_club = st.multiselect("Filtra per Stato MPRO Club:", options=options_club)

        df_sel_filtrato = df_sel.copy()
        if tipo_gestione and "Tipo Gestione" in df_sel.columns:
            df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["Tipo Gestione"].isin(tipo_gestione)]
        if mpro_club and "MPRO Club" in df_sel.columns:
            df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["MPRO Club"].isin(mpro_club)]
        if ricerca_cliente and "Customer" in df_sel.columns:
            df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["Customer"].astype(str).str.contains(ricerca_cliente, case=False, na=False)]

        # Conversione coerente e sicura delle metriche di Sellout
        sellout_sales_tot = float(parse_universal_numeric(df_sel_filtrato["Sales TT"]).sum()) if "Sales TT" in df_sel_filtrato.columns else 0.0
        sellout_margin_tot = float(parse_universal_numeric(df_sel_filtrato["Front Margin"]).sum()) if "Front Margin" in df_sel_filtrato.columns else 0.0
        sellout_visits_tot = float(parse_universal_numeric(df_sel_filtrato["# Visit"]).sum()) if "# Visit" in df_sel_filtrato.columns else 0.0
        sellout_margin_pct = (sellout_margin_tot / sellout_sales_tot * 100) if sellout_sales_tot != 0 else 0.0

        st.markdown("##### 📊 Indicatori Chiave del Portafoglio Selezionato")
        ms1, ms2, ms3 = st.columns(3)
        with ms1: st.metric(label="💼 Fatturato Portafoglio (Sellout)", value=fmt_valuta_interi(sellout_sales_tot))
        with ms2: st.metric(label="🎯 Front Margin % Realizzato", value=fmt_percentuale(sellout_margin_pct), help=f"Valore assoluto: {fmt_valuta_decimali(sellout_margin_tot)}")
        with ms3: st.metric(label="👣 Volume Totale Visite", value=f"{int(sellout_visits_tot):,}".replace(',', '.'))
        # -----------------------------------------------------------------------------
        # SCHEDA 2: ANALISI PORTAFOGLIO (Parte B - Tabella Analitica Clienti)
        # -----------------------------------------------------------------------------
        st.markdown("<br>### 📋 Elenco Analitico Clienti (Ordinati per Fatturato Decrescente)", unsafe_allow_html=True)
        raggruppamento_cols = [c for c in ["Customer", "Customer Category", "Venditore", "MPRO Club"] if c in df_sel_filtrato.columns]
        
        if raggruppamento_cols:
            agg_dict = {"Sales TT": "sum"}
            if "Front Margin" in df_sel_filtrato.columns: agg_dict["Front Margin"] = "sum"
            if "# Visit" in df_sel_filtrato.columns: agg_dict["# Visit"] = "sum"
            
            df_customer_pivoted = df_sel_filtrato.groupby(raggruppamento_cols).agg(agg_dict).reset_index()
            
            # Ordinamento basato su valori numerici reali decrescenti prima della formattazione stringa
            df_customer_pivoted["Sales_Numeric"] = parse_universal_numeric(df_customer_pivoted["Sales TT"])
            df_customer_pivoted = df_customer_pivoted.sort_values(by="Sales_Numeric", ascending=False)
            
            # Formattazione per la visualizzazione Streamlit
            df_customer_pivoted["Sales TT"] = df_customer_pivoted["Sales_Numeric"].map(fmt_valuta_interi)
            if "Front Margin" in df_customer_pivoted.columns:
                df_customer_pivoted["Front Margin"] = parse_universal_numeric(df_customer_pivoted["Front Margin"]).map(fmt_valuta_decimali)
            if "# Visit" in df_customer_pivoted.columns:
                df_customer_pivoted["# Visit"] = parse_universal_numeric(df_customer_pivoted["# Visit"]).map('{:,.0f}'.format)

            df_customer_pivoted = df_customer_pivoted.drop(columns=["Sales_Numeric"])
            st.dataframe(df_customer_pivoted, use_container_width=True, hide_index=True)
    else:
        st.info("Carica il report Free Analysis Sellout per sbloccare l'esplorazione del portafoglio clienti.")
