import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# -----------------------------------------------------------------------------
# CONFIGURAZIONE DELLA PAGINA E TITOLO PRINCIPALE
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Dashboard Commerciale Avanzata", layout="wide", page_icon="📊")

st.title("📊 Dashboard Commerciale Integrata")
st.markdown("### Analisi Multilivello: Store, Aree, Reparti e Segmentazione Clienti")

# -----------------------------------------------------------------------------
# FUNZIONI DI FORMATTAZIONE VALUTA ED ESPRESSIONI ITALIANE
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
# ENGINE CENTRALIZZATO DI PULIZIA E PARSING DEI REPORT
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

    # Funzione di pulizia corretta e protetta contro i crash di tipo (nativi/NaN)
    def parse_italian_numeric(dataframe, col_index):
        if len(dataframe.columns) > col_index:
            # Estrazione e conversione forzata a stringa rimuovendo gli spazi
            s = dataframe.iloc[:, col_index].astype(str).str.replace(r'\s+', '', regex=True)
            s = s.replace(['-', '--', 'nan', 'NaN', 'None', ''], '0')
                    
            def fix_format(val):
                val_str = str(val) # Forzatura stringa locale di sicurezza
                if ',' in val_str and '.' in val_str:
                    return val_str.replace('.', '').replace(',', '.')
                elif ',' in val_str:
                    return val_str.replace(',', '.')
                elif '.' in val_str:
                    return val_str.replace('.', '')
                return val_str
                    
            s = s.apply(fix_format)
            return pd.to_numeric(s, errors='coerce').fillna(0.0)
        return pd.Series(0.0, index=dataframe.index)

# -----------------------------------------------------------------------------
# INTERFACCIA UNICA DI CARICAMENTO NELLA SIDEBAR LATERALE
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

# Caricamento effettivo dei dataframe puliti
df_rep, df_ctg, df_sel, df_ind, df_men = load_and_clean_data(u_rep, u_ctg, u_sel, u_ind, u_men)

# Inizializzazione contatori di reset distinti per i due tab nel Session State
if "reset_tab1" not in st.session_state:
    st.session_state.reset_tab1 = 0
if "reset_tab2" not in st.session_state:
    st.session_state.reset_tab2 = 0
    
# Generazione della struttura dei macro Tab in alto nella pagina
tab1, tab2 = st.tabs(["🏬 Vista Store e Performance Reparti", "👥 Analisi Profilazione Clienti (Sellout)"])
# =============================================================================
# PARTE 3.A: FILTRI GERARCHICI COMPLETI DENTRO IL TAB 1
# =============================================================================
with tab1:

    if len(df_men.columns) >= 5:
        df_men_clean = df_men.copy()
        df_men_clean.iloc[:, 1] = df_men_clean.iloc[:, 1].astype(str).str.strip() 
        df_men_clean.iloc[:, 3] = df_men_clean.iloc[:, 3].astype(str).str.strip() 
        df_men_clean.iloc[:, 4] = df_men_clean.iloc[:, 4].astype(str).str.strip() 
        
        lista_store = sorted([x for x in df_men_clean.iloc[:, 1].unique() if x not in ['nan', 'None', '']])
        
        # Generazione colonne per disporre i filtri in orizzontale
        col_f1, col_f2, col_f3, col_btn = st.columns(4)
        
        with col_btn:
            st.markdown("<div style='padding-top: 24px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Reset Filtri Store", use_container_width=True, key="btn_reset_t1"):
                st.session_state.reset_tab1 += 1
                st.rerun()
                
        with col_f1:
            selected_store = st.selectbox("Seleziona Store:", lista_store, key=f"sb_store_t1_{st.session_state.reset_tab1}")
        
        df_filtrato_store = df_men_clean[df_men_clean.iloc[:, 1] == selected_store]
        lista_aree = ["--- TOTALE STORE ---"] + sorted([x for x in df_filtrato_store.iloc[:, 3].unique() if x not in ['nan', 'None', '']])
        
        with col_f2:
            selected_area = st.selectbox("Seleziona Area di Vendita:", lista_aree, key=f"sb_area_t1_{st.session_state.reset_tab1}")
        
        if selected_area != "--- TOTALE STORE ---":
            df_filtrato_area = df_filtrato_store[df_filtrato_store.iloc[:, 3] == selected_area]
            lista_reparti = ["--- TOTALE AREA ---"] + sorted([x for x in df_filtrato_area.iloc[:, 4].unique() if x not in ['nan', 'None', '']])
        else:
            df_filtrato_area = df_filtrato_store.copy()
            lista_reparti = ["--- DETTAGLIO RICHIESTO ---"]
            
        with col_f3:
            selected_reparto = st.selectbox("Seleziona Reparto:", lista_reparti, key=f"sb_reparto_t1_{st.session_state.reset_tab1}")
