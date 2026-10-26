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
# 2. ENGINE CENTRALIZZATO DI PULIZIA E PARSING DEI REPORT (RIGA 0)
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

    for col in df_rep.columns:
        if any(k in col.lower() for k in colonne_valori) and not any(x in col.lower() for x in ["department", "reparto"]):
            df_rep[col] = parse_numeric(df_rep[col])
    for col in df_ctg.columns:
        if any(k in col.lower() for k in colonne_valori) and not any(x in col.lower() for x in ["department", "reparto", "detail", "category", "ctg", "flag"]):
            df_ctg[col] = parse_numeric(df_ctg[col])
    for col in df_sel.columns:
        if any(k in col.lower() for k in colonne_valori) and not any(x in col.lower() for x in ["customer", "venditore", "gestione", "club"]):
            df_sel[col] = parse_numeric(df_sel[col])
    for col in df_ind.columns:
        if any(k in col.lower() for k in colonne_valori) and not any(x in col.lower() for x in ["article", "department", "reparto"]):
            df_ind[col] = parse_numeric(df_ind[col])
    for col in df_men.columns:
        if any(k in col.lower() for k in colonne_valori) and not any(x in col.lower() for x in ["store", "department", "area", "reparto"]):
            df_men[col] = parse_numeric(df_men[col])

    return df_rep, df_ctg, df_sel, df_ind, df_men
# -----------------------------------------------------------------------------
# 3. INTERFACCIA CARICAMENTO NELLA SIDEBAR LATERALE
# -----------------------------------------------------------------------------
st.sidebar.header("📁 Caricamento File Sorgente")
u_rep = st.sidebar.file_uploader("1. File BMPL Reparti (.csv)", type="csv")
u_ctg = st.sidebar.file_uploader("2. File CTG (.csv)", type="csv")
u_sel = st.sidebar.file_uploader("3. File Free Analysis Sellout (.csv)", type="csv")
u_ind = st.sidebar.file_uploader("4. File Indispensabili (.csv)", type="csv")
u_men = st.sidebar.file_uploader("5. File Mensilizzazione (.csv)", type="csv")

if not (u_rep and u_ctg and u_sel and u_ind and u_men):
    st.info("💡 Carica i 5 report commerciali puliti nel pannello laterale per attivare l'analisi interattiva.")
    st.stop()

# Inizializzazione asincrona dei dataframe e delle schede
df_rep, df_ctg, df_sel, df_ind, df_men = load_and_clean_data(u_rep, u_ctg, u_sel, u_ind, u_men)
tab1, tab2 = st.tabs(["🏬 Vista Store e Performance Reparti", "👥 Analisi Profilazione Clienti (Sellout)"])

# -----------------------------------------------------------------------------
# 4. MOTORE GRAFICO DI GENERAZIONE DELLE CONTEMPORARY KPI CARD
# -----------------------------------------------------------------------------
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
# -----------------------------------------------------------------------------
# 3. INTERFACCIA CARICAMENTO NELLA SIDEBAR LATERALE
# -----------------------------------------------------------------------------
st.sidebar.header("📁 Caricamento File Sorgente")
u_rep = st.sidebar.file_uploader("1. File BMPL Reparti (.csv)", type="csv")
u_ctg = st.sidebar.file_uploader("2. File CTG (.csv)", type="csv")
u_sel = st.sidebar.file_uploader("3. File Free Analysis Sellout (.csv)", type="csv")
u_ind = st.sidebar.file_uploader("4. File Indispensabili (.csv)", type="csv")
u_men = st.sidebar.file_uploader("5. File Mensilizzazione (.csv)", type="csv")

if not (u_rep and u_ctg and u_sel and u_ind and u_men):
    st.info("💡 Carica i 5 report commerciali puliti nel pannello laterale per attivare l'analisi interattiva.")
    st.stop()

