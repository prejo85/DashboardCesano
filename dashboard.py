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
        df_men_clean.iloc[:, 1] = df_men_clean.iloc[:, 1].astype(str).str.strip() 
        df_men_clean.iloc[:, 3] = df_men_clean.iloc[:, 3].astype(str).str.strip() 
        df_men_clean.iloc[:, 4] = df_men_clean.iloc[:, 4].astype(str).str.strip() 
        
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
        
        def parse_to_numeric_series(dataframe, col_index, is_stock=False):
            if len(dataframe.columns) > col_index:
                s = dataframe.iloc[:, col_index].astype(str).str.replace(r'\s+', '', regex=True)
                s = s.replace(['-', '--', 'nan', 'NaN', ''], '0')
                if is_stock:
                    s = s.str.replace('.', '', regex=False)
                else:
                    if s.str.count(r'\.').max() > 1:
                        s = s.str.replace('.', '', regex=False)
                    elif s.str.contains(r'\.').any() and s.str.contains(',').any():
                        s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    elif s.str.contains(',').any() and not s.str.contains(r'\.').any():
                        s = s.str.replace(',', '.', regex=False)
                return pd.to_numeric(s, errors='coerce').fillna(0.0)
            return pd.Series(dtype=float, index=dataframe.index)

        df_calc = dati_vista.copy()
        df_calc['Sales_TY_Num'] = parse_to_numeric_series(df_calc, 5)   
        df_calc['Sales_PY_Num'] = parse_to_numeric_series(df_calc, 6)   
        df_calc['Margin_TY_Num'] = parse_to_numeric_series(df_calc, 11) 
        df_calc['Margin_PY_Num'] = parse_to_numeric_series(df_calc, 12) 
        df_calc['Stock_TY_Num'] = parse_to_numeric_series(df_calc, 13, is_stock=True)  
        df_calc['Shrink_TY_Num'] = parse_to_numeric_series(df_calc, 16) 
        df_calc['Shrink_PY_Num'] = parse_to_numeric_series(df_calc, 17) 

        sales_tot = float(df_calc['Sales_TY_Num'].sum())
        sales_py_tot = float(df_calc['Sales_PY_Num'].sum())
        margin_tot = float(df_calc['Margin_TY_Num'].sum())
        margin_py_tot = float(df_calc['Margin_PY_Num'].sum())
        shrink_tot = float(df_calc['Shrink_TY_Num'].sum())
        shrink_py_tot = float(df_calc['Shrink_PY_Num'].sum())
        avg_stock_tot = float(df_calc['Stock_TY_Num'].sum())

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
                df_ultimo_giorno_stock = df_date_valide[df_date_valide['Date_Parsed'] == ultima_data_assoluta]
                val_avg_stock_ultimo_giorno = float(df_ultimo_giorno_stock['Stock_TY_Num'].sum())
        except:
            pass

