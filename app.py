import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Monitor S.E.R. | Anahat", page_icon="🧘", layout="centered")
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>""", unsafe_allow_html=True)

# --- 2. CONEXIÓN DIRECTA POR ID ---
def conectar_db():
    # ID QUE TU ME DISTE
    SHEET_ID = "1y5FIw_mvGUSKwhc41JaB01Ti6_93dBJmfC1BTpqrvHw"
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Abrimos por ID (Mucho más seguro)
        sheet = client.open_by_key(SHEET_ID).sheet1
        return sheet
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        st.stop()

# --- 3. CÁLCULOS ---
def calcular_ser(respuestas):
    # A. ENERGÍA (Inverso)
    raw_ene = respuestas['insomnio'] + respuestas['neblina'] + respuestas['suspiros'] + respuestas['aire']
    score_ene = ((20 - raw_ene) / 20) * 100 
    
    # B. REGULACIÓN (Inverso)
    raw_reg = respuestas['espalda'] + respuestas['estomago'] + respuestas['panico'] + respuestas['cabeza']
    score_reg = ((20 - raw_reg) / 20) * 100 
    
    # C. SOMÁTICA (Mixto)
    directas = respuestas['incomodo'] + respuestas['resp'] + respuestas['postura'] + respuestas['emocion'] + respuestas['calma']
    inversas = (5 - respuestas['distraigo']) + (5 - respuestas['preocupo']) + (5 - respuestas['ignoro'])
    score_som = ((directas + inversas) / 40) * 100
    
    indice = (score_ene + score_reg + score_som) / 3
    return score_som, score_ene, score_reg, indice

# --- 4. INTERFAZ ---
st.title("👁️ Tu Monitor S.E.R.")

# Prueba silenciosa de conexión
try:
    sheet = conectar_db()
    st.toast("Conectado a Google Sheets", icon="✅")
except:
    st.error("No se pudo conectar a la hoja.")

email = st.text_input("Ingresa tu correo registrado para iniciar:").strip().lower()

if email:
    tab1, tab2 = st.tabs(["📝 NUEVA MEDICIÓN", "📈 MI PROGRESO"])
    
    with tab1:
        st.write("### ¿Cómo te sientes hoy?")
        with st.form("test_ser"):
            st.info("SECCIÓN 1: ENERGÍA")
            e1 = st.slider("Insomnio / sueño no reparador", 0, 5, 0)
            e2 = st.slider("Neblina mental / Falta de foco", 0, 5, 0)
            e3 = st.slider("Suspiros frecuentes involuntarios", 0, 5, 0)
            e4 = st.slider("Sensación de falta de aire", 0, 5, 0)
            
            st.info("SECCIÓN 2: REGULACIÓN")
            r1 = st.slider("Dolor de espalda / tensión", 0, 5, 0)
            r2 = st.slider("Problemas estomacales", 0, 5, 0)
            r3 = st.slider("Ataques de pánico / ansiedad", 0, 5, 0)
            r4 = st.slider("Dolor de cabeza frecuente", 0, 5, 0)
            
            st.info("SECCIÓN 3: SOMÁTICA")
            s1 = st.slider("Noto cuando me siento incómodo", 0, 5, 0)
            s2 = st.slider("Noto cambios en mi respiración", 0, 5, 0)
            s3 = st.slider("Noto mi postura al conversar", 0, 5, 0)
            s4 = st.slider("Noto dónde siento las emociones", 0, 5, 0)
            s5 = st.slider("Encuentro calma interna ante el caos", 0, 5, 0)
            
            st.markdown("*Hébitos:*")
            s_inv1 = st.slider("Me distraigo para no sentir", 0, 5, 0)
            s_inv2 = st.slider("Me preocupo apenas siento molestia", 0, 5, 0)
            s_inv3 = st.slider("Ignoro el dolor hasta que es severo", 0, 5, 0)
            
            nombre_input = st.text_input("Tu Nombre:")
            
            if st.form_submit_button("CALCULAR"):
                if nombre_input:
                    datos = {
                        'insomnio': e1, 'neblina': e2, 'suspiros': e3, 'aire': e4,
                        'espalda': r1, 'estomago': r2, 'panico': r3, 'cabeza': r4,
                        'incomodo': s1, 'resp': s2, 'postura': s3, 'emocion': s4, 'calma': s5,
                        'distraigo': s_inv1, 'preocupo': s_inv2, 'ignoro': s_inv3
                    }
                    s_s, s_e, s_r, idx = calcular_ser(datos)
                    
                    if idx < 45: nivel = "🔴 Supervivencia"
                    elif idx < 75: nivel = "🟡 Resistencia"
                    else: nivel = "🟢 Coherencia"
                    
                    fecha = datetime.now().strftime("%Y-%m-%d")
                    sheet.append_row([fecha, email, nombre_input, s_s, s_e, s_r, idx, nivel])
                    st.success("✅ ¡Guardado!")
                    st.balloons()
                else:
                    st.warning("Escribe tu nombre.")

    with tab2:
        try:
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            if not df.empty:
                mis_datos = df[df['Email'] == email]
                if not mis_datos.empty:
                    ultimo = mis_datos.iloc[-1]
                    col1, col2 = st.columns([1,2])
                    col1.metric("TU ÍNDICE S.E.R.", f"{int(ultimo['INDICE_TOTAL'])}%")
                    col2.info(f"Estado: **{ultimo['Nivel']}**")
                    
                    st.subheader("Tu Mapa vs La Tribu")
                    promedio = df[['Score_Somatica', 'Score_Energia', 'Score_Regulacion']].mean()
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(r=[ultimo['Score_Somatica'], ultimo['Score_Energia'], ultimo['Score_Regulacion']], theta=['Somática','Energía','Regulación'], fill='toself', name='TÚ'))
                    fig.add_trace(go.Scatterpolar(r=[promedio['Score_Somatica'], promedio['Score_Energia'], promedio['Score_Regulacion']], theta=['Somática','Energía','Regulación'], fill='toself', name='TRIBU', opacity=0.3))
                    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
                    st.plotly_chart(fig)
                else:
                    st.warning("No tienes datos aún.")
        except:
            st.error("Error leyendo datos.")