# Inizializzazione asincrona dei dataframe e delle schede
df_rep, df_ctg, df_sel, df_ind, df_men = load_and_clean_data(u_rep, u_ctg, u_sel, u_ind, u_men)
tab1, tab2 = st.tabs(["🏬 Vista Store e Performance Reparti", "👥 Analisi Profilazione Clienti (Sellout)"])

# -----------------------------------------------------------------------------
# 4. MOTORE GRAFICO DI GENERAZIONE DELLE CONTEMPORARY KPI CARD
# -----------------------------------------------------------------------------
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
        # RENDERING GRAFICO RIGA 1 (Stile Antracite Sfocato)
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(get_modern_kpi_card("💰", "Sales TT", f"€ {sales_tot:,.2f}", delta_sales_pct, f"Prec: € {sales_py_tot:,.2f}", True), unsafe_allow_html=True)
        with m2:
            st.markdown(get_modern_kpi_card("📈", "Front Margin %", f"{margin_on_sales:.2f}%", delta_margin_pct, f"Valore: € {margin_tot:,.2f}", True), unsafe_allow_html=True)
        with m3:
            st.markdown(get_modern_kpi_card("📦", "Stock Days", f"{val_stock_days:.1f} gg", delta_stock_pct, f"Prec: {val_stock_days_py:.1f} gg", False), unsafe_allow_html=True)
        with m4:
            st.markdown(get_modern_kpi_card("📉", "Shrinkage (Sfrido)", f"{shrink_on_sales:.2f}%", delta_shrink_pct, f"Valore: € {shrink_tot:,.2f}", False), unsafe_allow_html=True)
        
        # RENDERING GRAFICO RIGA 2 (Focus Canali CTG)
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

    # MINI CARD ORIZZONTALI PER I FILE ESTERNI
    st.markdown("---")
    st.subheader("🔗 Indicatori di Performance dai File Esterni (BMPL & Indispensabili)")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        with st.container(border=True):
            st.markdown("#### 📈 Sintesi Totale BMPL Reparti")
            col_rep_bmpl = [c for c in df_rep.columns if 'department' in c.lower() or 'reparto' in c.lower()]
            if col_rep_bmpl:
                match_bmpl = df_rep[df_rep[col_rep_bmpl[0]].astype(str).str[:3].str.strip().isin(lista_codici_target)] if lista_codici_target else pd.DataFrame()
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
                match_indisp = df_ind[df_ind[col_rep_ind[0]].astype(str).str[:3].str.strip().isin(lista_codici_target)] if lista_codici_target else pd.DataFrame()
                if not match_indisp.empty:
                    ind_sales = float(match_indisp['DA - Sales TT'].sum())
                    ind_sales_py = float(match_indisp['DA - Sales TT PY Custom Cal'].sum())
                    ind_colli = float(match_indisp['DA - #Colli'].sum())
                    ind_colli_py = float(match_indisp['DA - #Colli PY Custom Cal'].sum())
                    
                    st.markdown(get_mini_kpi_block("Sales TT (Indispensabili)", ind_sales, ind_sales_py), unsafe_allow_html=True)
                    st.markdown(get_mini_kpi_block("Volume # Colli (Indispensabili)", ind_colli, ind_colli_py, is_currency=False), unsafe_allow_html=True)
