import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# 1. CONFIGURAZIONE DELLA PAGINA E TITOLO PRINCIPALE
st.set_page_config(page_title="Dashboard Commerciale Avanzata", layout="wide", page_icon="📊")

st.title("📊 Dashboard Commerciale Integrata")
st.markdown("### Analisi Multilivello: Store, Aree, Reparti e Segmentazione Clienti")

# 2. ENGINE CENTRALIZZATO DI CARICAMENTO AUTOMATICO DA REPOSITORY GITHUB
@st.cache_data
def load_and_clean_data(file_reparti, file_ctg, file_sellout, file_indispensabili, file_mensile):
    def clean_df(file_path):
        if not os.path.exists(file_path):
            return pd.DataFrame()
        try:
            df = pd.read_csv(file_path, sep=";", skiprows=0, skip_blank_lines=True)
            if len(df.columns) <= 1:
                df = pd.read_csv(file_path, sep=",", skiprows=0, skip_blank_lines=True)
        except:
            df = pd.read_csv(file_path, sep=",", skiprows=0, skip_blank_lines=True)
        df.columns = df.columns.str.strip()
        df = df[df.iloc[:, 0].notna()]
        return df

    def parse_numeric(series):
        series_clean = series.astype(str).str.replace(r'\s+', '', regex=True)
        series_clean = series_clean.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        series_clean = series_clean.replace(['-', '--', 'nan', 'NaN', ''], '0')
        return pd.to_numeric(series_clean, errors='coerce').fillna(0.0)

    df_rep = clean_df(file_reparti)
    df_ctg = clean_df(file_ctg)
    df_sel = clean_df(file_sellout)
    df_ind = clean_df(file_indispensabili)
    df_men = clean_df(file_mensile)

    colonne_valori = ["sales", "margin", "colli", "visite", "visit", "stock", "shrinkage", "sfrido", "accrediti"]

    for df_target in [df_rep, df_ctg, df_sel, df_ind, df_men]:
        if df_target.empty:
            continue
        for col in df_target.columns:
            # Riconoscimento automatico e conversione delle colonne numeriche
            if any(k in col.lower() for k in colonne_valori) and not any(x in col.lower() for x in ["customer", "venditore", "gestione", "club", "department", "reparto", "detail", "category", "ctg", "flag", "store", "area", "article"]):
                df_target[col] = parse_numeric(df_target[col])

    return df_rep, df_ctg, df_sel, df_ind, df_men

# Mappatura dei file attesi all'interno del repository GitHub
FILE_REPARTI = "reparti.csv"
FILE_CTG = "canali_ctg.csv"
FILE_SELLOUT = "free_analysis.csv"  # Il file Free Analysis Sellout commerciale
FILE_INDISPENSABILI = "indispensabili.csv"
FILE_MENSILE = "mensilizzazione.csv"

# Verifica iniziale dei file necessari
controllo_file = [FILE_REPARTI, FILE_CTG, FILE_SELLOUT, FILE_INDISPENSABILI, FILE_MENSILE]
file_mancanti = [f for f in controllo_file if not os.path.exists(f)]

if file_mancanti:
    st.error(f"⚠️ Attenzione! Impossibile avviare la dashboard. Mancano i seguenti file nel repository: {', '.join(file_mancanti)}")
    st.info("💡 Carica questi file direttamente su GitHub mantenendo esattamente i nomi indicati sopra.")
    st.stop()

# Caricamento centralizzato in cache dei dati
df_rep, df_ctg, df_sel, df_ind, df_men = load_and_clean_data(FILE_REPARTI, FILE_CTG, FILE_SELLOUT, FILE_INDISPENSABILI, FILE_MENSILE)

