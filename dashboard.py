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
        # Legge il file rilevando automaticamente se il separatore è la virgola o il punto e virgola
        try:
            df = pd.read_csv(file_path, sep=";", skiprows=skip_rows, skip_blank_lines=True)
            if df.shape[1] <= 1: # Se ha letto tutto in una sola colonna, riprova con la virgola
                df = pd.read_csv(file_path, sep=",", skiprows=skip_rows, skip_blank_lines=True)
        except:
            df = pd.read_csv(file_path, sep=",", skiprows=skip_rows, skip_blank_lines=True)
            
        # Pulisce gli spazi bianchi dai nomi delle colonne per evitare mancate corrispondenze
        df.columns = df.columns.str.strip()
        
        # Rimuove righe di commento, filtri iniziali o stringhe vuote
        df = df[df.iloc[:, 0].notna() & ~df.iloc[:, 0].astype(str).str.contains("Report Filter|View Filter|^$|bmplreparti", case=False)]
        return df

    def parse_numeric(series):
        # Rimuove gli spazi e sistema la formattazione dei numeri italiani
        series_clean = series.astype(str).str.replace(r'\s+', '', regex=True)
        series_clean = series_clean.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        return pd.to_numeric(series_clean, errors='coerce').fillna(0)

    # Allineamento perfetto del salto righe (skip_rows=5 per leggere la riga 6 di Excel)
    df_rep = clean_df(file_reparti, skip_rows=5)
    df_ctg = clean_df(file_ctg, skip_rows=5)
    df_sel = clean_df(file_sellout, skip_rows=5)
    df_ind = clean_df(file_indispensabili, skip_rows=5)
    df_men = clean_df(file_mensile, skip_rows=5)

    # Pulizia colonne numeriche se presenti nei file
    for col in ["Sales TT", "Sales TT PY Custom Cal", "Front Margin", "Front Margin PY Custom Cal"]:
        if col in df_rep.columns: df_rep[col] = parse_numeric(df_rep[col])
        if col in df_ctg.columns: df_ctg[col] = parse_numeric(df_ctg[col])
    
    if "Sales TT" in df_sel.columns: df_sel["Sales TT"] = parse_numeric(df_sel["Sales TT"])
    if "Front Margin" in df_sel.columns: df_sel["Front Margin"] = parse_numeric(df_sel["Front Margin"])
        
    for col in ["DA - Sales TT", "DA - Sales TT PY Custom Cal", "DA - #Colli", "DA - #Colli PY Custom Cal"]:
        if col in df_ind.columns: df_ind[col] = parse_numeric(df_ind[col])

    for col in ["DA - Sales TT", "DA - Sales TT PY Custom Cal", "DA - Front Margin", "DA - Front Margin PY Custom Cal", "DA - #Colli", "DA - Stock Days", "DA - Stock Days PY Custom Cal", "DA - Avg Stock", "DA - Shrinkage NNBP"]:
        if col in df_men.columns: df_men[col] = parse_numeric(df_men[col])

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

    # -----------------------------------------------------------------------------
    # LOGICA DI AGGREGAZIONE DATI (STORE / AREA / REPARTO)
    # -----------------------------------------------------------------------------
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
        
        # Calcolo dei totali aggregati per le metriche correnti e PY
        sales_tot = dati_vista['DA - Sales TT'].sum()
        sales_py_tot = dati_vista['DA - Sales TT PY Custom Cal'].sum()
        margin_tot = dati_vista['DA - Front Margin'].sum()
        shrink_tot = dati_vista['DA - Shrinkage NNBP'].sum()
        
        # Medie ponderate o semplici per i giorni di stock e stock medio
        val_stock_days = dati_vista['DA - Stock Days'].mean()
        val_stock_days_py = dati_vista['DA - Stock Days PY Custom Cal'].mean()
        avg_stock_tot = dati_vista['DA - Avg Stock'].sum()
        
        # Calcolo dei delta percentuali richiesti
        delta_sales_pct = ((sales_tot - sales_py_tot) / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
        delta_stock_pct = ((val_stock_days - val_stock_days_py) / val_stock_days_py * 100) if val_stock_days_py != 0 else 0.0
        
        margin_on_sales = (margin_tot / sales_tot * 100) if sales_tot != 0 else 0.0
        shrink_on_sales = (shrink_tot / sales_tot * 100) if sales_tot != 0 else 0.0

        # --- BLOCCO VISIVO CARD CON RIQUADRI CARINI ---
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            with st.container(border=True):
                st.markdown("**SALES TT**")
                st.markdown(f"## € {sales_tot:,.2f}")
                st.markdown(f"PY: € {sales_py_tot:,.2f} ({delta_sales_pct:+.2f}%)")
                
        with m2:
            with st.container(border=True):
                st.markdown("**FRONT MARGIN**")
                st.markdown(f"## € {margin_tot:,.2f}")
                st.markdown(f"**{margin_on_sales:.2f}%** su Sales")
                
        with m3:
            with st.container(border=True):
                st.markdown("**STOCK DAYS**")
                st.markdown(f"## {val_stock_days:.1f} gg")
                st.markdown(f"PY: {val_stock_days_py:.1f} gg ({delta_stock_pct:+.1f}%)")
                
        with m4:
            with st.container(border=True):
                st.markdown("**SHRINKAGE NNBP (Sfrido)**")
                st.markdown(f"## € {shrink_tot:,.2f}")
                st.markdown(f"**{shrink_on_sales:+.2f}%** su Sales")
        
        st.markdown("#### 📦 Dettaglio Giacenze e Rotazioni")
        df_stock_kpi = pd.DataFrame({
            "Metrica": ["Giorni di Giacenza Correnti", "Giorni di Giacenza Anno Prec. (PY)", "Stock Medio Corrente Complessivo"],
            "Valore": [f"{val_stock_days:.1f} Giorni", f"{val_stock_days_py:.1f} Giorni", f"€ {avg_stock_tot:,.2f}"]
        })
        st.dataframe(df_stock_kpi, use_container_width=True, hide_index=True)
    else:
        st.warning("Nessun dato corrispondente trovato per la selezione indicata.")

    # -----------------------------------------------------------------------------
    # SEZIONE FILE ESTERNI (BMPL / INDISPENSABILI / CTG)
    # -----------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("🔗 Indicatori di Reparto Integrati (File Esterni)")
    
    # Determiniamo il codice reparto per fare i match (usiamo le prime 3 cifre se siamo a livello reparto)
    rep_filter_code = str(selected_reparto)[:3] if selected_reparto not in ["--- TOTALE AREA ---", "--- DETTAGLIO RICHIESTO ---"] else ""
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("#### 📈 Indicatori BMPL Reparti")
        col_rep_bmpl = [c for c in df_rep.columns if 'department' in c.lower() or 'reparto' in c.lower()]
        if col_rep_bmpl:
            col_rep_bmpl = col_rep_bmpl[0]
            # Se siamo in modalità totale mostra tutto lo store/area, altrimenti filtra per reparto
            match_bmpl = df_rep[df_rep[col_rep_bmpl].astype(str).str.contains(rep_filter_code, na=False)] if rep_filter_code else df_rep.copy()
            cols_to_show = [c for c in ["F/NF", col_rep_bmpl, "Sales TT", "Front Margin", "# Colli"] if c in df_rep.columns]
            if not match_bmpl.empty:
                st.dataframe(match_bmpl[cols_to_show], use_container_width=True, hide_index=True)
            else:
                st.caption("Nessuna corrispondenza BMPL trovata.")
        else:
            st.caption("Colonna del Reparto non identificata nel file BMPL.")

    with col_c2:
        st.markdown("#### 📌 Monitoraggio Articoli Indispensabili (Focus Selezione)")
        col_rep_ind = [c for c in df_ind.columns if 'department' in c.lower() or 'reparto' in c.lower()]
        if col_rep_ind:
            col_rep_ind = col_rep_ind[0]
            match_indisp = df_ind[df_ind[col_rep_ind].astype(str).str.contains(rep_filter_code, na=False)] if rep_filter_code else df_ind.copy()
            cols_to_show_ind = [c for c in ["G2", "Article", "DA - Sales TT", "DA - #Colli"] if c in df_ind.columns]
            if not match_indisp.empty:
                st.dataframe(match_indisp[cols_to_show_ind], use_container_width=True, hide_index=True)
            else:
                st.caption("Nessun articolo indispensabile censito per questa selezione.")
        else:
            st.caption("Colonna del Reparto non identificata nel file Indispensabili.")

    st.markdown("---")
    st.subheader("👥 Vista Canale e Categoria Cliente (Dati Report CTG)")
    
    col_rep_ctg = [c for c in df_ctg.columns if 'department' in c.lower() or 'reparto' in c.lower()]
    if col_rep_ctg:
        col_rep_ctg = col_rep_ctg[0]
        dati_ctg_filtrati = df_ctg[df_ctg[col_rep_ctg].astype(str).str.contains(rep_filter_code, na=False)] if rep_filter_code else df_ctg.copy()
        if not dati_ctg_filtrati.empty:
            groupby_cols = [c for c in ["Channel Detail", "Customer Category", "CTG"] if c in df_ctg.columns]
            if groupby_cols:
                metrics_cols = [c for c in ["Sales TT", "# Visits", "Sales per Visit"] if c in df_ctg.columns]
                pivot_ctg = dati_ctg_filtrati.groupby(groupby_cols)[metrics_cols].sum().reset_index()
                
                if "Customer Category" in pivot_ctg.columns and "Sales TT" in pivot_ctg.columns:
                    color_col = "CTG" if "CTG" in pivot_ctg.columns else None
                    fig_ctg_bar = px.bar(pivot_ctg, x="Customer Category", y="Sales TT", color=color_col, barmode="group", title="Fatturato per Canale/Categoria Cliente")
                    st.plotly_chart(fig_ctg_bar, use_container_width=True)
                st.dataframe(pivot_ctg.sort_values(by="Sales TT", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("Nessun dato di profilazione canali/clienti (CTG) disponibile.")


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