# =============================================================================
# BLOCCO 3 - PARTE 1: VISUALIZZAZIONE DELLE CARDS KPI SUPERIORI (PROTETTA)
# =============================================================================
        import re

        # Estrazione dinamica dei codici reparto filtrati (es. {'110', '190'})
        reparti_mensilizzazione = dati_vista.iloc[:, 4].dropna().astype(str).str.strip()
        codici_target = set()
        for r in reparti_mensilizzazione:
            match = re.search(r'\d+', r)
            if match:
                codici_target.add(match.group())

        ind_sales, ind_sales_py, ind_colli, ind_colli_py, ind_shrink, ind_shrink_py = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        match_indisp = pd.DataFrame()
        col_rep_ind = [c for c in df_ind.columns if 'department' in c.lower() or 'reparto' in c.lower()]
        
        if col_rep_ind and len(codici_target) > 0:
            col_ind_nome = col_rep_ind[0]
            df_ind_clean = df_ind.copy()
            
            # RISOLTO TYPEERROR: Forziamo il casting a str(x) all'interno del motore Regex per evitare blocchi sui valori nulli
            df_ind_clean['Codice_Reparto_IND'] = df_ind_clean[col_ind_nome].apply(
                lambda x: re.search(r'\d+', str(x)).group() if re.search(r'\d+', str(x)) else ''
            )
            match_indisp = df_ind_clean[df_ind_clean['Codice_Reparto_IND'].isin(codici_target)].copy()
            
            if not match_indisp.empty:
                def parse_indisp_totals(dataframe, col_name):
                    if col_name in dataframe.columns:
                        s = dataframe[col_name].astype(str).str.replace(r'\s+', '', regex=True)
                        s = s.replace(['-', '--', 'nan', 'NaN', 'None', ''], '0')
                        s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                        return pd.to_numeric(s, errors='coerce').fillna(0.0)
                    return pd.Series(0.0, index=dataframe.index)

                # Identificazione dinamica flessibile delle colonne degli Indispensabili per evitare KeyError
                c_sales = [c for c in match_indisp.columns if 'sales' in c.lower() and 'py' not in c.lower()]
                c_sales_py = [c for c in match_indisp.columns if 'sales' in c.lower() and 'py' in c.lower()]
                c_colli = [c for c in match_indisp.columns if 'colli' in c.lower() and 'py' not in c.lower()]
                c_colli_py = [c for c in match_indisp.columns if 'colli' in c.lower() and 'py' in c.lower()]
                c_shk = [c for c in match_indisp.columns if 'shrinkage' in c.lower() and 'py' not in c.lower() and 'net' not in c.lower()]
                c_shk_py = [c for c in match_indisp.columns if 'shrinkage' in c.lower() and ('py' in c.lower() or 'net' in c.lower())]

                ind_sales = float(parse_indisp_totals(match_indisp, c_sales[0]).sum()) if c_sales else 0.0
                ind_sales_py = float(parse_indisp_totals(match_indisp, c_sales_py[0]).sum()) if c_sales_py else 0.0
                ind_colli = float(parse_indisp_totals(match_indisp, c_colli[0]).sum()) if c_colli else 0.0
                ind_colli_py = float(parse_indisp_totals(match_indisp, c_colli_py[0]).sum()) if c_colli_py else 0.0
                ind_shrink = float(parse_indisp_totals(match_indisp, c_shk[0]).sum()) if c_shk else 0.0
                ind_shrink_py = float(parse_indisp_totals(match_indisp, c_shk_py[0]).sum()) if c_shk_py else 0.0

        # Rendering a cinque colonne in puro Python nativo delle card superiori dello Store
        st.markdown("#### 📊 Indicatori Chiave di Performance")
        m1, m2, m3, m4, m5 = st.columns(5)
        
        with m1:
            st.metric(label="💰 Sales TT", value=fmt_valuta_interi(sales_tot), delta=f"{delta_sales_pct:+.2f}% vs PY")
        with m2:
            st.metric(label="📈 Front Margin %", value=fmt_percentuale(margin_on_sales), delta=f"{delta_margin_pp:+.2f} pp vs PY")
        with m3:
            st.metric(label="📦 Stock Days", value=fmt_giorni(val_stock_days), delta=f"{delta_stock_pct:+.2f}% vs PY", delta_color="inverse")
        with m4:  
            st.metric(label="🏬 Avg Stock Last Day", value=fmt_valuta_interi(val_avg_stock_ultimo_giorno), delta=None)
        with m5:  
            st.metric(label="📉 Shrinkage (Sfrido)", value=fmt_percentuale(shrink_on_sales), delta=f"{delta_shrink_pp:+.2f} pp vs PY", delta_color="inverse")

