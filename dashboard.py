import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configurazione iniziale della pagina
st.set_page_config(page_title="Dashboard Commerciale Avanzata", layout="wide", page_icon="📊")

st.title("📊 Dashboard Commerciale Integrata")
st.markdown("### Analisi Multilivello: Store, Reparti, Clienti e Indicatori di Performance")
@st.cache_data
def load_and_clean_data(file_reparti, file_ctg, file_sellout, file_indispensabili, file_mensile):
    def clean_df(file_path, skip_rows=5):
        # Legge il file rilevando e correggendo al volo il separatore corretto (, o ;)
        try:
            df = pd.read_csv(file_path, sep=";", skiprows=skip_rows, skip_blank_lines=True)
            # Se ha letto tutto in una sola colonna, significa che il vero separatore è la virgola
            if len(df.columns) <= 1:
                df = pd.read_csv(file_path, sep=",", skiprows=skip_rows, skip_blank_lines=True)
        except:
            df = pd.read_csv(file_path, sep=",", skiprows=skip_rows, skip_blank_lines=True)
            
        # Rimuove spazi vuoti nascosti nei nomi delle colonne
        df.columns = df.columns.str.strip()
        
        # Elimina le righe nulle iniziali o finali e i commenti di sistema
        if len(df) > 0:
            df = df[df.iloc[:, 0].notna()]
            df = df[~df.iloc[:, 0].astype(str).str.contains("Report Filter|View Filter|^$|bmplreparti", case=False, na=False)]
        return df

    def parse_numeric(series):
        # Pulisce i dati rimuovendo spazi e formattando i separatori decimali europei
        series_clean = series.astype(str).str.replace(r'\s+', '', regex=True)
        series_clean = series_clean.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        series_clean = series_clean.replace(['-', '--', 'nan', 'NaN', ''], '0')
        return pd.to_numeric(series_clean, errors='coerce').fillna(0.0)

    # Caricamento con saltariga allineato alla struttura dei tuoi report reali
    df_rep = clean_df(file_reparti, skip_rows=8)
    df_ctg = clean_df(file_ctg, skip_rows=5)
    df_sel = clean_df(file_sellout, skip_rows=5)
    df_ind = clean_df(file_indispensabili, skip_rows=5)
    df_men = clean_df(file_mensile, skip_rows=5)

    # Filtro selettivo per pulire solo i valori numerici ed economici (lasciando stare i testi HVS, Store, Reparti)
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


# Pannello laterale per l'inserimento manuale dei CSV
st.sidebar.header("📁 Caricamento File Sorgente")
st.sidebar.markdown("Carica i 5 file estratti per generare la dashboard aggiornata.")

u_rep = st.sidebar.file_uploader("1. File BMPL Reparti (.csv)", type="csv")
u_ctg = st.sidebar.file_uploader("2. File CTG (.csv)", type="csv")
u_sel = st.sidebar.file_uploader("3. File Free Analysis Sellout (.csv)", type="csv")
u_ind = st.sidebar.file_uploader("4. File Indispensabili (.csv)", type="csv")
u_men = st.sidebar.file_uploader("5. File Mensilizzazione (.csv)", type="csv")

# Messaggio di blocco di sicurezza in assenza di file
if not (u_rep and u_ctg and u_sel and u_ind and u_men):
    st.info("💡 Per iniziare, carica tutti e 5 i file richiesti nel pannello laterale sinistro.")
    st.stop()

# Lettura asincrona e inizializzazione delle tabelle
df_rep, df_ctg, df_sel, df_ind, df_men = load_and_clean_data(u_rep, u_ctg, u_sel, u_ind, u_men)