# Creazione delle schede separate per isolare la parte commerciale
tab1, tab2 = st.tabs(["🏬 Vista Store e Performance Reparti", "👥 Analisi Profilazione Clienti (Sellout FASO)"])
# MOTORE GRAFICO DI GENERAZIONE DELLE KPI CARD AD ALTA LEGGIBILITÀ
def get_modern_kpi_card(icon, label, value_str, delta_val, py_info_str="", is_positive_good=True, show_delta=True):
    is_positive = delta_val >= 0
    if not is_positive_good:
        is_positive = not is_positive
        
    bg_badge = "#23c45e" if is_positive else "#ef4444"
    icon_color = "#3b82f6" if is_positive_good else "#f59e0b"
    
    badge_html = f"""
    <div style="background-color: {bg_badge}; color: #ffffff; padding: 3px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; display: inline-block; width: fit-content; text-align: center;">
        {delta_val:+.2f}% vs PY
    </div>
    """ if show_delta else ""

    py_html = f'<span style="color: #718096; font-size: 0.75rem; font-weight: 500; margin-top: 2px;">{py_info_str}</span>' if py_info_str else ""

    return f"""
    <div style="background: linear-gradient(135deg, #1e2530 0%, #161b24 100%); padding: 20px; border-radius: 12px; border: 1px solid #2d3748; box-shadow: 0 4px 15px rgba(0,0,0,0.3); min-height: 155px; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 15px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #a0aec0; font-size: 0.85rem; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">{label}</span>
            <span style="font-size: 1.3rem; color: {icon_color};">{icon}</span>
        </div>
        <div style="margin: 6px 0;">
            <h2 style="font-size: 1.85rem; font-weight: 800; color: #ffffff; margin: 0; letter-spacing: -0.5px;">{value_str}</h2>
        </div>
        <div style="display: flex; flex-direction: column; gap: 2px;">
            {badge_html}
            {py_html}
        </div>
    </div>
    """