# =============================================================================
# BLOCCO 3 - PARTE 2: INDICATORI CROSS-REPORT SUI VALORI ASSOLUTI
# =============================================================================
        st.markdown("<br>---", unsafe_allow_html=True)
        st.subheader("🔗 Indicatori di Performance Cross-Report (BMPL & Indispensabili)")

        col_c1, col_c2 = st.columns(2)
        
        # --- PANNELLO 1: REPORT BMPL REPARTI (VERSIONE DINAMICA AGGIORNATA AI FILTRI) ---
        with col_c1:
            st.markdown("#### 📈 Sintesi Report BMPL Reparti")
            
            if not df_rep.empty:
                def parse_bmpl_direct(dataframe, col_name):
                    if col_name in dataframe.columns:
                        s = dataframe[col_name].astype(str).str.replace(r'\s+', '', regex=True)
                        s = s.replace(['-', '--', 'nan', 'NaN', ''], '0')
                        s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                        return pd.to_numeric(s, errors='coerce').fillna(0.0)
                    return pd.Series(0.0, index=dataframe.index)

                # Pulizia preliminare: escludiamo eventuali righe spurie di totale finale scritte a mano nel CSV
                df_rep_pure = df_rep[df_rep.iloc[:, 0].astype(str).str.contains('FOOD', case=False, na=False)].copy()

                # LOGICA DI FILTRO AGGANCIO REPARTI:
                # Se è selezionato un reparto o un'area specifica, filtriamo il file BMPL in base ai codici target estratti
                if selected_area != "--- TOTALE STORE ---" or (selected_reparto != "--- DETTAGLIO RICHIESTO ---" and selected_reparto != "--- TOTALE AREA ---"):
                    col_bmpl_rep = [c for c in df_rep_pure.columns if 'department' in c.lower() or 'reparto' in c.lower()]
                    if col_bmpl_rep and len(codici_target) > 0:
                        df_rep_pure['Codice_Reparto_BMPL'] = df_rep_pure[col_bmpl_rep[0]].astype(str).apply(
                            lambda x: re.search(r'\d+', str(x)).group() if re.search(r'\d+', str(x)) else ''
                        )
                        match_bmpl = df_rep_pure[df_rep_pure['Codice_Reparto_BMPL'].isin(codici_target)]
                    else:
                        match_bmpl = df_rep_pure.copy()
                else:
                    # Se siamo sul Totale Store, prendiamo l'intero foglio valido per far quadrare i subtotali complessivi
                    match_bmpl = df_rep_pure.copy()

                # Se il filtro produce un set vuoto per quel reparto specifico, evitiamo il blocco impostando a zero
                if not match_bmpl.empty:
                    bmpl_sales = float(parse_bmpl_direct(match_bmpl, 'Sales TT').sum())
                    bmpl_sales_py = float(parse_bmpl_direct(match_bmpl, 'Sales TT PY Custom Cal').sum())
                    bmpl_margin = float(parse_bmpl_direct(match_bmpl, 'Front Margin').sum())
                    bmpl_margin_py = float(parse_bmpl_direct(match_bmpl, 'Front Margin PY Custom Cal').sum())
                    bmpl_colli = float(parse_bmpl_direct(match_bmpl, '# Colli').sum())
                    bmpl_colli_py = float(parse_bmpl_direct(match_bmpl, '# Colli PY Custom Cal').sum())
                else:
                    bmpl_sales, bmpl_sales_py, bmpl_margin, bmpl_margin_py, bmpl_colli, bmpl_colli_py = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                
                # Calcolo indici percentuali e delta pp
                margin_pct_ty = (bmpl_margin / bmpl_sales * 100) if bmpl_sales != 0 else 0.0
                margin_pct_py = (bmpl_margin_py / bmpl_sales_py * 100) if bmpl_sales_py != 0 else 0.0
                delta_margin_bmpl_pp = margin_pct_ty - margin_pct_py
                
                delta_sales_bmpl = ((bmpl_sales - bmpl_sales_py) / bmpl_sales_py * 100) if bmpl_sales_py != 0 else 0.0
                delta_colli_bmpl = ((bmpl_colli - bmpl_colli_py) / bmpl_colli_py * 100) if bmpl_colli_py != 0 else 0.0

                # Rendering a schermo delle tre card metriche native
                sub_col1, sub_col2, sub_col3 = st.columns(3)
                with sub_col1: 
                    st.metric(label="Sales TT (BMPL)", value=fmt_valuta_interi(bmpl_sales), delta=f"{delta_sales_bmpl:+.2f}% vs PY" if bmpl_sales_py != 0 else None)
                with sub_col2: 
                    st.metric(label="Front Margin % (BMPL)", value=fmt_percentuale(margin_pct_ty), delta=f"{delta_margin_bmpl_pp:+.2f} pp vs PY")
                with sub_col3: 
                    st.metric(label="Volume Colli (BMPL)", value=f"{int(round(bmpl_colli)):,}".replace(',', '.'), delta=f"{delta_colli_bmpl:+.2f}% vs PY" if bmpl_colli_py != 0 else None)
            else:
                st.caption("⚠️ Il file BMPL caricato resulta vuoto.")

        # --- PANNELLO 2: REPORT ARTICOLI INDISPENSABILI (VERSIONE POSIZIONALE CORRETTA) ---
        with col_c2:
            st.markdown("#### 📌 Sintesi Articoli Indispensabili nel Mix")
            
            if not match_indisp.empty:
                # Sottofunzione locale che pulisce i formati europei basandosi sulla posizione della colonna
                def parse_indisp_positional(dataframe, col_index):
                    if len(dataframe.columns) > col_index:
                        s = dataframe.iloc[:, col_index].astype(str).str.replace(r'\s+', '', regex=True)
                        s = s.replace(['-', '--', 'nan', 'NaN', 'None', ''], '0')
                        s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                        return pd.to_numeric(s, errors='coerce').fillna(0.0)
                    return pd.Series(0.0, index=dataframe.index)

                # Estrazione dei totali usando gli indici numerici precisi del file Excel
                ind_sales = float(parse_indisp_positional(match_indisp, 5).sum())       # Colonna F (Indice 5)
                ind_sales_py = float(parse_indisp_positional(match_indisp, 6).sum())    # Colonna G (Indice 6)
                ind_colli = float(parse_indisp_positional(match_indisp, 7).sum())       # CORRETTO: Colonna H (Indice 7)
                ind_colli_py = float(parse_indisp_positional(match_indisp, 8).sum())    # Colonna I (Indice 8)
                ind_shrink = float(parse_indisp_positional(match_indisp, 11).sum())     # Colonna L (Indice 11)
                ind_shrink_py = float(parse_indisp_positional(match_indisp, 12).sum())  # Colonna M (Indice 12)

                # Calcolo delle variazioni percentuali anno su anno (vs PY)
                delta_sales_ind = ((ind_sales - ind_sales_py) / ind_sales_py * 100) if ind_sales_py != 0 else 0.0
                delta_colli_ind = ((ind_colli - ind_colli_py) / ind_colli_py * 100) if ind_colli_py != 0 else 0.0
                delta_shk_ind = ((ind_shrink - ind_shrink_py) / ind_shrink_py * 100) if ind_shrink_py != 0 else 0.0

                # Generiamo le 3 card metriche native Streamlit affiancate
                sub_ind1, sub_ind2, sub_ind3 = st.columns(3)
                with sub_ind1: 
                    st.metric(label="Sales (Indispensabili)", value=fmt_valuta_interi(ind_sales), delta=f"{delta_sales_ind:+.2f}% vs PY")
                with sub_ind2: 
                    st.metric(label="Volume Colli (Indisp.)", value=f"{int(round(ind_colli)):,}".replace(',', '.'), delta=f"{delta_colli_ind:+.2f}% vs PY")
                with sub_ind3: 
                    st.metric(
                        label="📉 Shrinkage (Indisp.)", 
                        value=fmt_valuta_interi(ind_shrink), 
                        delta=f"{delta_shk_ind:+.2f}% vs PY" if ind_shrink_py != 0 else None,
                        delta_color="inverse"
                    )
            else:
                st.caption("⚠️ Nessun articolo indispensabile trovato per questa selezione.")