# =============================================================================
# PARTE 3.B: ASSEGNAZIONE DATI VISTA E MOTORE DI CALCOLO KPI COMMERCIALI
# =============================================================================
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
            
        st.markdown("---")
        
        if not dati_vista.empty:
            st.markdown(f"### 🎯 {titolo_vista}")
            
            # Applicazione foglio di stile locale per le metriche Streamlit
            st.markdown("""
                <style>
                    div[data-testid="stMetricValue"] { font-size: 21px !important; }
                    div[data-testid="stMetricLabel"] p { font-size: 13px !important; white-space: nowrap !important; }
                </style>
            """, unsafe_allow_html=True)

            st.markdown("#### 📊 Indicatori Chiave di Performance")
            
            # Iniezione del calcolo e conversione numerica sulle colonne del file Mensilizzazione
            df_calc = dati_vista.copy()
            df_calc['Sales_TY_Num'] = parse_to_numeric_series(df_calc, 5)   
            df_calc['Sales_PY_Num'] = parse_to_numeric_series(df_calc, 6)   
            df_calc['Margin_TY_Num'] = parse_to_numeric_series(df_calc, 11) 
            df_calc['Margin_PY_Num'] = parse_to_numeric_series(df_calc, 12) 
            df_calc['Stock_TY_Num'] = parse_to_numeric_series(df_calc, 13, is_stock=True)  
            df_calc['Shrink_TY_Num'] = parse_to_numeric_series(df_calc, 16) 
            df_calc['Shrink_PY_Num'] = parse_to_numeric_series(df_calc, 17) 

            # Aggregazioni dei totali correnti e storici
            sales_tot = float(df_calc['Sales_TY_Num'].sum())
            sales_py_tot = float(df_calc['Sales_PY_Num'].sum())
            margin_tot = float(df_calc['Margin_TY_Num'].sum())
            margin_py_tot = float(df_calc['Margin_PY_Num'].sum())
            shrink_tot = float(df_calc['Shrink_TY_Num'].sum())
            shrink_py_tot = float(df_calc['Shrink_PY_Num'].sum())

            # Calcolo indici percentuali e scostamenti (Delta)
            margin_on_sales = (margin_tot / sales_tot * 100) if sales_tot != 0 else 0.0
            shrink_on_sales = (shrink_tot / sales_tot * 100) if sales_tot != 0 else 0.0
            margin_on_sales_py = (margin_py_tot / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
            shrink_on_sales_py = (shrink_py_tot / sales_py_tot * 100) if sales_py_tot != 0 else 0.0

            delta_sales_pct = ((sales_tot - sales_py_tot) / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
            delta_margin_pp = margin_on_sales - margin_on_sales_py
            delta_shrink_pp = shrink_on_sales - shrink_on_sales_py

            # Analisi della rotazione dello stock su base giornaliera
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
# =============================================================================
# PARTE 3.C: ACCOPPIAMENTO CODICI REPARTO E PARSING DATI REPORT CTG
# =============================================================================
            codici_target = set()
            for r in dati_vista.iloc[:, 4].dropna().astype(str).str.strip():
                match = re.search(r'\d+', r)
                if match: codici_target.add(match.group())

            # Elaborazione delle performance promozionali dal file CTG
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

                    c_promo = next((c for c in match_ctg.columns if 'promo' in c.lower()), None)
                    c_hvs = next((c for c in match_ctg.columns if 'hvs' in c.lower()), None)
                    
                    t_s_ty = match_ctg['Sales_TY'].sum()
                    t_s_py = match_ctg['Sales_PY'].sum()
                    
                    if c_promo:
                        df_p = match_ctg[match_ctg[c_promo].astype(str).str.upper().str.strip() == 'PROMO']
                        promo_share_ty = (df_p['Sales_TY'].sum() / t_s_ty * 100) if t_s_ty > 0 else 0.0
                        promo_share_py = (df_p['Sales_PY'].sum() / t_s_py * 100) if t_s_py > 0 else 0.0
                        delta_promo_pp = promo_share_ty - promo_share_py
                    
                    if c_hvs:
                        df_h = match_ctg[match_ctg[c_hvs].astype(str).str.upper().str.strip() == 'HVS']
                        hvs_sales_ty = df_h['Sales_TY'].sum()
                        h_py = df_h['Sales_PY'].sum()
                        delta_hvs_pct = ((hvs_sales_ty - h_py) / h_py * 100) if h_py > 0 else 0.0
# =============================================================================
# PARTE 3.D: INIEZIONE FISICA NEI COLUMNS E BOX METRICHE DEL TAB 1
# =============================================================================
            col_m1, col_m2, col_m3, col_m4, col_m5, col_m6, col_m7 = st.columns(7)
            box_m1 = col_m1.empty()
            box_m2 = col_m2.empty()
            box_m3 = col_m3.empty()
            box_m4 = col_m4.empty()
            box_m5 = col_m5.empty()
            box_m6 = col_m6.empty()
            box_m7 = col_m7.empty()

            # Popolamento dei singoli tasselli prestazionali con formattazione localizzata
            box_m1.metric(label="💰 Sales TT", value=fmt_valuta_interi(sales_tot), delta=f"{delta_sales_pct:+.2f}% vs PY")
            box_m2.metric(label="📈 Front Margin %", value=fmt_percentuale(margin_on_sales), delta=f"{delta_margin_pp:+.2f} pp vs PY")
            box_m3.metric(label="📦 Stock Days", value=fmt_giorni(val_stock_days), delta=f"{delta_stock_pct:+.2f}% vs PY", delta_color="inverse")
            box_m4.metric(label="🏬 Avg Stock Last Day", value=fmt_valuta_interi(val_avg_stock_ultimo_giorno), delta=None)
            box_m5.metric(label="📉 Shrinkage (Sfrido)", value=fmt_percentuale(shrink_on_sales), delta=f"{delta_shrink_pp:+.2f} pp vs PY", delta_color="inverse")
            box_m6.metric(label="🏷️ Share Promo %", value=fmt_percentuale(promo_share_ty), delta=f"{delta_promo_pp:+.2f} pp vs PY")
            box_m7.metric(label="💎 Sales HVS", value=fmt_valuta_interi(hvs_sales_ty), delta=f"{delta_hvs_pct:+.2f}% vs PY")
# =============================================================================
# PARTE 3.D_BIS: BLOCCO DI CALCOLO E METRICHE BMPL & ARTICOLI INDISPENSABILI (CORRETTO)
# =============================================================================
            st.markdown("---")
            
            # Isolamento stringa numerica del reparto per la mappatura incrociata sui report esterni
            codice_reparto_selezionato = ""
            if selected_reparto not in ["--- TOTALE AREA ---", "--- DETTAGLIO RICHIESTO ---"]:
                match_cod = re.search(r'\d+', str(selected_reparto))
                if match_cod:
                    codice_reparto_selezionato = match_cod.group()

            # Funzione di pulizia dedicata per interpretare correttamente il formato italiano (es. 31.368 o 9.549,92)
            def parse_italian_numeric(dataframe, col_index):
                if len(dataframe.columns) > col_index:
                    s = dataframe.iloc[:, col_index].astype(str).str.replace(r'\s+', '', regex=True)
                    s = s.replace(['-', '--', 'nan', 'NaN', 'None', ''], '0')
                    
                    # Se contiene sia punto che virgola (es. 9.549,92) -> togliamo il punto, cambiamo la virgola in punto
                    # Se contiene solo il punto (es. 31.368 o 4.166) -> è un separatore di migliaia, lo rimuoviamo
                    def fix_format(val):
                        if ',' in val and '.' in val:
                            return val.replace('.', '').replace(',', '.')
                        elif ',' in val:
                            return val.replace(',', '.')
                        elif '.' in val:
                            # Controlliamo se sembra un decimale puro (es. meno di 3 cifre dopo il punto) 
                            # ma nei report commerciali BMPL/Indispensabili i numeri interi hanno il punto delle migliaia
                            return val.replace('.', '')
                        return val
                    
                    s = s.apply(fix_format)
                    return pd.to_numeric(s, errors='coerce').fillna(0.0)
                return pd.Series(0.0, index=dataframe.index)

            # Configurazione colonne principali dell'interfaccia split
            col_bmpl, col_indisp = st.columns(2)

            # -----------------------------------------------------------------
            # SEZIONE 1: ANALISI PERFORMANCE REPARTI BMPL
            # -----------------------------------------------------------------
            with col_bmpl:
                st.markdown("#### 📈 Target Anagrafico Reparti BMPL")
                
                # Filtraggio dinamico del dataset BMPL Reparti
                df_rep_filtrato = df_rep.copy()
                df_rep_filtrato['Codice_Reparto'] = df_rep_filtrato.iloc[:, 1].astype(str).apply(lambda x: re.search(r'\d+', x).group() if re.search(r'\d+', x) else '')
                
                # Applicazione dei filtri ereditati dai selettori centrali
                if selected_area != "--- TOTALE STORE ---" and codice_reparto_selezionato:
                    df_rep_filtrato = df_rep_filtrato[df_rep_filtrato['Codice_Reparto'] == codice_reparto_selezionato]
                elif selected_area != "--- TOTALE STORE ---":
                    df_rep_filtrato = df_rep_filtrato[df_rep_filtrato['Codice_Reparto'].isin(codici_target)]

                if not df_rep_filtrato.empty:
                    # Parsing contabile con la nuova logica italiana corretta
                    sales_bmpl_ty = parse_italian_numeric(df_rep_filtrato, 3).sum()
                    sales_bmpl_py = parse_italian_numeric(df_rep_filtrato, 4).sum()
                    colli_bmpl_ty = parse_italian_numeric(df_rep_filtrato, 5).sum()
                    colli_bmpl_py = parse_italian_numeric(df_rep_filtrato, 6).sum()
                    margin_bmpl_ty = parse_italian_numeric(df_rep_filtrato, 7).sum()
                    margin_bmpl_py = parse_italian_numeric(df_rep_filtrato, 8).sum()

                    # Calcolo degli scostamenti percentuali e assoluti verso l'anno precedente (PY)
                    delta_sales_bmpl = ((sales_bmpl_ty - sales_bmpl_py) / sales_bmpl_py * 100) if sales_bmpl_py > 0 else 0.0
                    delta_colli_bmpl = ((colli_bmpl_ty - colli_bmpl_py) / colli_bmpl_py * 100) if colli_bmpl_py > 0 else 0.0
                    
                    margin_pct_bmpl_ty = (margin_bmpl_ty / sales_bmpl_ty * 100) if sales_bmpl_ty > 0 else 0.0
                    margin_pct_bmpl_py = (margin_bmpl_py / sales_bmpl_py * 100) if sales_bmpl_py > 0 else 0.0
                    delta_margin_bmpl_pp = margin_pct_bmpl_ty - margin_pct_bmpl_py

                    # Rendering orizzontale dei tre tasselli KPI richiesti
                    cb1, cb2, cb3 = st.columns(3)
                    cb1.metric(label="💰 Sales BMPL", value=fmt_valuta_interi(sales_bmpl_ty), delta=f"{delta_sales_bmpl:+.2f}% vs PY")
                    cb2.metric(label="📦 Volumi BMPL (Colli)", value=f"{int(round(colli_bmpl_ty)):,}".replace(',', '.'), delta=f"{delta_colli_bmpl:+.2f}% vs PY")
                    cb3.metric(label="📈 Margin % BMPL", value=fmt_percentuale(margin_pct_bmpl_ty), delta=f"{delta_margin_bmpl_pp:+.2f} pp vs PY")
                else:
                    st.info("ℹ️ Nessun record anagrafico BMPL corrispondente ai filtri selezionati.")

            # -----------------------------------------------------------------
            # SEZIONE 2: ANALISI PERFORMANCE ARTICOLI INDISPENSABILI
            # -----------------------------------------------------------------
            with col_indisp:
                st.markdown("#### 💎 Monitoraggio Articoli Indispensabili")
                
                # Filtraggio dinamico del dataset Indispensabili Articoli
                df_ind_filtrato = df_ind.copy()
                df_ind_filtrato['Codice_Reparto'] = df_ind_filtrato.iloc[:, 2].astype(str).apply(lambda x: re.search(r'\d+', x).group() if re.search(r'\d+', x) else '')
                
                if selected_area != "--- TOTALE STORE ---" and codice_reparto_selezionato:
                    df_ind_filtrato = df_ind_filtrato[df_ind_filtrato['Codice_Reparto'] == codice_reparto_selezionato]
                elif selected_area != "--- TOTALE STORE ---":
                    df_ind_filtrato = df_ind_filtrato[df_ind_filtrato['Codice_Reparto'].isin(codici_target)]

                if not df_ind_filtrato.empty:
                    # Parsing e conversione delle colonne specifiche con la nuova logica italiana corretta
                    sales_ind_ty = parse_italian_numeric(df_ind_filtrato, 5).sum()
                    sales_ind_py = parse_italian_numeric(df_ind_filtrato, 6).sum()
                    colli_ind_ty = parse_italian_numeric(df_ind_filtrato, 7).sum()
                    colli_ind_py = parse_italian_numeric(df_ind_filtrato, 8).sum()
                    shrink_ind_ty = parse_italian_numeric(df_ind_filtrato, 11).sum()
                    shrink_ind_py = parse_italian_numeric(df_ind_filtrato, 12).sum()

                    # Calcolo degli scostamenti e delle incidenze percentuali (Sfrido su Sales)
                    delta_sales_ind = ((sales_ind_ty - sales_ind_py) / sales_ind_py * 100) if sales_ind_py > 0 else 0.0
                    delta_colli_ind = ((colli_ind_ty - colli_ind_py) / colli_ind_py * 100) if colli_ind_py > 0 else 0.0
                    
                    shrink_pct_ind_ty = (shrink_ind_ty / sales_ind_ty * 100) if sales_ind_ty > 0 else 0.0
                    shrink_pct_ind_py = (shrink_ind_py / sales_ind_py * 100) if sales_ind_py > 0 else 0.0
                    delta_shrink_ind_pp = shrink_pct_ind_ty - shrink_pct_ind_py

                    # Rendering orizzontale delle tre metriche per gli indispensabili
                    ci1, ci2, ci3 = st.columns(3)
                    ci1.metric(label="💰 Sales Indispensabili", value=fmt_valuta_interi(sales_ind_ty), delta=f"{delta_sales_ind:+.2f}% vs PY")
                    ci2.metric(label="📦 Volumi Indisp. (Colli)", value=f"{int(round(colli_ind_ty)):,}".replace(',', '.'), delta=f"{delta_colli_ind:+.2f}% vs PY")
                    ci3.metric(label="📉 Shrinkage % Indisp.", value=fmt_percentuale(shrink_pct_ind_ty), delta=f"{delta_shrink_ind_pp:+.2f} pp vs PY", delta_color="inverse")
                else:
                    st.info("ℹ️ Nessun articolo indispensabile intercettato per la selezione corrente.")

# =============================================================================
# PARTE 4.A: GRAFICI DI PERFORMANCE MACRO CATEGORIE (HORECA / SCO / TRADER)
# =============================================================================
            st.subheader("📊 Analisi e Performance Mix Categorie e Canali (Report CTG)")
            if not df_ctg.empty and not match_ctg.empty:
                c_macro_find = [c for c in match_ctg.columns if 'category' in c.lower() or 'segmento' in c.lower()]
                if c_macro_find and len(c_macro_find) > 0:
                    c_macro_name = c_macro_find[0]
                    match_ctg['Macro_Category_Clean'] = match_ctg[c_macro_name].astype(str).str.upper().apply(
                        lambda x: 'HORECA' if 'HORECA' in x else ('SCO' if 'SCO' in x else ('TRADER' if 'TRADER' in x else 'ALTRO'))
                    )
                else:
                    match_ctg['Macro_Category_Clean'] = match_ctg.iloc[:, 2].astype(str).str.upper().apply(
                        lambda x: 'HORECA' if 'HORECA' in x else ('SCO' if 'SCO' in x else ('TRADER' if 'TRADER' in x else 'ALTRO'))
                    )
                    
                df_m_g = match_ctg.groupby('Macro_Category_Clean').agg({'Sales_TY':'sum', 'Visits_TY':'sum'}).reset_index()
                
                mc1, mc2 = st.columns(2)
                with mc1: 
                    st.plotly_chart(px.bar(df_m_g, x='Macro_Category_Clean', y='Sales_TY', title="Fatturato per Macro Categoria", template='plotly_dark', color='Macro_Category_Clean'), use_container_width=True)
                with mc2: 
                    st.plotly_chart(px.pie(df_m_g, values='Visits_TY', names='Macro_Category_Clean', title="Mix Visite Segmenti", template='plotly_dark', hole=0.4), use_container_width=True)
# =============================================================================
# PARTE 4.B: PORTAFOGLIO CATEGORIE E CANALI - SEGMENTO HORECA
# =============================================================================
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.subheader("🍽️ Performance Sotto-Categorie Segmento HORECA")
                df_horeca_only = match_ctg[match_ctg['Macro_Category_Clean'] == 'HORECA'].copy()
                df_ctg_g_horeca = df_horeca_only.groupby('CTG_Label').agg({'Sales_TY': 'sum', 'Visits_TY': 'sum'}).reset_index().sort_values(by='Sales_TY', ascending=True)
                df_ctg_g_horeca = df_ctg_g_horeca[df_ctg_g_horeca['Sales_TY'] > 0]

                if not df_ctg_g_horeca.empty:
                    g1, g2 = st.columns(2)
                    with g1: 
                        st.plotly_chart(px.bar(df_ctg_g_horeca, x='Sales_TY', y='CTG_Label', orientation='h', title="Fatturato per Sotto-Categoria HORECA", template='plotly_dark', color='Sales_TY', color_continuous_scale='Blues'), use_container_width=True)
                    with g2: 
                        st.plotly_chart(px.pie(df_ctg_g_horeca, values='Visits_TY', names='CTG_Label', title="Mix Visite HORECA", template='plotly_dark', hole=0.4), use_container_width=True)
                    
                    df_ch_horeca = df_horeca_only.groupby('Channel_Label').agg({'Sales_TY': 'sum', 'Visits_TY': 'sum'}).reset_index()
                    df_ch_horeca['Scontrino_Medio'] = df_ch_horeca.apply(lambda r: r['Sales_TY']/r['Visits_TY'] if r['Visits_TY'] > 0 else 0, axis=1)
                    
                    ch1, ch2 = st.columns(2)
                    with ch1: 
                        st.plotly_chart(px.bar(df_ch_horeca, x='Channel_Label', y='Sales_TY', title="Fatturato HORECA per Canale", template="plotly_dark", color='Channel_Label'), use_container_width=True)
                    with ch2: 
                        st.plotly_chart(px.bar(df_ch_horeca, x='Channel_Label', y='Scontrino_Medio', title="Scontrino Medio HORECA (€ per Visita)", template="plotly_dark", color='Channel_Label'), use_container_width=True)
# =============================================================================
# PARTE 4.C: PORTAFOGLIO CATEGORIE E CANALI - SEGMENTO SCO
# =============================================================================
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.subheader("🏪 Performance Sotto-Categorie Segmento SCO")
                df_sco_only = match_ctg[match_ctg['Macro_Category_Clean'] == 'SCO'].copy()
                df_ctg_g_sco = df_sco_only.groupby('CTG_Label').agg({'Sales_TY': 'sum', 'Visits_TY': 'sum'}).reset_index().sort_values(by='Sales_TY', ascending=True)
                df_ctg_g_sco = df_ctg_g_sco[df_ctg_g_sco['Sales_TY'] > 0]

                if not df_ctg_g_sco.empty:
                    g1_sco, g2_sco = st.columns(2)
                    with g1_sco: 
                        st.plotly_chart(px.bar(df_ctg_g_sco, x='Sales_TY', y='CTG_Label', orientation='h', title="Fatturato per Sotto-Categoria SCO", template='plotly_dark', color='Sales_TY', color_continuous_scale='Greens'), use_container_width=True)
                    with g2_sco: 
                        st.plotly_chart(px.pie(df_ctg_g_sco, values='Visits_TY', names='CTG_Label', title="Mix Visite SCO", template='plotly_dark', hole=0.4, color_discrete_sequence=px.colors.sequential.Greens_r), use_container_width=True)
                    
                    df_ch_sco = df_sco_only.groupby('Channel_Label').agg({'Sales_TY': 'sum', 'Visits_TY': 'sum'}).reset_index()
                    df_ch_sco['Scontrino_Medio'] = df_ch_sco.apply(lambda r: r['Sales_TY']/r['Visits_TY'] if r['Visits_TY'] > 0 else 0, axis=1)
                    
                    ch1_sco, ch2_sco = st.columns(2)
                    with ch1_sco: 
                        st.plotly_chart(px.bar(df_ch_sco, x='Channel_Label', y='Sales_TY', title="Fatturato SCO per Canale", template="plotly_dark", color='Channel_Label', color_discrete_sequence=px.colors.qualitative.Set2), use_container_width=True)
                    with ch2_sco: 
                        st.plotly_chart(px.bar(df_ch_sco, x='Channel_Label', y='Scontrino_Medio', title="Scontrino Medio SCO (€ per Visita)", template="plotly_dark", color='Channel_Label', color_discrete_sequence=px.colors.qualitative.Set2), use_container_width=True)
# =============================================================================
# PARTE 4.D: PORTAFOGLIO CATEGORIE E CANALI - SEGMENTO TRADER E CHIUSURA
# =============================================================================
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.subheader("📦 Performance Sotto-Categorie Segmento TRADER")
                df_trader_only = match_ctg[match_ctg['Macro_Category_Clean'] == 'TRADER'].copy()
                df_ctg_g_trader = df_trader_only.groupby('CTG_Label').agg({'Sales_TY': 'sum', 'Visits_TY': 'sum'}).reset_index().sort_values(by='Sales_TY', ascending=True)
                df_ctg_g_trader = df_trader_only.groupby('CTG_Label').agg({'Sales_TY': 'sum', 'Visits_TY': 'sum'}).reset_index().sort_values(by='Sales_TY', ascending=True)
                df_ctg_g_trader = df_ctg_g_trader[df_ctg_g_trader['Sales_TY'] > 0]

                if not df_ctg_g_trader.empty:
                    g1_tr, g2_tr = st.columns(2)
                    with g1_tr: 
                        st.plotly_chart(px.bar(df_ctg_g_trader, x='Sales_TY', y='CTG_Label', orientation='h', title="Fatturato per Sotto-Categoria TRADER", template='plotly_dark', color='Sales_TY', color_continuous_scale='Oranges'), use_container_width=True)
                    with g2_tr: 
                        st.plotly_chart(px.pie(df_ctg_g_trader, values='Visits_TY', names='CTG_Label', title="Mix Visite TRADER", template='plotly_dark', hole=0.4, color_discrete_sequence=px.colors.sequential.Oranges_r), use_container_width=True)
                    
                    df_ch_trader = df_trader_only.groupby('Channel_Label').agg({'Sales_TY': 'sum', 'Visits_TY': 'sum'}).reset_index()
                    df_ch_trader['Scontrino_Medio'] = df_ch_trader.apply(lambda r: r['Sales_TY']/r['Visits_TY'] if r['Visits_TY'] > 0 else 0, axis=1)
                    
                    ch1_tr, ch2_tr = st.columns(2)
                    with ch1_tr: 
                        st.plotly_chart(px.bar(df_ch_trader, x='Channel_Label', y='Sales_TY', title="Fatturato TRADER per Canale", template="plotly_dark", color='Channel_Label', color_discrete_sequence=px.colors.qualitative.Pastel1), use_container_width=True)
                    with ch2_tr: 
                        st.plotly_chart(px.bar(df_ch_trader, x='Channel_Label', y='Scontrino_Medio', title="Scontrino Medio TRADER (€ per Visita)", template="plotly_dark", color='Channel_Label', color_discrete_sequence=px.colors.qualitative.Pastel1), use_container_width=True)
    else:
        st.error("Il file Mensilizzazione non ha colonne sufficienti per la mappatura gerarchica.")
        
# =============================================================================
# PARTE 5.A: FILTRI DINAMICI INTEGRALI E PUNTAMENTO COLONNE H, I, J (RISOLTO)
# =============================================================================
with tab2:
    if not df_sel.empty:
        # Pulizia e formattazione preventiva delle colonne per evitare spazi nascosti
        df_sel_clean = df_sel.copy()
        df_sel_clean.columns = df_sel_clean.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
        
        # Identificazione delle colonne chiave per indice e nome (Case Insensitive)
        c_store_name = df_sel_clean.columns[0] # La colonna Store (Colonna A)
        c_area_name = next((c for c in df_sel_clean.columns if 'area' in c.lower()), df_sel_clean.columns[1])
        c_rep_name = next((c for c in df_sel_clean.columns if 'department' in c.lower() or 'reparto' in c.lower()), df_sel_clean.columns[2])
        c_cust_name = next((c for c in df_sel_clean.columns if 'customer' in c.lower() or 'cliente' in c.lower()), df_sel_clean.columns[4])
        c_cat_name = next((c for c in df_sel_clean.columns if 'cluster' in c.lower() or 'mpro' in c.lower()), df_sel_clean.columns[5])
        c_chan_name = next((c for c in df_sel_clean.columns if 'channel' in c.lower() or 'canale' in c.lower()), df_sel_clean.columns[3])

        # IDENTIFICAZIONE DIRETTA E SICURA MEDIANTE INDICE POSIZIONALE (H=7, I=8, J=9)
        c_tipo_gestione = df_sel_clean.columns[7] # Colonna H (Tipo Gestione)
        c_venditore = df_sel_clean.columns[8]      # Colonna I (Venditore)
        c_am_om = df_sel_clean.columns[9]          # Colonna J (AM - OM)

        # FUNZIONE DI PULIZIA SPECIFICA PER CAMPI VUOTI O TRATTINI
        def clean_gestione_fields(valore):
            val_str = str(valore).strip()
            if val_str in ['', 'nan', 'NaN', 'None', '-', "'-", '- ', "'- "]:
                return "Non Gestito"
            return val_str

        # Applicazione della pulizia sui campi H, I, J
        df_sel_clean[c_tipo_gestione] = df_sel_clean[c_tipo_gestione].apply(clean_gestione_fields)
        df_sel_clean[c_venditore] = df_sel_clean[c_venditore].apply(clean_gestione_fields)
        df_sel_clean[c_am_om] = df_sel_clean[c_am_om].apply(clean_gestione_fields)

        # Mappatura della Colonna F (MPRO CL)
        df_sel_clean['Mappatura_VP'] = df_sel_clean[c_cat_name].astype(str).str.strip().str.upper().apply(
            lambda x: 'Si' if x == 'VP' else 'No'
        )

        # Estrazione degli Store reali presenti all'interno del report Free Analysis Sellout
        stores_sellout = sorted([str(x).strip() for x in df_sel_clean[c_store_name].unique() if str(x).strip() not in ['nan', 'None', '']])
        lista_store_t2 = ["STORE AREA METROPOLITANA"] + stores_sellout
        
        # Disposizione orizzontale dei selettori gerarchici in alto
        col_f1_t2, col_f2_t2, col_f3_t2, col_btn_t2 = st.columns(4)
        
        with col_btn_t2:
            st.markdown("<div style='padding-top: 24px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Reset Filtri Clienti", use_container_width=True, key="btn_reset_t2"):
                st.session_state.reset_tab2 += 1
                st.rerun()
                
        with col_f1_t2:
            selected_store_t2 = st.selectbox("Seleziona Store Cliente:", lista_store_t2, key=f"sb_store_t2_{st.session_state.reset_tab2}")
            
        # Isola lo store selezionato o mantiene l'intero dataset per l'Area Metropolitana (Totalone)
        if selected_store_t2 == "STORE AREA METROPOLITANA":
            df_filtrato_store_t2 = df_sel_clean.copy()
            label_totale_area = "--- TOTALE REGIONE ---"
        else:
            df_filtrato_store_t2 = df_sel_clean[df_sel_clean[c_store_name] == selected_store_t2]
            label_totale_area = "--- TOTALE STORE ---"
        
        # Estrazione dinamica delle Aree di Vendita associate allo store/totalone scelto
        aree_sellout = sorted([str(x).strip() for x in df_filtrato_store_t2[c_area_name].unique() if str(x).strip() not in ['nan', 'None', '']])
        lista_aree_t2 = [label_totale_area] + aree_sellout
        
        with col_f2_t2:
            selected_area_t2 = st.selectbox("Seleziona Area Clienti:", lista_aree_t2, key=f"sb_area_t2_{st.session_state.reset_tab2}")
            
        # Esplosione dei Reparti a cascata
        if selected_area_t2 not in ["--- TOTALE STORE ---", "--- TOTALE REGIONE ---"]:
            df_filtrato_area_t2 = df_filtrato_store_t2[df_filtrato_store_t2[c_area_name] == selected_area_t2]
            reparti_sellout = sorted([str(x).strip() for x in df_filtrato_area_t2[c_rep_name].unique() if str(x).strip() not in ['nan', 'None', '']])
            lista_reparti_t2 = ["--- TOTALE AREA ---"] + reparti_sellout
        else:
            df_filtrato_area_t2 = df_filtrato_store_t2.copy()
            lista_reparti_t2 = ["--- DETTAGLIO RICHIESTO ---"]
            
        with col_f3_t2:
            selected_reparto_t2 = st.selectbox("Seleziona Reparto Clienti:", lista_reparti_t2, key=f"sb_reparto_t2_{st.session_state.reset_tab2}")
            
        # Definizione del titolo della vista a schermo
        if selected_store_t2 == "STORE AREA METROPOLITANA":
            titolo_vista_t2 = "Portafoglio Clienti: STORE AREA METROPOLITANA (TUTTI)"
        else:
            titolo_vista_t2 = f"Portafoglio Clienti: {selected_store_t2}"
            
        st.markdown("---")
        st.markdown(f"### 👥 {titolo_vista_t2}")

# =============================================================================
# PARTE 5.B: ENGINE DI AGGREGAZIONE E CALCOLO METRICHE SELLOUT (TAB 2)
# =============================================================================
        match_sel = df_sel_clean.copy()
        
        # 1. Filtro Store (se non è selezionato il totalone metropolitano)
        if selected_store_t2 != "STORE AREA METROPOLITANA":
            match_sel = match_sel[match_sel[c_store_name] == selected_store_t2]
            
        # 2. Filtro Area di Vendita
        if selected_area_t2 not in ["--- TOTALE STORE ---", "--- TOTALE REGIONE ---"]:
            match_sel = match_sel[match_sel[c_area_name] == selected_area_t2]
            
        # 3. Filtro Reparto specifico
        if selected_reparto_t2 not in ["--- TOTALE AREA ---", "--- DETTAGLIO RICHIESTO ---"]:
            match_sel = match_sel[match_sel[c_rep_name] == selected_reparto_t2]
            
        if not match_sel.empty:
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

            # Parsing delle metriche contabili del Sellout
            match_sel['Sales_TY'] = parse_sellout_numeric(match_sel, 'Sales TT', 'Sales 1')
            match_sel['Sales_PY'] = parse_sellout_numeric(match_sel, 'PY Custom Cal', 'Sales per')
            match_sel['Colli_TY'] = parse_sellout_numeric(match_sel, '# Colli', 'Colli')
            match_sel['Visits_TY'] = parse_sellout_numeric(match_sel, '# Visit', 'Visit')
            match_sel['Margin_TY'] = parse_sellout_numeric(match_sel, 'Front Margin', 'Margin')
            match_sel['Margin_PY'] = parse_sellout_numeric(match_sel, 'PY Front Margin', 'Margin per')

            sel_s_tot = match_sel['Sales_TY'].sum()
            sel_s_py_tot = match_sel['Sales_PY'].sum()
            sel_v_tot = match_sel['Visits_TY'].sum()
            sel_cust_qty = match_sel[c_cust_name].nunique()
            
            sel_delta = ((sel_s_tot - sel_s_py_tot) / sel_s_py_tot * 100) if sel_s_py_tot > 0 else 0.0
            sc_medio = (sel_s_tot / sel_v_tot) if sel_v_tot > 0 else 0.0

            c_sel1, c_sel2, c_sel3, c_sel4 = st.columns(4)
            with c_sel1: st.metric(label="👥 Buying Customers Unici (Tot.)", value=f"{sel_cust_qty:,}".replace(',', '.'))
            with c_sel2: st.metric(label="💰 Totale Sales (Sellout Tot.)", value=fmt_valuta_interi(sel_s_tot), delta=f"{sel_delta:+.2f}% vs PY")
            with c_sel3: st.metric(label="🎫 Totale Visite/Scontrini (Tot.)", value=f"{int(sel_v_tot):,}".replace(',', '.'))
            with c_sel4: st.metric(label="🛒 Scontrino Medio Portafoglio (Tot.)", value=fmt_valuta_decimali(sc_medio))
            st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# PARTE 5.C.1: GRAFICI STORICI DEL TAB 2 (TARGET VP E CANALI LOGISTICI)
# =============================================================================
            sg1, sg2 = st.columns(2)
            with sg1:
                st.markdown("#### 🎯 Quota Fatturato Corrente per Target (VP = Si / Altri = No)")
                df_cat_g = match_sel.groupby('Mappatura_VP')['Sales_TY'].sum().reset_index()
                df_cat_g = df_cat_g[df_cat_g['Sales_TY'] > 0]
                st.plotly_chart(px.pie(df_cat_g, values='Sales_TY', names='Mappatura_VP', template='plotly_dark', hole=0.3, color_discrete_sequence=px.colors.qualitative.Pastel2), use_container_width=True)
                
            with sg2:
                st.markdown("#### 🏪 Incidenza Canali Logistici di Vendita (Channel Detail)")
                df_cha_g = match_sel.groupby(c_chan_name)['Sales_TY'].sum().reset_index()
                df_cha_g = df_cha_g[df_cha_g['Sales_TY'] > 0]
                st.plotly_chart(px.bar(df_cha_g, x=c_chan_name, y='Sales_TY', template='plotly_dark', color=c_chan_name, color_discrete_sequence=px.colors.qualitative.Safe), use_container_width=True)

            st.markdown("<br><br>---", unsafe_allow_html=True)
            st.markdown("### 🏆 Classifica Analitica Clienti con Dettaglio Commerciale")
# =============================================================================
# PARTE 5.C.2: SEZIONE FILTRI COMMERCIALI SPOSTATI PRIMA DELLA TABELLA
# =============================================================================
            st.markdown("##### 🛠️ Modello di Gestione Commerciale (Colonna H)")
            opzioni_gestione = ["TUTTI"] + sorted(list(match_sel[c_tipo_gestione].unique()))
            
            selected_gestione = st.segmented_control(
                "Seleziona Tipo Gestione:",
                options=opzioni_gestione,
                default="TUTTI",
                key=f"seg_gestione_{st.session_state.reset_tab2}"
            )

            df_commerciale_filtrato = match_sel.copy()
            if selected_gestione != "TUTTI":
                df_commerciale_filtrato = df_commerciale_filtrato[df_commerciale_filtrato[c_tipo_gestione] == selected_gestione]

            # FILTRAGGIO GERARCHICO INVERTITO: PRIMA AM/OM (J), POI VENDITORE (I) ASSOCIATO
            col_v1, col_v2 = st.columns(2)
            
            with col_v1:
                opzioni_amom = ["--- TUTTI GLI AM/OM ---"] + sorted(list(df_commerciale_filtrato[c_am_om].unique()))
                selected_amom = st.selectbox(
                    "1. Filtraggio per Responsabile AM - OM (Colonna J):", 
                    opzioni_amom, 
                    key=f"sb_amom_t2_{st.session_state.reset_tab2}"
                )

            # Il dataset dei venditori si restringe dinamicamente in base all'AM/OM scelto
            df_venditori_disponibili = df_commerciale_filtrato.copy()
            if selected_amom != "--- TUTTI GLI AM/OM ---":
                df_venditori_disponibili = df_venditori_disponibili[df_venditori_disponibili[c_am_om] == selected_amom]
                
            with col_v2:
                opzioni_venditori = ["--- TUTTI I VENDITORI ASSOCIATI ---"] + sorted(list(df_venditori_disponibili[c_venditore].unique()))
                selected_venditore = st.selectbox(
                    "2. Filtraggio per Venditore Associato (Colonna I):", 
                    opzioni_venditori, 
                    key=f"sb_venditore_t2_{st.session_state.reset_tab2}"
                )

            # Applicazione definitiva dei filtri a cascata per il calcolo della tabella e dei KPI inferiori
            df_final_kpi_table = df_venditori_disponibili.copy()
            if selected_venditore != "--- TUTTI I VENDITORI ASSOCIATI ---":
                df_final_kpi_table = df_final_kpi_table[df_final_kpi_table[c_venditore] == selected_venditore]
# =============================================================================
# PARTE 5.C.3: RIQUADRI RIEPILOGATIVI KPI FORMATTATI (MARGINE ESPRESSO IN %)
# =============================================================================
            st.markdown("<br>", unsafe_allow_html=True)
            if not df_final_kpi_table.empty:
                kpi_sales_ty = float(df_final_kpi_table['Sales_TY'].sum())
                kpi_sales_py = float(df_final_kpi_table['Sales_PY'].sum())
                kpi_colli_ty = float(df_final_kpi_table['Colli_TY'].sum())
                kpi_colli_py = float(df_final_kpi_table['Sales_PY'].sum() / (kpi_sales_ty / kpi_colli_ty if kpi_colli_ty > 0 else 1.0))
                kpi_margin_ty = float(df_final_kpi_table['Margin_TY'].sum())
                kpi_margin_py = float(df_final_kpi_table['Margin_PY'].sum())
                
                delta_sales_kpi = ((kpi_sales_ty - kpi_sales_py) / kpi_sales_py * 100) if kpi_sales_py > 0 else 0.0
                delta_colli_kpi = ((kpi_colli_ty - kpi_colli_py) / kpi_colli_py * 100) if kpi_colli_py > 0 else 0.0
                
                margin_pct_ty = (kpi_margin_ty / kpi_sales_ty * 100) if kpi_sales_ty > 0 else 0.0
                margin_pct_py = (kpi_margin_py / kpi_sales_py * 100) if kpi_sales_py > 0 else 0.0
                delta_margin_kpi_pp = margin_pct_ty - margin_pct_py
                
                st.markdown("""
                    <style>
                        div[data-testid="stMetricValue"] { font-size: 21px !important; }
                        div[data-testid="stMetricLabel"] p { font-size: 13px !important; white-space: nowrap !important; }
                    </style>
                """, unsafe_allow_html=True)

                st.markdown("##### 📊 Sintesi Performance Selezione Commerciale Corrente")
                c_kpi1, c_kpi2, c_kpi3 = st.columns(3)
                
                c_kpi1.metric(
                    label="💰 Sales (Fatturato TY)", 
                    value=fmt_valuta_interi(kpi_sales_ty), 
                    delta=f"{delta_sales_kpi:+.2f}% vs PY"
                )
                c_kpi2.metric(
                    label="📦 Volume TY (Colli)", 
                    value=f"{int(round(kpi_colli_ty)):,}".replace(',', '.'), 
                    delta=f"{delta_colli_kpi:+.2f}% vs PY" if kpi_colli_py > 0 else None
                )
                c_kpi3.metric(
                    label="📈 Front Margin % (Income)", 
                    value=fmt_percentuale(margin_pct_ty), 
                    delta=f"{delta_margin_kpi_pp:+.2f} pp vs PY"
                )
                st.markdown("<br>", unsafe_allow_html=True)
# =============================================================================
# PARTE 5.C.4: NUOVA SEZIONE GRAFICA: ISTOGRAMMA AM/OM (TOP 10 CON VALORI) E TORTA GESTIONE
# =============================================================================
                g_comm1, g_comm2 = st.columns(2)
                
                with g_comm1:
                    st.markdown("##### 📊 Top 10 Sales per Responsabile AM / OM")
                    # Raggruppamento e selezione rigorosa dei primi 10 nominativi per fatturato decrescente
                    df_sales_amom = df_final_kpi_table.groupby(c_am_om)['Sales_TY'].sum().reset_index()
                    df_sales_amom = df_sales_amom[df_sales_amom['Sales_TY'] > 0]
                    df_sales_amom = df_sales_amom.sort_values(by='Sales_TY', ascending=False).head(10)
                    df_sales_amom = df_sales_amom.sort_values(by='Sales_TY', ascending=True) # Per mostrare il più alto in cima nel grafico orizzontale
                    
                    fig_bar_amom = px.bar(
                        df_sales_amom, 
                        x='Sales_TY', 
                        y=c_am_om, 
                        orientation='h',
                        template='plotly_dark',
                        color='Sales_TY',
                        color_continuous_scale='Purples',
                        text_auto='.2s', # Mostra automaticamente i valori sulle barre formattati in modo compatto (es. 1.2M, 450k)
                        labels={'Sales_TY': 'Fatturato Corrente (€)', c_am_om: 'Responsabile AM/OM'}
                    )
                    fig_bar_amom.update_layout(coloraxis_showscale=False)
                    fig_bar_amom.update_traces(textposition='outside') # Posiziona il testo all'esterno delle barre per miglior leggibilità
                    st.plotly_chart(fig_bar_amom, use_container_width=True)
                    
                with g_comm2:
                    st.markdown("##### 🍕 Mix Fatturato per Modello Gestione Commerciale")
                    df_sales_gest = df_final_kpi_table.groupby(c_tipo_gestione)['Sales_TY'].sum().reset_index()
                    df_sales_gest = df_sales_gest[df_sales_gest['Sales_TY'] > 0]
                    fig_pie_gest = px.pie(
                        df_sales_gest, 
                        values='Sales_TY', 
                        names=c_tipo_gestione, 
                        template='plotly_dark', 
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    st.plotly_chart(fig_pie_gest, use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
# =============================================================================
# PARTE 5.C.5: RENDERING TABELLA, SELEZIONE E DETTAGLIO GRAFICO CON BENCHMARK PY (RISOLTO)
# =============================================================================
            if not df_final_kpi_table.empty:
                # 1. Calcolo del dataset aggregato base per anagrafica
                df_c_g = df_final_kpi_table.groupby([c_cust_name, c_tipo_gestione, c_venditore, c_am_om, 'Mappatura_VP']).agg({
                    'Sales_TY': 'sum', 'Sales_PY': 'sum', 'Colli_TY': 'sum', 'Margin_TY': 'sum'
                }).reset_index()
                
                df_c_g['Scostamento_vs_PY'] = df_c_g['Sales_TY'] - df_c_g['Sales_PY']
                df_c_g['Margin_Pct'] = df_c_g.apply(lambda r: (r['Margin_TY'] / r['Sales_TY'] * 100) if r['Sales_TY'] > 0 else 0.0, axis=1)
                df_c_g = df_c_g.sort_values(by='Sales_TY', ascending=False).reset_index(drop=True)
                
                # 2. INSERIMENTO DELLA RICERCA RAPIDA TESTUALE PRIMA DELLA TABELLA
                st.markdown("##### 🔍 Ricerca Rapida Anagrafica Clienti")
                search_query = st.text_input(
                    "Digita il Codice Cliente o la Ragione Sociale per filtrare la tabella sottostante:",
                    placeholder="Es. 11-711160 oppure LA PAELLA...",
                    key=f"search_input_t2_{st.session_state.reset_tab2}"
                ).strip().lower()
                
                # Applicazione immediata del filtro digitato dall'utente
                if search_query:
                    df_c_g = df_c_g[df_c_g[c_cust_name].astype(str).str.lower().str.contains(search_query, regex=False)]
                
                # 3. Conversione estetica con le funzioni di formattazione locale
                if not df_c_g.empty:
                    df_c_v = df_c_g.copy()
                    df_c_v['Sales_TY'] = df_c_v['Sales_TY'].apply(fmt_valuta_decimali)
                    df_c_v['Sales_PY'] = df_c_v['Sales_PY'].apply(fmt_valuta_decimali)
                    df_c_v['Scostamento_vs_PY'] = df_c_v['Scostamento_vs_PY'].apply(lambda x: f"+{fmt_valuta_decimali(x)}" if x > 0 else fmt_valuta_decimali(x))
                    df_c_v['Margin_Pct'] = df_c_v['Margin_Pct'].apply(fmt_percentuale)
                    df_c_v['Colli_TY'] = df_c_v['Colli_TY'].apply(lambda x: f"{int(round(x)):,}".replace(',', '.'))
                    
                    df_c_v.columns = ['Ragione Sociale / Cliente', 'Tipo Gestione (H)', 'Venditore Riferimento (I)', 'Responsabile AM-OM (J)', 'Target VP', 'Fatturato TY (Sales)', 'Fatturato PY', 'Volume TY (Colli)', 'Margine € (Income Omissis)', 'Delta vs PY', 'Margine % (Income)']
                    
                    colonne_output = [
                        'Ragione Sociale / Cliente', 'Fatturato TY (Sales)', 'Volume TY (Colli)', 'Margine % (Income)', 
                        'Tipo Gestione (H)', 'Responsabile AM-OM (J)', 'Venditore Riferimento (I)', 'Delta vs PY'
                    ]
                    
                    st.markdown("👉 *Clicca sulla riga di un cliente nella tabella per visualizzare l'approfondimento dei suoi acquisti in basso.*")
                    selection = st.dataframe(
                        df_c_v[colonne_output], 
                        use_container_width=True, 
                        hide_index=False,
                        on_select="rerun",
                        selection_mode="single-row"
                    )
                    
                    # 4. LOGICA DI RENDERING DETTAGLIO CON PUNTARE ESTRATTO COME STRINGA PURA
                    if selection and len(selection.get("selection", {}).get("rows", [])) > 0:
                        selected_row_idx = selection["selection"]["rows"][0]
                        # Estrazione pulita del valore stringa nativo evitando Series con indici disallineati
                        cliente_selezionato = str(df_c_g.iloc[selected_row_idx][c_cust_name]).strip()
                        
                        st.markdown(f"### 📈 Dettaglio Acquisti e Confronto Storico Cliente: {cliente_selezionato}")
                        
                        # Il confronto tramite stringa ora non genera più il KeyError / ValueError
                        df_singolo_cliente = df_final_kpi_table[df_final_kpi_table[c_cust_name].astype(str).str.strip() == cliente_selezionato].copy()
                        
                        col_det1, col_det2 = st.columns(2)
                        
                        with col_det1:
                            st.markdown("##### 📦 Distribuzione Fatturato per Reparto (TY vs PY)")
                            df_rep_dettaglio = df_singolo_cliente.groupby(c_rep_name).agg({
                                'Sales_TY': 'sum',
                                'Sales_PY': 'sum'
                            }).reset_index()
                            
                            df_rep_dettaglio = df_rep_dettaglio[(df_rep_dettaglio['Sales_TY'] > 0) | (df_rep_dettaglio['Sales_PY'] > 0)]
                            df_rep_dettaglio = df_rep_dettaglio.sort_values(by='Sales_TY', ascending=True)
                            
                            if not df_rep_dettaglio.empty:
                                df_rep_melt = df_rep_dettaglio.melt(
                                    id_vars=[c_rep_name], 
                                    value_vars=['Sales_TY', 'Sales_PY'],
                                    var_name='Anno', 
                                    value_name='Fatturato (€)'
                                )
                                df_rep_melt['Anno'] = df_rep_melt['Anno'].map({'Sales_TY': 'TY Corrente', 'Sales_PY': 'PY Precedente'})
                                
                                fig_rep_det = px.bar(
                                    df_rep_melt,
                                    x='Fatturato (€)',
                                    y=c_rep_name,
                                    color='Anno',
                                    barmode='group',
                                    orientation='h',
                                    template='plotly_dark',
                                    color_discrete_map={'TY Corrente': '#1f77b4', 'PY Precedente': '#7f7f7f'},
                                    text_auto='.2s',
                                    labels={'Fatturato (€)': 'Sales (€)', c_rep_name: 'Reparto', 'Anno': 'Periodo'}
                                )
                                fig_rep_det.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                                fig_rep_det.update_traces(textposition='outside')
                                st.plotly_chart(fig_rep_det, use_container_width=True)
                            else:
                                st.caption("Nessun dato storico commerciale sui reparti per il cliente corrente.")
                                
                        with col_det2:
                            st.markdown("##### 🏪 Confronto Acquisti per Canale Logistico (TY vs PY)")
                            df_chan_dettaglio = df_singolo_cliente.groupby(c_chan_name).agg({
                                'Sales_TY': 'sum',
                                'Sales_PY': 'sum'
                            }).reset_index()
                            
                            df_chan_dettaglio = df_chan_dettaglio[(df_chan_dettaglio['Sales_TY'] > 0) | (df_chan_dettaglio['Sales_PY'] > 0)]
                            df_chan_dettaglio = df_chan_dettaglio.sort_values(by='Sales_TY', ascending=False)
                            
                            if not df_chan_dettaglio.empty:
                                df_chan_melt = df_chan_dettaglio.melt(
                                    id_vars=[c_chan_name], 
                                    value_vars=['Sales_TY', 'Sales_PY'],
                                    var_name='Anno', 
                                    value_name='Fatturato (€)'
                                )
                                df_chan_melt['Anno'] = df_chan_melt['Anno'].map({'Sales_TY': 'TY Corrente', 'Sales_PY': 'PY Precedente'})
                                
                                fig_chan_det = px.bar(
                                    df_chan_melt,
                                    x=c_chan_name,
                                    y='Fatturato (€)',
                                    color='Anno',
                                    barmode='group',
                                    template='plotly_dark',
                                    color_discrete_map={'TY Corrente': '#9467bd', 'PY Precedente': '#bcbd22'},
                                    text_auto='.2s',
                                    labels={'Fatturato (€)': 'Sales (€)', c_chan_name: 'Canale Logistico (Channel Detail)', 'Anno': 'Periodo'}
                                )
                                fig_chan_det.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                                fig_chan_det.update_traces(textposition='outside')
                                st.plotly_chart(fig_chan_det, use_container_width=True)
                            else:
                                st.caption("Nessun dato storico commerciale sui canali per il cliente corrente.")
                    else:
                        st.info("💡 Seleziona un cliente cliccando sulla casella a sinistra nella tabella per sbloccare i grafici di dettaglio comparativi TY vs PY.")
                else:
                    st.info("ℹ️ Nessun cliente corrisponde ai criteri di ricerca digitati.")
            else:
                st.caption("⚠️ Nessun record risponde alla combinazione di filtri commerciali selezionata.")
