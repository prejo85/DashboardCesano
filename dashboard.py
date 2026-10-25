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
        try:
            df = pd.read_csv(file_path, sep=";", skiprows=skip_rows, skip_blank_lines=True)
            if df.shape[1] <= 1:
                df = pd.read_csv(file_path, sep=",", skiprows=skip_rows, skip_blank_lines=True)
        except:
            df = pd.read_csv(file_path, sep=",", skiprows=skip_rows, skip_blank_lines=True)
            
        df.columns = df.columns.str.strip()
        df = df[df.iloc[:, 0].notna() & ~df.iloc[:, 0].astype(str).str.contains("Report Filter|View Filter|^$|bmplreparti", case=False)]
        return df

    def parse_numeric(series):
        # Converte in stringa pulita
        series_clean = series.astype(str).str.replace(r'\s+', '', regex=True)
        series_clean = series_clean.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        series_clean = series_clean.replace(['-', '--', 'nan', 'NaN', ''], '0')
        return pd.to_numeric(series_clean, errors='coerce').fillna(0.0)

    df_rep = clean_df(file_reparti, skip_rows=5)
    df_ctg = clean_df(file_ctg, skip_rows=5)
    df_sel = clean_df(file_sellout, skip_rows=5)
    df_ind = clean_df(file_indispensabili, skip_rows=5)
    df_men = clean_df(file_mensile, skip_rows=5)

    # --- APPLICAZIONE SELETTIVA SOLO SUI VALORI ECONOMICI E QUANTITATIVI ---
    # Evitiamo accuratamente colonne chiave come Store, Department, Area, CTG, Customer, Article
    colonne_valori = ["sales", "margin", "colli", "visite", "visit", "stock", "shrinkage", "sfrido"]

    for col in df_rep.columns:
        if any(k in col.lower() for k in colonne_valori) and not any(x in col.lower() for x in ["department", "reparto"]):
            df_rep[col] = parse_numeric(df_rep[col])
            
    for col in df_ctg.columns:
        if any(k in col.lower() for k in colonne_valori) and not any(x in col.lower() for x in ["department", "reparto", "detail", "category", "ctg"]):
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
        
        # Somma complessiva dei KPI correnti e PY assicurando la conversione numerica al volo
        sales_tot = float(dati_vista['DA - Sales TT'].sum())
        sales_py_tot = float(dati_vista['DA - Sales TT PY Custom Cal'].sum())
        margin_tot = float(dati_vista['DA - Front Margin'].sum())
        margin_py_tot = float(dati_vista['DA - Front Margin PY Custom Cal'].sum())
        shrink_tot = float(dati_vista['DA - Shrinkage NNBP'].sum())
        
        if 'DA - Shrinkage NNBP PY Custom Cal' in dati_vista.columns:
            shrink_py_tot = float(dati_vista['DA - Shrinkage NNBP PY Custom Cal'].sum())
        else:
            shrink_py_tot = 0.0
        
        # Medie per la gestione dei giorni di stock
        val_stock_days = float(dati_vista['DA - Stock Days'].mean())
        val_stock_days_py = float(dati_vista['DA - Stock Days PY Custom Cal'].mean())
        avg_stock_tot = float(dati_vista['DA - Avg Stock'].sum())
        
        # Formule specifiche richieste: Front Margin e Shrinkage espresse solo su Sales
        margin_on_sales = (margin_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        shrink_on_sales = (shrink_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        
        # Calcolo protetto degli scostamenti percentuali vs Anno Precedente (PY) per evitare l'UFuncNoLoopError
        delta_sales_pct = ((sales_tot - sales_py_tot) / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
        delta_margin_pct = ((margin_tot - margin_py_tot) / margin_py_tot * 100) if margin_py_tot != 0 else 0.0
        delta_stock_pct = ((val_stock_days - val_stock_days_py) / val_stock_days_py * 100) if val_stock_days_py != 0 else 0.0
        delta_shrink_pct = ((shrink_tot - shrink_py_tot) / shrink_py_tot * 100) if shrink_py_tot != 0 else 0.0

        # Funzione integrata per la formattazione dei riquadri colorati condizionali
        def get_colored_text(label, value_str, subtext, is_positive_good=True, check_val=0.0):
            color = "#2ecc71" if (check_val >= 0 if is_positive_good else check_val <= 0) else "#e74c3c"
            return f"""
            <div style="background-color: #1e2430; padding: 15px; border-radius: 8px; border: 1px solid #2d3748; min-height: 120px;">
                <span style="color: #a0aec0; font-size: 0.85rem; font-weight: bold; text-transform: uppercase;">{label}</span>
                <h2 style="margin: 5px 0; font-size: 1.8rem; font-weight: 700; color: #ffffff;">{value_str}</h2>
                <span style="color: {color}; font-size: 0.9rem; font-weight: 600;">{subtext}</span>
            </div>
            """

        # Creazione del layout a 4 colonne per i riquadri commerciali
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            sub_sales = f"{delta_sales_pct:+.2f}% vs PY (ex € {sales_py_tot:,.2f})"
            st.markdown(get_colored_text("Sales TT", f"€ {sales_tot:,.2f}", sub_sales, is_positive_good=True, check_val=delta_sales_pct), unsafe_allow_html=True)
                
        with m2:
            sub_margin = f"{delta_margin_pct:+.2f}% vs PY" if margin_py_tot != 0 else "vs PY: N/D"
            st.markdown(get_colored_text("Front Margin %", f"{margin_on_sales:.2f}%", sub_margin, is_positive_good=True, check_val=delta_margin_pct), unsafe_allow_html=True)
                
        with m3:
            sub_stock = f"{delta_stock_pct:+.1f}% vs PY (ex {val_stock_days_py:.1f} gg)"
            # Per le giacenze, un aumento dei giorni è un fattore negativo, quindi is_positive_good=False
            st.markdown(get_colored_text("Stock Days", f"{val_stock_days:.1f} gg", sub_stock, is_positive_good=False, check_val=delta_stock_pct), unsafe_allow_html=True)
                
        with m4:
            sub_shrink = f"{delta_shrink_pct:+.2f}% vs PY" if shrink_py_tot != 0 else "vs PY: N/D"
            # Per lo sfrido (shrinkage), una riduzione o valore negativo è un fattore positivo
            st.markdown(get_colored_text("Shrinkage NNBP", f"{shrink_on_sales:.2f}% su Sales", sub_shrink, is_positive_good=False, check_val=shrink_tot), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📦 Dettaglio Giacenze e Rotazioni")
        df_stock_kpi = pd.DataFrame({
            "Metrica": ["Giorni di Giacenza Correnti", "Giorni di Giacenza Anno Prec. (PY)", "Stock Medio Corrente Complessivo"],
            "Valore": [f"{val_stock_days:.1f} Giorni", f"{val_stock_days_py:.1f} Giorni", f"€ {avg_stock_tot:,.2f}"]
        })
        st.dataframe(df_stock_kpi, use_container_width=True, hide_index=True)
    else:
        st.warning("Nessun dato corrispondente trovato per la selezione indicata.")

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
