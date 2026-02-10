import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials
from fpdf import FPDF
import urllib.parse
# IMPORTAMOS TUS TEXTOS
from textos_legales import AVISO_LEGAL_COMPLETO, DEFINICIONES_SER, TABLA_NIVELES

# ==========================================
# 1. CONFIGURACIÓN VISUAL
# ==========================================
st.set_page_config(page_title="Indice S.E.R. | Anahat", page_icon="🫀", layout="centered")

# 🔐 TUS DATOS
CLAVE_AULA = "ANAHAT2026"
ID_SHEET = "1y5FIw_mvGUSKwhc41JaB01Ti6_93dBJmfC1BTpqrvHw"
WHATSAPP = "525512345678"

st.markdown("""
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* Título Principal */
    h1 {color: #4B0082; font-family: 'Helvetica Neue', sans-serif; font-weight: 300; text-align: center;}
    
    /* Estilos de Tablas de Niveles (Recuperado del diseño anterior) */
    .levels-table {width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;}
    .levels-table th {background-color: #f0f2f6; padding: 10px; border-bottom: 2px solid #4B0082; color: #4B0082;}
    .levels-table td {padding: 10px; border-bottom: 1px solid #eee;}
    
    /* KPI Grande */
    .big-score {font-size: 48px; font-weight: bold; color: #4B0082; text-align: center;}
    .kpi-label {font-size: 16px; color: gray; text-align: center; text-transform: uppercase; letter-spacing: 1px;}
    
    /* Botones */
    .stButton>button {
        border-radius: 20px; background-color: white; 
        color: #4B0082; border: 1px solid #4B0082; font-weight: bold;
    }
    .stButton>button:hover {background-color: #4B0082; color: white;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN DB
# ==========================================
@st.cache_resource
def conectar_db():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_key(ID_SHEET)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

def obtener_datos_comunidad():
    """Trae todos los datos para calcular promedios"""
    client = conectar_db()
    if client:
        try:
            ws = client.worksheet("DB_Anahat_Clientes")
            records = ws.get_all_records()
            df = pd.DataFrame(records)
            # Limpieza de columnas
            df.columns = df.columns.str.strip()
            
            # Asegurar numéricos
            cols = ['Score_Somatica', 'Score_Energia', 'Score_Regulacion', 'INDICE_TOTAL']
            for c in cols:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce')
            
            # Filtrar datos válidos (evitar ceros o errores)
            df = df[df['INDICE_TOTAL'] > 0]
            return df
        except: return pd.DataFrame()
    return pd.DataFrame()

def verificar_privacidad(email):
    df = obtener_datos_comunidad()
    if not df.empty and 'Email' in df.columns and 'Privacidad_Aceptada' in df.columns:
        email_clean = email.strip().lower()
        usuario = df[df['Email'].astype(str).str.strip().str.lower() == email_clean]
        if not usuario.empty:
            estado = str(usuario.iloc[-1]['Privacidad_Aceptada']).strip().upper()
            if estado == "SI": return True
    return False

def guardar_completo(datos):
    client = conectar_db()
    if client:
        try:
            ws = client.worksheet("DB_Anahat_Clientes")
            ws.append_row(datos)
            return True
        except Exception as e:
            st.error(f"Error al guardar: {e}")
            return False

def obtener_videos():
    client = conectar_db()
    if client:
        try:
            ws = client.worksheet("VIDEOS_AULA")
            records = ws.get_all_records()
            df = pd.DataFrame(records)
            if not df.empty and 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'])
                df = df.sort_values(by='Fecha', ascending=False)
            return df
        except: pass
    return pd.DataFrame()

# ==========================================
# 3. LÓGICA CIENTÍFICA (INVERSA)
# ==========================================
def calcular_ser(resp):
    # Energía y Regulación (Síntomas) -> Se invierten (6-x)
    # Somática (Capacidades) -> Se mantiene directo (x)
    ene = sum([6-x for x in resp[0:4]]) / 4
    reg = sum([6-x for x in resp[4:12]]) / 8
    som = sum([x for x in resp[12:29]]) / 17
    idx = (ene + reg + som) / 3
    return round(som,2), round(ene,2), round(reg,2), round(idx,2)

def interpretar(idx):
    if idx < 2.0: return "🔴 ZONA DE DESCONEXIÓN", "Sistema inmovilizado. Urge regulación."
    elif idx < 3.0: return "🟠 ZONA REACTIVA", "Sistema en defensa y alerta perpetua."
    elif idx < 4.0: return "🟡 MODO RESISTENCIA", "Funcionalidad mediante tensión."
    elif idx < 4.6: return "🟢 ZONA DE PRESENCIA", "Flexibilidad y retorno al equilibrio."
    else: return "🟣 ALTA SINTERGIA", "Coherencia total cerebro-corazón."

# ==========================================
# 4. PDF (CORREGIDO PARA EVITAR ERROR)
# ==========================================
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(75, 0, 130)
        self.cell(0, 10, 'INDICE S.E.R. | UNIDAD CONSCIENTE', 0, 1, 'C')
        self.ln(5)

def generar_pdf(nombre, s, e, r, idx, estado):
    # Usamos utf-8 limpiando caracteres raros si es necesario
    pdf = PDF()
    pdf.add_page()
    
    # Definiciones
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(50, 50, 50)
    # Reemplazamos caracteres que FPDF básico no soporta bien
    clean_def = DEFINICIONES_SER.replace("🔹", "-").encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, clean_def)
    pdf.ln(5)
    
    # Datos Usuario
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)
    clean_nombre = nombre.encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 10, f"Usuario: {clean_nombre} | {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
    
    # Resultado
    pdf.ln(5)
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, f"INDICE: {idx}/5.0", ln=True, align='C')
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(75, 0, 130)
    clean_estado = estado.encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 10, f"{clean_estado}", ln=True, align='C')
    
    # Desglose
    pdf.ln(5)
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"   - Somatica: {s}", ln=True, align='C')
    pdf.cell(0, 8, f"   - Energia: {e}", ln=True, align='C')
    pdf.cell(0, 8, f"   - Regulacion: {r}", ln=True, align='C')
    
    # Niveles
    pdf.ln(15)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 10, "MAPA DE EVOLUCION:", ln=True)
    pdf.set_font("Arial", "", 9)
    clean_tabla = TABLA_NIVELES.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, clean_tabla)
    
    return pdf.output(dest="S").encode("latin-1")

# ==========================================
# 5. INTERFAZ
# ==========================================
with st.sidebar:
    st.markdown("### 🫀 Menú")
    modo = st.radio("", ["📝 Diagnóstico", "🧘 Aula Virtual"], label_visibility="collapsed")
    st.divider()
    acceso = False
    if modo == "🧘 Aula Virtual":
        pwd = st.text_input("Clave de Acceso:", type="password")
        if pwd == CLAVE_AULA: acceso = True

if modo == "📝 Diagnóstico":
    # --- TÍTULO CORREGIDO ---
    st.markdown("<h1>Indice S.E.R (Somática, Energía, Regulación) | Anahat</h1>", unsafe_allow_html=True)
    
    # --- DISEÑO LIMPIO DE DEFINICIONES (SIN CUADRO AZUL FEO) ---
    c_def1, c_def2, c_def3 = st.columns(3)
    with c_def1: st.markdown("**🧘 SOMÁTICA**\n\nEl Sentir (Interocepción).")
    with c_def2: st.markdown("**⚡ ENERGÍA**\n\nEl Motor (Vitalidad).")
    with c_def3: st.markdown("**🌊 REGULACIÓN**\n\nEl Freno (Seguridad).")
    st.divider()
    
    if 'email_ok' not in st.session_state: st.session_state.email_ok = False
    
    with st.form("test_ser"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre")
        email = c2.text_input("Email").strip().lower()
        
        st.caption("Responde: 1 (Nunca) - 5 (Siempre)")
        
        # PREGUNTAS (Tus 29)
        st.subheader("⚡ Energía")
        r_e = [st.slider(q,1,5,1) for q in ["¿Tienes insomnio con frecuencia?", "¿Tienes dificultad para concentrarte?", "¿Sientes falta de aire frecuentemente?", "¿Te dan infecciones respiratorias con frecuencia?"]]
        st.subheader("🌊 Regulación")
        r_r = [st.slider(q,1,5,1) for q in ["¿Sientes dolor de espalda?", "¿Tienes problemas estomacales?", "¿Experimentas ataques de pánico?", "¿Tienes dolores de cabeza?", "¿Suspiros frecuentemente?", "¿Ignoras la tensión física hasta que es severa?", "¿Te distraes de las sensaciones de malestar?", "¿Te preocupas apenas sientes una molestia?"]]
        st.subheader("🧘 Somática")
        r_s = [st.slider(q,1,5,1) for q in ["¿Notas cuando te sientes incómodo en tu cuerpo?", "¿Notas cambios en mi respiración?", "¿Puedes prestar atención a tu respiración sin distraerte?", "¿Puedes mantener consciencia interna aunque haya movimiento alrededor?", "¿Al conversar, puedes prestar atención a tu postura?", "¿Puedes volver a concentrarte en tu cuerpo si te distraes?", "¿Puedes redirigir tu atención de pensamientos a sensaciones?", "¿Mantienes consciencia del cuerpo aunque una parte duela?", "¿Eres capaz de enfocarte en tu cuerpo como un todo?", "¿Notas cómo cambia tu cuerpo cuando estás enojado?", "¿Notas que tu cuerpo se siente diferente tras una experiencia pacífica?", "¿Notas que tu respiración se libera cuando estás cómodo?", "¿Al sentirte abrumado, encuentras un lugar de calma dentro de ti?", "¿Al sentirte tenso, usas tu respiración para reducir tensión?", "¿Cuando estás estresado, sabes relajarte físicamente?", "¿Respetas lo que tu cuerpo pide (descanso, comida)?", "¿Al tomar decisiones, consultas tus sensaciones corporales?"]]
        
        st.markdown("---")
        
        ya_acepto = False
        if email: ya_acepto = verificar_privacidad(email)
        acepto_check = True
        priv_val = "SI"
        
        if ya_acepto:
            st.success(f"Hola de nuevo {nombre}.")
        else:
            st.warning("⚠️ Acción Requerida")
            with st.expander("📄 Leer Aviso de Privacidad"):
                st.markdown(AVISO_LEGAL_COMPLETO)
            acepto_check = st.checkbox("He leído y acepto el Aviso de Privacidad.")
            priv_val = "SI" if acepto_check else "NO"

        enviar = st.form_submit_button("🏁 OBTENER INDICE S.E.R.")
    
    if enviar:
        if not nombre or not email:
            st.error("Por favor completa nombre y email.")
        elif not ya_acepto and not acepto_check:
            st.error("Debes aceptar el Aviso de Privacidad.")
        else:
            # Cálculos
            todas = r_e + r_r + r_s
            s, e, r, idx = calcular_ser(todas)
            tit, desc = interpretar(idx)
            fecha = datetime.now(pytz.timezone('America/Mexico_City')).strftime("%Y-%m-%d")
            
            # Guardar
            datos = [fecha, email, nombre, s, e, r, idx, tit] + todas + [priv_val]
            
            if guardar_completo(datos):
                st.balloons()
                
                # --- AQUÍ EMPIEZA EL DASHBOARD CORREGIDO ---
                
                # 0. MAPA DE NIVELES (VISIBLE AL PRINCIPIO COMO PEDISTE)
                st.markdown("### 🗺️ Mapa de Niveles")
                st.markdown("""
                <table class="levels-table">
                  <tr><th>Nivel</th><th>Estado</th></tr>
                  <tr><td>🟣 4.6 - 5.0</td><td>ALTA SINTERGIA</td></tr>
                  <tr><td>🟢 4.0 - 4.5</td><td>ZONA DE PRESENCIA</td></tr>
                  <tr><td>🟡 3.0 - 3.9</td><td>MODO RESISTENCIA</td></tr>
                  <tr><td>🟠 2.0 - 2.9</td><td>ZONA REACTIVA</td></tr>
                  <tr><td>🔴 1.0 - 1.9</td><td>ZONA DE DESCONEXIÓN</td></tr>
                </table>
                """, unsafe_allow_html=True)
                
                # 1. TU NÚMERO GRANDE
                st.markdown(f"<div class='kpi-label'>Tu Índice S.E.R.</div><div class='big-score'>{idx}</div>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='text-align: center; color: #4B0082;'>{tit}</h3>", unsafe_allow_html=True)
                st.info(desc)
                
                # 2. CÁLCULO DE PROMEDIOS COMUNIDAD
                df_com = obtener_datos_comunidad()
                if not df_com.empty:
                    prom_s = df_com['Score_Somatica'].mean()
                    prom_e = df_com['Score_Energia'].mean()
                    prom_r = df_com['Score_Regulacion'].mean()
                else:
                    prom_s = prom_e = prom_r = 0

                # 3. RADAR COMPARATIVO (TÚ VS COMUNIDAD)
                st.markdown("---")
                st.markdown("### 📊 Comparativa con la Comunidad")
                
                fig = go.Figure()
                # TÚ
                fig.add_trace(go.Scatterpolar(r=[s,e,r,s], theta=['SOM','ENE','REG','SOM'], fill='toself', name='TÚ', line_color='#4B0082'))
                # COMUNIDAD
                if prom_s > 0:
                    fig.add_trace(go.Scatterpolar(r=[prom_s,prom_e,prom_r,prom_s], theta=['SOM','ENE','REG','SOM'], fill='toself', name='COMUNIDAD', line_color='gray', opacity=0.3))
                
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,5])), height=300)
                st.plotly_chart(fig, use_container_width=True)
                
                # 4. EVOLUCIÓN (LINEA DE TIEMPO)
                if not df_com.empty and 'Email' in df_com.columns:
                     mis_datos = df_com[df_com['Email'] == email]
                     if len(mis_datos) > 1:
                         st.markdown("### 📈 Tu Evolución")
                         fig_line = px.line(mis_datos, x='Fecha', y='INDICE_TOTAL', markers=True)
                         fig_line.update_traces(line_color='#4B0082')
                         st.plotly_chart(fig_line, use_container_width=True)

                # 5. ENTREGABLES
                st.markdown("---")
                pdf_bytes = generar_pdf(nombre, s, e, r, idx, tit)
                c_d1, c_d2 = st.columns(2)
                with c_d1:
                    st.download_button("📥 Descargar PDF", pdf_bytes, f"Reporte_{nombre}.pdf", "application/pdf")
                with c_d2:
                    msg = f"Hola, soy {nombre}. Mi índice S.E.R. es {idx} ({tit}). Quiero unirme a la comunidad y subir mi índice."
                    link_wa = f"https://wa.me/{WHATSAPP}?text={urllib.parse.quote(msg)}"
                    st.link_button("🟢 Unirme (WhatsApp)", link_wa, type="primary")

elif modo == "🧘 Aula Virtual":
    st.title("Aula Virtual")
    if acceso:
        df = obtener_videos()
        if not df.empty:
            for i, row in df.iterrows():
                f_str = str(row['Fecha'])[:10]
                with st.expander(f"📅 {f_str} | {row['Titulo']}", expanded=(i==0)):
                    st.write(row.get('Descripcion',''))
                    st.video(row['Link'])
        else: st.info("No hay clases cargadas aún.")
    else: st.warning("🔒 Ingresa tu clave en la barra lateral.")
