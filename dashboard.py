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
            df = pd.read_csv(file_path, sep=";", skiprows=0, skip_blank_lines=True, dtype=str)
            if len(df.columns) <= 1:
                df = pd.read_csv(file_path, sep=",", skiprows=0, skip_blank_lines=True, dtype=str)
        except:
            df = pd.read_csv(file_path, sep=",", skiprows=0, skip_blank_lines=True, dtype=str)
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

df_rep, df_ctg, df_sel, df_ind, df_men = load_and_clean_data(u_rep, u_ctg, u_sel, u_ind, u_men)

# =============================================================================
# 5. FILTRI GERARCHICI IN ALTO CON LOGICA DI RESET IN SESSION STATE
# =============================================================================
st.markdown("---")
col_f1, col_f2, col_f3, col_btn = st.columns([3, 3, 3, 1])

if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

with col_btn:
    st.markdown("<div style='padding-top: 24px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.reset_counter += 1
        st.rerun()

if len(df_men.columns) >= 5:
    df_men_clean = df_men.copy()
    df_men_clean.iloc[:, 1] = df_men_clean.iloc[:, 1].astype(str).str.strip() 
    df_men_clean.iloc[:, 3] = df_men_clean.iloc[:, 3].astype(str).str.strip() 
    df_men_clean.iloc[:, 4] = df_men_clean.iloc[:, 4].astype(str).str.strip() 
    
    lista_store = sorted([x for x in df_men_clean.iloc[:, 1].unique() if x not in ['nan', 'None', '']])
    
    with col_f1:
        selected_store = st.selectbox("Seleziona Store:", lista_store, key=f"sb_store_{st.session_state.reset_counter}")
    
    df_filtrato_store = df_men_clean[df_men_clean.iloc[:, 1] == selected_store]
    lista_aree = ["--- TOTALE STORE ---"] + sorted([x for x in df_filtrato_store.iloc[:, 3].unique() if x not in ['nan', 'None', '']])
    
    with col_f2:
        selected_area = st.selectbox("Seleziona Area di Vendita:", lista_aree, key=f"sb_area_{st.session_state.reset_counter}")
    
    if selected_area != "--- TOTALE STORE ---":
        df_filtrato_area = df_filtrato_store[df_filtrato_store.iloc[:, 3] == selected_area]
        lista_reparti = ["--- TOTALE AREA ---"] + sorted([x for x in df_filtrato_area.iloc[:, 4].unique() if x not in ['nan', 'None', '']])
    else:
        df_filtrato_area = df_filtrato_store.copy()
        lista_reparti = ["--- DETTAGLIO RICHIESTO ---"]
        
    with col_f3:
        selected_reparto = st.selectbox("Seleziona Reparto:", lista_reparti, key=f"sb_reparto_{st.session_state.reset_counter}")

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
with tab1:
    if not dati_vista.empty:
        st.markdown(f"### 🎯 {titolo_vista}")
        
        # --- STILE CSS PERSONALIZZATO PER EVITARE TRONCAMENTI DI STRINGHE E VALORI ---
        st.markdown("""
            <style>
                div[data-testid="stMetricValue"] { font-size: 21px !important; }
                div[data-testid="stMetricLabel"] p { font-size: 13px !important; white-space: nowrap !important; }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("#### 📊 Indicatori Chiave di Performance")
        
        # Generazione della riga orizzontale a 7 box tramite segnaposto dinamici
        col_m1, col_m2, col_m3, col_m4, col_m5, col_m6, col_m7 = st.columns(7)
        box_m1 = col_m1.empty()
        box_m2 = col_m2.empty()
        box_m3 = col_m3.empty()
        box_m4 = col_m4.empty()
        box_m5 = col_m5.empty()
        box_m6 = col_m6.empty()
        box_m7 = col_m7.empty()
        
        # --- FUNZIONE DI PARSING NUMERICO DELLE RIGHE ---
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
        # --- LOGICA DI CALCOLO E COPERTURA METRICHE BASE STORE ---
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

        reparti_mensilizzazione = dati_vista.iloc[:, 4].dropna().astype(str).str.strip()
        codici_target = set()
        for r in reparti_mensilizzazione:
            match = re.search(r'\d+', r)
            if match: codici_target.add(match.group())

        # Iniezione istantanea dei primi 5 KPI calcolati nei segnaposto in alto
        box_m1.metric(label="💰 Sales TT", value=fmt_valuta_interi(sales_tot), delta=f"{delta_sales_pct:+.2f}% vs PY")
        box_m2.metric(label="📈 Front Margin %", value=fmt_percentuale(margin_on_sales), delta=f"{delta_margin_pp:+.2f} pp vs PY")
        box_m3.metric(label="📦 Stock Days", value=fmt_giorni(val_stock_days), delta=f"{delta_stock_pct:+.2f}% vs PY", delta_color="inverse")
        box_m4.metric(label="🏬 Avg Stock Last Day", value=fmt_valuta_interi(val_avg_stock_ultimo_giorno), delta=None)
        box_m5.metric(label="📉 Shrinkage (Sfrido)", value=fmt_percentuale(shrink_on_sales), delta=f"{delta_shrink_pp:+.2f} pp vs PY", delta_color="inverse")
        # --- SEZIONE REPORT SECONDARI CROSS-REPORT (BMPL & INDISPENSABILI) ---
        st.markdown("<br>---", unsafe_allow_html=True)
        st.subheader("🔗 Indicatori di Performance Cross-Report (BMPL & Indispensabili)")
        col_c1, col_c2 = st.columns(2)
        
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

                df_rep_pure = df_rep.copy()
                col_bmpl_rep = [c for c in df_rep_pure.columns if 'department' in c.lower() or 'reparto' in c.lower()]
                if col_bmpl_rep and len(codici_target) > 0:
                    df_rep_pure['Codice_Reparto_BMPL'] = df_rep_pure[col_bmpl_rep[0]].astype(str).apply(lambda x: re.search(r'\d+', str(x)).group() if re.search(r'\d+', str(x)) else '')
                    if selected_area != "--- TOTALE STORE ---" or (selected_reparto != "--- DETTAGLIO RICHIESTO ---" and selected_reparto != "--- TOTALE AREA ---"):
                        match_bmpl = df_rep_pure[df_rep_pure['Codice_Reparto_BMPL'].isin(codici_target)]
                    else: match_bmpl = df_rep_pure.copy()
                else: match_bmpl = df_rep_pure.copy()

                if not match_bmpl.empty:
                    bmpl_sales = float(parse_bmpl_direct(match_bmpl, 'Sales TT').sum())
                    bmpl_sales_py = float(parse_bmpl_direct(match_bmpl, 'Sales TT PY Custom Cal').sum())
                    bmpl_margin = float(parse_bmpl_direct(match_bmpl, 'Front Margin').sum())
                    bmpl_margin_py = float(parse_bmpl_direct(match_bmpl, 'Front Margin PY Custom Cal').sum())
                    bmpl_colli = float(parse_bmpl_direct(match_bmpl, '# Colli').sum())
                    bmpl_colli_py = float(parse_bmpl_direct(match_bmpl, '# Colli PY Custom Cal').sum())
                else: bmpl_sales, bmpl_sales_py, bmpl_margin, bmpl_margin_py, bmpl_colli, bmpl_colli_py = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                
                margin_pct_ty = (bmpl_margin / bmpl_sales * 100) if bmpl_sales != 0 else 0.0
                margin_pct_py = (bmpl_margin_py / bmpl_sales_py * 100) if bmpl_sales_py != 0 else 0.0
                delta_margin_bmpl_pp = margin_pct_ty - margin_pct_py
                delta_sales_bmpl = ((bmpl_sales - bmpl_sales_py) / bmpl_sales_py * 100) if bmpl_sales_py != 0 else 0.0
                delta_colli_bmpl = ((bmpl_colli - bmpl_colli_py) / bmpl_colli_py * 100) if bmpl_colli_py != 0 else 0.0

                sub_col1, sub_col2, sub_col3 = st.columns(3)
                with sub_col1: st.metric(label="Sales TT (BMPL)", value=fmt_valuta_interi(bmpl_sales), delta=f"{delta_sales_bmpl:+.2f}% vs PY" if bmpl_sales_py != 0 else None)
                with sub_col2: st.metric(label="Front Margin % (BMPL)", value=fmt_percentuale(margin_pct_ty), delta=f"{delta_margin_bmpl_pp:+.2f} pp vs PY")
                with sub_col3: st.metric(label="Volume Colli (BMPL)", value=f"{int(round(bmpl_colli)):,}".replace(',', '.'), delta=f"{delta_colli_bmpl:+.2f}% vs PY" if bmpl_colli_py != 0 else None)
                
                with st.expander("🔍 Debug: Vedi righe BMPL incluse nel calcolo"):
                    st.dataframe(match_bmpl[[col_bmpl_rep[0], 'Sales TT', '# Colli']], use_container_width=True)

        with col_c2:
            st.markdown("#### 📌 Sintesi Articoli Indispensabili nel Mix")
            col_rep_ind = [c for c in df_ind.columns if 'department' in c.lower() or 'reparto' in c.lower()]
            match_indisp = pd.DataFrame()
            if col_rep_ind and len(codici_target) > 0:
                col_ind_nome = col_rep_ind[0]
                df_ind_clean = df_ind.copy()
                df_ind_clean['Codice_Reparto_IND'] = df_ind_clean[col_ind_nome].apply(lambda x: re.search(r'\d+', str(x)).group() if re.search(r'\d+', str(x)) else '' )
                match_indisp = df_ind_clean[df_ind_clean['Codice_Reparto_IND'].isin(codici_target)].copy()
            
            if not match_indisp.empty:
                def parse_indisp_positional(dataframe, col_index):
                    if len(dataframe.columns) > col_index:
                        s = dataframe.iloc[:, col_index].astype(str).str.replace(r'\s+', '', regex=True)
                        s = s.replace(['-', '--', 'nan', 'NaN', 'None', ''], '0')
                        s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                        return pd.to_numeric(s, errors='coerce').fillna(0.0)
                    return pd.Series(0.0, index=dataframe.index)

                ind_sales = float(parse_indisp_positional(match_indisp, 5).sum())       
                ind_sales_py = float(parse_indisp_positional(match_indisp, 6).sum())    
                ind_colli = float(parse_indisp_positional(match_indisp, 7).sum())       
                ind_colli_py = float(parse_indisp_positional(match_indisp, 8).sum())    
                ind_shrink = float(parse_indisp_positional(match_indisp, 11).sum())     
                ind_shrink_py = float(parse_indisp_positional(match_indisp, 12).sum())  

                delta_sales_ind = ((ind_sales - ind_sales_py) / ind_sales_py * 100) if ind_sales_py != 0 else 0.0
                delta_colli_ind = ((ind_colli - ind_colli_py) / ind_colli_py * 100) if ind_colli_py != 0 else 0.0
                delta_shk_ind = ((ind_shrink - ind_shrink_py) / ind_shrink_py * 100) if ind_shrink_py != 0 else 0.0

                sub_ind1, sub_ind2, sub_ind3 = st.columns(3)
                with sub_ind1: st.metric(label="Sales (Indispensabili)", value=fmt_valuta_interi(ind_sales), delta=f"{delta_sales_ind:+.2f}% vs PY")
                with sub_ind2: st.metric(label="Volume Colli (Indisp.)", value=f"{int(round(ind_colli)):,}".replace(',', '.'), delta=f"{delta_colli_ind:+.2f}% vs PY")
                with sub_ind3: st.metric(label="📉 Shrinkage (Indisp.)", value=fmt_valuta_interi(ind_shrink), delta=f"{delta_shk_ind:+.2f}% vs PY" if ind_shrink_py != 0 else None, delta_color="inverse")

        st.markdown("<br>#### 📋 Elenco Dettagliato Articoli Indispensabili Rilevati", unsafe_allow_html=True)
        if not match_indisp.empty:
            colonne_totali = list(df_ind.columns)
            try:
                indice_g2 = colonne_totali.index('G2')
                colonne_filtrate = [c for c in colonne_totali[indice_g2:] if c != 'Codice_Reparto_IND']
                df_tabella_indisp = match_indisp[colonne_filtrate].copy()
            except ValueError:
                colonne_filtrate = [c for c in colonne_totali[3:] if c != 'Codice_Reparto_IND']
                df_tabella_indisp = match_indisp[colonne_filtrate].copy()
            
            df_tabella_indisp = df_tabella_indisp.fillna('-')
            
            def parse_valuta_indisp(val):
                v_str = str(val).strip().replace(' ', '')
                if v_str in ['-', '--', 'nan', 'None', 'NaN', '']: return '-'
                if ',' in v_str and '.' in v_str: v_str = v_str.replace('.', '').replace(',', '.')
                elif ',' in v_str and '.' not in v_str: v_str = v_str.replace(',', '.')
                try: return fmt_valuta_decimali(float(v_str))
                except: return v_str

            for col in df_tabella_indisp.columns:
                if col in ['G2', 'Article']:
                    df_tabella_indisp[col] = df_tabella_indisp[col].astype(str).replace(['None', 'nan', 'NaN'], '-')
                    continue
                if 'shrinkage' in col.lower() or ('margin' in col.lower() and '%' not in col.lower() and 'pp' not in col.lower()):
                    df_tabella_indisp[col] = df_tabella_indisp[col].apply(parse_valuta_indisp)
                else:
                    df_tabella_indisp[col] = df_tabella_indisp[col].astype(str).apply(lambda x: '-' if x.strip() in ['nan', 'None', 'NaN', ''] else x.strip())
            st.dataframe(df_tabella_indisp, use_container_width=True, hide_index=True)

# =============================================================================
# BLOCCO 6A: ELABORAZIONE DATI INTEGRATI REPORT CTG (PROMO E HVS)
# =============================================================================
        st.markdown("<br>---", unsafe_allow_html=True)
        st.subheader("📊 Analisi e Performance Mix Categorie e Canali (Report CTG)")

        # Inizializzazione variabili di contesto per evitare celle vuote in alto
        promo_share_ty, promo_share_py, delta_promo_pp = 0.0, 0.0, 0.0
        hvs_sales_ty, hvs_filtered_py, delta_hvs_pct = 0.0, 0.0, 0.0
        match_ctg = pd.DataFrame()

        if not df_ctg.empty:
            df_ctg_clean = df_ctg.copy()
            df_ctg_clean['Codice_Reparto_CTG'] = df_ctg_clean.iloc[:, 1].astype(str).apply(
                lambda x: re.search(r'\d+', str(x)).group() if re.search(r'\d+', str(x)) else ''
            )
            
            # Filtro gerarchico sui reparti attivi per lo Store/Area selezionati
            if selected_area != "--- TOTALE STORE ---" or (selected_reparto != "--- DETTAGLIO RICHIESTO ---" and selected_reparto != "--- TOTALE AREA ---"):
                match_ctg = df_ctg_clean[df_ctg_clean['Codice_Reparto_CTG'].isin(codici_target)].copy()
            else:
                match_ctg = df_ctg_clean.copy()
            
            if not match_ctg.empty:
                # FUNZIONE DI CONVERSIONE CORRETTA PER STRINGHE FORMATELLATE IN ITALIANO (es. 64.160)
                def parse_ctg_columns_fixed(dataframe, col_index):
                    if len(dataframe.columns) > col_index:
                        s = dataframe.iloc[:, col_index].astype(str).str.replace(r'\s+', '', regex=True)
                        s = s.replace(['-', '--', 'nan', 'NaN', 'None', ''], '0')
                        if s.str.contains(r'\.').any() and s.str.contains(',').any():
                            s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                        elif s.str.contains(r'\.').any() and not s.str.contains(',').any():
                            s = s.str.replace('.', '', regex=False)
                        elif s.str.contains(',').any():
                            s = s.str.replace(',', '.', regex=False)
                        return pd.to_numeric(s, errors='coerce').fillna(0.0)
                    return pd.Series(0.0, index=dataframe.index)

                match_ctg['Sales_TY'] = parse_ctg_columns_fixed(match_ctg, 7)
                match_ctg['Sales_PY'] = parse_ctg_columns_fixed(match_ctg, 8)
                match_ctg['Visits_TY'] = parse_ctg_columns_fixed(match_ctg, 11)
                
                match_ctg['CTG_Label'] = match_ctg['CTG'].astype(str).str.strip().str.replace("'", "", regex=False).replace(['nan', 'None', ''], '-')
                match_ctg['Channel_Label'] = match_ctg['Channel Detail'].astype(str).str.strip()

                # --- FIX ATTR_ERROR: Estrazione sicura usando indici di colonna espliciti ---
                col_flag_promo = [c for c in match_ctg.columns if 'promo' in c.lower()]
                col_flag_hvs = [c for c in match_ctg.columns if 'hvs' in c.lower()]
                
                total_filtered_sales_ty = match_ctg['Sales_TY'].sum()
                total_filtered_sales_py = match_ctg['Sales_PY'].sum()
                
                if col_flag_promo:
                    col_promo_name = col_flag_promo[0]  # Prende la stringa pura della colonna
                    df_promo_filtered = match_ctg[match_ctg[col_promo_name].astype(str).str.upper().str.strip() == 'PROMO']
                    promo_filtered_ty = df_promo_filtered['Sales_TY'].sum()
                    promo_filtered_py = df_promo_filtered['Sales_PY'].sum()
                    promo_share_ty = (promo_filtered_ty / total_filtered_sales_ty * 100) if total_filtered_sales_ty > 0 else 0.0
                    promo_share_py = (promo_filtered_py / total_filtered_sales_py * 100) if total_filtered_sales_py > 0 else 0.0
                    delta_promo_pp = promo_share_ty - promo_share_py
                
                if col_flag_hvs:
                    col_hvs_name = col_flag_hvs[0]  # Prende la stringa pura della colonna
                    df_hvs_filtered = match_ctg[match_ctg[col_hvs_name].astype(str).str.upper().str.strip() == 'HVS']
                    hvs_sales_ty = df_hvs_filtered['Sales_TY'].sum()
                    hvs_filtered_py = df_hvs_filtered['Sales_PY'].sum()
                    delta_hvs_pct = ((hvs_sales_ty - hvs_filtered_py) / hvs_filtered_py * 100) if hvs_filtered_py > 0 else 0.0

        # Iniezione asincrona nei riquadri 6 e 7 posti in cima alla pagina
        box_m6.metric(label="🏷️ Share Promo %", value=fmt_percentuale(promo_share_ty), delta=f"{delta_promo_pp:+.2f} pp vs PY")
        box_m7.metric(label="💎 Sales HVS", value=fmt_valuta_interi(hvs_sales_ty), delta=f"{delta_hvs_pct:+.2f}% vs PY")
# =============================================================================
# BLOCCO 6B: COMPONENTI GRAFICI DI PERFORMANCE MIX (HORECA CORRETTO)
# =============================================================================
        if not df_ctg.empty and not match_ctg.empty:
            st.markdown("#### 🎯 Performance Globale per Canale e Segmento Cliente")
            
            col_macro = [c for c in match_ctg.columns if 'customer category' in c.lower() or 'segmento' in c.lower() or 'macro' in c.lower()]
            match_ctg['Macro_Category'] = match_ctg[col_macro].astype(str).str.upper().str.strip() if col_macro else match_ctg.iloc[:, 2].astype(str).str.upper().str.strip()

            def normalizza_macro(val):
                val_str = str(val)
                if 'HORECA' in val_str: return 'HORECA'
                if 'SCO' in val_str: return 'SCO'
                if 'TRADER' in val_str: return 'TRADER'
                return 'ALTRO / NON CORE'
            match_ctg['Macro_Category_Clean'] = match_ctg['Macro_Category'].apply(normalizza_macro)

            df_macro_grouped = match_ctg.groupby('Macro_Category_Clean').agg({'Sales_TY': 'sum', 'Visits_TY': 'sum'}).reset_index().sort_values(by='Sales_TY', ascending=False)
            
            mc1, mc2 = st.columns(2)
            with mc1:
                fig_macro_sales = px.bar(df_macro_grouped, x='Macro_Category_Clean', y='Sales_TY', labels={'Sales_TY': 'Fatturato Corrente (€)', 'Macro_Category_Clean': 'Macro Segmento'}, title="Fatturato per Macro Categoria (HORECA, SCO, TRADER)", template='plotly_dark', color='Macro_Category_Clean', color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_macro_sales.update_layout(showlegend=False, height=350)
                st.plotly_chart(fig_macro_sales, use_container_width=True)
            with mc2:
                fig_macro_visits = px.pie(df_macro_grouped, values='Visits_TY', names='Macro_Category_Clean', title="Mix Incidenza Volumi Visite sui Macro Segmenti", template='plotly_dark', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_macro_visits.update_layout(height=350)
                st.plotly_chart(fig_macro_visits, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Sotto-segmentazione ed esplorazione verticale per il cluster HORECA
            df_horeca_only = match_ctg[match_ctg['Macro_Category_Clean'] == 'HORECA'].copy()
            df_ctg_grouped = df_horeca_only.groupby('CTG_Label').agg({'Sales_TY': 'sum', 'Sales_PY': 'sum', 'Visits_TY': 'sum'}).reset_index().sort_values(by='Sales_TY', ascending=True)
            df_ctg_grouped = df_ctg_grouped[df_ctg_grouped['Sales_TY'] > 0]

            if not df_ctg_grouped.empty:
                g1, g2 = st.columns(2)
                with g1:
                    st.markdown("#### 💰 Volume di Fatturato per Categoria - Dettaglio HORECA (Sales TT)")
                    fig_sales = px.bar(df_ctg_grouped, x='Sales_TY', y='CTG_Label', orientation='h', labels={'Sales_TY': 'Fatturato Corrente (€)', 'CTG_Label': 'Sotto-Categoria HORECA'}, template='plotly_dark', color='Sales_TY', color_continuous_scale='Blues')
                    fig_sales.update_layout(showlegend=False, coloraxis_showscale=False, height=450, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_sales, use_container_width=True)
                with g2:
                    st.markdown("#### 👥 Frequenza e Mix dei Volumi delle Visite (HORECA)")
                    fig_visits = px.pie(df_ctg_grouped, values='Visits_TY', names='CTG_Label', template='plotly_dark', hole=0.4)
                    fig_visits.update_layout(height=450, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_visits, use_container_width=True)

                st.markdown("<br>#### 🏪 Performance Distribuzione per Canale e Scontrino Medio HORECA (`Sales per Visit`)", unsafe_allow_html=True)
                df_channel_grouped = df_horeca_only.groupby('Channel_Label').agg({'Sales_TY': 'sum', 'Visits_TY': 'sum'}).reset_index()
                df_channel_grouped['Scontrino_Medio'] = df_channel_grouped.apply(lambda r: r['Sales_TY']/r['Visits_TY'] if r['Visits_TY'] > 0 else 0, axis=1)
                
                ch1, ch2 = st.columns(2)
                with ch1:
                    fig_ch_sales = px.bar(df_channel_grouped, x='Channel_Label', y='Sales_TY', title="Fatturato HORECA per Canale", template="plotly_dark", color='Channel_Label')
                    st.plotly_chart(fig_ch_sales, use_container_width=True)
                with ch2:
                    fig_ch_avg = px.bar(df_channel_grouped, x='Channel_Label', y='Scontrino_Medio', title="Scontrino Medio HORECA (€ per Visita)", template="plotly_dark", color='Channel_Label')
                    st.plotly_chart(fig_ch_avg, use_container_width=True)
            else:
                st.caption("⚠️ I record del file CTG per il segmento HORECA contengono volumi pari a zero o vuoti.")

            # =============================================================================
            # ESPLORAZIONE VERTICALE ESCLUSIVA PER IL CLUSTER SCO
            # =============================================================================
            st.markdown("<br><br>---", unsafe_allow_html=True)
            st.subheader("🏬 Analisi e Performance Sotto-Categorie Segmento SCO")
            
            df_sco_only = match_ctg[match_ctg['Macro_Category_Clean'] == 'SCO'].copy()
            df_ctg_grouped_sco = df_sco_only.groupby('CTG_Label').agg({'Sales_TY': 'sum', 'Sales_PY': 'sum', 'Visits_TY': 'sum'}).reset_index().sort_values(by='Sales_TY', ascending=True)
            df_ctg_grouped_sco = df_ctg_grouped_sco[df_ctg_grouped_sco['Sales_TY'] > 0]

            if not df_ctg_grouped_sco.empty:
                g1_sco, g2_sco = st.columns(2)
                with g1_sco:
                    st.markdown("#### 💰 Volume di Fatturato per Categoria - Dettaglio SCO (Sales TT)")
                    fig_sales_sco = px.bar(df_ctg_grouped_sco, x='Sales_TY', y='CTG_Label', orientation='h', labels={'Sales_TY': 'Fatturato Corrente (€)', 'CTG_Label': 'Sotto-Categoria SCO'}, template='plotly_dark', color='Sales_TY', color_continuous_scale='Greens')
                    fig_sales_sco.update_layout(showlegend=False, coloraxis_showscale=False, height=450, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_sales_sco, use_container_width=True)
                with g2_sco:
                    st.markdown("#### 👥 Frequenza e Mix dei Volumi delle Visite (SCO)")
                    fig_visits_sco = px.pie(df_ctg_grouped_sco, values='Visits_TY', names='CTG_Label', template='plotly_dark', hole=0.4, color_discrete_sequence=px.colors.sequential.Greens_r)
                    fig_visits_sco.update_layout(height=450, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_visits_sco, use_container_width=True)

                st.markdown("<br>#### 🏪 Performance Distribuzione per Canale e Scontrino Medio SCO (`Sales per Visit`)", unsafe_allow_html=True)
                df_channel_grouped_sco = df_sco_only.groupby('Channel_Label').agg({'Sales_TY': 'sum', 'Visits_TY': 'sum'}).reset_index()
                df_channel_grouped_sco['Scontrino_Medio'] = df_channel_grouped_sco.apply(lambda r: r['Sales_TY']/r['Visits_TY'] if r['Visits_TY'] > 0 else 0, axis=1)
                
                ch1_sco, ch2_sco = st.columns(2)
                with ch1_sco:
                    fig_ch_sales_sco = px.bar(df_channel_grouped_sco, x='Channel_Label', y='Sales_TY', title="Fatturato SCO per Canale", template="plotly_dark", color='Channel_Label', color_discrete_sequence=px.colors.qualitative.Set2)
                    st.plotly_chart(fig_ch_sales_sco, use_container_width=True)
                with ch2_sco:
                    fig_ch_avg_sco = px.bar(df_channel_grouped_sco, x='Channel_Label', y='Scontrino_Medio', title="Scontrino Medio SCO (€ per Visita)", template="plotly_dark", color='Channel_Label', color_discrete_sequence=px.colors.qualitative.Set2)
                    st.plotly_chart(fig_ch_avg_sco, use_container_width=True)
            else:
                st.caption("⚠️ I record del file CTG per il segmento SCO contengono volumi pari a zero o vuoti.")


            # =============================================================================
            # ESPLORAZIONE VERTICALE ESCLUSIVA PER IL CLUSTER TRADER
            # =============================================================================
            st.markdown("<br><br>---", unsafe_allow_html=True)
            st.subheader("📦 Analisi e Performance Sotto-Categorie Segmento TRADER")
            
            df_trader_only = match_ctg[match_ctg['Macro_Category_Clean'] == 'TRADER'].copy()
            df_ctg_grouped_trader = df_trader_only.groupby('CTG_Label').agg({'Sales_TY': 'sum', 'Sales_PY': 'sum', 'Visits_TY': 'sum'}).reset_index().sort_values(by='Sales_TY', ascending=True)
            df_ctg_grouped_trader = df_ctg_grouped_trader[df_ctg_grouped_trader['Sales_TY'] > 0]

            if not df_ctg_grouped_trader.empty:
                g1_tr, g2_tr = st.columns(2)
                with g1_tr:
                    st.markdown("#### 💰 Volume di Fatturato per Categoria - Dettaglio TRADER (Sales TT)")
                    fig_sales_trader = px.bar(df_ctg_grouped_trader, x='Sales_TY', y='CTG_Label', orientation='h', labels={'Sales_TY': 'Fatturato Corrente (€)', 'CTG_Label': 'Sotto-Categoria TRADER'}, template='plotly_dark', color='Sales_TY', color_continuous_scale='Oranges')
                    fig_sales_trader.update_layout(showlegend=False, coloraxis_showscale=False, height=450, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_sales_trader, use_container_width=True)
                with g2_tr:
                    st.markdown("#### 👥 Frequenza e Mix dei Volumi delle Visite (TRADER)")
                    fig_visits_trader = px.pie(df_ctg_grouped_trader, values='Visits_TY', names='CTG_Label', template='plotly_dark', hole=0.4, color_discrete_sequence=px.colors.sequential.Oranges_r)
                    fig_visits_trader.update_layout(height=450, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_visits_trader, use_container_width=True)

                st.markdown("<br>#### 🏪 Performance Distribuzione per Canale e Scontrino Medio TRADER (`Sales per Visit`)", unsafe_allow_html=True)
                df_channel_grouped_trader = df_trader_only.groupby('Channel_Label').agg({'Sales_TY': 'sum', 'Visits_TY': 'sum'}).reset_index()
                df_channel_grouped_trader['Scontrino_Medio'] = df_channel_grouped_trader.apply(lambda r: r['Sales_TY']/r['Visits_TY'] if r['Visits_TY'] > 0 else 0, axis=1)
                
                ch1_tr, ch2_tr = st.columns(2)
                with ch1_tr:
                    fig_ch_sales_trader = px.bar(df_channel_grouped_trader, x='Channel_Label', y='Sales_TY', title="Fatturato TRADER per Canale", template="plotly_dark", color='Channel_Label', color_discrete_sequence=px.colors.qualitative.Pastel1)
                    st.plotly_chart(fig_ch_sales_trader, use_container_width=True)
                with ch2_tr:
                    fig_ch_avg_trader = px.bar(df_channel_grouped_trader, x='Channel_Label', y='Scontrino_Medio', title="Scontrino Medio TRADER (€ per Visita)", template="plotly_dark", color='Channel_Label', color_discrete_sequence=px.colors.qualitative.Pastel1)
                    st.plotly_chart(fig_ch_avg_trader, use_container_width=True)
            else:
                st.caption("⚠️ I record del file CTG per il segmento TRADER contengono volumi pari a zero o vuoti.")
# =============================================================================
# TAB 2: ANALISI PROFILAZIONE E PERFORMANCE DETTAGLIO CLIENTI (SELLOUT)
# =============================================================================
with tab2:
    st.markdown(f"### 👥 Profilazione e Performance Portafoglio Clienti")
    
    if not df_sel.empty:
        df_sel_clean = df_sel.copy()
        
        # Pulizia dei nomi delle colonne per evitare disallineamenti da spazi bianchi
        df_sel_clean.columns = df_sel_clean.columns.str.strip()
        
        # Filtro gerarchico automatico basato sui reparti dello store selezionato
        # Estrae i codici reparto dalla colonna 'Sales Department' (es. "110 - CONSERVE")
        df_sel_clean['Codice_Reparto_SEL'] = df_sel_clean['Sales Department'].astype(str).apply(
            lambda x: re.search(r'\d+', str(x)).group() if re.search(r'\d+', str(x)) else ''
        )
        
        if selected_area != "--- TOTALE STORE ---" or (selected_reparto != "--- DETTAGLIO RICHIESTO ---" and selected_reparto != "--- TOTALE AREA ---"):
            match_sel = df_sel_clean[df_sel_clean['Codice_Reparto_SEL'].isin(codici_target)].copy()
        else:
            match_sel = df_sel_clean.copy()
            
        if not match_sel.empty:
            # FUNZIONE DI CONVERSIONE ROBUSTA PER FORMATI NUMERICI ITALIANI DEL FILE SELLOUT (es. 1.037 o 3,28)
            def parse_sellout_numeric(dataframe, col_name):
                if col_name in dataframe.columns:
                    s = dataframe[col_name].astype(str).str.replace(r'\s+', '', regex=True)
                    s = s.replace(['-', '--', 'nan', 'NaN', 'None', ''], '0')
                    # Gestione stringhe miste tipo (100) per i numeri negativi
                    s = s.str.replace('(', '-', regex=False).str.replace(')', '', regex=False)
                    
                    if s.str.contains(r'\.').any() and s.str.contains(',').any():
                        s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    elif s.str.contains(r'\.').any() and not s.str.contains(',').any():
                        # Se contiene il punto ma ha lunghezza >= 5 o pattern da migliaia, lo rimuove
                        s = s.str.replace('.', '', regex=False)
                    elif s.str.contains(',').any():
                        s = s.str.replace(',', '.', regex=False)
                    return pd.to_numeric(s, errors='coerce').fillna(0.0)
                return pd.Series(0.0, index=dataframe.index)

            # Conversione contabile delle metriche principali
            match_sel['Sales_TY'] = parse_sellout_numeric(match_sel, 'Sales TT')
            match_sel['Sales_PY'] = parse_sellout_numeric(match_sel, 'Sales TT PY Custom Cal')
            match_sel['Colli_TY'] = parse_sellout_numeric(match_sel, '# Colli')
            match_sel['Visits_TY'] = parse_sellout_numeric(match_sel, '# Visit')
            match_sel['Margin_TY'] = parse_sellout_numeric(match_sel, 'Front Margin')

            # --- SINTESI NUMERICA INIZIALE DEL TAB 2 ---
            sel_sales_tot = match_sel['Sales_TY'].sum()
            sel_sales_py_tot = match_sel['Sales_PY'].sum()
            sel_visits_tot = match_sel['Visits_TY'].sum()
            sel_customers_qty = match_sel['Customer'].nunique()
            
            sel_delta_sales = ((sel_sales_tot - sel_sales_py_tot) / sel_sales_py_tot * 100) if sel_sales_py_tot > 0 else 0.0
            scontrino_medio_sel = (sel_sales_tot / sel_visits_tot) if sel_visits_tot > 0 else 0.0

            c_sel1, c_sel2, c_sel3, c_sel4 = st.columns(4)
            with c_sel1:
                st.metric(label="👥 Buying Customers Unici", value=f"{sel_customers_qty:,}".replace(',', '.'))
            with c_sel2:
                st.metric(label="💰 Totale Sales (Report Sellout)", value=fmt_valuta_interi(sel_sales_tot), delta=f"{sel_delta_sales:+.2f}% vs PY")
            with c_sel3:
                st.metric(label="🎫 Totale Visite/Scontrini", value=f"{int(sel_visits_tot):,}".replace(',', '.'))
            with c_sel4:
                st.metric(label="🛒 Scontrino Medio Complessivo", value=fmt_valuta_decimali(scontrino_medio_sel))
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- SEZIONE GRAFICA DEI MACRO CLUSTER ---
            sg1, sg2 = st.columns(2)
            
            with sg1:
                st.markdown("#### 🎯 Quota Fatturato Corrente per Customer Category")
                df_cat_grouped = match_sel.groupby('Customer Category')['Sales_TY'].sum().reset_index().sort_values(by='Sales_TY', ascending=False)
                df_cat_grouped = df_cat_grouped[df_cat_grouped['Sales_TY'] > 0]
                
                fig_cat_pie = px.pie(
                    df_cat_grouped,
                    values='Sales_TY',
                    names='Customer Category',
                    template='plotly_dark',
                    hole=0.3,
                    color_discrete_sequence=px.colors.qualitative.Pastel2
                )
                fig_cat_pie.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
                fig_cat_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_cat_pie, use_container_width=True)
                
            with sg2:
                st.markdown("#### 🏪 Incidenza Canali Logistici di Vendita (Sales TT)")
                df_chan_grouped = match_sel.groupby('Channel Detail')['Sales_TY'].sum().reset_index().sort_values(by='Sales_TY', ascending=False)
                df_chan_grouped = df_chan_grouped[df_chan_grouped['Sales_TY'] > 0]
                
                fig_chan_bar = px.bar(
                    df_chan_grouped,
                    x='Channel Detail',
                    y='Sales_TY',
                    labels={'Sales_TY': 'Fatturato Corrente (€)', 'Channel Detail': 'Canale Logistico'},
                    template='plotly_dark',
                    color='Channel_Label' if 'Channel_Label' in df_chan_grouped.columns else 'Channel Detail',
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_chan_bar.update_layout(showlegend=False, height=380)
                st.plotly_chart(fig_chan_bar, use_container_width=True)

            # --- CLASSIFICA DETTAGLIATA TOP BUYERS ---
            st.markdown("<br>---", unsafe_allow_html=True)
            st.markdown("#### 🏆 Classifica Analitica dei Top Buying Customers (Fatturato Decrescente)")
            
            # Aggregazione per singolo codice e anagrafica cliente
            df_cust_grouped = match_sel.groupby(['Customer', 'Customer Category', 'Channel Detail']).agg({
                'Sales_TY': 'sum',
                'Sales_PY': 'sum',
                'Colli_TY': 'sum',
                'Visits_TY': 'sum',
                'Margin_TY': 'sum'
            }).reset_index()
            
            # Calcolo scostamenti e scontrino medio per singolo cliente
            df_cust_grouped['Scostamento_vs_PY'] = df_cust_grouped['Sales_TY'] - df_cust_grouped['Sales_PY']
            df_cust_grouped['Scontrino_Medio'] = df_cust_grouped.apply(
                lambda r: r['Sales_TY'] / r['Visits_TY'] if r['Visits_TY'] > 0 else 0.0, axis=1
            )
            df_cust_grouped['Margin_Pct'] = df_cust_grouped.apply(
                lambda r: (r['Margin_TY'] / r['Sales_TY'] * 100) if r['Sales_TY'] > 0 else 0.0, axis=1
            )

            # Ordinamento per vendite correnti decrescenti
            df_cust_grouped = df_cust_grouped.sort_values(by='Sales_TY', ascending=False).reset_index(drop=True)
            
            # Formattazione estetica della tabella per l'utente finale
            df_cust_view = df_cust_grouped.copy()
            df_cust_view['Sales_TY'] = df_cust_view['Sales_TY'].apply(fmt_valuta_decimali)
            df_cust_view['Sales_PY'] = df_cust_view['Sales_PY'].apply(fmt_valuta_decimali)
            df_cust_view['Scostamento_vs_PY'] = df_cust_view['Scostamento_vs_PY'].apply(
                lambda x: f"+{fmt_valuta_decimali(x)}" if x > 0 else fmt_valuta_decimali(x)
            )
            df_cust_view['Scontrino_Medio'] = df_cust_view['Scontrino_Medio'].apply(fmt_valuta_decimali)
            df_cust_view['Margin_Pct'] = df_cust_view['Margin_Pct'].apply(fmt_percentuale)
            df_cust_view['Colli_TY'] = df_cust_view['Colli_TY'].apply(lambda x: f"{int(round(x)):,}".replace(',', '.'))
            df_cust_view['Visits_TY'] = df_cust_view['Visits_TY'].apply(lambda x: f"{int(round(x)):,}".replace(',', '.'))
            
            # Rinominazione colonne per l'interfaccia Streamlit
            df_cust_view.columns = [
                'Anagrafica Cliente', 'Categoria', 'Canale Detail', 'Sales TY', 'Sales PY', 
                'Volume Colli TY', 'Num. Visite', 'Front Margin €', 'Delta Assoluto vs PY', 
                'Scontrino Medio', 'Front Margin %'
            ]
            
            # Visualizzazione della griglia dati filtrabile e ordinabile
            st.dataframe(
                df_cust_view[[
                    'Anagrafica Cliente', 'Categoria', 'Canale Detail', 'Sales TY', 'Sales PY', 
                    'Delta Assoluto vs PY', 'Volume Colli TY', 'Num. Visite', 'Scontrino Medio', 'Front Margin %'
                ]], 
                use_container_width=True, 
                hide_index=False
            )
        else:
            st.caption("⚠️ Nessun dato nel report Free Analysis Sellout corrisponde ai reparti attivi nei filtri gerarchici.")
    else:
        st.info("Carica il file Free Analysis Sellout nella barra laterale sinistra per sbloccare l'anagrafica analitica clienti.")
