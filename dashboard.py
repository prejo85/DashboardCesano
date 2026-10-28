import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# 1. Configurazione Corporate della pagina (Layout Wide nativo)
st.set_page_config(
    page_title="Executive Commercial Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Funzione ottimizzata per il parsing dei decimali europei e pulizia stringhe (SAP/Microstrategy style)
def pulisci_e_carica_data(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path, sep=";", skiprows=0, skip_blank_lines=True)
        if len(df.columns) <= 1:
            df = pd.read_csv(file_path, sep=",", skiprows=0, skip_blank_lines=True)
    except:
        return None
    
    df.columns = df.columns.str.strip()
    df = df[df.iloc[:, 0].notna()]
    return df

def parsa_colonna_numerica(series):
    # Rimuove gli spazi, elimina i punti delle migliaia e trasforma le virgole in punti decimali
    s_clean = series.astype(str).str.replace(r'\s+', '', regex=True)
    s_clean = s_clean.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    s_clean = s_clean.replace(['-', '--', 'nan', 'NaN', ''], '0')
    return pd.to_numeric(s_clean, errors='coerce').fillna(0.0)

# 2. Caricamento automatico delle tabelle dalla cartella di GitHub
# (Assicurati che i file nel tuo repository si chiamino esattamente così)
df_bmpl = pulisci_e_carica_data("reparti.csv")          # File sorgente 1
df_ctg = pulisci_e_carica_data("canali_ctg.csv")        # File sorgente 2
df_men = pulisci_e_carica_data("mensilizzazione.csv")   # File sorgente 5/6
df_ind = pulisci_e_carica_data("indispensabili.csv")    # File sorgente 5
df_sel = pulisci_e_carica_data("free_analysis.csv")     # File sorgente 4 (FASO Commerciale)

# Applicazione del parsing numerico automatico sui campi finanziari/volumi rilevati
colonne_metriche = ["sales", "margin", "colli", "visite", "visit", "stock", "shrinkage", "sfrido", "accrediti", "da - "]
for df in [df_bmpl, df_ctg, df_men, df_sel, df_ind]:
    if df is None or df.empty: continue
    for col in df.columns:
        if any(k in col.lower() for k in colonne_metriche) and not any(x in col.lower() for x in ["department", "reparto", "detail", "category", "ctg", "store", "area", "customer", "venditore", "article"]):
            df[col] = parsa_colonna_numerica(df[col])
# 3. Struttura della Dashboard e Navigazione principale
st.title("📊 Executive Commercial Dashboard")
st.markdown("### Controllo di Gestione Avanzato & Performance Mix")
st.write("---")

# Creazione delle schede: isolamento totale per la parte commerciale FASO
tab_store, tab_commerciale = st.tabs([
    "🏬 Vista Struttura Store & Performance Reparti", 
    "👥 Sezione Separata Portafoglio Clienti (Sellout FASO)"
])

# =============================================================================
# TAB 1: OPERAZIONI STORE E REPORT AGGREGATI
# =============================================================================
with tab_store:
    if df_men is not None:
        c_f1, c_f2, c_f3 = st.columns(3)
        with c_f1:
            stores = sorted(df_men["Store"].unique()) if "Store" in df_men.columns else []
            sel_store = st.selectbox("Seleziona Punto Vendita:", stores)
        with c_f2:
            df_store_filtered = df_men[df_men["Store"] == sel_store] if "Store" in df_men.columns else df_men.copy()
            areas = ["--- TUTTO LO STORE ---"] + sorted(df_store_filtered["Sales Area Deparment"].unique()) if "Sales Area Deparment" in df_store_filtered.columns else ["--- TUTTO LO STORE ---"]
            sel_area = st.selectbox("Seleziona Area di Vendita (Macro):", areas)
        with c_f3:
            if sel_area != "--- TUTTO LO STORE ---" and "Sales Area Deparment" in df_store_filtered.columns:
                df_area_filtered = df_store_filtered[df_store_filtered["Sales Area Deparment"] == sel_area]
                departments = ["--- TOTALE AREA ---"] + sorted(df_area_filtered["Sales Department"].unique()) if "Sales Department" in df_area_filtered.columns else ["--- TOTALE AREA ---"]
            else:
                df_area_filtered = df_store_filtered.copy()
                departments = ["--- DETTAGLIO SELEZIONATO ---"]
            sel_dep = st.selectbox("Seleziona Reparto Specifico:", departments)

        if sel_area == "--- TUTTO LO STORE ---":
            view_data = df_store_filtered.copy()
        elif sel_dep == "--- TOTALE AREA ---":
            view_data = df_area_filtered.copy()
        else:
            view_data = df_area_filtered[df_area_filtered["Sales Department"] == sel_dep] if "Sales Department" in df_area_filtered.columns else pd.DataFrame()

        if not view_data.empty:
            s_tt = float(view_data['DA - Sales TT'].sum())
            s_tt_py = float(view_data['DA - Sales TT PY Custom Cal'].sum())
            m_front = float(view_data['DA - Front Margin'].sum())
            margin_pct = (m_front / s_tt * 100) if s_tt != 0 else 0.0
            d_sales = ((s_tt - s_tt_py) / s_tt_py * 100) if s_tt_py != 0 else 0.0
            
            st.markdown(f"##### Performance per l'aggregato selezionato")
            k1, k2 = st.columns(2)
            with k1:
                st.metric("Sales TT (Corrente)", f"€ {s_tt:,.2f}", f"{d_sales:+.2f}% vs PY")
            with k2:
                st.metric("Margine Front % Raggiunto", f"{margin_pct:.2f}%", f"Valore assoluto: € {m_front:,.2f}")
            
            st.markdown("<br>##### Database di Controllo Operativo", unsafe_allow_html=True)
            st.dataframe(view_data, use_container_width=True, hide_index=True)
    else:
        st.info("Ripristina il file `mensilizzazione.csv` su GitHub per sbloccare la vista di controllo Store.")
# =============================================================================
# TAB 2: SEZIONE COMMERCIALE SEPARATA (FREE ANALYSIS SELLOUT)
# =============================================================================
with tab_commerciale:
    st.subheader("💼 Business Portafoglio Clienti & Performance Agenti")
    st.markdown("Estrazione analitica isolata derivante dal flusso dati *Free Analysis Sellout (FASO)*.")
    
    if df_sel is not None and not df_sel.empty:
        c_sel1, c_sel2 = st.columns(2)
        with c_sel1:
            gestione_opts = sorted(df_sel["Tipo Gestione"].dropna().unique()) if "Tipo Gestione" in df_sel.columns else []
            sel_gestione = st.multiselect("Filtra per Tipo Gestione Rete:", gestione_opts)
        with c_sel2:
            search_query = st.text_input("🔍 Cerca Ragione Sociale Cliente o Codice Contabile:").strip()

        # Applicazione filtri
        df_s_filtered = df_sel.copy()
        if sel_gestione and "Tipo Gestione" in df_s_filtered.columns:
            df_s_filtered = df_s_filtered[df_s_filtered["Tipo Gestione"].isin(sel_gestione)]
        if search_query and "Customer" in df_s_filtered.columns:
            df_s_filtered = df_s_filtered[df_s_filtered["Customer"].astype(str).str.contains(search_query, case=False, na=False)]

        f_sales = float(df_s_filtered["Sales TT"].sum()) if "Sales TT" in df_s_filtered.columns else 0.0
        f_margin = float(df_s_filtered["Front Margin"].sum()) if "Front Margin" in df_s_filtered.columns else 0.0
        f_margin_pct = (f_margin / f_sales * 100) if f_sales != 0 else 0.0

        # KPI Commerciali Superiori
        sk1, sk2 = st.columns(2)
        with sk1:
            st.metric("Fatturato Totale Sviluppato (Sellout)", f"€ {f_sales:,.2f}")
        with sk2:
            st.metric("Front Margin % Medio Realizzato", f"{f_margin_pct:.2f}%", f"Margine Assoluto: € {f_margin:,.2f}")

        st.markdown("<br>", unsafe_allow_html=True)
        g_c1, g_c2 = st.columns(2)
        
        with g_c1:
            if "Venditore" in df_s_filtered.columns:
                df_v = df_s_filtered.groupby("Venditore")["Sales TT"].sum().reset_index().sort_values(by="Sales TT", ascending=False).head(10)
                fig_venditori = px.bar(
                    df_v, x="Sales TT", y="Venditore", orientation="h",
                    title="Top 10 Venditori per Sviluppo di Fatturato (€)",
                    color="Sales TT", color_continuous_scale="Blugrn"
                )
                fig_venditori.update_layout(yaxis={'categoryorder':'total ascending'}, template="plotly_white")
                st.plotly_chart(fig_venditori, use_container_width=True)
        
        with g_c2:
            if "Customer Category" in df_s_filtered.columns:
                df_cc = df_s_filtered.groupby("Customer Category")["Sales TT"].sum().reset_index()
                fig_pie = px.pie(df_cc, values="Sales TT", names="Customer Category", title="Quota Mix Fatturato per Macrocategoria Canale", hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("##### 📋 Elenco Ordinato Clienti per Fatturato Decrescente")
        cluster_cols = [c for c in ["Customer", "Customer Category", "Venditore", "MPRO Club"] if c in df_s_filtered.columns]
        if cluster_cols:
            df_final_customers = df_s_filtered.groupby(cluster_cols).agg({"Sales TT": "sum", "Front Margin": "sum", "# Visit": "sum"}).reset_index().sort_values(by="Sales TT", ascending=False)
            
            # Formattazione per la visualizzazione corporate finale
            df_final_customers["Sales TT"] = df_final_customers["Sales TT"].map('€ {:,.2f}'.format)
            df_final_customers["Front Margin"] = df_final_customers["Front Margin"].map('€ {:,.2f}'.format)
            st.dataframe(df_final_customers, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Carica il file `free_analysis.csv` per popolare la sezione commerciale FASO.")