# =============================================================================
# SCHEDA 2: ANALISI PORTAFOGLIO FORZA VENDITE E CLIENTI (Free Analysis Sellout)
# =============================================================================
with tab2:
    st.header("👥 Analisi Profilazione e Portafoglio Clienti (Sellout)")
    st.markdown("Esplorazione analitica delle performance per singolo Cliente basata sul report *Free Analysis Sellout*.")

    # Sezione filtri interattivi ad alto impatto
    col_s1, col_f_cust, col_s2 = st.columns(3)
    with col_s1:
        tipo_gestione = st.multiselect("Filtra per Tipo Gestione:", options=sorted(df_sel["Tipo Gestione"].dropna().unique()) if "Tipo Gestione" in df_sel.columns else [])
    with col_f_cust:
        ricerca_cliente = st.text_input("🔍 Cerca Ragione Sociale o Codice Cliente Contabile:")
    with col_s2:
        mpro_club = st.multiselect("Filtra per Stato MPRO Club:", options=sorted(df_sel["MPRO Club"].dropna().unique()) if "MPRO Club" in df_sel.columns else [])

    # Filtrazione logica condizionale del dataframe di Sellout
    df_sel_filtrato = df_sel.copy()
    if tipo_gestione and "Tipo Gestione" in df_sel.columns:
        df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["Tipo Gestione"].isin(tipo_gestione)]
    if mpro_club and "MPRO Club" in df_sel.columns:
        df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["MPRO Club"].isin(mpro_club)]
    if ricerca_cliente and "Customer" in df_sel.columns:
        df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["Customer"].astype(str).str.contains(ricerca_cliente, case=False, na=False)]

    # --- CALCOLO METRICHE AGGREGATE PER LE NUOVE CARD DELLA SCHEDA 2 ---
    sellout_sales_tot = float(df_sel_filtrato["Sales TT"].sum()) if "Sales TT" in df_sel_filtrato.columns else 0.0
    sellout_margin_tot = float(df_sel_filtrato["Front Margin"].sum()) if "Front Margin" in df_sel_filtrato.columns else 0.0
    sellout_visits_tot = float(df_sel_filtrato["# Visit"].sum()) if "# Visit" in df_sel_filtrato.columns else 0.0
    sellout_margin_pct = (sellout_margin_tot / sellout_sales_tot * 100) if sellout_sales_tot != 0 else 0.0

    # RENDERING DELLE NUOVE CARD GRAFICHE SPECULARI PER IL PORTAFOGLIO CLIENTI
    st.markdown("##### 📊 Indicatori Chiave del Portafoglio Selezionato")
    ms1, ms2, ms3 = st.columns(3)
    with ms1:
        st.markdown(get_modern_kpi_card("💼", "Fatturato Portafoglio (Sellout)", f"€ {sellout_sales_tot:,.2f}", 0.0, "", True, show_delta=False), unsafe_allow_html=True)
    with ms2:
        st.markdown(get_modern_kpi_card("🎯", "Front Margin % Realizzato", f"{sellout_margin_pct:.2f}%", sellout_margin_pct, f"Valore Assoluto: € {sellout_margin_tot:,.2f}", True, show_delta=False), unsafe_allow_html=True)
    with ms3:
        st.markdown(get_modern_kpi_card("👣", "Volume Totale Visite", f"{int(sellout_visits_tot):,}", 0.0, "", True, show_delta=False), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Layout Grafici Rete Commerciale
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

    # Griglia Tabellare Pivot Univoca dei Clienti
    st.markdown("### 📋 Elenco Analitico Clienti (Ordinati per Fatturato Decrescente)")
    raggruppamento_cols = [c for c in ["Customer", "Customer Category", "Venditore", "MPRO Club"] if c in df_sel_filtrato.columns]
    
    if raggruppamento_cols:
        agg_dict = {"Sales TT": "sum"}
        if "Front Margin" in df_sel_filtrato.columns: agg_dict["Front Margin"] = "sum"
        if "# Visit" in df_sel_filtrato.columns: agg_dict["# Visit"] = "sum"
        
        df_customer_pivoted = df_sel_filtrato.groupby(raggruppamento_cols).agg(agg_dict).reset_index().sort_values(by="Sales TT", ascending=False)
        df_customer_pivoted["Sales TT"] = df_customer_pivoted["Sales TT"].map('€ {:,.2f}'.format)
        if "Front Margin" in df_customer_pivoted.columns:
            df_customer_pivoted["Front Margin"] = df_customer_pivoted["Front Margin"].map('€ {:,.2f}'.format)
            
        st.dataframe(df_customer_pivoted, use_container_width=True, hide_index=True)
