import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px  # <--- RECUPERAMOS ESTO PARA LAS BARRAS Y LINEAS
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials
from fpdf import FPDF
import urllib.parse
# IMPORTAMOS TUS TEXTOS
from textos_legales import AVISO_LEGAL_COMPLETO, DEFINICIONES_SER, TABLA_NIVELES

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Indice S.E.R.", page_icon="🫀", layout="centered")

# 🔐 TUS DATOS
CLAVE_AULA = "ANAHAT2026"
ID_SHEET = "1y5FIw_mvGUSKwhc41JaB01Ti6_93dBJmfC1BTpqrvHw"
WHATSAPP = "525512345678"

st.markdown("""
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    h1 {color: #4B0082; font-family: 'Helvetica Neue', sans-serif; font-weight: 300; text-align: center;}
    .stButton>button {
        border-radius: 20px; background-color: white; 
        color: #4B0082; border: 1px solid #4B0082; font-weight: bold;
    }
    .stButton>button:hover {background-color: #4B0082; color: white;}
    .stAlert {background-color: #f8f9fa; border-left: 4px solid #4B0082; color: #333;}
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

def verificar_privacidad(email):
    client = conectar_db()
    if not client or not email: return False
    try:
        ws = client.worksheet("DB_Anahat_Clientes")
        records = ws.get_all_records()
        df = pd.DataFrame(records)
        df.columns = df.columns.str.strip()
        email_clean = email.strip().lower()
        if 'Email' in df.columns and 'Privacidad_Aceptada' in df.columns:
            usuario = df[df['Email'].astype(str).str.strip().str.lower() == email_clean]
            if not usuario.empty:
                estado = str(usuario.iloc[-1]['Privacidad_Aceptada']).strip().upper()
                if estado == "SI": return True
    except: return False
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

def obtener_historial(email):
    """Recupera los datos previos de este usuario para la gráfica de evolución"""
    client = conectar_db()
    if not client or not email: return pd.DataFrame()
    try:
        ws = client.worksheet("DB_Anahat_Clientes")
        records = ws.get_all_records()
        df = pd.DataFrame(records)
        df.columns = df.columns.str.strip()
        
        # Filtrar por email
        if 'Email' in df.columns:
            email_clean = email.strip().lower()
            historial = df[df['Email'].astype(str).str.strip().str.lower() == email_clean]
            return historial
    except: return pd.DataFrame()
    return pd.DataFrame()

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
    return round(som,1), round(ene,1), round(reg,1), round(idx,1)

def interpretar(idx):
    if idx < 2.0: return "🔴 ZONA DE DESCONEXIÓN", "Sistema inmovilizado. Urge regulación."
    elif idx < 3.0: return "🟠 ZONA REACTIVA", "Sistema en defensa y alerta perpetua."
    elif idx < 4.0: return "🟡 MODO RESISTENCIA", "Funcionalidad mediante tensión."
    elif idx < 4.6: return "🟢 ZONA DE PRESENCIA", "Flexibilidad y retorno al equilibrio."
    else: return "🟣 ALTA SINTERGIA", "Coherencia total cerebro-corazón."

# ==========================================
# 4. PDF
# ==========================================
def generar_pdf(nombre, s, e, r, idx, estado):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(75, 0, 130)
    pdf.cell(0, 15, "INDICE S.E.R. | UNIDAD CONSCIENTE", ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5, DEFINICIONES_SER)
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Usuario: {nombre} | {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, f"TU ÍNDICE: {idx}/5.0", ln=True, align='C')
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(75, 0, 130)
    pdf.cell(0, 10, f"{estado}", ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"   - Somática (Sentir): {s}", ln=True, align='C')
    pdf.cell(0, 8, f"   - Energía (Hacer): {e}", ln=True, align='C')
    pdf.cell(0, 8, f"   - Regulación (Freno): {r}", ln=True, align='C')
    
    pdf.ln(15)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 10, "MAPA DE EVOLUCIÓN (Referencia):", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5, TABLA_NIVELES)
    
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
    st.title("Indice S.E.R.")
    
    st.info(DEFINICIONES_SER.replace("🔹", "**").replace(":", "**:") )
    
    if 'email_ok' not in st.session_state: st.session_state.email_ok = False
    
    with st.form("test_ser"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre")
        email = c2.text_input("Email").strip().lower()
        
        st.caption("Responde: 1 (Nunca) - 5 (Siempre)")
        
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
            st.success(f"Hola de nuevo {nombre}. Términos verificados.")
        else:
            st.warning("⚠️ Acción Requerida")
            with st.expander("📄 Leer Aviso de Privacidad y Términos"):
                st.markdown(AVISO_LEGAL_COMPLETO)
            acepto_check = st.checkbox("He leído y acepto el Aviso de Privacidad y Términos.")
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
            
            # GUARDAR
            datos = [fecha, email, nombre, s, e, r, idx, tit] + todas + [priv_val]
            
            if guardar_completo(datos):
                st.balloons()
                
                # --- DASHBOARD VISUAL (LO QUE PEDISTE) ---
                
                # 1. KPI y RADAR
                c_g, c_t = st.columns([1,2])
                with c_g:
                    fig = go.Figure(go.Scatterpolar(r=[s,e,r,s], theta=['SOM','ENE','REG','SOM'], fill='toself', line_color='#4B0082'))
                    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,5])), showlegend=False, height=200, margin=dict(t=20,b=20,l=20,r=20))
                    st.plotly_chart(fig, use_container_width=True)
                with c_t:
                    st.subheader(tit)
                    st.write(desc)
                
                # 2. GRÁFICA DE BARRAS (LAS 3 DIMENSIONES)
                st.markdown("##### 📊 Desglose por Dimensión")
                df_bar = pd.DataFrame({'Dimensión':['Somática','Energía','Regulación'], 'Puntaje':[s,e,r]})
                fig_bar = px.bar(df_bar, x='Puntaje', y='Dimensión', orientation='h', color='Dimensión', color_discrete_sequence=['#4B0082'])
                fig_bar.update_layout(height=150, xaxis=dict(range=[0,5.5]), margin=dict(t=0,b=0,l=0,r=0))
                st.plotly_chart(fig_bar, use_container_width=True)

                # 3. EVOLUCIÓN (SI HAY HISTORIAL)
                historial = obtener_historial(email)
                if len(historial) > 1:
                    st.markdown("##### 📈 Tu Evolución")
                    # Asegurar que la fecha sea datetime
                    historial['Fecha'] = pd.to_datetime(historial['Fecha'])
                    historial = historial.sort_values('Fecha')
                    fig_line = px.line(historial, x='Fecha', y='INDICE_TOTAL', markers=True, title="Histórico de Progreso")
                    fig_line.update_traces(line_color='#4B0082')
                    fig_line.update_layout(yaxis=dict(range=[1,5.5]))
                    st.plotly_chart(fig_line, use_container_width=True)

                # 4. TABLA DE NIVELES (CONTEXTO)
                with st.expander("ℹ️ Ver Mapa de Niveles Completo"):
                    st.markdown(TABLA_NIVELES)

                # 5. ENTREGABLES
                st.divider()
                pdf_bytes = generar_pdf(nombre, s, e, r, idx, tit)
                c_d1, c_d2 = st.columns(2)
                with c_d1:
                    st.download_button("📥 Descargar Reporte (PDF)", pdf_bytes, f"Reporte_{nombre}.pdf", "application/pdf")
                with c_d2:
                    msg = f"Hola, soy {nombre}. Mi índice S.E.R. es {idx} ({tit}). Quiero unirme a la comunidad y subir mi índice."
                    link_wa = f"https://wa.me/{WHATSAPP}?text={urllib.parse.quote(msg)}"
                    st.link_button("🟢 Unirme a la Comunidad (WhatsApp)", link_wa, type="primary")

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