# Definizione dei due pannelli di visualizzazione principali
tab1, tab2 = st.tabs(["🏬 Vista Store e Performance Reparti", "👥 Analisi Profilazione Clienti (Sellout)"])
with tab1:
    st.header("🏬 Monitoraggio Gerarchico Store & Performance Mix")
    
    # Generazione dei selettori a cascata con opzione TOTALE
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

    # Identificazione della granularità dei dati da mostrare
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
        
        # Somma complessiva dei KPI correnti e PY dal file principale
        sales_tot = float(dati_vista['DA - Sales TT'].sum())
        sales_py_tot = float(dati_vista['DA - Sales TT PY Custom Cal'].sum())
        margin_tot = float(dati_vista['DA - Front Margin'].sum())
        margin_py_tot = float(dati_vista['DA - Front Margin PY Custom Cal'].sum())
        shrink_tot = float(dati_vista['DA - Shrinkage NNBP'].sum())
        
        if 'DA - Shrinkage NNBP PY Custom Cal' in dati_vista.columns:
            shrink_py_tot = float(dati_vista['DA - Shrinkage NNBP PY Custom Cal'].sum())
        else:
            shrink_py_tot = 0.0
        
        # Medie e stock del file principale
        val_stock_days = float(dati_vista['DA - Stock Days'].mean())
        val_stock_days_py = float(dati_vista['DA - Stock Days PY Custom Cal'].mean())
        avg_stock_tot = float(dati_vista['DA - Avg Stock'].sum())
        
        # -----------------------------------------------------------------------------
        # CALCOLI EXTRA ESTRAZIONE DAL FILE CTG IN BASE AL FILTRO
        # -----------------------------------------------------------------------------
        if selected_area == "--- TOTALE STORE ---":
            reparti_inclusi = df_men[df_men["Store"] == selected_store]["Sales Department"].dropna().unique()
        elif selected_reparto == "--- TOTALE AREA ---":
            reparti_inclusi = df_men[(df_men["Store"] == selected_store) & (df_men["Sales Area Deparment"] == selected_area)]["Sales Department"].dropna().unique()
        else:
            reparti_inclusi = [selected_reparto]
            
        lista_codici_target = [str(r)[:3].strip() for r in reparti_inclusi if pd.notna(r)]
        
        col_rep_ctg_check = [c for c in df_ctg.columns if 'department' in c.lower() or 'reparto' in c.lower()]
        if col_rep_ctg_check:
            dati_ctg_macro = df_ctg[df_ctg[col_rep_ctg_check].astype(str).str[:3].str.strip().isin(lista_codici_target)]
        else:
            dati_ctg_macro = pd.DataFrame()
            
        if not dati_ctg_macro.empty:
            ctg_sales = float(dati_ctg_macro['Sales TT'].sum()) if 'Sales TT' in dati_ctg_macro.columns else 0.0
            ctg_sales_py = float(dati_ctg_macro['Sales TT PY Custom Cal'].sum()) if 'Sales TT PY Custom Cal' in dati_ctg_macro.columns else 0.0
            
            # Somma algebrica mantenendo il valore nativo negativo degli accrediti
            accrediti_tot = float(dati_ctg_macro['Accrediti'].sum()) if 'Accrediti' in dati_ctg_macro.columns else 0.0
            accrediti_py_tot = float(dati_ctg_macro['Accrediti PY Custom Cal'].sum()) if 'Accrediti PY Custom Cal' in dati_ctg_macro.columns else 0.0
            
            # Calcolo percentuale reale con segno negativo
            accrediti_pct = (accrediti_tot / ctg_sales * 100) if ctg_sales != 0 else 0.0
            accrediti_py_pct = (accrediti_py_tot / ctg_sales_py * 100) if ctg_sales_py != 0 else 0.0
            delta_accrediti_pct = accrediti_pct - accrediti_py_pct
            
            # Ripristino del filtro testuale corretto per il fatturato HVS (Bulk)
            col_hvs = [c for c in dati_ctg_macro.columns if 'hvs' in c.lower()]
            if col_hvs:
                match_hvs = dati_ctg_macro[dati_ctg_macro[col_hvs[0]].astype(str).str.upper().str.contains('HVS', na=False) & ~dati_ctg_macro[col_hvs[0]].astype(str).str.upper().str.contains('NO', na=False)]
                hvs_sales_tot = float(match_hvs['Sales TT'].sum()) if 'Sales TT' in match_hvs.columns else 0.0
                hvs_sales_py = float(match_hvs['Sales TT PY Custom Cal'].sum()) if 'Sales TT PY Custom Cal' in match_hvs.columns else 0.0
                delta_hvs_pct = ((hvs_sales_tot - hvs_sales_py) / hvs_sales_py * 100) if hvs_sales_py != 0 else 0.0
            else:
                hvs_sales_tot, hvs_sales_py, delta_hvs_pct = 0.0, 0.0, 0.0
        else:
            accrediti_pct, delta_accrediti_pct, accrediti_py_tot = 0.0, 0.0, 0.0
            hvs_sales_tot, hvs_sales_py, delta_hvs_pct = 0.0, 0.0, 0.0

        margin_on_sales = (margin_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        shrink_on_sales = (shrink_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        delta_sales_pct = ((sales_tot - sales_py_tot) / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
        delta_margin_pct = ((margin_tot - margin_py_tot) / margin_py_tot * 100) if margin_py_tot != 0 else 0.0
        delta_stock_pct = ((val_stock_days - val_stock_days_py) / val_stock_days_py * 100) if val_stock_days_py != 0 else 0.0
        delta_shrink_pct = ((shrink_tot - shrink_py_tot) / shrink_py_tot * 100) if shrink_py_tot != 0 else 0.0

        def get_colored_text(label, value_str, subtext, is_positive_good=True, check_val=0.0):
            color = "#2ecc71" if (check_val >= 0 if is_positive_good else check_val <= 0) else "#e74c3c"
            return f"""
            <div style="background-color: #1e2430; padding: 15px; border-radius: 8px; border: 1px solid #2d3748; min-height: 120px;">
                <span style="color: #a0aec0; font-size: 0.85rem; font-weight: bold; text-transform: uppercase;">{label}</span>
                <h2 style="margin: 5px 0; font-size: 1.8rem; font-weight: 700; color: #ffffff;">{value_str}</h2>
                <span style="color: {color}; font-size: 0.9rem; font-weight: 600;">{subtext}</span>
            </div>
            """
        # RIGA 1: Riquadri Standard
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            sub_sales = f"{delta_sales_pct:+.2f}% vs PY (ex € {sales_py_tot:,.2f})"
            st.markdown(get_colored_text("Sales TT", f"€ {sales_tot:,.2f}", sub_sales, is_positive_good=True, check_val=delta_sales_pct), unsafe_allow_html=True)
        with m2:
            sub_margin = f"{delta_margin_pct:+.2f}% vs PY" if margin_py_tot != 0 else "vs PY: N/D"
            st.markdown(get_colored_text("Front Margin %", f"{margin_on_sales:.2f}%", sub_margin, is_positive_good=True, check_val=delta_margin_pct), unsafe_allow_html=True)
        with m3:
            sub_stock = f"{delta_stock_pct:+.1f}% vs PY (ex {val_stock_days_py:.1f} gg)"
            st.markdown(get_colored_text("Stock Days", f"{val_stock_days:.1f} gg", sub_stock, is_positive_good=False, check_val=delta_stock_pct), unsafe_allow_html=True)
        with m4:
            sub_shrink = f"{delta_shrink_pct:+.2f}% vs PY" if shrink_py_tot != 0 else "vs PY: N/D"
            st.markdown(get_colored_text("Shrinkage NNBP", f"{shrink_on_sales:.2f}% su Sales", sub_shrink, is_positive_good=False, check_val=delta_shrink_pct), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # RIGA 2: Nuovi Riquadri CTG (Accrediti negativi e HVS alimentato)
        st.markdown("##### 👥 Focus Canali & Qualità Vendite (Dati Report CTG)")
        m_extra1, m_extra2 = st.columns(2)
        with m_extra1:
            sub_acc = f"{delta_accrediti_pct:+.2f}% scostamento vs PY"
            # Esibisce la percentuale con segno negativo appropriato (es. -0.08%)
            st.markdown(get_colored_text("Accrediti % su Sales", f"{accrediti_pct:.2f}%", sub_acc, is_positive_good=False, check_val=delta_accrediti_pct), unsafe_allow_html=True)
        with m_extra2:
            sub_hvs = f"{delta_hvs_pct:+.2f}% vs PY (ex € {hvs_sales_py:,.2f})"
            st.markdown(get_colored_text("Fatturato Clienti HVS (Bulk)", f"€ {hvs_sales_tot:,.2f}", sub_hvs, is_positive_good=True, check_val=delta_hvs_pct), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📦 Dettaglio Giacenze e Rotazioni")
        df_stock_kpi = pd.DataFrame({
            "Metrica": ["Giorni di Giacenza Correnti", "Giorni di Giacenza Anno Prec. (PY)", "Stock Medio Corrente Complessivo"],
            "Valore": [f"{val_stock_days:.1f} Giorni", f"{val_stock_days_py:.1f} Giorni", f"€ {avg_stock_tot:,.2f}"]
        })
        st.dataframe(df_stock_kpi, use_container_width=True, hide_index=True)
    else:
        st.warning("Nessun dato corrispondente trovato per la selezione indicata.")

    # -----------------------------------------------------------------------------
    # SEZIONE KPI FILE ESTERNI (BMPL & INDISPENSABILI)
    # -----------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("🔗 Indicatori di Performance dai File Esterni (BMPL & Indispensabili)")

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        with st.container(border=True):
            st.markdown("#### 📈 Sintesi Totale BMPL Reparti")
            col_rep_bmpl = [c for c in df_rep.columns if 'department' in c.lower() or 'reparto' in c.lower()]
            if col_rep_bmpl:
                match_bmpl = df_rep[df_rep[col_rep_bmpl[0]].astype(str).str[:3].str.strip().isin(lista_codici_target)]
                if not match_bmpl.empty:
                    bmpl_sales = float(match_bmpl['Sales TT'].sum())
                    bmpl_sales_py = float(match_bmpl['Sales TT PY Custom Cal'].sum())
                    bmpl_margin = float(match_bmpl['Front Margin'].sum())
                    bmpl_margin_py = float(match_bmpl['Front Margin PY Custom Cal'].sum())
                    bmpl_colli = float(match_bmpl['# Colli'].sum())
                    bmpl_colli_py = float(match_bmpl['# Colli PY Custom Cal'].sum())
                    
                    st.markdown(get_mini_kpi_block("Sales TT (BMPL)", bmpl_sales, bmpl_sales_py, is_currency=True), unsafe_allow_html=True)
                    st.markdown(get_mini_kpi_block("Front Margin (BMPL)", bmpl_margin, bmpl_margin_py, is_currency=True), unsafe_allow_html=True)
                    st.markdown(get_mini_kpi_block("Volume # Colli (BMPL)", bmpl_colli, bmpl_colli_py, is_currency=False), unsafe_allow_html=True)
                else:
                    st.caption("Nessun dato BMPL corrispondente ai filtri attuali.")

    with col_c2:
        with st.container(border=True):
            st.markdown("#### 📌 Sintesi Totale Articoli Indispensabili")
            col_rep_ind = [c for c in df_ind.columns if 'department' in c.lower() or 'reparto' in c.lower()]
            if col_rep_ind:
                match_indisp = df_ind[df_ind[col_rep_ind[0]].astype(str).str[:3].str.strip().isin(lista_codici_target)]
                if not match_indisp.empty:
                    ind_sales = float(match_indisp['DA - Sales TT'].sum())
                    ind_sales_py = float(match_indisp['DA - Sales TT PY Custom Cal'].sum())
                    ind_colli = float(match_indisp['DA - #Colli'].sum())
                    ind_colli_py = float(match_indisp['DA - #Colli PY Custom Cal'].sum())
                    
                    st.markdown(get_mini_kpi_block("Sales TT (Indispensabili)", ind_sales, ind_sales_py, is_currency=True), unsafe_allow_html=True)
                    st.markdown(get_mini_kpi_block("Volume # Colli (Indispensabili)", ind_colli, ind_colli_py, is_currency=False), unsafe_allow_html=True)
                    n_articoli = match_indisp['Article'].nunique() if 'Article' in match_indisp.columns else 0
                    st.markdown(f"""<div style="background-color: #232936; padding: 8px; border-radius: 4px; text-align: center; border: 1px dashed #4a5568; margin-top: 12px;"><span style="color: #cbd5e0; font-size: 0.85rem;">Articoli Indispensabili Movimentati: <b>{n_articoli}</b></span></div>""", unsafe_allow_html=True)
                else:
                    st.caption("Nessun articolo indispensabile abbinato ai filtri attuali.")

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

with tab2:
    st.header("👥 Analisi Granulare del Portafoglio Clienti (Sellout)")
    
    # Configurazione filtri di ricerca portafoglio clienti
    col_s1, col_f_cust, col_s2 = st.columns(3)
    with col_s1:
        tipo_gestione = st.multiselect("Filtra per Tipo Gestione:", options=sorted(df_sel["Tipo Gestione"].dropna().unique()) if "Tipo Gestione" in df_sel.columns else [])
    with col_f_cust:
        ricerca_cliente = st.text_input("🔍 Cerca per Ragione Sociale / Codice Cliente:")
    with col_s2:
        mpro_club = st.multiselect("Filtra per Stato MPRO Club:", options=sorted(df_sel["MPRO Club"].dropna().unique()) if "MPRO Club" in df_sel.columns else [])

    # Filtrazione logica condizionale sul dataset di Sellout
    df_sel_filtrato = df_sel.copy()
    if tipo_gestione and "Tipo Gestione" in df_sel.columns:
        df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["Tipo Gestione"].isin(tipo_gestione)]
    if mpro_club and "MPRO Club" in df_sel.columns:
        df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["MPRO Club"].isin(mpro_club)]
    if ricerca_cliente and "Customer" in df_sel.columns:
        df_sel_filtrato = df_sel_filtrato[df_sel_filtrato["Customer"].astype(str).str.contains(ricerca_cliente, case=False, na=False)]

    # Layout per i macro trend del sellout
    c_g1, c_g2 = st.columns(2)
    with c_g1:
        if "Venditore" in df_sel_filtrato.columns:
            df_v_sales = df_sel_filtrato.groupby("Venditore")["Sales TT"].sum().reset_index().sort_values(by="Sales TT", ascending=False).head(10)
            fig_v_sales = px.bar(df_v_sales, x="Sales TT", y="Venditore", orientation="h", title="Top 10 Venditori per Fatturato Sviluppato (Sellout)", color="Sales TT", color_continuous_scale="Blugrn")
            st.plotly_chart(fig_v_sales, use_container_width=True)
    with c_g2:
        if "Customer Category" in df_sel_filtrato.columns:
            df_cat_sales = df_sel_filtrato.groupby("Customer Category")["Sales TT"].sum().reset_index()
            fig_cat_sales = px.pie(df_cat_sales, values="Sales TT", names="Customer Category", title="Fatturato per Macrocategoria Cliente", hole=0.3)
            st.plotly_chart(fig_cat_sales, use_container_width=True)

    st.markdown("### 📋 Elenco Analitico Clienti (Ordinati per Fatturato Decrescente)")
    
    # Aggregazione finale sui clienti per evitare record duplicati per lo stesso codice
    raggruppamento_cols = [c for c in ["Customer", "Customer Category", "Venditore", "MPRO Club"] if c in df_sel_filtrato.columns]
    if raggruppamento_cols:
        agg_dict = {"Sales TT": "sum"}
        if "Front Margin" in df_sel_filtrato.columns: agg_dict["Front Margin"] = "sum"
        if "# Visit" in df_sel_filtrato.columns: agg_dict["# Visit"] = "sum"
        
        df_customer_pivoted = df_sel_filtrato.groupby(raggruppamento_cols).agg(agg_dict).reset_index().sort_values(by="Sales TT", ascending=False)
        
        # Formattazione per la stampa finale pulita in tabella
        df_customer_pivoted["Sales TT"] = df_customer_pivoted["Sales TT"].map('€ {:,.2f}'.format)
        if "Front Margin" in df_customer_pivoted.columns:
            df_customer_pivoted["Front Margin"] = df_customer_pivoted["Front Margin"].map('€ {:,.2f}'.format)
        
        st.dataframe(df_customer_pivoted, use_container_width=True, hide_index=True)
