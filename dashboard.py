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

# SEPARAZIONE IN DUE PAGINE/TAB INDIPENDENTI
tab1, tab2 = st.tabs(["🏬 Vista Store e Performance Reparti", "👥 Analisi Profilazione Clienti (Sellout)"])
with tab1:
    if not dati_vista.empty:
        st.markdown(f"### 🎯 {titolo_vista}")
        
        # Iniezione stili per evitare il troncamento dei numeri lunghi in "..."
        st.markdown("""
            <style>
                div[data-testid="stMetricValue"] { font-size: 21px !important; }
                div[data-testid="stMetricLabel"] p { font-size: 13px !important; white-space: nowrap !important; }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("#### 📊 Indicatori Chiave di Performance")
        
        # Configurazione della griglia a 7 elementi vuoti a inizio pagina
        col_m1, col_m2, col_m3, col_m4, col_m5, col_m6, col_m7 = st.columns(7)
        box_m1 = col_m1.empty()
        box_m2 = col_m2.empty()
        box_m3 = col_m3.empty()
        box_m4 = col_m4.empty()
        box_m5 = col_m5.empty()
        box_m6 = col_m6.empty()
        box_m7 = col_m7.empty()
        
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

        margin_on_sales = (margin_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        shrink_on_sales = (shrink_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        margin_on_sales_py = (margin_py_tot / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
        shrink_on_sales_py = (shrink_py_tot / sales_py_tot * 100) if sales_py_tot != 0 else 0.0

        delta_sales_pct = ((sales_tot - sales_py_tot) / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
        delta_margin_pp = margin_on_sales - margin_on_sales_py
        delta_shrink_pp = shrink_on_sales - shrink_on_sales_py

        df_giornaliero = df_calc.groupby(df_calc.iloc[:, 0]).agg({'Stock_TY_Num':'sum', 'Sales_TY_Num':'sum', 'Sales_PY_Num':'sum'}).reset_index()
        df_giornaliero['Days_TY'] = df_giornaliero.apply(lambda r: r['Stock_TY_Num'] / r['Sales_TY_Num'] if r['Sales_TY_Num'] > 0 else 0.0, axis=1)
        df_giornaliero['Days_PY'] = df_giornaliero.apply(lambda r: r['Stock_TY_Num'] / r['Sales_PY_Num'] if r['Sales_PY_Num'] > 0 else 0.0, axis=1)

        val_stock_days = float(df_giornaliero[df_giornaliero['Days_TY'] > 0]['Days_TY'].mean()) if not df_giornaliero[df_giornaliero['Days_TY'] > 0].empty else 0.0
        val_stock_days_py = float(df_giornaliero[df_giornaliero['Days_PY'] > 0]['Days_PY'].mean()) if not df_giornaliero[df_giornaliero['Days_PY'] > 0].empty else 0.0
        delta_stock_pct = ((val_stock_days - val_stock_days_py) / val_stock_days_py * 100) if val_stock_days_py != 0 else 0.0

        val_avg_stock_ultimo_giorno = 0.0
        try:
            df_calc['Date_Parsed'] = pd.to_datetime(df_calc.iloc[:, 0].astype(str).str.strip(), format='mixed', errors='coerce')
            if not df_calc[df_calc['Date_Parsed'].notna()].empty:
                val_avg_stock_ultimo_giorno = float(df_calc[df_calc['Date_Parsed'] == df_calc[df_calc['Date_Parsed'].notna()]['Date_Parsed'].max()]['Stock_TY_Num'].sum())
        except: pass

        codici_target = set()
        for r in dati_vista.iloc[:, 4].dropna().astype(str).str.strip():
            match = re.search(r'\d+', r)
            if match: codici_target.add(match.group())

        # Scrittura istantanea dei primi 5 KPI calcolati nei segnaposto superiori
        box_m1.metric(label="💰 Sales TT", value=fmt_valuta_interi(sales_tot), delta=f"{delta_sales_pct:+.2f}% vs PY")
        box_m2.metric(label="📈 Front Margin %", value=fmt_percentuale(margin_on_sales), delta=f"{delta_margin_pp:+.2f} pp vs PY")
        box_m3.metric(label="📦 Stock Days", value=fmt_giorni(val_stock_days), delta=f"{delta_stock_pct:+.2f}% vs PY", delta_color="inverse")
        box_m4.metric(label="🏬 Avg Stock Last Day", value=fmt_valuta_interi(val_avg_stock_ultimo_giorno), delta=None)
        box_m5.metric(label="📉 Shrinkage (Sfrido)", value=fmt_percentuale(shrink_on_sales), delta=f"{delta_shrink_pp:+.2f} pp vs PY", delta_color="inverse")
        # --- SEZIONE REPORT COMPLEMENTARI CROSS-REPORT ---
        st.markdown("<br>---", unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.markdown("#### 📈 Sintesi Report BMPL Reparti")
            if not df_rep.empty:
                def parse_bmpl_direct(dataframe, col_name):
                    if col_name in dataframe.columns:
                        s = dataframe[col_name].astype(str).str.replace(r'\s+', '', regex=True).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                        return pd.to_numeric(s, errors='coerce').fillna(0.0)
                    return pd.Series(0.0, index=dataframe.index)

                df_rep_pure = df_rep.copy()
                col_bmpl_rep = [c for c in df_rep_pure.columns if 'department' in c.lower() or 'reparto' in c.lower()]
                if col_bmpl_rep and len(codici_target) > 0:
                    df_rep_pure['Codice_Reparto_BMPL'] = df_rep_pure[col_bmpl_rep].astype(str).apply(lambda x: re.search(r'\d+', str(x)).group() if re.search(r'\d+', str(x)) else '')
                    match_bmpl = df_rep_pure[df_rep_pure['Codice_Reparto_BMPL'].isin(codici_target)] if (selected_area != "--- TOTALE STORE ---" or selected_reparto != "--- DETTAGLIO RICHIESTO ---") else df_rep_pure.copy()
                else: match_bmpl = df_rep_pure.copy()

                if not match_bmpl.empty:
                    bmpl_s = float(parse_bmpl_direct(match_bmpl, 'Sales TT').sum())
                    bmpl_s_py = float(parse_bmpl_direct(match_bmpl, 'Sales TT PY Custom Cal').sum())
                    bmpl_m = float(parse_bmpl_direct(match_bmpl, 'Front Margin').sum())
                    bmpl_m_py = float(parse_bmpl_direct(match_bmpl, 'Front Margin PY Custom Cal').sum())
                    bmpl_c = float(parse_bmpl_direct(match_bmpl, '# Colli').sum())
                    
                    m_ty = (bmpl_m / bmpl_s * 100) if bmpl_s != 0 else 0.0
                    m_py = (bmpl_m_py / bmpl_s_py * 100) if bmpl_s_py != 0 else 0.0
                    
                    sub1, sub2, sub3 = st.columns(3)
                    with sub1: st.metric(label="Sales TT (BMPL)", value=fmt_valuta_interi(bmpl_s), delta=f"{((bmpl_s - bmpl_s_py)/bmpl_s_py*100):+.2f}%" if bmpl_s_py else None)
                    with sub2: st.metric(label="Front Margin % (BMPL)", value=fmt_percentuale(m_ty), delta=f"{(m_ty - m_py):+.2f} pp")
                    with sub3: st.metric(label="Volume Colli (BMPL)", value=f"{int(round(bmpl_c)):,}".replace(',', '.'))

        with col_c2:
            st.markdown("#### 📌 Sintesi Articoli Indispensabili")
            if not df_ind.empty:
                col_rep_ind = [c for c in df_ind.columns if 'department' in c.lower() or 'reparto' in c.lower()]
                if col_rep_ind and len(codici_target) > 0:
                    df_ind['Codice_Reparto_IND'] = df_ind[col_rep_ind].apply(lambda x: re.search(r'\d+', str(x)).group() if re.search(r'\d+', str(x)) else '')
                    match_ind = df_ind[df_ind['Codice_Reparto_IND'].isin(codici_target)]
                    if not match_ind.empty:
                        st.caption(f"ℹ️ Rilevati {len(match_ind)} Articoli Indispensabili inseriti nel perimetro corrente.")

        # --- APERTURA ENGINE DEL CALCOLO DINAMICO REPORT CTG ---
        promo_share_ty, delta_promo_pp, hvs_sales_ty, delta_hvs_pct = 0.0, 0.0, 0.0, 0.0
        if not df_ctg.empty:
            df_ctg_clean = df_ctg.copy()
            df_ctg_clean['Codice_Reparto_CTG'] = df_ctg_clean.iloc[:, 1].astype(str).apply(lambda x: re.search(r'\d+', str(x)).group() if re.search(r'\d+', str(x)) else '')
            match_ctg = df_ctg_clean[df_ctg_clean['Codice_Reparto_CTG'].isin(codici_target)].copy() if (selected_area != "--- TOTALE STORE ---" or selected_reparto != "--- DETTAGLIO RICHIESTO ---") else df_ctg_clean.copy()
            
            if not match_ctg.empty:
                def parse_ctg_fixed(dataframe, col_index):
                    s = dataframe.iloc[:, col_index].astype(str).str.replace(r'\s+', '', regex=True).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    return pd.to_numeric(s, errors='coerce').fillna(0.0)

                match_ctg['Sales_TY'] = parse_ctg_fixed(match_ctg, 7)
                match_ctg['Sales_PY'] = parse_ctg_fixed(match_ctg, 8)
                match_ctg['Visits_TY'] = parse_ctg_fixed(match_ctg, 11)
                match_ctg['CTG_Label'] = match_ctg['CTG'].astype(str).str.strip()
                match_ctg['Channel_Label'] = match_ctg['Channel Detail'].astype(str).str.strip()

                c_promo = [c for c in match_ctg.columns if 'promo' in c.lower()][0]
                c_hvs = [c for c in match_ctg.columns if 'hvs' in c.lower()][0]
                
                t_s_ty = match_ctg['Sales_TY'].sum()
                t_s_py = match_ctg['Sales_PY'].sum()
                
                df_p = match_ctg[match_ctg[c_promo].astype(str).str.upper().str.strip() == 'PROMO']
                promo_share_ty = (df_p['Sales_TY'].sum() / t_s_ty * 100) if t_s_ty > 0 else 0.0
                promo_share_py = (df_p['Sales_PY'].sum() / t_s_py * 100) if t_s_py > 0 else 0.0
                delta_promo_pp = promo_share_ty - promo_share_py
                
                df_h = match_ctg[match_ctg[c_hvs].astype(str).str.upper().str.strip() == 'HVS']
                hvs_sales_ty = df_h['Sales_TY'].sum()
                delta_hvs_pct = ((hvs_sales_ty - df_h['Sales_PY'].sum()) / df_h['Sales_PY'].sum() * 100) if df_h['Sales_PY'].sum() > 0 else 0.0

        # Iniezione asincrona negli ultimi due segnaposto rimasti in sospeso in alto
        box_m6.metric(label="🏷️ Share Promo %", value=fmt_percentuale(promo_share_ty), delta=f"{delta_promo_pp:+.2f} pp vs PY")
        box_m7.metric(label="💎 Sales HVS", value=fmt_valuta_interi(hvs_sales_ty), delta=f"{delta_hvs_pct:+.2f}% vs PY")

        st.subheader("📊 Analisi e Performance Mix Categorie e Canali (Report CTG)")
        if not df_ctg.empty and not match_ctg.empty:
            c_macro_find = [c for c in match_ctg.columns if 'category' in c.lower() or 'segmento' in c.lower()][0]
            match_ctg['Macro_Category_Clean'] = match_ctg[c_macro_find].astype(str).str.upper().apply(lambda x: 'HORECA' if 'HORECA' in x else ('SCO' if 'SCO' in x else ('TRADER' if 'TRADER' in x else 'ALTRO')))
            df_m_g = match_ctg.groupby('Macro_Category_Clean').agg({'Sales_TY':'sum', 'Visits_TY':'sum'}).reset_index()
            
            mc1, mc2 = st.columns(2)
            with mc1: st.plotly_chart(px.bar(df_m_g, x='Macro_Category_Clean', y='Sales_TY', title="Fatturato per Macro Categoria", template='plotly_dark', color='Macro_Category_Clean'), use_container_width=True)
            with mc2: st.plotly_chart(px.pie(df_m_g, values='Visits_TY', names='Macro_Category_Clean', title="Mix Visite Segmenti", template='plotly_dark', hole=0.4), use_container_width=True)
# =============================================================================
# TAB 2: ANALISI PROFILAZIONE E PERFORMANCE DETTAGLIO CLIENTI (SELLOUT)
# =============================================================================
with tab2:
    st.markdown(f"### 👥 Profilazione e Performance Portafoglio Clienti")
    
    if not df_sel.empty:
        df_sel_clean = df_sel.copy()
        
        # 1. Pulizia degli spazi bianchi all'inizio e alla fine dei nomi delle colonne
        df_sel_clean.columns = df_sel_clean.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
        
        # 2. IDENTIFICAZIONE ROBUSTA DELLE COLONNE DI RAGGRUPPAMENTO (CASE-INSENSITIVE)
        c_rep_name = next((c for c in df_sel_clean.columns if 'department' in c.lower() or 'reparto' in c.lower() or 'sales dep' in c.lower()), None)
        c_cust_name = next((c for c in df_sel_clean.columns if 'customer' in c.lower() or 'cliente' in c.lower()), None)
        c_cat_name = next((c for c in df_sel_clean.columns if 'cluster' in c.lower() or 'mpro' in c.lower() or 'category' in c.lower()), None)
        c_chan_name = next((c for c in df_sel_clean.columns if 'channel' in c.lower() or 'canale' in c.lower()), None)

        # Fallback di sicurezza basati sull'ordine standard se la ricerca testuale fallisce
        if not c_rep_name: c_rep_name = df_sel_clean.columns[2] if len(df_sel_clean.columns) > 2 else df_sel_clean.columns[0]
        if not c_chan_name: c_chan_name = df_sel_clean.columns[3] if len(df_sel_clean.columns) > 3 else df_sel_clean.columns[0]
        if not c_cust_name: c_cust_name = df_sel_clean.columns[4] if len(df_sel_clean.columns) > 4 else df_sel_clean.columns[0]
        if not c_cat_name: c_cat_name = df_sel_clean.columns[5] if len(df_sel_clean.columns) > 5 else df_sel_clean.columns[0]

        # Estrazione del codice reparto numerico per applicare i filtri gerarchici attivi in cima alla dashboard
        df_sel_clean['Codice_Reparto_SEL'] = df_sel_clean[c_rep_name].astype(str).apply(
            lambda x: re.search(r'\d+', str(x)).group() if re.search(r'\d+', str(x)) else ''
        )
        
        if selected_area != "--- TOTALE STORE ---" or (selected_reparto != "--- DETTAGLIO RICHIESTO ---" and selected_reparto != "--- TOTALE AREA ---"):
            match_sel = df_sel_clean[df_sel_clean['Codice_Reparto_SEL'].isin(codici_target)].copy()
        else:
            match_sel = df_sel_clean.copy()
            
        if not match_sel.empty:
            # FUNZIONE DI CONVERSIONE CONTABILE ITALIANA CON RILEVAMENTO DINAMICO DELLA COLONNA
            def parse_sellout_numeric(dataframe, primary_keyword, secondary_keyword=None):
                actual_col = next((c for c in dataframe.columns if primary_keyword.lower() in c.lower()), None)
                if not actual_col and secondary_keyword:
                    actual_col = next((c for c in dataframe.columns if secondary_keyword.lower() in c.lower()), None)
                
                if actual_col:
                    s = dataframe[actual_col].astype(str).str.replace(r'\s+', '', regex=True)
                    s = s.replace(['-', '--', 'nan', 'NaN', 'None', ''], '0')
                    s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    return pd.to_numeric(s, errors='coerce').fillna(0.0)
                return pd.Series(0.0, index=dataframe.index)

            # Collegamento flessibile alle colonne metriche (gestisce varianti come "Sales TT" o "Sales TT PY Custom Cal")
            match_sel['Sales_TY'] = parse_sellout_numeric(match_sel, 'Sales TT', 'Sales 1')
            match_sel['Sales_PY'] = parse_sellout_numeric(match_sel, 'PY Custom Cal', 'Sales per')
            match_sel['Colli_TY'] = parse_sellout_numeric(match_sel, '# Colli', 'Colli')
            match_sel['Visits_TY'] = parse_sellout_numeric(match_sel, '# Visit', 'Visit')
            match_sel['Margin_TY'] = parse_sellout_numeric(match_sel, 'Front Margin', 'Margin')

            # --- SINTESI CONTABILE DEI KPI IN ALTO NEL TAB 2 ---
            sel_s_tot = match_sel['Sales_TY'].sum()
            sel_s_py_tot = match_sel['Sales_PY'].sum()
            sel_v_tot = match_sel['Visits_TY'].sum()
            sel_cust_qty = match_sel[c_cust_name].nunique()
            
            sel_delta = ((sel_s_tot - sel_s_py_tot) / sel_s_py_tot * 100) if sel_s_py_tot > 0 else 0.0
            sc_medio = (sel_s_tot / sel_v_tot) if sel_v_tot > 0 else 0.0

            c_sel1, c_sel2, c_sel3, c_sel4 = st.columns(4)
            with c_sel1: st.metric(label="👥 Buying Customers Unici", value=f"{sel_cust_qty:,}".replace(',', '.'))
            with c_sel2: st.metric(label="💰 Totale Sales (Sellout)", value=fmt_valuta_interi(sel_s_tot), delta=f"{sel_delta:+.2f}% vs PY")
            with c_sel3: st.metric(label="🎫 Totale Visite/Scontrini", value=f"{int(sel_v_tot):,}".replace(',', '.'))
            with c_sel4: st.metric(label="🛒 Scontrino Medio Portafoglio", value=fmt_valuta_decimali(sc_medio))
            st.markdown("<br>", unsafe_allow_html=True)
            sg1, sg2 = st.columns(2)
            
            with sg1:
                st.markdown("#### 🎯 Quota Fatturato Corrente per Customer Category")
                df_cat_g = match_sel.groupby(c_cat_name)['Sales_TY'].sum().reset_index()
                df_cat_g = df_cat_g[df_cat_g['Sales_TY'] > 0]
                st.plotly_chart(px.pie(df_cat_g, values='Sales_TY', names=c_cat_name, template='plotly_dark', hole=0.3, color_discrete_sequence=px.colors.qualitative.Pastel2), use_container_width=True)
                
            with sg2:
                st.markdown("#### 🏪 Incidenza Canali Logistici di Vendita")
                df_cha_g = match_sel.groupby(c_chan_name)['Sales_TY'].sum().reset_index()
                df_cha_g = df_cha_g[df_cha_g['Sales_TY'] > 0]
                st.plotly_chart(px.bar(df_cha_g, x=c_chan_name, y='Sales_TY', template='plotly_dark', color=c_chan_name, color_discrete_sequence=px.colors.qualitative.Safe), use_container_width=True)

            # --- TABELLA ANALITICA DEI TOP BUYERS ---
            st.markdown("<br>---", unsafe_allow_html=True)
            st.markdown("#### 🏆 Classifica Analitica dei Top Buying Customers (Fatturato Decrescente)")
            
            df_c_g = match_sel.groupby([c_cust_name, c_cat_name, c_chan_name]).agg({
                'Sales_TY': 'sum', 'Sales_PY': 'sum', 'Colli_TY': 'sum', 'Visits_TY': 'sum', 'Margin_TY': 'sum'
            }).reset_index()
            
            df_c_g['Scostamento_vs_PY'] = df_c_g['Sales_TY'] - df_c_g['Sales_PY']
            df_c_g['Scontrino_Medio'] = df_c_g.apply(lambda r: r['Sales_TY'] / r['Visits_TY'] if r['Visits_TY'] > 0 else 0.0, axis=1)
            df_c_g['Margin_Pct'] = df_c_g.apply(lambda r: (r['Margin_TY'] / r['Sales_TY'] * 100) if r['Sales_TY'] > 0 else 0.0, axis=1)
            df_c_g = df_c_g.sort_values(by='Sales_TY', ascending=False).reset_index(drop=True)
            
            # Formattazione estetica finale della griglia dati
            df_c_v = df_c_g.copy()
            df_c_v['Sales_TY'] = df_c_v['Sales_TY'].apply(fmt_valuta_decimali)
            df_c_v['Sales_PY'] = df_c_v['Sales_PY'].apply(fmt_valuta_decimali)
            df_c_v['Scostamento_vs_PY'] = df_c_v['Scostamento_vs_PY'].apply(lambda x: f"+{fmt_valuta_decimali(x)}" if x > 0 else fmt_valuta_decimali(x))
            df_c_v['Scontrino_Medio'] = df_c_v['Scontrino_Medio'].apply(fmt_valuta_decimali)
            df_c_v['Margin_Pct'] = df_c_v['Margin_Pct'].apply(fmt_percentuale)
            df_c_v['Colli_TY'] = df_c_v['Colli_TY'].apply(lambda x: f"{int(round(x)):,}".replace(',', '.'))
            df_c_v['Visits_TY'] = df_c_v['Visits_TY'].apply(lambda x: f"{int(round(x)):,}".replace(',', '.'))
            
            df_c_v.columns = ['Codice Cliente', 'Cluster', 'Canale Detail', 'Sales TY', 'Sales PY', 'Colli TY', 'Visite', 'Margin €', 'Delta vs PY', 'Scontrino Medio', 'Margin %']
            st.dataframe(df_c_v[['Codice Cliente', 'Cluster', 'Canale Detail', 'Sales TY', 'Sales PY', 'Delta vs PY', 'Colli TY', 'Visite', 'Scontrino Medio', 'Margin %']], use_container_width=True, hide_index=False)
        else:
            st.caption("⚠️ Nessun dato nel report Free Analysis Sellout corrisponde ai reparti attivi.")
    else:
        st.info("Carica il file Free Analysis Sellout nella barra laterale sinistra per sbloccare il pannello di profilazione clienti.")
