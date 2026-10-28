import streamlit as st
import pandas as pd
import plotly.express as px

# Configurazione della pagina Streamlit (Layout largo per visualizzazione tabelle)
st.set_page_config(
    page_title="Dashboard Commerciale Avanzata", 
    layout="wide", 
    page_icon="📊"
)

st.title("📊 Dashboard Commerciale Integrata")
st.markdown("### Analisi Multilivello: Store, Aree e Reparti")
@st.cache_data
def load_and_clean_data(file_mensile):
    def parse_numeric(series):
        s_clean = series.astype(str).str.replace(r'\s+', '', regex=True)
        s_clean = s_clean.str.replace('"', '', regex=False)
        s_clean = s_clean.str.replace('(', '-', regex=False).str.replace(')', '', regex=False)
        s_clean = s_clean.str.replace(',', '', regex=False)
        s_clean = s_clean.replace(['-', '--', 'nan', 'NaN', ''], '0')
        return pd.to_numeric(s_clean, errors='coerce').fillna(0.0)

    # AGGIORNATO: Aggiunto encoding="latin1" per evitare l'UnicodeDecodeError
    df = pd.read_csv(file_mensile, sep=",", skip_blank_lines=True, encoding="latin1")
    
    df.columns = df.columns.str.replace('"', '').str.strip()
    for col in ["Store", "F/NF", "Sales Area Deparment", "Sales Department"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('"', '').str.strip()

    colonne_valori = [
        "DA - Sales TT", "DA - Sales TT PY Custom Cal", 
        "DA - Front Margin", "DA - Front Margin PY Custom Cal",
        "DA - Stock Days", "DA - Avg Stock", "DA - Stock Days PY Custom Cal",
        "DA - Shrinkage NNBP", "DA - Shrinkage NNBP PY Custom Cal"
    ]

    for col in colonne_valori:
        if col in df.columns:
            df[col] = parse_numeric(df[col])

    if "Date" in df.columns:
        df["Date"] = df["Date"].astype(str).str.replace('"', '').str.strip()
        df["Date_Parsed"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")

    return 
    
    df = pd.read_csv(file_mensile, sep=",", skip_blank_lines=True, encoding="latin1")
 
    # Pulizia nomi colonne e testi da spazi e doppie virgolette
    df.columns = df.columns.str.replace('"', '').str.strip()
    for col in ["Store", "F/NF", "Sales Area Deparment", "Sales Department"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('"', '').str.strip()

    # Colonne target da convertire in numeri fluttuanti (float)
    colonne_valori = [
        "DA - Sales TT", "DA - Sales TT PY Custom Cal", 
        "DA - Front Margin", "DA - Front Margin PY Custom Cal",
        "DA - Stock Days", "DA - Avg Stock", "DA - Stock Days PY Custom Cal",
        "DA - Shrinkage NNBP", "DA - Shrinkage NNBP PY Custom Cal"
    ]

    for col in colonne_valori:
        if col in df.columns:
            df[col] = parse_numeric(df[col])

    # Parsing asse temporale per calcolo ultimo stock disponibile
    if "Date" in df.columns:
        df["Date"] = df["Date"].astype(str).str.replace('"', '').str.strip()
        df["Date_Parsed"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")

    return df
def get_modern_kpi_card(icon, label, value_str, delta_val, py_info_str="", is_positive_good=True, show_delta=True):
    # Logica di colore dinamica basata sul tipo di indicatore (es: per lo shrinkage un aumento è negativo)
    is_positive = delta_val >= 0 if is_positive_good else delta_val <= 0
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
st.sidebar.header("📁 Caricamento File Sorgente")
u_men = st.sidebar.file_uploader("Carica il File Report Mensilizzazione (.csv)", type="csv")

if not u_men:
    st.info("💡 Carica il report commerciale di mensilizzazione (File 2) nel pannello laterale sinistro per attivare l'interfaccia.")
    st.stop()

# Iniezione dei dati nell'engine di pulizia
df_men = load_and_clean_data(u_men)

# Creazione delle colonne di filtro nella parte superiore della dashboard
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    lista_store = sorted(df_men["Store"].dropna().unique()) if "Store" in df_men.columns else []
    selected_store = st.selectbox("Seleziona Store:", lista_store)

df_filtrato_store = df_men[df_men["Store"] == selected_store] if "Store" in df_men.columns else df_men.copy()

with col_f2:
    lista_aree = ["--- TOTALE STORE ---"] + sorted(df_filtrato_store["Sales Area Deparment"].dropna().unique()) if "Sales Area Deparment" in df_filtrato_store.columns else ["--- TOTALE STORE ---"]
    selected_area = st.selectbox("Seleziona Area di Vendita:", lista_aree)

with col_f3:
    if selected_area != "--- TOTALE STORE ---" and "Sales Area Deparment" in df_filtrato_store.columns:
        df_filtrato_area = df_filtrato_store[df_filtrato_store["Sales Area Deparment"] == selected_area]
        lista_reparti = ["--- TOTALE AREA ---"] + sorted(df_filtrato_area["Sales Department"].dropna().unique()) if "Sales Department" in df_filtrato_area.columns else ["--- TOTALE AREA ---"]
    else:
        df_filtrato_area = df_filtrato_store.copy()
        lista_reparti = ["--- DETTAGLIO RICHIESTO ---"]
    selected_reparto = st.selectbox("Seleziona Reparto:", lista_reparti)
# Determinazione del perimetro dati in base ai filtri applicati
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
    
    # 1. Calcoli Fatturato (Sales TT)
    sales_tot = float(dati_vista['DA - Sales TT'].sum())
    sales_py_tot = float(dati_vista['DA - Sales TT PY Custom Cal'].sum())
    delta_sales_pct = ((sales_tot - sales_py_tot) / sales_py_tot * 100) if sales_py_tot != 0 else 0.0

    # 2. Calcoli Margine (Incidenza % pesata su Fatturato)
    margin_tot = float(dati_vista['DA - Front Margin'].sum())
    margin_py_tot = float(dati_vista['DA - Front Margin PY Custom Cal'].sum())
    margin_on_sales = (margin_tot / sales_tot * 100) if sales_tot != 0 else 0.0
    margin_py_on_sales = (margin_py_tot / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
    delta_margin_points = margin_on_sales - margin_py_on_sales 

    # 3. Calcoli Sfrido / Shrinkage (Incidenza % pesata su Fatturato)
    shrink_tot = float(dati_vista['DA - Shrinkage NNBP'].sum())
    shrink_py_tot = float(dati_vista['DA - Shrinkage NNBP PY Custom Cal'].sum())
    shrink_on_sales = (shrink_tot / sales_tot * 100) if sales_tot != 0 else 0.0
    shrink_py_on_sales = (shrink_py_tot / sales_py_tot * 100) if sales_py_tot != 0 else 0.0
    delta_shrink_points = shrink_on_sales - shrink_py_on_sales 

    # 4. Calcolo Giorni Rotazione Stock (Media della colonna)
    val_stock_days = float(dati_vista['DA - Stock Days'].mean())
    val_stock_days_py = float(dati_vista['DA - Stock Days PY Custom Cal'].mean())
    delta_stock_pct = ((val_stock_days - val_stock_days_py) / val_stock_days_py * 100) if val_stock_days_py != 0 else 0.0

    # 5. Estrazione AVG Stock relativo all'ultima data utile a file
    if "Date_Parsed" in dati_vista.columns and not dati_vista["Date_Parsed"].isna().all():
        ultima_data = dati_vista["Date_Parsed"].max()
        dati_ultima_data = dati_vista[dati_vista["Date_Parsed"] == ultima_data]
        avg_stock_ultimo = float(dati_ultima_data['DA - Avg Stock'].sum())
        data_stringa = ultima_data.strftime("%d/%m/%Y")
    else:
        avg_stock_ultimo = float(dati_vista['DA - Avg Stock'].sum())
        data_stringa = "Dati Correnti"

    # Creazione delle 4 colonne per il posizionamento delle KPI Cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(get_modern_kpi_card("💰", "Sales TT", f"€ {sales_tot:,.2f}", delta_sales_pct, f"PY: € {sales_py_tot:,.2f}", True), unsafe_allow_html=True)
    with m2:
        st.markdown(get_modern_kpi_card("📈", "Front Margin %", f"{margin_on_sales:.2f}%", delta_margin_points, f"PY: {margin_py_on_sales:.2f}% | Assoluto: € {margin_tot:,.2f}", True), unsafe_allow_html=True)
    with m3:
        st.markdown(get_modern_kpi_card("📦", "Stock Days", f"{val_stock_days:.1f} gg", delta_stock_pct, f"PY: {val_stock_days_py:.1f} gg", False), unsafe_allow_html=True)
    with m4:
        st.markdown(get_modern_kpi_card("📉", "Shrinkage %", f"{shrink_on_sales:.2f}%", delta_shrink_points, f"PY: {shrink_py_on_sales:.2f}% | Assoluto: € {shrink_tot:,.2f}", False), unsafe_allow_html=True)

    # Visualizzazione Tabella riassuntiva Stock Richiesta
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📦 Focus Capitale Circolante e Giacenze")
    df_stock_kpi = pd.DataFrame({
        "Indicatore di Performance": ["Giorni di Giacenza Correnti (Media)", "Giorni di Giacenza Anno Prec. (PY Media)", f"Valore Stock Disponibile (Ultimo Rilevamento: {data_stringa})"],
        "Valore Rilevato": [f"{val_stock_days:.1f} Giorni", f"{val_stock_days_py:.1f} Giorni", f"€ {avg_stock_ultimo:,.2f}"]
    })
    st.dataframe(df_stock_kpi, use_container_width=True, hide_index=True)

    # Creazione del grafico a barre Plotly per i reparti
    st.markdown("<br>#### 📊 Performance Mix Vendite per Singolo Reparto")
    df_rep_chart = dati_vista.groupby("Sales Department")["DA - Sales TT"].sum().reset_index().sort_values(by="DA - Sales TT", ascending=False)
    fig_rep = px.bar(df_rep_chart, x="Sales Department", y="DA - Sales TT", title="Fatturato per Reparto", labels={"DA - Sales TT": "Fatturato (€)", "Sales Department": "Reparto"})
    st.plotly_chart(fig_rep, use_container_width=True)
else:
    st.warning("⚠️ Nessun dato corrispondente trovato per i filtri selezionati.")