# =============================================================================
# BLOCCO 3 - PARTE 3: GRIGLIA PRODOTTI INDISPENSABILI DA COLONNA G2 IN POI
# =============================================================================
        st.markdown("<br>#### 📋 Elenco Dettagliato Articoli Indispensabili Rilevati", unsafe_allow_html=True)
        if col_rep_ind and len(codici_target) > 0 and not match_indisp.empty:
            colonne_totali = list(df_ind.columns)
            try:
                indice_g2 = colonne_totali.index('G2')
                colonne_filtrate = [c for c in colonne_totali[indice_g2:] if c != 'Codice_Reparto_IND']
                df_tabella_indisp = match_indisp[colonne_filtrate].copy()
            except ValueError:
                colonne_filtrate = [c for c in colonne_totali[3:] if c != 'Codice_Reparto_IND']
                df_tabella_indisp = match_indisp[colonne_filtrate].copy()
            
            # Pulisce i valori vuoti/nulli prima dell'elaborazione delle stringhe
            df_tabella_indisp = df_tabella_indisp.fillna('-')
            
            def parse_valuta_indisp(val):
                v_str = str(val).strip().replace(' ', '')
                if v_str in ['-', '--', 'nan', 'None', 'NaN', '']:
                    return '-'
                if ',' in v_str and '.' in v_str:
                    v_str = v_str.replace('.', '').replace(',', '.')
                elif ',' in v_str and '.' not in v_str:
                    v_str = v_str.replace(',', '.')
                try:
                    num = float(v_str)
                    return fmt_valuta_decimali(num)
                except:
                    return v_str

            for col in df_tabella_indisp.columns:
                col_lower = col.lower()
                
                if col in ['G2', 'Article']:
                    df_tabella_indisp[col] = df_tabella_indisp[col].astype(str).replace(['None', 'nan', 'NaN'], '-')
                    continue
                
                if 'shrinkage' in col_lower or ('margin' in col_lower and '%' not in col_lower and 'pp' not in col_lower):
                    df_tabella_indisp[col] = df_tabella_indisp[col].apply(parse_valuta_indisp)
                else:
                    df_tabella_indisp[col] = df_tabella_indisp[col].astype(str).apply(
                        lambda x: '-' if x.strip() in ['nan', 'None', 'NaN', ''] else x.strip()
                    )
            
            st.dataframe(df_tabella_indisp, use_container_width=True, hide_index=True)
        else:
            st.info("Carica i report aggiornati per popolare la griglia analitica degli articoli indispensabili.")

        # =============================================================================
        # NUOVA SEZIONE GRAFICA: ANALISI MERCEOLOGICA CTG (VERSIONE CORRETTA)
        # =============================================================================
        st.markdown("<br>---", unsafe_allow_html=True)
        st.subheader("📊 Analisi e Performance Mix Categorie (Report CTG)")

        if not df_ctg.empty:
            df_ctg_clean = df_ctg.copy()
            
            # 1. Rilevamento dinamico ed intelligente delle colonne chiave nel file CTG
            col_rep_ctg = [c for c in df_ctg_clean.columns if 'department' in c.lower() or 'reparto' in c.lower()]
            col_cat_ctg = [c for c in df_ctg_clean.columns if 'category' in c.lower() or 'categoria' in c.lower() or 'ctg' in c.lower() or 'desc' in c.lower()]
            col_sales_ctg = [c for c in df_ctg_clean.columns if 'sales' in c.lower() and 'py' not in c.lower() and '%' not in c.lower()]
            col_margin_ctg = [c for c in df_ctg_clean.columns if 'margin' in c.lower() and 'py' not in c.lower() and '%' not in c.lower()]
            
            # Fallback posizionali sicuri se il rilevamento testuale fallisce o trova liste vuote
            c_rep = col_rep_ctg[0] if col_rep_ctg else df_ctg_clean.columns[2]
            c_cat = col_cat_ctg[0] if col_cat_ctg else df_ctg_clean.columns[3]
            c_sales = col_sales_ctg[0] if col_sales_ctg else df_ctg_clean.columns[5]
            c_margin = col_margin_ctg[0] if col_margin_ctg else df_ctg_clean.columns[11]

            # 2. Isolamento dei codici reparto numerici a 3 cifre per il matching
            df_ctg_clean['Codice_Reparto_CTG'] = df_ctg_clean[c_rep].astype(str).apply(
                lambda x: re.search(r'\d+', str(x)).group() if re.search(r'\d+', str(x)) else ''
            )
            
            # Se siamo sul Totale Store carichiamo tutto il file, altrimenti filtriamo per i reparti target scelti
            if selected_area != "--- TOTALE STORE ---" or (selected_reparto != "--- DETTAGLIO RICHIESTO ---" and selected_reparto != "--- TOTALE AREA ---"):
                match_ctg = df_ctg_clean[df_ctg_clean['Codice_Reparto_CTG'].isin(codici_target)].copy()
            else:
                match_ctg = df_ctg_clean.copy()
            
            if not match_ctg.empty:
                # Sottofunzione di pulizia stringhe e formati europei
                def parse_ctg_flexible(dataframe, col_name):
                    s = dataframe[col_name].astype(str).str.replace(r'\s+', '', regex=True)
                    s = s.replace(['-', '--', 'nan', 'NaN', 'None', ''], '0')
                    s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    return pd.to_numeric(s, errors='coerce').fillna(0.0)

                # Parsing delle metriche di fatturato e margine
                match_ctg['Sales_Num'] = parse_ctg_flexible(match_ctg, c_sales)
                match_ctg['Margin_Num'] = parse_ctg_flexible(match_ctg, c_margin)
                match_ctg['Categoria_Testo'] = match_ctg[c_cat].astype(str).str.strip().replace(['nan', 'None', ''], '-')

                # Raggruppamento per Categoria merceologica unica
                df_ctg_grafici = match_ctg.groupby('Categoria_Testo').agg({
                    'Sales_Num': 'sum',
                    'Margin_Num': 'sum'
                }).reset_index()
                
                df_ctg_grafici = df_ctg_grafici.sort_values(by='Sales_Num', ascending=True)
                df_ctg_grafici = df_ctg_grafici[df_ctg_grafici['Sales_Num'] > 0]

                if not df_ctg_grafici.empty:
                    g1, g2 = st.columns(2)
                    
                    with g1:
                        st.markdown("#### 💰 Volume di Fatturato per Categoria (Sales TT)")
                        fig_sales = px.bar(
                            df_ctg_grafici,
                            x='Sales_Num',
                            y='Categoria_Testo',
                            orientation='h',
                            labels={'Sales_Num': 'Fatturato (€)', 'Categoria_Testo': 'Categoria'},
                            template='plotly_dark',
                            color='Sales_Num',
                            color_continuous_scale='Blues'
                        )
                        fig_sales.update_layout(showlegend=False, coloraxis_showscale=False, height=450, margin=dict(l=20, r=20, t=20, b=20))
                        fig_sales.update_traces(hovertemplate="<b>%{y}</b><br>Fatturato: € %{x:,.0f}<extra></extra>".replace(',', '.'))
                        st.plotly_chart(fig_sales, use_container_width=True)
                        
                    with g2:
                        st.markdown("#### 🎯 Mix di Incidenza del Margine Commerciale (Front Margin)")
                        df_pie = df_ctg_grafici[df_ctg_grafici['Margin_Num'] > 0]
                        
                        if not df_pie.empty:
                            fig_margin = px.pie(
                                df_pie,
                                values='Margin_Num',
                                names='Categoria_Testo',
                                template='plotly_dark',
                                hole=0.4
                            )
                            fig_margin.update_layout(height=450, margin=dict(l=20, r=20, t=20, b=20))
                            fig_margin.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>%{label}</b><br>Margine: € %{value:,.2f}<br>Incidenza: %{percent}<extra></extra>".replace(',', 'X').replace('.', ',').replace('X', '.'))
                            st.plotly_chart(fig_margin, use_container_width=True)
                        else:
                            st.info("💡 Margine commerciale non sufficiente o negativo per generare la torta del mix.")
                else:
                    st.caption("⚠️ I record del file CTG per la selezione corrente contengono volumi pari a zero.")
            else:
                st.caption("⚠️ Nessuna categoria merceologica nel file CTG corrisponde ai filtri attivi.")
        else:
            st.info("Carica il file CTG nella barra laterale sinistra per sbloccare l'analisi grafica merceologica.")

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
