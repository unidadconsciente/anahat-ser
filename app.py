import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# 1. CONFIGURACIÓN ESTÉTICA
# ==========================================
st.set_page_config(page_title="Monitor S.E.R. | Anahat", page_icon="🧘", layout="centered")
st.markdown("""<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .stMetric {text-align: center;}
    .big-font {font-size:20px !important; font-weight: bold; color: #8A2BE2;}
    .info-box {background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px;}
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
        sheet = client.open_by_key(SHEET_ID).sheet1
        return sheet
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        st.stop()

# ==========================================
# 3. MATEMÁTICA: ESCALA 1.0 a 5.0
# ==========================================
def calcular_ser(respuestas):
    # Fórmula: (Ratio de Bienestar * 4) + 1
    # Resultado: 1.0 (Peor) a 5.0 (Mejor)
    
    # A. ENERGÍA (Inverso: 0 es mejor) -> Total 20 pts
    # Si suma 0 (perfecto) -> (20-0)/20 = 1.0 -> 1*4+1 = 5.0
    raw_ene = respuestas['insomnio'] + respuestas['neblina'] + respuestas['suspiros'] + respuestas['aire']
    score_ene = ((20 - raw_ene) / 20) * 4 + 1
    
    # B. REGULACIÓN (Inverso: 0 es mejor) -> Total 20 pts
    raw_reg = respuestas['espalda'] + respuestas['estomago'] + respuestas['panico'] + respuestas['cabeza']
    score_reg = ((20 - raw_reg) / 20) * 4 + 1
    
    # C. SOMÁTICA (Mixto) -> Total 40 pts posibles
    # Directas (0 malo, 5 bueno) + Inversas (0 bueno, 5 malo)
    directas = respuestas['incomodo'] + respuestas['resp'] + respuestas['postura'] + respuestas['emocion'] + respuestas['calma']
    inversas_pts = (5 - respuestas['distraigo']) + (5 - respuestas['preocupo']) + (5 - respuestas['ignoro'])
    
    total_som = directas + inversas_pts # Max 40
    score_som = (total_som / 40) * 4 + 1
    
    # Promedio Final
    indice = (score_ene + score_reg + score_som) / 3
    return round(score_som, 2), round(score_ene, 2), round(score_reg, 2), round(indice, 2)

# ==========================================
# 4. DIAGNÓSTICO DE NIVELES (RIGOR CIENTÍFICO)
# ==========================================
def obtener_diagnostico(indice):
    if indice < 2.0:
        titulo = "🔴 NIVEL 1: DESCONEXIÓN (Colapso Dorsal)"
        desc = "**Tu cuerpo dice:** 'No es seguro estar aquí, apágate'.\n\n**Significado:** Tu sistema está en modo de ahorro de energía extremo. Es probable que sientas entumecimiento, neblina mental severa o fatiga crónica. No es que 'no quieras', es que tu biología no tiene recursos."
    elif indice < 3.0:
        titulo = "🟠 NIVEL 2: SOBREVIVENCIA (Activación Simpática)"
        desc = "**Tu cuerpo dice:** '¡Peligro! Lucha o huye'.\n\n**Significado:** Hay mucha energía pero desregulada. Ansiedad, reactividad, dolor agudo o insomnio. Tu sistema está gastando todos sus recursos en defenderse de amenazas (reales o percibidas)."
    elif indice < 4.0:
        titulo = "🟡 NIVEL 3: RESISTENCIA FUNCIONAL"
        desc = "**Tu cuerpo dice:** 'Aguanta, no te detengas'.\n\n**Significado:** Eres funcional y productivo, pero a un costo metabólico muy alto. 'Aguantas' el estrés en lugar de procesarlo. Es el estado más común antes del agotamiento o burnout."
    elif indice < 4.6:
        titulo = "🟢 NIVEL 4: REGULACIÓN ACTIVA"
        desc = "**Tu cuerpo dice:** 'Puedo manejar esto'.\n\n**Significado:** Tienes herramientas. Sientes el estrés, pero logras volver a la calma (Ventana de Tolerancia). Tu energía es estable y tu descanso es reparador."
    else:
        titulo = "🟣 NIVEL 5: COHERENCIA (Ventral Vagal)"
        desc = "**Tu cuerpo dice:** 'Estoy a salvo para crear y conectar'.\n\n**Significado:** Estado óptimo. Tu mente, emociones y cuerpo están alineados. Tienes disponibilidad energética para expandirte, crear y sostener a otros."
    return titulo, desc

# ==========================================
# 5. GRÁFICAS (RADAR Y BARRAS)
# ==========================================
def graficar_radar(val_som, val_ene, val_reg, prom_som, prom_ene, prom_reg):
    fig = go.Figure()
    # TÚ
    fig.add_trace(go.Scatterpolar(r=[val_som, val_ene, val_reg], theta=['SOMÁTICA', 'ENERGÍA', 'REGULACIÓN'], fill='toself', name='TÚ', line_color='#8A2BE2'))
    # GRUPO
    fig.add_trace(go.Scatterpolar(r=[prom_som, prom_ene, prom_reg], theta=['SOMÁTICA', 'ENERGÍA', 'REGULACIÓN'], fill='toself', name='PROMEDIO GRUPO', line_color='gray', opacity=0.3, line_dash='dot'))
    
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=True, height=350, margin=dict(t=20, b=20, l=40, r=40))
    return fig

def graficar_barra_comparativa(titulo, valor_usuario, valor_grupo, color_barra):
    df_chart = pd.DataFrame({
        'Entidad': ['TÚ', 'GRUPO'],
        'Puntaje': [valor_usuario, valor_grupo],
        'Color': [color_barra, 'gray']
    })
    fig = px.bar(df_chart, x='Puntaje', y='Entidad', orientation='h', text='Puntaje', title=titulo, color='Color', color_discrete_map={color_barra: color_barra, 'gray': 'gray'})
    fig.update_layout(xaxis=dict(range=[0, 5.5]), showlegend=False, height=200, margin=dict(l=20, r=20, t=40, b=20))
    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    return fig

# ==========================================
# 6. INTERFAZ PRINCIPAL
# ==========================================
st.title("👁️ Tu Monitor S.E.R.")

try: sheet = conectar_db()
except: pass

email_input = st.text_input("Ingresa tu correo registrado para iniciar:").strip().lower()

if email_input:
    tab1, tab2 = st.tabs(["📝 NUEVA MEDICIÓN", "📈 MI PROGRESO"])
    
    # --- PESTAÑA 1: FORMULARIO ---
    with tab1:
        st.write("### Chequeo de Coherencia")
        st.caption("Responde con honestidad (0 = Nunca/No | 5 = Siempre/Mucho)")
        with st.form("test_ser"):
            c1, c2 = st.columns(2)
            with c1:
                st.info("⚡ ENERGÍA")
                e1 = st.slider("Insomnio / sueño no reparador", 0, 5, 0)
                e2 = st.slider("Neblina mental", 0, 5, 0)
                e3 = st.slider("Suspiros involuntarios", 0, 5, 0)
                e4 = st.slider("Falta de aire", 0, 5, 0)
            with c2:
                st.info("🌊 REGULACIÓN")
                r1 = st.slider("Dolor de espalda", 0, 5, 0)
                r2 = st.slider("Problemas estomacales", 0, 5, 0)
                r3 = st.slider("Pánico / ansiedad", 0, 5, 0)
                r4 = st.slider("Dolor de cabeza", 0, 5, 0)
            
            st.info("🧘 SOMÁTICA")
            s1 = st.slider("Noto cuando estoy incómodo", 0, 5, 0)
            s2 = st.slider("Noto cambios en mi respiración", 0, 5, 0)
            s3 = st.slider("Noto mi postura", 0, 5, 0)
            s4 = st.slider("Noto dónde siento emociones", 0, 5, 0)
            s5 = st.slider("Encuentro calma interna", 0, 5, 0)
            st.markdown("**Hébitos de Desconexión:**")
            s_inv1 = st.slider("Me distraigo para no sentir", 0, 5, 0)
            s_inv2 = st.slider("Me preocupo por molestias físicas", 0, 5, 0)
            s_inv3 = st.slider("Ignoro el dolor", 0, 5, 0)
            
            nombre_input = st.text_input("Tu Nombre:")
            submitted = st.form_submit_button("CALCULAR ÍNDICE")
            
            if submitted and nombre_input:
                datos = {'insomnio': e1, 'neblina': e2, 'suspiros': e3, 'aire': e4,
                         'espalda': r1, 'estomago': r2, 'panico': r3, 'cabeza': r4,
                         'incomodo': s1, 'resp': s2, 'postura': s3, 'emocion': s4, 'calma': s5,
                         'distraigo': s_inv1, 'preocupo': s_inv2, 'ignoro': s_inv3}
                
                s_s, s_e, s_r, idx = calcular_ser(datos)
                titulo, desc = obtener_diagnostico(idx)
                
                # Guardar (Fecha, Email, Nombre, Score_Somatica, Score_Energia, Score_Regulacion, INDICE_TOTAL, Nivel)
                fecha = datetime.now().strftime("%Y-%m-%d")
                try:
                    sheet.append_row([fecha, email_input, nombre_input, s_s, s_e, s_r, idx, titulo])
                    st.success("✅ ¡Guardado!")
                    st.divider()
                    st.markdown(f"<h1 style='text-align: center; color: #8A2BE2;'>{idx} / 5.0</h1>", unsafe_allow_html=True)
                    st.info(f"**{titulo}**\n\n{desc}")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error guardando: {e}")
            elif submitted:
                st.warning("Falta tu nombre.")

    # --- PESTAÑA 2: REPORTE ---
    with tab2:
        if st.button("🔄 Actualizar Reporte"): st.rerun()
        
        # A) ENCABEZADO EDUCATIVO (TEXTO QUE PEDISTE)
        with st.expander("ℹ️ ¿QUÉ MIDE EL ÍNDICE S.E.R.?", expanded=True):
            st.markdown("""
            **El índice S.E.R mide lo siguiente:**
            
            **🧘 SOMÁTICA (Conexión / Interocepción):**
            * **Concepto:** Es la capacidad de tu cerebro para "escuchar" las señales internas del cuerpo.
            * **¿Qué mide?** Si habitas tu cuerpo (sientes las señales sutiles) o si vives "en tu cabeza" (desconectado hasta que duele).

            **⚡ ENERGÍA (Disponibilidad Metabólica):**
            * **Concepto:** Es tu "presupuesto" real de vitalidad.
            * **¿Qué mide?** Diferencia entre tener energía real vs. funcionar con "adrenalina prestada" (estrés).

            **🌊 REGULACIÓN (Gestión de estrés):**
            * **Concepto:** La adaptabilidad de tu sistema nervioso.
            * **¿Qué mide?** Tu capacidad para transitar el estrés y volver a la calma sin quedarte atorado en el pánico o el dolor.
            """)
        
        try:
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            
            if not df.empty:
                # 1. Limpieza de datos (Evitar error de lectura)
                df.columns = [c.strip() for c in df.columns]
                cols_num = ['Score_Somatica', 'Score_Energia', 'Score_Regulacion', 'INDICE_TOTAL']
                for c in cols_num:
                    if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce')
                
                # 2. Filtrar usuario
                mis_datos = df[df['Email'] == email_input]
                
                if not mis_datos.empty:
                    ultimo = mis_datos.iloc[-1]
                    idx_val = ultimo.get('INDICE_TOTAL', 0)
                    titulo, desc = obtener_diagnostico(idx_val)
                    
                    st.divider()
                    st.markdown("### 🎯 TU DIAGNÓSTICO ACTUAL")
                    
                    # KPI Principal
                    col_kpi1, col_kpi2 = st.columns([1, 2])
                    col_kpi1.markdown(f"<h1 style='text-align: center; color: #8A2BE2; font-size: 60px;'>{idx_val}</h1>", unsafe_allow_html=True)
                    col_kpi1.caption("Escala 1.0 a 5.0")
                    col_kpi2.success(f"**{titulo}**")
                    col_kpi2.write(desc)
                    
                    st.divider()
                    
                    # 3. COMPARATIVAS (GRÁFICAS INDIVIDUALES)
                    st.markdown("### 📊 TU MAPA VS LA TRIBU")
                    
                    # Cálculos de promedios grupales (ignorando vacíos)
                    p_som = df['Score_Somatica'].mean()
                    p_ene = df['Score_Energia'].mean()
                    p_reg = df['Score_Regulacion'].mean()
                    
                    # A. RADAR GENERAL
                    st.markdown("##### 1. Visión Global (Equilibrio)")
                    fig_radar = graficar_radar(
                        ultimo['Score_Somatica'], ultimo['Score_Energia'], ultimo['Score_Regulacion'],
                        p_som, p_ene, p_reg
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)
                    
                    # B. BARRAS INDIVIDUALES
                    c1, c2, c3 = st.columns(3)
                    
                    with c1:
                        st.markdown("**🧘 SOMÁTICA**")
                        fig_s = graficar_barra_comparativa("Somática", ultimo['Score_Somatica'], p_som, "#FF69B4") # Rosa
                        st.plotly_chart(fig_s, use_container_width=True)
                        
                    with c2:
                        st.markdown("**⚡ ENERGÍA**")
                        fig_e = graficar_barra_comparativa("Energía", ultimo['Score_Energia'], p_ene, "#FFD700") # Amarillo
                        st.plotly_chart(fig_e, use_container_width=True)
                        
                    with c3:
                        st.markdown("**🌊 REGULACIÓN**")
                        fig_r = graficar_barra_comparativa("Regulación", ultimo['Score_Regulacion'], p_reg, "#00BFFF") # Azul
                        st.plotly_chart(fig_r, use_container_width=True)
                        
                    # 4. EVOLUCIÓN
                    if len(mis_datos) > 1:
                        st.divider()
                        st.markdown("### 📈 TU EVOLUCIÓN")
                        fig_line = px.line(mis_datos, x='Fecha', y='INDICE_TOTAL', markers=True, title="Histórico de tu Índice S.E.R.")
                        fig_line.update_layout(yaxis=dict(range=[1, 5.5]))
                        fig_line.update_traces(line_color='#8A2BE2', line_width=4)
                        st.plotly_chart(fig_line, use_container_width=True)
                        
                else:
                    st.warning("No hay registros para este correo.")
            else:
                st.info("Base de datos vacía.")
        except Exception as e:
            st.error(f"Error procesando el reporte: {e}")
