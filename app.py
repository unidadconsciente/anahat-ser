import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Monitor S.E.R. | Anahat", page_icon="🧘", layout="centered")

# Ocultamos el menú de desarrollador para que se vea como una App Pro
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>""", unsafe_allow_html=True)

# --- 2. CONEXIÓN CON GOOGLE SHEETS (LA BASE DE DATOS) ---
def conectar_db():
    # Definimos los permisos que necesitamos
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # Leemos la "Llave" (JSON) desde los secretos de Streamlit (esto lo configuras en la nube)
    # Streamlit guarda esto de forma segura para no poner la contraseña en el código
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # Abrimos tu hoja de cálculo
    sheet = client.open('DB_Anahat_Clientes').sheet1
    return sheet

# --- 3. LÓGICA MATEMÁTICA (TU FORMULA) ---
def calcular_ser(respuestas):
    # Todo se convierte a base 100.
    
    # A. ENERGÍA (4 preguntas inversas: 5=Malo)
    # Insomnio, Neblina, Suspiros, Aire. Total max crude = 20.
    raw_ene = respuestas['insomnio'] + respuestas['neblina'] + respuestas['suspiros'] + respuestas['aire']
    score_ene = ((20 - raw_ene) / 20) * 100 # Invertimos
    
    # B. REGULACIÓN (4 preguntas inversas: 5=Malo)
    # Espalda, Estomago, Panico, Cabeza. Total max crude = 20.
    raw_reg = respuestas['espalda'] + respuestas['estomago'] + respuestas['panico'] + respuestas['cabeza']
    score_reg = ((20 - raw_reg) / 20) * 100 # Invertimos
    
    # C. SOMÁTICA (8 preguntas mixtas)
    # Directas (5): Incomodo, Resp, Postura, Emocion, Calma
    directas = respuestas['incomodo'] + respuestas['resp'] + respuestas['postura'] + respuestas['emocion'] + respuestas['calma']
    # Inversas (3): Distraigo, Preocupo, Ignoro (5=Malo)
    inversas = (5 - respuestas['distraigo']) + (5 - respuestas['preocupo']) + (5 - respuestas['ignoro'])
    
    score_som = ((directas + inversas) / 40) * 100
    
    # INDICE TOTAL
    indice = (score_ene + score_reg + score_som) / 3
    return score_som, score_ene, score_reg, indice

# --- 4. LA INTERFAZ (LO QUE VE EL USUARIO) ---
st.title("👁️ Tu Monitor S.E.R.")
st.markdown("Unidad Consciente: **Somática • Energía • Regulación**")

# Login simple
email = st.text_input("Ingresa tu correo registrado para iniciar:").strip().lower()

if email:
    # Pestañas para organizar la vista
    tab1, tab2 = st.tabs(["📝 NUEVA MEDICIÓN", "📈 MI PROGRESO"])
    
    # --- PESTAÑA 1: EL FORMULARIO ---
    with tab1:
        st.write("### ¿Cómo te sientes esta semana?")
        with st.form("test_ser"):
            
            st.info("SECCIÓN 1: ENERGÍA (Vitalidad)")
            e1 = st.slider("Insomnio o sueño no reparador", 0, 5, 0)
            e2 = st.slider("Neblina mental / Falta de foco", 0, 5, 0)
            e3 = st.slider("Suspiros frecuentes involuntarios", 0, 5, 0)
            e4 = st.slider("Sensación de falta de aire", 0, 5, 0)
            
            st.info("SECCIÓN 2: REGULACIÓN (Carga de Estrés)")
            r1 = st.slider("Dolor de espalda / tensión", 0, 5, 0)
            r2 = st.slider("Problemas estomacales", 0, 5, 0)
            r3 = st.slider("Ataques de pánico / ansiedad", 0, 5, 0)
            r4 = st.slider("Dolor de cabeza frecuente", 0, 5, 0)
            
            st.info("SECCIÓN 3: SOMÁTICA (Conexión)")
            st.caption("0 = Nunca | 5 = Siempre")
            s1 = st.slider("Noto cuando me siento incómodo", 0, 5, 0)
            s2 = st.slider("Noto cambios en mi respiración", 0, 5, 0)
            s3 = st.slider("Noto mi postura al conversar", 0, 5, 0)
            s4 = st.slider("Noto dónde siento las emociones", 0, 5, 0)
            s5 = st.slider("Encuentro calma interna ante el caos", 0, 5, 0)
            
            st.markdown("*Hébitos (Frecuencia):*")
            s_inv1 = st.slider("Me distraigo para no sentir (celular/comida)", 0, 5, 0)
            s_inv2 = st.slider("Me preocupo apenas siento una molestia", 0, 5, 0)
            s_inv3 = st.slider("Ignoro el dolor hasta que es severo", 0, 5, 0)
            
            nombre_input = st.text_input("Confirma tu Nombre:")
            
            btn_enviar = st.form_submit_button("CALCULAR RESULTADOS")
            
            if btn_enviar and nombre_input:
                # Diccionario de datos
                datos = {
                    'insomnio': e1, 'neblina': e2, 'suspiros': e3, 'aire': e4,
                    'espalda': r1, 'estomago': r2, 'panico': r3, 'cabeza': r4,
                    'incomodo': s1, 'resp': s2, 'postura': s3, 'emocion': s4, 'calma': s5,
                    'distraigo': s_inv1, 'preocupo': s_inv2, 'ignoro': s_inv3
                }
                
                s_s, s_e, s_r, idx = calcular_ser(datos)
                
                # Nivel
                if idx < 45: nivel = "🔴 Supervivencia"
                elif idx < 75: nivel = "🟡 Resistencia"
                else: nivel = "🟢 Coherencia"
                
                # Guardar en Sheet
                try:
                    sheet = conectar_db()
                    fecha = datetime.now().strftime("%Y-%m-%d")
                    sheet.append_row([fecha, email, nombre_input, s_s, s_e, s_r, idx, nivel])
                    st.success("✅ ¡Datos guardados! Ve a la pestaña 'MI PROGRESO'.")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

    # --- PESTAÑA 2: RESULTADOS Y GRÁFICAS ---
    with tab2:
        try:
            sheet = conectar_db()
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            
            if not df.empty:
                # Filtrar solo al usuario actual
                mis_datos = df[df['Email'] == email]
                
                if not mis_datos.empty:
                    ultimo = mis_datos.iloc[-1]
                    
                    # 1. MOSTRAR NIVEL ACTUAL
                    col1, col2 = st.columns([1,2])
                    col1.metric("TU ÍNDICE S.E.R.", f"{int(ultimo['INDICE_SER'])}%")
                    col2.info(f"Estado Actual: **{ultimo['Nivel']}**")
                    
                    # 2. GRÁFICA DE RADAR (YO vs TRIBU)
                    st.subheader("Tu Mapa vs La Tribu")
                    
                    # Promedio del grupo (excluyendo datos vacíos)
                    promedio_grupo = df[['Somatica', 'Energia', 'Regulacion']].mean()
                    
                    categorias = ['Somática', 'Energía', 'Regulación']
                    
                    fig = go.Figure()
                    # Yo
                    fig.add_trace(go.Scatterpolar(
                        r=[ultimo['Somatica'], ultimo['Energia'], ultimo['Regulacion']],
                        theta=categorias, fill='toself', name='TÚ', line_color='#8A2BE2'
                    ))
                    # Tribu
                    fig.add_trace(go.Scatterpolar(
                        r=[promedio_grupo['Somatica'], promedio_grupo['Energia'], promedio_grupo['Regulacion']],
                        theta=categorias, fill='toself', name='TRIBU', line_color='gray', opacity=0.3
                    ))
                    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 3. GRÁFICA DE EVOLUCIÓN (SI HAY MÁS DE 1 DATO)
                    if len(mis_datos) > 1:
                        st.subheader("Tu Evolución")
                        fig_line = px.line(mis_datos, x='Fecha', y='INDICE_SER', markers=True, title="Tu progreso en el tiempo")
                        fig_line.update_traces(line_color='#8A2BE2')
                        st.plotly_chart(fig_line, use_container_width=True)
                    else:
                        st.info("💡 Este es tu primer registro. ¡El próximo mes verás aquí tu línea de progreso!")
                        
                else:
                    st.warning("No tienes registros aún. Llena el formulario en la primera pestaña.")
        except Exception as e:
            st.error("Conectando con la base de datos...")

else:
    st.info("👈 Ingresa tu email arriba para ver tus datos.")
