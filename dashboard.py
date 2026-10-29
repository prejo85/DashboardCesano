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

# Inizializzazione controllata dei dataframe (Eseguita una sola volta)
df_rep, df_ctg, df_sel, df_ind, df_men = load_and_clean_data(u_rep, u_ctg, u_sel, u_ind, u_men)
# =============================================================================
# 5. FILTRI GERARCHICI IN ALTO CON LOGICA DI RESET IN SESSION STATE
# =============================================================================
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
# TAB 1: VISUALIZZAZIONE DELLE VISTE GENERALI E CROSS-REPORT SINK
# =============================================================================
with tab1:
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

        margin_on_sales = (margin_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        shrink_on_sales = (shrink_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        margin_on_sales_py = (margin_py_tot / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
        shrink_on_sales_py = (shrink_py_tot / sales_py_tot * 100) if sales_py_tot != 0 else 0.0

        delta_sales_pct = ((sales_tot - sales_py_tot) / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
        delta_margin_pp = margin_on_sales - margin_on_sales_py
        delta_shrink_pp = shrink_on_sales - shrink_on_sales_py

        df_giornaliero = df_calc.groupby(df_calc.iloc[:, 0]).agg({
            'Stock_TY_Num': 'sum', 'Sales_TY_Num': 'sum', 'Sales_PY_Num': 'sum'
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

        st.markdown("#### 📊 Indicatori Chiave di Performance")
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1: st.metric(label="💰 Sales TT", value=fmt_valuta_interi(sales_tot), delta=f"{delta_sales_pct:+.2f}% vs PY")
        with m2: st.metric(label="📈 Front Margin %", value=fmt_percentuale(margin_on_sales), delta=f"{delta_margin_pp:+.2f} pp vs PY")
        with m3: st.metric(label="📦 Stock Days", value=fmt_giorni(val_stock_days), delta=f"{delta_stock_pct:+.2f}% vs PY", delta_color="inverse")
        with m4: st.metric(label="🏬 Avg Stock Last Day", value=fmt_valuta_interi(val_avg_stock_ultimo_giorno), delta=None)
        with m5: st.metric(label="📉 Shrinkage (Sfrido)", value=fmt_percentuale(shrink_on_sales), delta=f"{delta_shrink_pp:+.2f} pp vs PY", delta_color="inverse")
        st.markdown("<br>---", unsafe_allow_html=True)
        st.subheader("📊 Analisi e Performance Mix Categorie e Canali (Report CTG)")

        if not df_ctg.empty:
            df_ctg_clean = df_ctg.copy()
            df_ctg_clean['Codice_Reparto_CTG'] = df_ctg_clean.iloc[:, 1].astype(str).apply(
                lambda x: re.search(r'\d+', str(x)).group() if re.search(r'\d+', str(x)) else ''
            )
            
            if selected_area != "--- TOTALE STORE ---" or (selected_reparto != "--- DETTAGLIO RICHIESTO ---" and selected_reparto != "--- TOTALE AREA ---"):
                match_ctg = df_ctg_clean[df_ctg_clean['Codice_Reparto_CTG'].isin(codici_target)].copy()
            else:
                match_ctg = df_ctg_clean.copy()
            
            if not match_ctg.empty:
                # CORREZIONE CHIRURGICA: Rimuove i punti prima di sommare le celle
                def parse_ctg_columns_fixed(dataframe, col_index):
                    if len(dataframe.columns) > col_index:
                        s = dataframe.iloc[:, col_index].astype(str).str.replace(r'\s+', '', regex=True)
                        s = s.replace(['-', '--', 'nan', 'NaN', 'None', ''], '0')
                        s = s.str.replace('.', '', regex=False)
                        s = s.str.replace(',', '.', regex=False)
                        return pd.to_numeric(s, errors='coerce').fillna(0.0)
                    return pd.Series(0.0, index=dataframe.index)

                match_ctg['Sales_TY'] = parse_ctg_columns_fixed(match_ctg, 7)
                match_ctg['Sales_PY'] = parse_ctg_columns_fixed(match_ctg, 8)
                match_ctg['Visits_TY'] = parse_ctg_columns_fixed(match_ctg, 11)
                match_ctg['Sales_Per_Visit'] = parse_ctg_columns_fixed(match_ctg, 13)
                
                match_ctg['CTG_Label'] = match_ctg['CTG'].astype(str).str.strip().str.replace("'", "", regex=False).replace(['nan', 'None', ''], '-')
                match_ctg['Channel_Label'] = match_ctg['Channel Detail'].astype(str).str.strip()

                df_ctg_grouped = match_ctg.groupby('CTG_Label').agg({'Sales_TY': 'sum', 'Sales_PY': 'sum', 'Visits_TY': 'sum'}).reset_index()
                df_ctg_grouped = df_ctg_grouped.sort_values(by='Sales_TY', ascending=True)
                df_ctg_grouped = df_ctg_grouped[df_ctg_grouped['Sales_TY'] > 0]

                if not df_ctg_grouped.empty:
                    g1, g2 = st.columns(2)
                    with g1:
                        st.markdown("#### 💰 Volume di Fatturato per Categoria (Sales TT)")
                        fig_sales = px.bar(df_ctg_grouped, x='Sales_TY', y='CTG_Label', orientation='h', labels={'Sales_TY': 'Fatturato Corrente (€)', 'CTG_Label': 'Categoria CTG'}, template='plotly_dark', color='Sales_TY', color_continuous_scale='Blues')
                        fig_sales.update_layout(showlegend=False, coloraxis_showscale=False, height=450, margin=dict(l=20, r=20, t=20, b=20))
                        fig_sales.update_traces(hovertemplate="<b>%{y}</b><br>Fatturato: € %{x:,.0f}<extra></extra>".replace(',', '.'))
                        st.plotly_chart(fig_sales, use_container_width=True)
                    with g2:
                        st.markdown("#### 👥 Frequenza e Mix dei Volumi delle Visite")
                        fig_visits = px.pie(df_ctg_grouped, values='Visits_TY', names='CTG_Label', template='plotly_dark', hole=0.4)
                        fig_visits.update_layout(height=450, margin=dict(l=20, r=20, t=20, b=20))
                        fig_visits.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>%{label}</b><br>Visite: %{value:,.0f}<br>Incidenza: %{percent}<extra></extra>".replace(',', '.'))
                        st.plotly_chart(fig_visits, use_container_width=True)

                    st.markdown("<br>#### 🏪 Performance Distribuzione per Canale e Scontrino Medio", unsafe_allow_html=True)
                    df_channel_grouped = match_ctg.groupby('Channel_Label').agg({'Sales_TY': 'sum', 'Visits_TY': 'sum'}).reset_index()
                    df_channel_grouped['Scontrino_Medio'] = df_channel_grouped.apply(lambda r: r['Sales_TY']/r['Visits_TY'] if r['Visits_TY'] > 0 else 0, axis=1)
                    
                    ch1, ch2 = st.columns(2)
                    with ch1:
                        fig_ch_sales = px.bar(df_channel_grouped, x='Channel_Label', y='Sales_TY', title="Fatturato per Canale", template="plotly_dark", color='Channel_Label')
                        st.plotly_chart(fig_ch_sales, use_container_width=True)
                    with ch2:
                        fig_ch_avg = px.bar(df_channel_grouped, x='Channel_Label', y='Scontrino_Medio', title="Scontrino Medio (€ per Visita)", template="plotly_dark", color='Channel_Label')
                        st.plotly_chart(fig_ch_avg, use_container_width=True)

# =============================================================================
# SCHEDA 2: ANALISI PORTAFOGLIO FORZA VENDITE E CLIENTI
# =============================================================================
with tab2:
    st.header("👥 Analisi Profilazione e Portafoglio Clienti (Sellout)")
    if not df_sel.empty:
        col_s1, col_f_cust, col_s2 = st.columns(3)
        with col_s1: tipo_gestione = st.multiselect("Filtra per Tipo Gestione:", options=sorted(df_sel["Tipo Gestione"].dropna().unique()) if "Tipo Gestione" in df_sel.columns else [])
        with col_f_cust: ricerca_cliente = st.text_input("🔍 Cerca Ragione Sociale o Codice Cliente Contabile:")
        with col_s2: mpro_club = st.multiselect("Filtra per Stato MPRO Club:", options=sorted(df_sel["MPRO Club"].dropna().unique()) if "MPRO Club" in df_sel.columns else [])

        df_sel_filtrato = df_sel.copy()
        if tipo_gestione and "Tipo Gestione" in df_sel.columns: df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["Tipo Gestione"].isin(tipo_gestione)]
        if mpro_club and "MPRO Club" in df_sel.columns: df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["MPRO Club"].isin(mpro_club)]
        if ricerca_cliente and "Customer" in df_sel.columns: df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["Customer"].astype(str).str.contains(ricerca_cliente, case=False, na=False)]

        def parse_sellout_col(series):
            s = series.astype(str).str.replace(r'\s+', '', regex=True).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            return pd.to_numeric(s, errors='coerce').fillna(0.0)

        sellout_sales_tot = float(parse_sellout_col(df_sel_filtrato["Sales TT"]).sum()) if "Sales TT" in df_sel_filtrato.columns else 0.0
        sellout_margin_tot = float(parse_sellout_col(df_sel_filtrato["Front Margin"]).sum()) if "Front Margin" in df_sel_filtrato.columns else 0.0
        sellout_visits_tot = float(parse_sellout_col(df_sel_filtrato["# Visit"]).sum()) if "# Visit" in df_sel_filtrato.columns else 0.0
        sellout_margin_pct = (sellout_margin_tot / sellout_sales_tot * 100) if sellout_sales_tot != 0 else 0.0

        st.markdown("##### 📊 Indicatori Chiave del Portafoglio Selezionato")
        ms1, ms2, ms3 = st.columns(3)
        with ms1: st.metric(label="💼 Fatturato Portafoglio (Sellout)", value=fmt_valuta_interi(sellout_sales_tot))
        with ms2: st.metric(label="🎯 Front Margin % Realizzato", value=fmt_percentuale(sellout_margin_pct))
        with ms3: st.metric(label="👣 Volume Totale Visite", value=f"{int(sellout_visits_tot):,}".replace(',', '.'))

        st.markdown("<br>### 📋 Elenco Analitico Clienti (Ordinati per Fatturato Decrescente)", unsafe_allow_html=True)
        raggruppamento_cols = [c for c in ["Customer", "Customer Category", "Venditore", "MPRO Club"] if c in df_sel_filtrato.columns]
        if raggruppamento_cols:
            agg_dict = {"Sales TT": "sum"}
            if "Front Margin" in df_sel_filtrato.columns: agg_dict["Front Margin"] = "sum"
            if "# Visit" in df_sel_filtrato.columns: agg_dict["# Visit"] = "sum"
            df_customer_pivoted = df_sel_filtrato.groupby(raggruppamento_cols).agg(agg_dict).reset_index().sort_values(by="Sales TT", ascending=False)
            df_customer_pivoted["Sales TT"] = df_customer_pivoted["Sales TT"].map(fmt_valuta_interi)
            if "Front Margin" in df_customer_pivoted.columns: df_customer_pivoted["Front Margin"] = df_customer_pivoted["Front Margin"].map(fmt_valuta_decimali)
            if "# Visit" in df_customer_pivoted.columns: df_customer_pivoted["# Visit"] = df_customer_pivoted["# Visit"].map('{:,.0f}'.format)
            st.dataframe(df_customer_pivoted, use_container_width=True, hide_index=True)
