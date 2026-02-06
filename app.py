import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pytz # Zona horaria CDMX
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# 1. CONFIGURACIÓN ESTÉTICA Y BRANDING
# ==========================================
st.set_page_config(page_title="Monitor S.E.R. | Anahat", page_icon="🧘", layout="centered")

st.markdown("""<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .stMetric {text-align: center;}
    .big-font {font-size:20px !important; font-weight: bold; color: #8A2BE2;}
    
    /* Estilo para la Tabla de Niveles */
    .levels-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
        font-size: 14px;
    }
    .levels-table th {
        background-color: #f0f2f6;
        padding: 8px;
        text-align: left;
        border-bottom: 2px solid #ddd;
    }
    .levels-table td {
        padding: 8px;
        border-bottom: 1px solid #eee;
    }
    
    .scale-legend {
        background-color: #e6e6fa; 
        color: #000000 !important; 
        padding: 15px; 
        border-radius: 10px; 
        text-align: center; 
        font-weight: bold; 
        font-size: 16px;
        margin-bottom: 25px;
        border: 1px solid #dcdcdc;
    }
</style>""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN A GOOGLE SHEETS
# ==========================================
def conectar_db():
    SHEET_ID = "1y5FIw_mvGUSKwhc41JaB01Ti6_93dBJmfC1BTpqrvHw"
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet("DB_Anahat_Clientes")
        return sheet
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        st.stop()

# ==========================================
# 3. LÓGICA MATEMÁTICA (ESCALA 1-5)
# ==========================================
def calcular_ser_v2(respuestas):
    # A. ENERGÍA (Inversas: 6 - x)
    raw_ene = [respuestas['e1'], respuestas['e2'], respuestas['e3'], respuestas['e4']]
    score_ene = sum([(6 - x) for x in raw_ene]) / 4
    
    # B. REGULACIÓN (Inversas: 6 - x)
    raw_reg = [respuestas[f'r{i}'] for i in range(1, 9)]
    score_reg = sum([(6 - x) for x in raw_reg]) / 8
    
    # C. SOMÁTICA (Directas: x)
    raw_som = [respuestas[f's{i}'] for i in range(1, 18)]
    score_som = sum(raw_som) / 17
    
    # Promedio Final
    indice = (score_ene + score_reg + score_som) / 3
    
    return round(score_som, 2), round(score_ene, 2), round(score_reg, 2), round(indice, 2)

def obtener_diagnostico(indice):
    if indice < 2.0:
        titulo = "🔴 NIVEL 1: DESCONEXIÓN (Colapso)"
        desc = "Tu sistema está en 'ahorro de energía' extremo. Sensación de apagado o fatiga crónica."
    elif indice < 3.0:
        titulo = "🟠 NIVEL 2: SOBREVIVENCIA (Alerta)"
        desc = "Tu sistema está en lucha/huida. Mucha energía desregulada, ansiedad o dolor agudo."
    elif indice < 4.0:
        titulo = "🟡 NIVEL 3: RESISTENCIA (Funcional)"
        desc = "Eres funcional y productivo, pero a un costo energético alto. 'Aguantas' el estrés."
    elif indice < 4.6:
        titulo = "🟢 NIVEL 4: REGULACIÓN (Equilibrio)"
        desc = "Tienes herramientas. Sientes el estrés pero logras volver a la calma."
    else:
        titulo = "🟣 NIVEL 5: COHERENCIA (Fluidez)"
        desc = "Estado óptimo. Mente y cuerpo alineados, con energía disponible para crear."
    return titulo, desc

# ==========================================
# 4. GRÁFICAS
# ==========================================
def graficar_radar(val_som, val_ene, val_reg, prom_som, prom_ene, prom_reg):
    fig = go.Figure()
    # TÚ
    fig.add_trace(go.Scatterpolar(
        r=[val_som, val_ene, val_reg], 
        theta=['SOMÁTICA', 'ENERGÍA', 'REGULACIÓN'], 
        fill='toself', name='TÚ', line_color='#8A2BE2'
    ))
    # COMUNIDAD
    if prom_som > 0:
        fig.add_trace(go.Scatterpolar(
            r=[prom_som, prom_ene, prom_reg], 
            theta=['SOMÁTICA', 'ENERGÍA', 'REGULACIÓN'], 
            fill='toself', name='COMUNIDAD', line_color='gray', opacity=0.3, line_dash='dot'
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5.2],
                tickvals=[1, 2, 3, 4, 5],
                ticktext=['1', '2', '3', '4', '5'],
                tickfont=dict(color="black", size=14, family="Arial Black")
            )
        ),
        showlegend=True,
        height=350,
        margin=dict(t=20, b=20, l=40, r=40)
    )
    return fig

def graficar_barra_comparativa(titulo, valor_usuario, valor_grupo, color_barra):
    df_chart = pd.DataFrame({
        'Entidad': ['TÚ', 'COMUNIDAD'],
        'Puntaje': [valor_usuario, valor_grupo],
        'Color': [color_barra, 'gray']
    })
    fig = px.bar(df_chart, x='Puntaje', y='Entidad', orientation='h', text='Puntaje', title=titulo, color='Color', color_discrete_map={color_barra: color_barra, 'gray': 'gray'})
    fig.update_layout(xaxis=dict(range=[0, 5.5]), showlegend=False, height=180, margin=dict(l=20, r=20, t=30, b=20))
    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    return fig

# ==========================================
# 5. DASHBOARD DE RESULTADOS (STORYTELLING)
# ==========================================
def mostrar_dashboard_completo(df, email_usuario):
    # 1. Limpieza de columnas
    df.columns = [c.strip() for c in df.columns]
    
    if 'Email' not in df.columns:
        st.error("Error leyendo la base de datos (Columna Email no encontrada).")
        return

    # 2. Convertir a números
    cols_num = ['Score_Somatica', 'Score_Energia', 'Score_Regulacion', 'INDICE_TOTAL']
    for c in cols_num:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce')

    # 3. FILTRAR DATOS VÁLIDOS PARA COMUNIDAD (Ignorar datos viejos > 5)
    df_clean_comunidad = df[df['INDICE_TOTAL'] <= 5.5] # Margen de seguridad
    
    # 4. Datos del usuario
    mis_datos = df[df['Email'] == email_usuario]
    
    if mis_datos.empty:
        st.warning("No se encontraron datos.")
        return

    ultimo = mis_datos.iloc[-1]
    idx_val = ultimo.get('INDICE_TOTAL', 0)
    titulo, desc = obtener_diagnostico(idx_val)
    
    # 5. Calcular Promedios Comunidad (Solo de datos limpios)
    promedio_comunidad = df_clean_comunidad['INDICE_TOTAL'].mean()
    p_som = df_clean_comunidad['Score_Somatica'].mean()
    p_ene = df_clean_comunidad['Score_Energia'].mean()
    p_reg = df_clean_comunidad['Score_Regulacion'].mean()

    # --- RENDERIZADO DEL DASHBOARD ---
    st.divider()
    
    # 1. EDUCACIÓN
    st.markdown("### 1. ¿Qué estoy midiendo?")
    c1, c2, c3 = st.columns(3)
    with c1: st.info("**🧘 SOMÁTICA**\n\nConexión: Capacidad de 'escuchar' las señales internas.")
    with c2: st.info("**⚡ ENERGÍA**\n\nVitalidad: Presupuesto real de energía vs. estrés.")
    with c3: st.info("**🌊 REGULACIÓN**\n\nEquilibrio: Capacidad de volver a la calma.")

    # 2. CONTEXTO (TABLA DE NIVELES)
    st.markdown("### 2. Escala de Niveles")
    st.markdown("""
    <table class="levels-table">
      <tr><th>Nivel</th><th>Estado</th><th>Descripción</th></tr>
      <tr><td>🟣 4.6 - 5.0</td><td><b>COHERENCIA</b></td><td>Estado óptimo. Fluidez y creatividad.</td></tr>
      <tr><td>🟢 4.0 - 4.5</td><td><b>REGULACIÓN</b></td><td>Equilibrio. Tienes herramientas para gestionar el estrés.</td></tr>
      <tr><td>🟡 3.0 - 3.9</td><td><b>RESISTENCIA</b></td><td>Funcional pero costoso. "Aguantas" mucho.</td></tr>
      <tr><td>🟠 2.0 - 2.9</td><td><b>SOBREVIVENCIA</b></td><td>Alerta máxima. Ansiedad, dolor o reactividad.</td></tr>
      <tr><td>🔴 1.0 - 1.9</td><td><b>DESCONEXIÓN</b></td><td>Colapso. Fatiga crónica o "apagado".</td></tr>
    </table>
    """, unsafe_allow_html=True)

    # 3. KPI Principal
    st.markdown("### 3. Tu Diagnóstico Actual")
    col_kpi1, col_kpi2 = st.columns([1, 2])
    with col_kpi1:
        st.markdown(f"<h1 style='text-align: center; color: #8A2BE2; font-size: 60px; margin-bottom: 0px;'>{idx_val}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: gray; font-weight: bold;'>Promedio Comunidad: {promedio_comunidad:.2f}</p>", unsafe_allow_html=True)
    
    with col_kpi2:
        st.success(f"**{titulo}**")
        st.write(desc)
    
    # 4. GRÁFICAS
    st.markdown("### 4. Tu Mapa vs La Comunidad")
    
    # Radar
    fig_radar = graficar_radar(
        ultimo['Score_Somatica'], ultimo['Score_Energia'], ultimo['Score_Regulacion'], 
        p_som, p_ene, p_reg
    )
    st.plotly_chart(fig_radar, use_container_width=True)
    
    # Barras
    gc1, gc2, gc3 = st.columns(3)
    with gc1: st.plotly_chart(graficar_barra_comparativa("Somática", ultimo['Score_Somatica'], p_som, "#FF69B4"), use_container_width=True)
    with gc2: st.plotly_chart(graficar_barra_comparativa("Energía", ultimo['Score_Energia'], p_ene, "#FFD700"), use_container_width=True)
    with gc3: st.plotly_chart(graficar_barra_comparativa("Regulación", ultimo['Score_Regulacion'], p_reg, "#00BFFF"), use_container_width=True)
    
    # Evolución
    if len(mis_datos) > 1:
        st.divider()
        st.markdown("### 📈 TU EVOLUCIÓN")
        fig_line = px.line(mis_datos, x='Fecha', y='INDICE_TOTAL', markers=True)
        fig_line.update_layout(yaxis=dict(range=[1, 5.5]))
        fig_line.update_traces(line_color='#8A2BE2', line_width=4)
        st.plotly_chart(fig_line, use_container_width=True)

# ==========================================
# 6. APP PRINCIPAL
# ==========================================
# st.image("logo.png", width=150) # Descomentar cuando tengas el logo

# --- ENCABEZADO TIPO MEMBRETE ---
st.markdown("<h4 style='text-align: left; color: gray;'>Unidad Consciente</h4>", unsafe_allow_html=True)

# --- TÍTULO PRINCIPAL ---
st.title("Índice S.E.R. (Somática, Energía, Regulación) | Comunidad Anahat")

try: sheet = conectar_db()
except: pass

# --- INICIO DEL FORMULARIO ---
with st.form("test_ser_v2"):
    
    # 1. NOMBRE (Primero)
    nombre_input = st.text_input("Tu Nombre Completo:")
    
    st.markdown("""
    <div class="scale-legend">
    ESCALA: 1 = Nunca | 2 = Casi nunca | 3 = A veces | 4 = Frecuentemente | 5 = Siempre
    </div>
    """, unsafe_allow_html=True)
    
    # 2. PREGUNTAS
    st.info("⚡ ENERGÍA")
    e1 = st.slider("1. ¿Tienes insomnio con frecuencia?", 1, 5, 1)
    e2 = st.slider("2. ¿Tienes dificultad para concentrarte?", 1, 5, 1)
    e3 = st.slider("3. ¿Sientes falta de aire frecuentemente?", 1, 5, 1)
    e4 = st.slider("4. ¿Te dan infecciones respiratorias con frecuencia?", 1, 5, 1)
    
    st.info("🌊 REGULACIÓN")
    r1 = st.slider("1. ¿Sientes dolor de espalda?", 1, 5, 1)
    r2 = st.slider("2. ¿Tienes problemas estomacales?", 1, 5, 1)
    r3 = st.slider("3. ¿Experimentas ataques de pánico?", 1, 5, 1)
    r4 = st.slider("4. ¿Tienes dolores de cabeza?", 1, 5, 1)
    r5 = st.slider("5. ¿Suspiras frecuentemente?", 1, 5, 1)
    r6 = st.slider("6. ¿Ignoras la tensión física hasta que es severa?", 1, 5, 1)
    r7 = st.slider("7. ¿Te distraes de las sensaciones de malestar?", 1, 5, 1)
    r8 = st.slider("8. ¿Te preocupas apenas sientes una molestia?", 1, 5, 1)
    
    st.info("🧘 SOMÁTICA")
    s1 = st.slider("1. ¿Notas cuando te sientes incómodo en tu cuerpo?", 1, 5, 1)
    s2 = st.slider("2. ¿Notas cambios en mi respiración?", 1, 5, 1)
    s3 = st.slider("3. ¿Puedes prestar atención a tu respiración sin distraerte?", 1, 5, 1)
    s4 = st.slider("4. ¿Puedes mantener consciencia interna aunque haya movimiento alrededor?", 1, 5, 1)
    s5 = st.slider("5. ¿Al conversar, puedes prestar atención a tu postura?", 1, 5, 1)
    s6 = st.slider("6. ¿Puedes volver a concentrarte en tu cuerpo si te distraes?", 1, 5, 1)
    s7 = st.slider("7. ¿Puedes redirigir tu atención de pensamientos a sensaciones?", 1, 5, 1)
    s8 = st.slider("8. ¿Mantienes consciencia del cuerpo aunque una parte duela?", 1, 5, 1)
    s9 = st.slider("9. ¿Eres capaz de enfocarte en tu cuerpo como un todo?", 1, 5, 1)
    s10 = st.slider("10. ¿Notas cómo cambia tu cuerpo cuando estás enojado?", 1, 5, 1)
    s11 = st.slider("11. ¿Notas que tu cuerpo se siente diferente tras una experiencia pacífica?", 1, 5, 1)
    s12 = st.slider("12. ¿Notas que tu respiración se libera cuando estás cómodo?", 1, 5, 1)
    s13 = st.slider("13. ¿Al sentirte abrumado, encuentras un lugar de calma dentro de ti?", 1, 5, 1)
    s14 = st.slider("14. ¿Al sentirte tenso, usas tu respiración para reducir tensión?", 1, 5, 1)
    s15 = st.slider("15. ¿Cuando estás estresado, sabes relajarte físicamente?", 1, 5, 1)
    s16 = st.slider("16. ¿Respetas lo que tu cuerpo pide (descanso, comida)?", 1, 5, 1)
    s17 = st.slider("17. ¿Al tomar decisiones, consultas tus sensaciones corporales?", 1, 5, 1)
    
    st.divider()
    
    # 3. CORREO (Al final)
    email_input = st.text_input("Tu Correo Electrónico (Para guardar tu historial):").strip().lower()
    
    submitted = st.form_submit_button("CALCULAR ÍNDICE")
    
    if submitted:
        if not nombre_input or not email_input:
            st.error("⚠️ Por favor ingresa tu Nombre y Correo para ver tus resultados.")
        else:
            # Cálculos
            datos = {
                'e1': e1, 'e2': e2, 'e3': e3, 'e4': e4,
                'r1': r1, 'r2': r2, 'r3': r3, 'r4': r4, 'r5': r5, 'r6': r6, 'r7': r7, 'r8': r8,
                's1': s1, 's2': s2, 's3': s3, 's4': s4, 's5': s5, 's6': s6, 's7': s7, 's8': s8, 's9': s9,
                's10': s10, 's11': s11, 's12': s12, 's13': s13, 's14': s14, 's15': s15, 's16': s16, 's17': s17
            }
            
            s_s, s_e, s_r, idx = calcular_ser_v2(datos)
            titulo, desc = obtener_diagnostico(idx)
            
            # Zona Horaria México
            zona_mx = pytz.timezone('America/Mexico_City')
            fecha = datetime.now(zona_mx).strftime("%Y-%m-%d")
            
            # Guardar en Sheet
            try:
                sheet.append_row([
                    fecha, email_input, nombre_input, 
                    s_s, s_e, s_r, idx, titulo
                ])
                st.toast("✅ Datos guardados con éxito")
            except Exception as e:
                st.error(f"Error guardando: {e}")

# --- MOSTRAR REPORTE INMEDIATAMENTE SI YA HAY DATOS ---
if email_input:
    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            mostrar_dashboard_completo(df, email_input)
    except Exception as e:
        # Silencioso si no hay conexión o datos
        pass
