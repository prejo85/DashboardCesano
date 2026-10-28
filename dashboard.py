import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Corporate Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stile CSS personalizzato per un look corporate e pulito
st.markdown("""
    <style>
    .main .block-container {padding-top: 2rem;}
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 5px solid #007bff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar per il caricamento dei file
st.sidebar.header("📁 Caricamento Documenti")
uploaded_files = st.sidebar.file_uploader(
    "Trascina qui i tuoi file (Excel o CSV)", 
    type=["xlsx", "csv"], 
    accept_multiple_files=True
)

# Funzione helper per leggere i dati in modo sicuro
def load_data(file):
    try:
        if file.name.endswith('.xlsx'):
            return pd.read_excel(file)
        else:
            return pd.read_csv(file)
    except Exception as e:
        st.sidebar.error(f"Errore nel caricamento di {file.name}: {e}")
        return None

# Dizionario per mappare i file caricati
data_dict = {}
if uploaded_files:
    for f in uploaded_files:
        data_dict[f.name] = load_data(f)
# Titolo Principale dell'Applicazione
st.title("📊 Enterprise Data Dashboard")
st.markdown("Analisi integrata dei dati aziendali e performance commerciali.")
st.write("---")

if uploaded_files:
    # Creazione dei Tab principali: la parte commerciale ha una vista dedicata
    tab_generale, tab_commerciale = st.tabs(["📈 Analisi Generale Dati", "💼 Focus Commerciale (Free Analysis)"])

    # ==========================================
    # TAB 1: ANALISI GENERALE (Altri File)
    # ==========================================
    with tab_generale:
        st.header("Visualizzazione Dataset Globali")
        
        # Filtra i file escludendo quello di analisi commerciale per questa sezione
        altri_file = [name for name in data_dict.keys() if "free" not in name.lower() and "analysis" not in name.lower()]
        
        if altri_file:
            selected_file = st.selectbox("Seleziona il report da analizzare:", altri_file)
            df = data_dict[selected_file]
            
            if df is not None:
                # KPI Generici di test (adattali alle tue colonne reali, es: df['Totale'].sum())
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(label="Righe Totali", value=f"{df.shape[0]:,}")
                with col2:
                    st.metric(label="Colonne Rilevate", value=df.shape[1])
                with col3:
                    st.metric(label="Campi Univoci", value=df.iloc[:, 0].nunique() if not df.empty else 0)
                
                st.subheader("Anteprima Dati")
                st.dataframe(df, use_container_width=True)
                
                # Grafico esplorativo dinamico basato sul tipo di colonne
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                if len(numeric_cols) >= 1:
                    st.subheader("Esplorazione Trend")
                    fig_gen = px.line(df, y=numeric_cols[0], title=f"Andamento variabile: {numeric_cols[0]}")
                    fig_gen.update_layout(template="plotly_white")
                    st.plotly_chart(fig_gen, use_container_width=True)
        else:
            st.info("Carica altri file di report per abilitare la vista generale. I file nominati 'Free Analysis' verranno mostrati nel tab commerciale.")
    # ==========================================
    # TAB 2: SEZIONE COMMERCIALE (Free Analysis)
    # ==========================================
    with tab_commerciale:
        st.header("💼 Business & Commercial Overview")
        
        # Identifica automaticamente il file "Free Analysis"
        free_analysis_key = next((name for name in data_dict.keys() if "free" in name.lower() or "analysis" in name.lower()), None)
        
        if free_analysis_key:
            df_comm = data_dict[free_analysis_key]
            
            if df_comm is not None:
                st.success(file_name:=f"Dati estratti con successo da: {free_analysis_key}")
                
                # Sostituisci i nomi delle colonne qui sotto ('Ricavi', 'Stato', 'Data') 
                # con i nomi reali presenti nel tuo file Excel/CSVcommerciale
                
                # Blocco KPI Commerciali Superiori
                c1, c2, c3 = st.columns(3)
                with c1:
                    # Esempio: Calcolo fittizio o reale se esiste la colonna Valore/Ricavi
                    valore_totale = df_comm.select_dtypes(include=['number']).iloc[:, 0].sum() if not df_comm.select_dtypes(include=['number']).empty else 0
                    st.metric(label="Volume d'Affari Potenziale", value=f"€ {valore_totale:,.2f}")
                with c2:
                    st.metric(label="Trattative / Lead Totali", value=f"{df_comm.shape[0]}")
                with c3:
                    # Assumendo una colonna di classificazione o stato
                    stato_col = df_comm.columns[1] if len(df_comm.columns) > 1 else df_comm.columns[0]
                    st.metric(label="Target Principale", value=f"{df_comm[stato_col].mode()[0] if not df_comm.empty else 'N/A'}")
                
                st.write("---")
                
                # Layout a due colonne per grafici e tabelle commerciali
                g_col1, g_col2 = st.columns([3, 2])
                
                with g_col1:
                    st.subheader("Performance e Distribuzione Commerciale")
                    # Genera un grafico a barre basato sulle prime due colonne utili
                    if len(df_comm.columns) >= 2:
                        fig_comm = px.bar(
                            df_comm, 
                            x=df_comm.columns[0], 
                            y=df_comm.select_dtypes(include=['number']).columns[0] if not df_comm.select_dtypes(include=['number']).empty else df_comm.columns[1],
                            color_discrete_sequence=["#2b5c8f"],
                            title="Performance Commerciale Dettagliata"
                        )
                        fig_comm.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
                        st.plotly_chart(fig_comm, use_container_width=True)
                
                with g_col2:
                    st.subheader("Data Table Commerciale")
                    st.dataframe(df_comm, use_container_width=True, height=350)
        else:
            st.warning("⚠️ Nessun file 'Free Analysis' rilevato. Assicurati che il nome del file contenga le parole 'free' o 'analysis' per sbloccare questa sezione.")
else:
    # Schermata di benvenuto se l'utente non ha ancora inserito file
    st.info("ℹ️ Per iniziare, trascina i tuoi file operativi e il file 'Free Analysis' nella barra laterale sinistra.")