# =============================================================================
# SCHEDA 1: PERFORMANCE STRUTTURA STORE, AREE E REPARTI (Dati aggregati)
# =============================================================================
with tab1:
    st.header("🏬 Monitoraggio Gerarchico Store & Performance Mix")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        lista_store = sorted(df_men["Store"].unique()) if "Store" in df_men.columns else []
        selected_store = st.selectbox("Seleziona Store:", lista_store)
    with col_f2:
        df_filtrato_store = df_men[df_men["Store"] == selected_store] if "Store" in df_men.columns else df_men.copy()
        lista_aree = ["--- TOTALE STORE ---"] + sorted(df_filtrato_store["Sales Area Deparment"].unique()) if "Sales Area Deparment" in df_filtrato_store.columns else ["--- TOTALE STORE ---"]
        selected_area = st.selectbox("Seleziona Area di Vendita:", lista_aree)
    with col_f3:
        if selected_area != "--- TOTALE STORE ---" and "Sales Area Deparment" in df_filtrato_store.columns:
            df_filtrato_area = df_filtrato_store[df_filtrato_store["Sales Area Deparment"] == selected_area]
            lista_reparti = ["--- TOTALE AREA ---"] + sorted(df_filtrato_area["Sales Department"].unique()) if "Sales Department" in df_filtrato_area.columns else ["--- TOTALE AREA ---"]
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
        dati_vista = df_filtrato_area[df_filtrato_area["Sales Department"] == selected_reparto] if "Sales Department" in df_filtrato_area.columns else pd.DataFrame()
        titolo_vista = f"Visualizzazione REPARTO: {selected_reparto} ({selected_store})"

    if not dati_vista.empty:
        st.markdown(f"### 🎯 {titolo_vista}")
        
        sales_tot = float(dati_vista['DA - Sales TT'].sum())
        sales_py_tot = float(dati_vista['DA - Sales TT PY Custom Cal'].sum())
        margin_tot = float(dati_vista['DA - Front Margin'].sum())
        margin_py_tot = float(dati_vista['DA - Front Margin PY Custom Cal'].sum())
        shrink_tot = float(dati_vista['DA - Shrinkage NNBP'].sum())
        shrink_py_tot = float(dati_vista['DA - Shrinkage NNBP PY Custom Cal'].sum()) if 'DA - Shrinkage NNBP PY Custom Cal' in dati_vista.columns else 0.0
        
        val_stock_days = float(dati_vista['DA - Stock Days'].mean())
        val_stock_days_py = float(dati_vista['DA - Stock Days PY Custom Cal'].mean())
        avg_stock_tot = float(dati_vista['DA - Avg Stock'].sum())
        
        margin_on_sales = (margin_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        shrink_on_sales = (shrink_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        
        delta_sales_pct = ((sales_tot - sales_py_tot) / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
        delta_margin_pct = ((margin_tot - margin_py_tot) / margin_py_tot * 100) if margin_py_tot != 0 else 0.0
        delta_stock_pct = ((val_stock_days - val_stock_days_py) / val_stock_days_py * 100) if val_stock_days_py != 0 else 0.0
        delta_shrink_pct = ((shrink_tot - shrink_py_tot) / shrink_py_tot * 100) if shrink_py_tot != 0 else 0.0

        reparti_inclusi = dati_vista["Sales Department"].dropna().unique() if "Sales Department" in dati_vista.columns else []
        lista_codici_target = [str(r)[:3].strip() for r in reparti_inclusi if pd.notna(r)]

        col_rep_ctg_check = [c for c in df_ctg.columns if 'department' in c.lower() or 'reparto' in c.lower()]
        if col_rep_ctg_check:
            col_ctg_singola = col_rep_ctg_check[0]
            dati_ctg_macro = df_ctg[df_ctg[col_ctg_singola].astype(str).str[:3].str.strip().isin(lista_codici_target)]
        else:
            dati_ctg_macro = pd.DataFrame()
            
        if not dati_ctg_macro.empty:
            ctg_sales = float(dati_ctg_macro['Sales TT'].sum()) if 'Sales TT' in dati_ctg_macro.columns else 0.0
            ctg_sales_py = float(dati_ctg_macro['Sales TT PY Custom Cal'].sum()) if 'Sales TT PY Custom Cal' in dati_ctg_macro.columns else 0.0
            accrediti_tot = float(dati_ctg_macro['Accrediti'].sum()) if 'Accrediti' in dati_ctg_macro.columns else 0.0
            accrediti_py_tot = float(dati_ctg_macro['Accrediti PY Custom Cal'].sum()) if 'Accrediti PY Custom Cal' in dati_ctg_macro.columns else 0.0
            
            if accrediti_tot > 0: accrediti_tot = -accrediti_tot
            if accrediti_py_tot > 0: accrediti_py_tot = -accrediti_py_tot
            accrediti_pct = (accrediti_tot / ctg_sales * 100) if ctg_sales != 0 else 0.0
            accrediti_py_pct = (accrediti_py_tot / ctg_sales_py * 100) if ctg_sales_py != 0 else 0.0
            delta_accrediti_pct = accrediti_pct - accrediti_py_pct
            
            col_flag_hvs = [c for c in dati_ctg_macro.columns if 'hvs' in c.lower()]
            if col_flag_hvs:
                col_hvs_singola = col_flag_hvs[0]
                hvs_pulito = dati_ctg_macro[col_hvs_singola].astype(str).str.upper().str.replace(r'\s+', '', regex=True)
                match_hvs = dati_ctg_macro[hvs_pulito == 'HVS']
                hvs_sales_tot = float(match_hvs['Sales TT'].sum()) if 'Sales TT' in match_hvs.columns else 0.0
                hvs_sales_py = float(match_hvs['Sales TT PY Custom Cal'].sum()) if 'Sales TT PY Custom Cal' in match_hvs.columns else 0.0
                delta_hvs_pct = ((hvs_sales_tot - hvs_sales_py) / hvs_sales_py * 100) if hvs_sales_py != 0 else 0.0
            else:
                hvs_sales_tot, hvs_sales_py, delta_hvs_pct = 0.0, 0.0, 0.0
        else:
            accrediti_pct, delta_accrediti_pct, accrediti_py_pct = 0.0, 0.0, 0.0
            hvs_sales_tot, hvs_sales_py, delta_hvs_pct = 0.0, 0.0, 0.0

        # RENDERING GRAFICO CARD RIGA 1 & RIGA 2
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(get_modern_kpi_card("💰", "Sales TT", f"€ {sales_tot:,.2f}", delta_sales_pct, f"Prec: € {sales_py_tot:,.2f}", True), unsafe_allow_html=True)
        with m2:
            st.markdown(get_modern_kpi_card("📈", "Front Margin %", f"{margin_on_sales:.2f}%", delta_margin_pct, f"Valore: € {margin_tot:,.2f}", True), unsafe_allow_html=True)
        with m3:
            st.markdown(get_modern_kpi_card("📦", "Stock Days", f"{val_stock_days:.1f} gg", delta_stock_pct, f"Prec: {val_stock_days_py:.1f} gg", False), unsafe_allow_html=True)
        with m4:
            st.markdown(get_modern_kpi_card("📉", "Shrinkage (Sfrido)", f"{shrink_on_sales:.2f}%", delta_shrink_pct, f"Valore: € {shrink_tot:,.2f}", False), unsafe_allow_html=True)
        st.markdown("<br>##### 👥 Focus Canali & Qualità Vendite (Dati Report CTG)", unsafe_allow_html=True)
        m_extra1, m_extra2 = st.columns(2)
        with m_extra1:
            st.markdown(get_modern_kpi_card("💳", "Accrediti % su Sales", f"{accrediti_pct:.2f}%", delta_accrediti_pct, f"Prec Incid: {accrediti_py_pct:.2f}%", False), unsafe_allow_html=True)
        with m_extra2:
            st.markdown(get_modern_kpi_card("🏆", "Fatturato Clienti HVS (Bulk)", f"€ {hvs_sales_tot:,.2f}", delta_hvs_pct, f"Prec: € {hvs_sales_py:,.2f}", True), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📦 Dettaglio Giacenze e Rotazioni")
        df_stock_kpi = pd.DataFrame({
            "Metrica": ["Giorni di Giacenza Correnti", "Giorni di Giacenza Anno Prec. (PY)", "Stock Medio Corrente Complessivo"],
            "Valore": [f"{val_stock_days:.1f} Giorni", f"{val_stock_days_py:.1f} Giorni", f"€ {avg_stock_tot:,.2f}"]
        })
        st.dataframe(df_stock_kpi, use_container_width=True, hide_index=True)
    else:
        st.warning("Nessun dato corrispondente trovato nel file Mensilizzazione.")
        
    st.markdown("---")
    st.subheader("🔗 Indicatori di Performance dai File Esterni (BMPL & Indispensabili)")

    def get_mini_kpi_block(label, current_val, py_val, is_currency=True, is_positive_good=True):
        delta_pct = ((current_val - py_val) / py_val * 100) if py_val != 0 else 0.0
        color = "#2ecc71" if (delta_pct >= 0 if is_positive_good else delta_pct <= 0) else "#e74c3c"
        val_str = f"€ {current_val:,.2f}" if is_currency else f"{int(current_val):,}"
        py_str = f"€ {py_val:,.2f}" if is_currency else f"{int(py_val):,}"
        return f"""
        <div style="background-color: #1e2430; padding: 12px; border-radius: 6px; border: 1px solid #2d3748; margin-bottom: 8px;">
            <span style="color: #a0aec0; font-size: 0.8rem; font-weight: bold; text-transform: uppercase;">{label}</span>
            <h3 style="margin: 2px 0; font-size: 1.4rem; font-weight: 700; color: #ffffff;">{val_str}</h3>
            <span style="color: {color}; font-size: 0.85rem; font-weight: 600;">{delta_pct:+.2f}% vs PY <span style="color: #718096; font-size: 0.75rem;">(ex {py_str})</span></span>
        </div>
        """

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        with st.container(border=True):
            st.markdown("#### 📈 Sintesi Totale BMPL Reparti")
            col_rep_bmpl = [c for c in df_rep.columns if 'department' in c.lower() or 'reparto' in c.lower()]
            if col_rep_bmpl:
                col_rep_target = col_rep_bmpl[0]
                match_bmpl = df_rep[df_rep[col_rep_target].astype(str).str[:3].str.strip().isin(lista_codici_target)] if lista_codici_target else pd.DataFrame()
                if not match_bmpl.empty:
                    bmpl_sales = float(match_bmpl['Sales TT'].sum())
                    bmpl_sales_py = float(match_bmpl['Sales TT PY Custom Cal'].sum())
                    bmpl_margin = float(match_bmpl['Front Margin'].sum())
                    bmpl_margin_py = float(match_bmpl['Front Margin PY Custom Cal'].sum())
                    bmpl_colli = float(match_bmpl['# Colli'].sum())
                    bmpl_colli_py = float(match_bmpl['# Colli PY Custom Cal'].sum())
                    
                    st.markdown(get_mini_kpi_block("Sales TT (BMPL)", bmpl_sales, bmpl_sales_py), unsafe_allow_html=True)
                    st.markdown(get_mini_kpi_block("Front Margin (BMPL)", bmpl_margin, bmpl_margin_py), unsafe_allow_html=True)
                    st.markdown(get_mini_kpi_block("Volume # Colli (BMPL)", bmpl_colli, bmpl_colli_py, is_currency=False), unsafe_allow_html=True)
                else:
                    st.caption("Nessun record BMPL associato ai filtri correnti.")

    with col_c2:
        with st.container(border=True):
            st.markdown("#### 📌 Sintesi Totale Articoli Indispensabili")
            col_rep_ind = [c for c in df_ind.columns if 'department' in c.lower() or 'reparto' in c.lower()]
            if col_rep_ind:
                col_rep_target_ind = col_rep_ind[0]
                match_indisp = df_ind[df_ind[col_rep_target_ind].astype(str).str[:3].str.strip().isin(lista_codici_target)] if lista_codici_target else pd.DataFrame()
                if not match_indisp.empty:
                    ind_sales = float(match_indisp['DA - Sales TT'].sum())
                    ind_sales_py = float(match_indisp['DA - Sales TT PY Custom Cal'].sum())
                    ind_colli = float(match_indisp['DA - #Colli'].sum())
                    ind_colli_py = float(match_indisp['DA - #Colli PY Custom Cal'].sum())
                    
                    st.markdown(get_mini_kpi_block("Sales TT (Indispensabili)", ind_sales, ind_sales_py), unsafe_allow_html=True)
                    st.markdown(get_mini_kpi_block("Volume # Colli (Indispensabili)", ind_colli, ind_colli_py, is_currency=False), unsafe_allow_html=True)
                    n_articoli = match_indisp['Article'].nunique() if 'Article' in match_indisp.columns else 0
                    st.markdown(f"""<div style="background-color: #232936; padding: 8px; border-radius: 4px; text-align: center; border: 1px dashed #4a5568; margin-top: 12px;"><span style="color: #cbd5e0; font-size: 0.85rem;">Articoli Chiave Tracciati nel Mix: <b>{n_articoli}</b></span></div>""", unsafe_allow_html=True)
                else:
                    st.caption("Nessun articolo indispensabile abbinato ai filtri correnti.")

    st.markdown("---")
    st.subheader("👥 Vista Canale e Categoria Cliente (Dati Report CTG)")
    if not dati_ctg_macro.empty:
        groupby_cols = [c for c in ["Channel Detail", "Customer Category", "CTG"] if c in dati_ctg_macro.columns]
        if groupby_cols:
            metrics_cols = [c for c in ["Sales TT", "# Visits", "Sales per Visit"] if c in dati_ctg_macro.columns]
            pivot_ctg = dati_ctg_macro.groupby(groupby_cols)[metrics_cols].sum().reset_index()
            if "Customer Category" in pivot_ctg.columns and "Sales TT" in pivot_ctg.columns:
                color_col = "CTG" if "CTG" in pivot_ctg.columns else None
                fig_ctg_bar = px.bar(pivot_ctg, x="Customer Category", y="Sales TT", color=color_col, barmode="group", title="Fatturato per Canale/Categoria Cliente")
                st.plotly_chart(fig_ctg_bar, use_container_width=True)
            st.dataframe(pivot_ctg.sort_values(by="Sales TT", ascending=False), use_container_width=True, hide_index=True)
# =============================================================================
# SCHEDA 2: ANALISI PORTAFOGLIO FORZA VENDITE E CLIENTI (Free Analysis Sellout)
# =============================================================================
with tab2:
    st.header("👥 Analisi Profilazione e Portafoglio Clienti (Sellout FASO)")
    st.markdown("Esplorazione analitica e commerciale isolata derivante dal flusso dati *Free Analysis Sellout*.")

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

    sellout_sales_tot = float(df_sel_filtrato["Sales TT"].sum()) if "Sales TT" in df_sel_filtrato.columns else 0.0
    sellout_margin_tot = float(df_sel_filtrato["Front Margin"].sum()) if "Front Margin" in df_sel_filtrato.columns else 0.0
    sellout_visits_tot = float(df_sel_filtrato["# Visit"].sum()) if "# Visit" in df_sel_filtrato.columns else 0.0
    sellout_margin_pct = (sellout_margin_tot / sellout_sales_tot * 100) if sellout_sales_tot != 0 else 0.0

    st.markdown("##### 📊 Indicatori Chiave del Portafoglio Selezionato")
    ms1, ms2, ms3 = st.columns(3)
    with ms1:
        st.markdown(get_modern_kpi_card("💼", "Fatturato Portafoglio (Sellout)", f"€ {sellout_sales_tot:,.2f}", 0.0, "", True, show_delta=False), unsafe_allow_html=True)
    with ms2:
        st.markdown(get_modern_kpi_card("🎯", "Front Margin % Realizzato", f"{sellout_margin_pct:.2f}%", 0.0, f"Valore Assoluto: € {sellout_margin_tot:,.2f}", True, show_delta=False), unsafe_allow_html=True)
    with ms3:
        st.markdown(get_modern_kpi_card("👣", "Volume Totale Visite", f"{int(sellout_visits_tot):,}", 0.0, "", True, show_delta=False), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    c_g1, c_g2 = st.columns(2)
    with c_g1:
        if "Venditore" in df_sel_filtrato.columns:
            df_v_sales = df_sel_filtrato.groupby("Venditore")["Sales TT"].sum().reset_index().sort_values(by="Sales TT", ascending=False).head(10)
            fig_v_sales = px.bar(df_v_sales, x="Sales TT", y="Venditore", orientation="h", title="Top 10 Venditori per Fatturato Sviluppato (Sellout)", color="Sales TT", color_continuous_scale="Blugrn")
            fig_v_sales.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_v_sales, use_container_width=True)
    with c_g2:
        if "Customer Category" in df_sel_filtrato.columns:
            df_cat_sales = df_sel_filtrato.groupby("Customer Category")["Sales TT"].sum().reset_index()
            fig_cat_sales = px.pie(df_cat_sales, values="Sales TT", names="Customer Category", title="Fatturato per Macrocategoria Canale Cliente", hole=0.3)
            fig_cat_sales.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_cat_sales, use_container_width=True)

    st.markdown("### 📋 Elenco Analitico Clienti (Ordinati per Fatturato Decrescente)")
    raggruppamento_cols = [c for c in ["Customer", "Customer Category", "Venditore", "MPRO Club"] if c in df_sel_filtrato.columns]
    
    if raggruppamento_cols:
        agg_dict = {"Sales TT": "sum"}
        if "Front Margin" in df_sel_filtrato.columns: agg_dict["Front Margin"] = "sum"
        if "# Visit" in df_sel_filtrato.columns: agg_dict["# Visit"] = "sum"
        
        df_customer_pivoted = df_sel_filtrato.groupby(raggruppamento_cols).agg(agg_dict).reset_index().sort_values(by="Sales TT", ascending=False)
        
        # Formattazione finale delle stringhe numeriche per la visualizzazione corporate
        df_customer_presentation = df_customer_pivoted.copy()
        df_customer_presentation["Sales TT"] = df_customer_presentation["Sales TT"].map('€ {:,.2f}'.format)
        if "Front Margin" in df_customer_presentation.columns:
            df_customer_presentation["Front Margin"] = df_customer_presentation["Front Margin"].map('€ {:,.2f}'.format)
        if "# Visit" in df_customer_presentation.columns:
            df_customer_presentation["# Visit"] = df_customer_presentation["# Visit"].map('{:,.0f}'.format)
            
        st.dataframe(df_customer_presentation, use_container_width=True, hide_index=True)
