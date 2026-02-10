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
import os

# IMPORTAMOS TUS TEXTOS
from textos_legales import AVISO_LEGAL_COMPLETO, DEFINICIONES_SER, TABLA_NIVELES

# ==========================================
# 1. CONFIGURACIÓN VISUAL
# ==========================================
st.set_page_config(page_title="Indice S.E.R. | Anahat", page_icon="🫀", layout="centered")

# DATOS DE CONTACTO
CLAVE_AULA = "ANAHAT2026"
ID_SHEET = "1y5FIw_mvGUSKwhc41JaB01Ti6_93dBJmfC1BTpqrvHw"
WHATSAPP = "525539333599"
WEB_LINK = "https://unidadconsciente.com/"
INSTA_LINK = "https://www.instagram.com/unidad_consciente?igsh=Z3hwNzZuOWVjcG91&utm_source=qr"

st.markdown("""
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    h1 {color: #4B0082; font-family: 'Helvetica Neue', sans-serif; font-weight: 300; text-align: center; margin-top: 0;}
    
    /* ENCABEZADO PERSONALIZADO */
    .header-brand {font-size: 24px; font-weight: bold; color: #4B0082; margin-bottom: 0px;}
    .header-links a {text-decoration: none; color: #666; font-size: 14px; margin-right: 15px;}
    .header-links a:hover {color: #4B0082; font-weight: bold;}
    
    /* TABLA DE NIVELES */
    .levels-table {width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px; font-family: sans-serif;}
    .levels-table th {background-color: #f0f2f6; padding: 12px; border-bottom: 2px solid #4B0082; color: #4B0082; text-align: left;}
    .levels-table td {padding: 12px; border-bottom: 1px solid #eee; vertical-align: top; color: #333;}
    
    /* KPI Y COMPARATIVA */
    .big-score {font-size: 56px; font-weight: bold; color: #4B0082; line-height: 1;}
    .community-score {font-size: 16px; color: gray; margin-top: 10px;}
    .kpi-container {text-align: center; padding: 20px; background-color: #fcfcfc; border-radius: 10px; border: 1px solid #eee;}

    /* TARJETAS DE DEFINICIÓN */
    .def-card {background-color: #f9f9f9; border-left: 4px solid #4B0082; padding: 10px; border-radius: 4px; height: 100%;}
    .def-title {color: #4B0082; font-weight: bold; font-size: 14px; margin-bottom: 5px;}
    .def-body {font-size: 12px; color: #333; line-height: 1.3;}

    /* ESCALA */
    .scale-guide {background-color: #f0f2f6; color: #333; padding: 10px; border-radius: 5px; text-align: center; font-weight: 600; font-size: 14px; margin-bottom: 15px;}
    
    .stButton>button {border-radius: 20px; background-color: white; color: #4B0082; border: 1px solid #4B0082; font-weight: bold;}
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
        except: return False
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
# 3. LÓGICA CIENTÍFICA
# ==========================================
def calcular_ser(resp):
    ene = sum([6-x for x in resp[0:4]]) / 4
    reg = sum([6-x for x in resp[4:12]]) / 8
    som = sum([x for x in resp[12:29]]) / 17
    idx = (ene + reg + som) / 3
    return round(som,2), round(ene,2), round(reg,2), round(idx,2)

def interpretar(idx):
    if idx < 2.0: return "🔴 ZONA DE DESCONEXIÓN", "Estado profundo de Burnout. El sistema nervioso activa la inmovilización para preservar la vida. Puede haber lesiones cerebrales (como PTSD); es necesaria la intervención profesional."
    elif idx < 3.0: return "🟠 ZONA REACTIVA", "Tu sistema opera bajo una química de defensa y alerta perpetua, bloqueando los mecanismos naturales de calma y seguridad."
    elif idx < 4.0: return "🟡 MODO RESISTENCIA", "Tu sistema mantiene la funcionalidad a través del esfuerzo y la tensión sostenida, sacrificando la capacidad de soltar y descansar profundamente."
    elif idx < 4.6: return "🟢 ZONA DE PRESENCIA", "Posees la flexibilidad interna para sentir la intensidad de la vida, trascender sus retos y retornar a tu centro con naturalidad y fortaleza."
    else: return "🟣 ALTA SINTERGIA", "Existe una coherencia total entre cerebro y corazón. Tu energía fluye sin obstáculos, permitiendo un estado de presencia absoluta y máxima expansión creativa."

# ==========================================
# 4. PDF (MEMBRETE MORADO + FOOTER)
# ==========================================
class PDF(FPDF):
    def header(self):
        # Franja Morada
        self.set_fill_color(75, 0, 130)
        self.rect(0, 0, 210, 40, 'F') 
        # Logo
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 25) 
        # Título
        self.set_font('Arial', 'B', 18)
        self.set_text_color(255, 255, 255)
        self.set_xy(40, 15) 
        self.cell(0, 10, 'INDICE S.E.R. | UNIDAD CONSCIENTE', 0, 1, 'L')
        self.ln(25)

    def footer(self):
        # Pie de página con links
        self.set_y(-30)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(75, 0, 130)
        self.cell(0, 5, 'UNIDAD CONSCIENTE', 0, 1, 'C')
        
        self.set_font('Arial', '', 9)
        self.set_text_color(50, 50, 50)
        self.cell(0, 5, 'Web: unidadconsciente.com', 0, 1, 'C', link=WEB_LINK)
        self.cell(0, 5, 'Instagram: @unidad_consciente', 0, 1, 'C', link=INSTA_LINK)
        self.cell(0, 5, f'WhatsApp: +{WHATSAPP}', 0, 1, 'C', link=f"https://wa.me/{WHATSAPP}")

def clean_text(text):
    if isinstance(text, str):
        return text.encode('latin-1', 'replace').decode('latin-1')
    return text

def generar_pdf(nombre, s, e, r, idx, estado, desc):
    pdf = PDF()
    pdf.add_page()
    
    # Contenido (ajustado para no chocar con el header)
    pdf.set_y(45)
    
    # Definiciones
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(50, 50, 50)
    clean_def = DEFINICIONES_SER.replace("🔹", "-").encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, clean_def)
    pdf.ln(5)
    
    # Usuario
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)
    clean_nombre = nombre.encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 10, f"Usuario: {clean_nombre} | {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
    
    # Resultado Grande
    pdf.ln(5)
    pdf.set_font("Arial", "B", 30)
    pdf.set_text_color(75, 0, 130)
    pdf.cell(0, 15, f"{idx}/5.0", ln=True, align='C')
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, clean_text(estado), ln=True, align='C')
    
    pdf.set_font("Arial", "I", 10)
    pdf.set_text_color(80,80,80)
    pdf.multi_cell(0, 5, clean_text(desc), align='C')
    
    # Desglose
    pdf.ln(10)
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"Somatica: {s}  |  Energia: {e}  |  Regulacion: {r}", ln=True, align='C')
    
    # Niveles
    pdf.ln(10)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(75, 0, 130)
    pdf.cell(0, 10, "MAPA DE EVOLUCION:", ln=True)
    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(0, 0, 0)
    clean_tabla = TABLA_NIVELES.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 4, clean_tabla)
    
    return pdf.output(dest="S").encode("latin-1")

# ==========================================
# 5. COMPONENTE DE ENCABEZADO
# ==========================================
def mostrar_encabezado():
    """Muestra Logo + Links"""
    col_logo, col_text = st.columns([1, 4])
    
    with col_logo:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=80)
    
    with col_text:
        st.markdown(f"""
        <div class="header-brand">UNIDAD CONSCIENTE</div>
        <div class="header-links">
            <a href="{WEB_LINK}" target="_blank">🌐 Web</a>
            <a href="{INSTA_LINK}" target="_blank">📸 Instagram</a>
            <a href="https://wa.me/{WHATSAPP}" target="_blank">🟢 WhatsApp</a>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 6. INTERFAZ PRINCIPAL
# ==========================================
with st.sidebar:
    st.markdown("### 🫀 Menú")
    # AQUÍ CAMBIÉ EL NOMBRE
    modo = st.radio("", ["📝 Índice S.E.R.", "🧘 Aula Virtual"], label_visibility="collapsed")
    st.divider()
    acceso = False
    if modo == "🧘 Aula Virtual":
        pwd = st.text_input("Clave de Acceso:", type="password")
        if pwd == CLAVE_AULA: acceso = True

if modo == "📝 Índice S.E.R.":
    # 1. ENCABEZADO
    mostrar_encabezado()
    st.markdown("---")
    
    # 2. TÍTULO Y DEFINICIONES
    st.markdown("<h1>Indice S.E.R (Somática, Energía, Regulación)</h1>", unsafe_allow_html=True)
    
    # Tarjetas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="def-card"><div class="def-title">🧘 SOMÁTICA</div><div class="def-body">Capacidad de percibir y traducir señales internas.</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="def-card"><div class="def-title">⚡ ENERGÍA</div><div class="def-body">Fuerza vital disponible para crear y sostener.</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="def-card"><div class="def-title">🌊 REGULACIÓN</div><div class="def-body">Capacidad de retornar al equilibrio y la calma.</div></div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Variables de Sesión
    if 'resultado_listo' not in st.session_state: st.session_state.resultado_listo = False
    if 'email_ok' not in st.session_state: st.session_state.email_ok = False
    
    with st.form("test_ser"):
        c1, c2 = st.columns(2)
        nombre = st.text_input("Nombre")
        email = st.text_input("Email").strip().lower()
        
        st.markdown('<div class="scale-guide">1 = Nunca | 2 = Casi nunca | 3 = A veces | 4 = Frecuentemente | 5 = Siempre</div>', unsafe_allow_html=True)
        
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
            st.success(f"Hola de nuevo. Términos verificados.")
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
            st.error("Debes aceptar el Aviso de Privacidad.")
        else:
            todas = r_e + r_r + r_s
            s, e, r, idx = calcular_ser(todas)
            tit, desc = interpretar(idx)
            fecha = datetime.now(pytz.timezone('America/Mexico_City')).strftime("%Y-%m-%d")
            
            datos = [fecha, email, nombre, s, e, r, idx, tit] + todas + [priv_val]
            guardar_completo(datos)
            
            # GUARDAR EN SESIÓN
            st.session_state.resultado_listo = True
            st.session_state.res_datos = (nombre, s, e, r, idx, tit, desc)

    # MOSTRAR RESULTADOS
    if st.session_state.resultado_listo:
        nombre, s, e, r, idx, tit, desc = st.session_state.res_datos
        
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
        
        st.divider()
        
        df_com = obtener_datos_comunidad()
        prom_total = df_com['INDICE_TOTAL'].mean() if not df_com.empty else 0
        prom_s = df_com['Score_Somatica'].mean() if not df_com.empty else 0
        prom_e = df_com['Score_Energia'].mean() if not df_com.empty else 0
        prom_r = df_com['Score_Regulacion'].mean() if not df_com.empty else 0
        
        c_kpi1, c_kpi2 = st.columns([1, 1])
        with c_kpi1:
            st.markdown(f"""
            <div class='kpi-container'>
                <div class='kpi-label'>TU ÍNDICE S.E.R.</div>
                <div class='big-score'>{idx}</div>
                <div class='community-score'>Promedio Comunidad: {prom_total:.1f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with c_kpi2:
            st.markdown(f"<h3 style='color: #4B0082; margin-top: 0;'>{tit}</h3>", unsafe_allow_html=True)
            st.info(desc)
            
        st.markdown("##### 📊 Desglose")
        df_bar = pd.DataFrame({'Dim':['Somática','Energía','Regulación'], 'Tu Puntaje':[s,e,r]})
        fig_bar = px.bar(df_bar, x='Tu Puntaje', y='Dim', orientation='h', color='Dim', color_discrete_sequence=['#4B0082'])
        fig_bar.update_layout(height=150, xaxis=dict(range=[0,5.5]), margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig_bar, use_container_width=True)
        
        st.markdown("##### 🆚 Radar Comparativo")
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=[s,e,r,s], theta=['SOM','ENE','REG','SOM'], fill='toself', name='TÚ', line_color='#4B0082'))
        if prom_s > 0:
            fig.add_trace(go.Scatterpolar(r=[prom_s,prom_e,prom_r,prom_s], theta=['SOM','ENE','REG','SOM'], fill='toself', name='COMUNIDAD', line_color='gray', opacity=0.3))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,5])), height=250, margin=dict(t=20,b=20))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        pdf_bytes = generar_pdf(nombre, s, e, r, idx, tit, desc)
        c_d1, c_d2 = st.columns(2)
        with c_d1:
            st.download_button("📥 Descargar Reporte (PDF)", pdf_bytes, f"Reporte_{nombre}.pdf", "application/pdf")
        with c_d2:
            msg = f"Hola, soy {nombre}. Mi índice S.E.R. es {idx} ({tit}). ¿Cómo puedo subir mi índice S.E.R. y unirme a la comunidad?"
            link_wa = f"https://wa.me/{WHATSAPP}?text={urllib.parse.quote(msg)}"
            st.link_button("🟢 Unirme a la Comunidad (WhatsApp)", link_wa, type="primary")

elif modo == "🧘 Aula Virtual":
    # 1. ENCABEZADO TAMBIÉN AQUÍ
    mostrar_encabezado()
    st.markdown("---")
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
