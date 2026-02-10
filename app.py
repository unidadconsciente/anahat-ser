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
WHATSAPP = "525539333599"

st.markdown("""
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* Título Principal */
    h1 {color: #4B0082; font-family: 'Helvetica Neue', sans-serif; font-weight: 300; text-align: center;}
    
    /* Estilos de Tablas de Niveles */
    .levels-table {width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px; font-family: sans-serif;}
    .levels-table th {background-color: #f0f2f6; padding: 12px; border-bottom: 2px solid #4B0082; color: #4B0082; text-align: left;}
    .levels-table td {padding: 12px; border-bottom: 1px solid #eee; vertical-align: top;}
    
    /* KPI Grande */
    .big-score {font-size: 48px; font-weight: bold; color: #4B0082; text-align: center;}
    .kpi-label {font-size: 16px; color: gray; text-align: center; text-transform: uppercase; letter-spacing: 1px;}
    
    /* TARJETAS DE DEFINICIÓN (DISEÑO BONITO) */
    .def-card {
        background-color: #f9f9f9;
        border-left: 5px solid #4B0082; /* Borde morado Anahat */
        padding: 15px;
        border-radius: 5px;
        height: 100%; /* Para que queden parejas */
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .def-title {
        color: #4B0082;
        font-weight: bold;
        font-size: 16px;
        margin-bottom: 8px;
    }
    .def-body {
        font-size: 13px;
        color: #333;
        line-height: 1.4;
    }

    /* Escala Visual */
    .scale-guide {
        background-color: #f8f9fa; 
        color: #333; 
        padding: 15px; 
        border-radius: 5px; 
        text-align: center; 
        font-weight: 600; 
        margin-bottom: 20px;
        border: 1px solid #ddd;
        font-size: 14px;
    }

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
    client = conectar_db()
    if client:
        try:
            ws = client.worksheet("DB_Anahat_Clientes")
            records = ws.get_all_records()
            df = pd.DataFrame(records)
            df.columns = df.columns.str.strip()
            cols = ['Score_Somatica', 'Score_Energia', 'Score_Regulacion', 'INDICE_TOTAL']
            for c in cols:
                if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce')
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
    if idx < 2.0: return "🔴 ZONA DE DESCONEXIÓN", "Estado profundo de Burnout. Sistema inmovilizado."
    elif idx < 3.0: return "🟠 ZONA REACTIVA", "Sistema en defensa y alerta perpetua."
    elif idx < 4.0: return "🟡 MODO RESISTENCIA", "Funcionalidad mediante tensión sostenida."
    elif idx < 4.6: return "🟢 ZONA DE PRESENCIA", "Flexibilidad interna y retorno al equilibrio."
    else: return "🟣 ALTA SINTERGIA", "Coherencia total cerebro-corazón y expansión."

# ==========================================
# 4. PDF (CORREGIDO)
# ==========================================
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(75, 0, 130)
        self.cell(0, 10, 'INDICE S.E.R. | UNIDAD CONSCIENTE', 0, 1, 'C')
        self.ln(5)

def generar_pdf(nombre, s, e, r, idx, estado):
    pdf = PDF()
    pdf.add_page()
    
    # 1. Definiciones
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(50, 50, 50)
    # Limpiamos caracteres para evitar error
    clean_def = DEFINICIONES_SER.replace("🔹", "-").encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, clean_def)
    pdf.ln(5)
    
    # 2. Datos Usuario
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)
    clean_nombre = nombre.encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 10, f"Usuario: {clean_nombre} | {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
    
    # 3. Resultado
    pdf.ln(5)
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, f"INDICE: {idx}/5.0", ln=True, align='C')
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(75, 0, 130)
    clean_estado = estado.encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 10, f"{clean_estado}", ln=True, align='C')
    
    # 4. Desglose
    pdf.ln(5)
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"   - Somatica: {s}", ln=True, align='C')
    pdf.cell(0, 8, f"   - Energia: {e}", ln=True, align='C')
    pdf.cell(0, 8, f"   - Regulacion: {r}", ln=True, align='C')
    
    # 5. Niveles
    pdf.ln(15)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 10, "MAPA DE NIVELES (Referencia):", ln=True)
    pdf.set_font("Arial", "", 8)
    clean_tabla = TABLA_NIVELES.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 4, clean_tabla)
    
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
    st.markdown("<h1>Indice S.E.R (Somática, Energía, Regulación) | Anahat</h1>", unsafe_allow_html=True)
    
    # --- DISEÑO DE DEFINICIONES CON TARJETAS (NUEVO ESTILO) ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="def-card">
            <div class="def-title">🧘 SOMÁTICA</div>
            <div class="def-body">Capacidad de tu sistema para percibir, traducir y habitar las señales internas de tu cuerpo como fuente de sabiduría.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="def-card">
            <div class="def-title">⚡ ENERGÍA</div>
            <div class="def-body">Cantidad de fuerza vital libre disponible para crear, expandirte y sostener tu propósito con claridad.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="def-card">
            <div class="def-title">🌊 REGULACIÓN</div>
            <div class="def-body">Capacidad biológica para transitar los retos de la vida y retornar a la seguridad y el equilibrio natural.</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    if 'email_ok' not in st.session_state: st.session_state.email_ok = False
    
    with st.form("test_ser"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre")
        email = c2.text_input("Email").strip().lower()
        
        # ESCALA VISUAL CLARA
        st.markdown("""
        <div class="scale-guide">
            ESCALA DE RESPUESTA:<br>
            1 = Nunca | 2 = Casi nunca | 3 = A veces | 4 = Frecuentemente | 5 = Siempre
        </div>
        """, unsafe_allow_html=True)
        
        # PREGUNTAS
        st.subheader("⚡ Energía")
        r_e = [st.slider(q,1,5,1) for q in ["¿Tienes insomnio con frecuencia?", "¿Tienes dificultad para concentrarte?", "¿Sientes falta de aire frecuentemente?", "¿Te dan infecciones respiratorias con frecuencia?"]]
        st.subheader("🌊 Regulación")
        r_r = [st.slider(q,1,5,1) for q in ["¿Sientes dolor de espalda?", "¿Tienes problemas estomacales?", "¿Experimentas ataques de pánico?", "¿Tienes dolores de cabeza?", "¿Suspiros frecuentemente?", "¿Ignoras la tensión física hasta que es severa?", "¿Te distraes de las sensaciones de malestar?", "¿Te preocupas apenas sientes una molestia?"]]
        st.subheader("🧘 Somática")
        r_s = [st.slider(q,1,5,1) for q in ["¿Notas cuando te sientes incómodo en tu cuerpo?", "¿Notas cambios en mi respiración?", "¿Puedes prestar atención a tu respiración sin distraerte?", "¿Puedes mantener consciencia interna aunque haya movimiento alrededor?", "¿Al conversar, puedes prestar atención a tu postura?", "¿Puedes volver a concentrarte en tu cuerpo si te distraes?", "¿Puedes redirigir tu atención de pensamientos a sensaciones?", "¿Mantienes consciencia del cuerpo aunque una parte duela?", "¿Eres capaz de enfocarte en tu cuerpo como un todo?", "¿Notas cómo cambia tu cuerpo cuando estás enojado?", "¿Notas que tu cuerpo se siente diferente tras una experiencia pacífica?", "¿Notas que tu respiración se libera cuando estás cómodo?", "¿Al sentirte abrumado, encuentras un lugar de calma dentro de ti?", "¿Al sentirte tenso, usas tu respiración para reducir tensión?", "¿Cuando estás estresado, sabes relajarte físicamente?", "¿Respetas lo que tu cuerpo pide (descanso, comida)?", "¿Al tomar decisiones, consultas tus sensaciones corporales?"]]
        
        st.markdown("---")
        
        # LÓGICA DE PRIVACIDAD
        ya_acepto = False
        if email: ya_acepto = verificar_privacidad(email)
        acepto_check = True
        priv_val = "SI"
        
        if ya_acepto:
            st.success(f"Hola de nuevo {nombre}.")
        else:
            st.warning("⚠️ Aviso de Privacidad")
            with st.expander("📄 Leer Aviso Legal"):
                st.markdown(AVISO_LEGAL_COMPLETO)
            acepto_check = st.checkbox("He leído y acepto el Aviso de Privacidad.")
            priv_val = "SI" if acepto_check else "NO"

        enviar = st.form_submit_button("🏁 OBTENER INDICE S.E.R.")
    
    if enviar:
        if not nombre or not email:
            st.error("Por favor completa nombre y email.")
        elif not ya_acepto and not acepto_check:
            st.error("Debes aceptar el Aviso de Privacidad para ver tus resultados.")
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
                
                # --- DASHBOARD VISUAL ---
                
                # KPI
                st.markdown(f"<div class='kpi-label'>Tu Índice S.E.R.</div><div class='big-score'>{idx}</div>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='text-align: center; color: #4B0082;'>{tit}</h3>", unsafe_allow_html=True)
                st.info(desc)
                
                # Tabla de Niveles (TUS TEXTOS)
                st.markdown("### 🗺️ Mapa de Niveles S.E.R.")
                st.markdown("""
                <table class="levels-table">
                  <tr><th style="width:140px;">Nivel</th><th>Descripción</th></tr>
                  <tr><td>🟣 ALTA SINTERGIA<br>(4.6 - 5.0)</td><td>Existe una coherencia total entre cerebro y corazón. Tu energía fluye sin obstáculos, permitiendo un estado de presencia absoluta y máxima expansión creativa.</td></tr>
                  <tr><td>🟢 ZONA DE PRESENCIA<br>(4.0 - 4.5)</td><td>Posees la flexibilidad interna para sentir la intensidad de la vida, trascender sus retos y retornar a tu centro con naturalidad y fortaleza.</td></tr>
                  <tr><td>🟡 MODO RESISTENCIA<br>(3.0 - 3.9)</td><td>Tu sistema mantiene la funcionalidad a través del esfuerzo y la tensión sostenida, sacrificando la capacidad de soltar y descansar profundamente.</td></tr>
                  <tr><td>🟠 ZONA REACTIVA<br>(2.0 - 2.9)</td><td>Tu sistema opera bajo una química de defensa y alerta perpetua, bloqueando los mecanismos naturales de calma y seguridad.</td></tr>
                  <tr><td>🔴 ZONA DE DESCONEXIÓN<br>(1.0 - 1.9)</td><td>Estado profundo de Burnout. El sistema nervioso activa la inmovilización para preservar la vida. Puede haber lesiones cerebrales (como PTSD); es necesaria la intervención profesional.</td></tr>
                </table>
                """, unsafe_allow_html=True)
                
                # Promedios
                df_com = obtener_datos_comunidad()
                if not df_com.empty:
                    prom_s = df_com['Score_Somatica'].mean()
                    prom_e = df_com['Score_Energia'].mean()
                    prom_r = df_com['Score_Regulacion'].mean()
                else: prom_s = prom_e = prom_r = 0

                # Radar
                st.markdown("---")
                st.markdown("### 📊 Comparativa")
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=[s,e,r,s], theta=['SOM','ENE','REG','SOM'], fill='toself', name='TÚ', line_color='#4B0082'))
                if prom_s > 0:
                    fig.add_trace(go.Scatterpolar(r=[prom_s,prom_e,prom_r,prom_s], theta=['SOM','ENE','REG','SOM'], fill='toself', name='COMUNIDAD', line_color='gray', opacity=0.3))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,5])), height=300)
                st.plotly_chart(fig, use_container_width=True)
                
                # Evolución
                if not df_com.empty and 'Email' in df_com.columns:
                     mis_datos = df_com[df_com['Email'] == email]
                     if len(mis_datos) > 1:
                         st.markdown("### 📈 Tu Evolución")
                         fig_line = px.line(mis_datos, x='Fecha', y='INDICE_TOTAL', markers=True)
                         fig_line.update_traces(line_color='#4B0082')
                         st.plotly_chart(fig_line, use_container_width=True)

                # Entregables
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
