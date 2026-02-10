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



# ==========================================

# 1. DATOS Y TEXTOS

# ==========================================

NIVELES_DATA = [

    ("4.6 - 5.0", "ALTA SINTERGIA", "Existe una coherencia total entre cerebro y corazón. Tu energía fluye sin obstáculos, permitiendo un estado de presencia absoluta y máxima expansión creativa."),

    ("4.0 - 4.5", "ZONA DE PRESENCIA", "Posees la flexibilidad interna para sentir la intensidad de la vida, trascender sus retos y retornar a tu centro con naturalidad y fortaleza."),

    ("3.0 - 3.9", "MODO RESISTENCIA", "Tu sistema mantiene la funcionalidad a través del esfuerzo y la tensión sostenida, sacrificando la capacidad de soltar y descansar profundamente."),

    ("2.0 - 2.9", "ZONA REACTIVA", "Tu sistema opera bajo una química de defensa y alerta perpetua, bloqueando los mecanismos naturales de calma y seguridad."),

    ("1.0 - 1.9", "ZONA DE DESCONEXIÓN", "Estado profundo de Burnout. El sistema nervioso activa la inmovilización para preservar la vida. Puede haber lesiones cerebrales (como PTSD).")

]



DEFINICIONES_DATA = [

    ("SOMATICA", "El Sentir", "Capacidad de tu sistema nervioso para percibir, traducir y habitar las señales internas de tu cuerpo como fuente primaria de sabiduría."),

    ("ENERGIA", "El Motor", "Cantidad de fuerza vital libre que tienes disponible para crear, expandirte y sostener tu propósito con claridad."),

    ("REGULACION", "El Freno", "Capacidad biológica para transitar los retos de la vida y retornar a la seguridad, al centro y al equilibrio de forma natural.")

]



from textos_legales import AVISO_LEGAL_COMPLETO, DEFINICIONES_SER



# ==========================================

# 2. CONFIGURACIÓN VISUAL

# ==========================================

icono_pagina = "logo.png" if os.path.exists("logo.png") else "🫀"



st.set_page_config(

    page_title="Indice S.E.R. | Anahat", 

    page_icon=icono_pagina, 

    layout="centered", 

    initial_sidebar_state="expanded" # Ordena al menú estar abierto

)



CLAVE_AULA = "ANAHAT2026"

ID_SHEET = "1y5FIw_mvGUSKwhc41JaB01Ti6_93dBJmfC1BTpqrvHw"

WHATSAPP = "525539333599"

WEB_LINK = "https://unidadconsciente.com/"

INSTA_LINK = "https://www.instagram.com/unidad_consciente?igsh=Z3hwNzZuOWVjcG91&utm_source=qr"



COLOR_MORADO = "#4B0082"

COLOR_DORADO = "#DAA520"

COLOR_AZUL = "#008080" 



st.markdown(f"""

<style>

    /* 1. ESTO HACE QUE APAREZCA LA BARRA SUPERIOR Y LA FLECHA */

    header {{visibility: visible !important;}}

    

    footer {{visibility: hidden;}}

    

    h1 {{color: {COLOR_MORADO}; font-family: 'Helvetica Neue', sans-serif; font-weight: 300; text-align: center; margin-top: 0;}}

    

    .header-brand {{font-size: 24px; font-weight: bold; color: {COLOR_MORADO}; margin-bottom: 0px;}}

    .header-links a {{text-decoration: none; color: #666; font-size: 14px; margin-right: 15px;}}

    .header-links a:hover {{color: {COLOR_MORADO}; font-weight: bold;}}

    

    /* TABLA DE NIVELES: FORZAR TEXTO BLANCO */

    .levels-table {{width: 100%; border-collapse: collapse; margin-bottom: 20px; font-family: sans-serif;}}

    .levels-table th {{

        background-color: {COLOR_MORADO}; 

        padding: 12px; 

        color: white !important; /* BLANCO OBLIGATORIO */

        text-align: left;

        font-weight: bold;

    }}

    .levels-table td {{padding: 12px; border-bottom: 1px solid #eee; vertical-align: top; color: #333; font-size: 13px;}}

    

    .big-score {{font-size: 56px; font-weight: bold; color: {COLOR_MORADO}; line-height: 1;}}

    .community-score {{font-size: 16px; color: gray; margin-top: 10px;}}

    .kpi-container {{text-align: center; padding: 20px; background-color: #fcfcfc; border-radius: 10px; border: 1px solid #eee;}}



    .def-card {{background-color: #f9f9f9; border-left: 4px solid {COLOR_MORADO}; padding: 10px; border-radius: 4px; height: 100%;}}

    .def-title {{color: {COLOR_MORADO}; font-weight: bold; font-size: 14px; margin-bottom: 5px;}}

    .def-body {{font-size: 12px; color: #333; line-height: 1.3;}}



    .scale-guide {{background-color: #f0f2f6; color: #333; padding: 10px; border-radius: 5px; text-align: center; font-weight: 600; font-size: 14px; margin-bottom: 15px;}}

    

    .stButton>button {{border-radius: 20px; background-color: white; color: {COLOR_MORADO}; border: 1px solid {COLOR_MORADO}; font-weight: bold;}}

    .stButton>button:hover {{background-color: {COLOR_MORADO}; color: white;}}

</style>

""", unsafe_allow_html=True)

# ==========================================

# 3. CONEXIÓN DB (TTL=0)

# ==========================================





# --- LÍNEA ANTERIOR ---
@st.cache_resource(ttl=0) 
def conectar_db():
    import os
    import json
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]

        # 1. LEER DIRECTAMENTE DEL SISTEMA (Ignoramos st.secrets para evitar el error)
        # Buscamos la variable de entorno que configuraste en el panel de Railway
        env_secrets = os.environ.get("gcp_service_account")
        
        if env_secrets:
            # Si estamos en Railway, usamos la variable de entorno
            info = json.loads(env_secrets)
        else:
            # Si no hay variable (estamos en local/Streamlit Cloud), usamos st.secrets
            # Pero solo lo llamamos si la variable de entorno falla
            info = dict(st.secrets["gcp_service_account"])

        creds = Credentials.from_service_account_info(info, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_key(ID_SHEET)
        
    except Exception as e:
        # Esto te dirá el error real (ej: si el JSON está mal pegado)
        st.error(f"Error técnico real: {e}")
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

            

            # Cálculo seguro

            df['Calculado_Total'] = (df['Score_Somatica'] + df['Score_Energia'] + df['Score_Regulacion']) / 3

            df = df[(df['Calculado_Total'] >= 1.0) & (df['Calculado_Total'] <= 5.0)]

            return df

        except: return pd.DataFrame()

    return pd.DataFrame()



def verificar_privacidad(email):

    # 1. Obtenemos datos frescos

    df = obtener_datos_comunidad()

    

    # 2. Si no hay datos, pedimos aceptar

    if df.empty:

        return False



    # 3. Limpieza de nombres de columnas (Quita espacios invisibles en el Excel)

    df.columns = df.columns.str.strip()

    

    # Verificamos que existan las columnas necesarias

    if 'Email' not in df.columns or 'Privacidad_Aceptada' not in df.columns:

        return False

        

    # 4. Limpieza del correo ingresado (minúsculas y sin espacios)

    email_clean = email.strip().lower()

    

    # 5. Filtramos por correo (limpiando también la columna del Excel para asegurar coincidencia)

    mis_registros = df[df['Email'].astype(str).str.strip().str.lower() == email_clean]

    

    # Si nunca ha usado la app con este correo, debe aceptar

    if mis_registros.empty:

        return False

        

    # 6. SOLUCIÓN AL BUCLE:

    # Buscamos en TODO el historial si hay algún "SI", "Si", "si" o "Sí".

    # .str.upper().str.startswith('S') detecta cualquier variante que empiece con S.

    aceptados = mis_registros[mis_registros['Privacidad_Aceptada'].astype(str).str.strip().str.upper().str.startswith('S')]

    

    if not aceptados.empty:

        return True # ¡Encontró un registro positivo! Acceso concedido.

        

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



@st.cache_data(ttl=60)
def obtener_videos():
    try:
        client = conectar_db()
        if not client:
            return pd.DataFrame()

        ws = client.worksheet("VIDEOS_AULA")
        records = ws.get_all_records()

        if records:
            df = pd.DataFrame(records)
            df.columns = [str(c).strip() for c in df.columns]

            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
                df = df.sort_values(by='Fecha', ascending=False)

            return df

    except Exception as e:
        st.error(f"Error Aula Virtual: {e}")

    return pd.DataFrame()

    
  

# ==========================================

# 4. LÓGICA CIENTÍFICA

# ==========================================

def calcular_ser(resp):

    ene = sum([6-x for x in resp[0:4]]) / 4

    reg = sum([6-x for x in resp[4:12]]) / 8

    som = sum([x for x in resp[12:29]]) / 17

    idx = (ene + reg + som) / 3

    return round(som,2), round(ene,2), round(reg,2), round(idx,2)



def interpretar(idx):

    if idx < 2.0: return NIVELES_DATA[4][1], NIVELES_DATA[4][2]

    elif idx < 3.0: return NIVELES_DATA[3][1], NIVELES_DATA[3][2]

    elif idx < 4.0: return NIVELES_DATA[2][1], NIVELES_DATA[2][2]

    elif idx < 4.6: return NIVELES_DATA[1][1], NIVELES_DATA[1][2]

    else: return NIVELES_DATA[0][1], NIVELES_DATA[0][2]



# ==========================================

# 5. PDF

# ==========================================

class PDF(FPDF):

    def header(self):

        # Franja DORADA

        self.set_fill_color(218, 165, 32)

        self.rect(0, 0, 210, 35, 'F') 

        

        # Logo Ajustado (8mm)

        if os.path.exists("logo.png"):

            self.image("logo.png", 10, 10, 8)

            

        # Textos Header

        self.set_font('Arial', '', 10)

        self.set_text_color(255, 255, 255)

        self.set_xy(25, 15)

        self.cell(0, 5, 'UNIDAD CONSCIENTE', 0, 1, 'L')

        self.ln(20)



    def footer(self):

        self.set_y(-30)

        self.set_font('Arial', 'B', 9)

        self.set_text_color(218, 165, 32)

        self.cell(0, 5, 'UNIDAD CONSCIENTE', 0, 1, 'C')

        

        self.set_font('Arial', '', 8)

        self.set_text_color(50, 50, 50)

        self.cell(0, 5, 'Web: unidadconsciente.com', 0, 1, 'C', link=WEB_LINK)

        self.cell(0, 5, 'Instagram: @unidad_consciente', 0, 1, 'C', link=INSTA_LINK)

        self.cell(0, 5, f'WhatsApp: +{WHATSAPP}', 0, 1, 'C', link=f"https://wa.me/{WHATSAPP}")



def clean_text(text):

    if isinstance(text, str):

        text = text.replace("🟣", "").replace("🟢", "").replace("🟡", "").replace("🟠", "").replace("🔴", "")

        text = text.replace("🔹", "").replace("🧘", "").replace("⚡", "").replace("🌊", "")

        return text.encode('latin-1', 'replace').decode('latin-1')

    return text



def draw_bar_chart(pdf, s, e, r):

    pdf.ln(5)

    pdf.set_font("Arial", "B", 10)

    pdf.set_text_color(0, 0, 0)

    factor = 20 

    

    pdf.cell(30, 8, "Somatica:", 0, 0)

    pdf.set_fill_color(75, 0, 130)

    pdf.cell(s * factor, 6, f" {s}", 0, 1, 'L', fill=True)

    

    pdf.cell(30, 8, "Energia:", 0, 0)

    pdf.set_fill_color(218, 165, 32)

    pdf.cell(e * factor, 6, f" {e}", 0, 1, 'L', fill=True)

    

    pdf.cell(30, 8, "Regulacion:", 0, 0)

    pdf.set_fill_color(0, 128, 128)

    pdf.cell(r * factor, 6, f" {r}", 0, 1, 'L', fill=True)

    

    # NUEVA NOTA SOLICITADA

    pdf.ln(2)

    pdf.set_font("Arial", "I", 8)

    pdf.set_text_color(100, 100, 100)

    pdf.cell(0, 5, "Nota: Entre mas cercano a 5, mas salud y bienestar", ln=True, align='L')

    pdf.ln(3)



def draw_definitions_table(pdf):

    pdf.set_font("Arial", "B", 11)

    pdf.set_text_color(0, 0, 0)

    pdf.cell(0, 10, "DEFINICIONES S.E.R.", ln=True, align='L')

    

    pdf.set_font("Arial", "B", 8)

    pdf.set_text_color(255, 255, 255)

    pdf.set_fill_color(75, 0, 130)

    

    pdf.cell(30, 8, "Concepto", 1, 0, 'C', fill=True)

    pdf.cell(30, 8, "Simbolo", 1, 0, 'C', fill=True)

    pdf.cell(0, 8, "Significado", 1, 1, 'C', fill=True)

    

    pdf.set_font("Arial", "", 8)

    pdf.set_text_color(0, 0, 0)

    

    for concepto, simbolo, desc in DEFINICIONES_DATA:

        clean_c = clean_text(concepto)

        clean_s = clean_text(simbolo)

        clean_d = clean_text(desc)

        x_start = pdf.get_x()

        y_start = pdf.get_y()

        pdf.set_xy(x_start + 60, y_start)

        pdf.multi_cell(0, 5, clean_d, border=1)

        y_end = pdf.get_y()

        row_h = y_end - y_start

        pdf.set_xy(x_start, y_start)

        pdf.cell(30, row_h, clean_c, 1, 0, 'C')

        pdf.cell(30, row_h, clean_s, 1, 0, 'C')

        pdf.set_xy(x_start, y_end)



def draw_levels_table(pdf):

    pdf.set_font("Arial", "B", 11)

    pdf.set_text_color(0, 0, 0)

    pdf.cell(0, 10, "DESCRIPCION NIVELES S.E.R.", ln=True, align='L')

    

    pdf.set_font("Arial", "B", 8)

    pdf.set_text_color(255, 255, 255)

    pdf.set_fill_color(75, 0, 130)

    

    pdf.cell(20, 8, "Rango", 1, 0, 'C', fill=True)

    pdf.cell(45, 8, "Nivel", 1, 0, 'C', fill=True)

    pdf.cell(0, 8, "Descripcion", 1, 1, 'C', fill=True)

    

    pdf.set_font("Arial", "", 8)

    pdf.set_text_color(0, 0, 0)

    

    for rango, nivel, desc in NIVELES_DATA:

        clean_d = clean_text(desc)

        clean_n = clean_text(nivel)

        x_start = pdf.get_x()

        y_start = pdf.get_y()

        pdf.set_xy(x_start + 65, y_start)

        pdf.multi_cell(0, 5, clean_d, border=1)

        y_end = pdf.get_y()

        row_h = y_end - y_start

        pdf.set_xy(x_start, y_start)

        pdf.cell(20, row_h, rango, 1, 0, 'C')

        pdf.cell(45, row_h, clean_n, 1, 0, 'C')

        pdf.set_xy(x_start, y_end)



def generar_pdf(nombre, s, e, r, idx, estado, desc):

    pdf = PDF()

    pdf.add_page()

    pdf.set_auto_page_break(auto=True, margin=35)

    

    # TITULO CENTRADO BAJO LA FRANJA

    pdf.set_y(40)

    pdf.set_font("Arial", "B", 18)

    pdf.set_text_color(75, 0, 130) 

    pdf.cell(0, 10, 'INDICE S.E.R.', 0, 1, 'C')

    pdf.ln(5)

    

    # Fecha discreta

    pdf.set_font("Arial", "", 10)

    pdf.set_text_color(0, 0, 0)

    fecha_str = datetime.now().strftime('%d/%m/%Y')

    pdf.cell(0, 5, f"{fecha_str}", ln=True, align='R') 

    pdf.ln(5)



    # Texto fluido

    clean_nombre = clean_text(nombre)

    clean_estado = clean_text(estado)

    clean_desc = clean_text(desc)

    

    pdf.set_font("Arial", "", 12)

    texto_fluido = (

        f"Hola {clean_nombre}, tu indice S.E.R. es de {idx}/5.0, es decir, {clean_estado}. "

        f"Esto quiere decir que {clean_desc}"

    )

    

    pdf.multi_cell(0, 6, texto_fluido)

    pdf.ln(10)

    

    # Gráficas

    draw_bar_chart(pdf, s, e, r)

    

    # Tablas

    pdf.ln(8)

    draw_definitions_table(pdf)

    pdf.ln(8)

    draw_levels_table(pdf)

    

    return pdf.output(dest="S").encode("latin-1")



def mostrar_encabezado():
    col_logo, col_text = st.columns([1, 4])
    with col_logo:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=80)
    with col_text:
        st.markdown(f"""
        <div style="font-size: 24px; font-weight: bold; color: {COLOR_MORADO};">UNIDAD CONSCIENTE</div>
        <div>
            <a href="{WEB_LINK}" target="_blank" style="text-decoration: none; color: #666; margin-right: 15px;">🌐 Web</a>
            <a href="{INSTA_LINK}" target="_blank" style="text-decoration: none; color: #666;">📸 Instagram</a>
        </div>
        """, unsafe_allow_html=True)



# ==========================================

# 6. INTERFAZ PRINCIPAL
# ==========================================

with st.sidebar:

    st.markdown("### 🫀 Menú")

    modo = st.radio(
        "",
        ["📝 Índice S.E.R.", "🧘 Aula Virtual"],
        label_visibility="collapsed"
    )

    st.divider()

    acceso = False

    if modo == "🧘 Aula Virtual":
        pwd = st.text_input("Clave de Acceso:", type="password")
        if pwd == CLAVE_AULA:
            acceso = True


# ================================
# ÍNDICE S.E.R.
# ================================
if modo == "📝 Índice S.E.R.":

    mostrar_encabezado()
    st.markdown("---")

    st.markdown(
        "<h1>Indice S.E.R (Somática, Energía, Regulación)</h1>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="def-card" style="border-left: 4px solid {COLOR_MORADO}">
                <div class="def-title" style="color:{COLOR_MORADO}">🧘 SOMÁTICA</div>
                <div class="def-body">Capacidad de percibir y traducir señales internas.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="def-card" style="border-left: 4px solid {COLOR_DORADO}">
                <div class="def-title" style="color:{COLOR_DORADO}">⚡ ENERGÍA</div>
                <div class="def-body">Fuerza vital disponible para crear y sostener.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="def-card" style="border-left: 4px solid {COLOR_AZUL}">
                <div class="def-title" style="color:{COLOR_AZUL}">🌊 REGULACIÓN</div>
                <div class="def-body">Capacidad de retornar al equilibrio y la calma.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    if "resultado_listo" not in st.session_state:
        st.session_state.resultado_listo = False

    if "email_ok" not in st.session_state:
        st.session_state.email_ok = False

    # ================================
    # FORMULARIO
    # ================================
    with st.form("test_ser"):

        nombre = st.text_input("Nombre")
        email = st.text_input("Email").strip().lower()

        st.markdown(
            '<div class="scale-guide">1 = Nunca | 2 = Casi nunca | 3 = A veces | 4 = Frecuentemente | 5 = Siempre</div>',
            unsafe_allow_html=True
        )

        st.subheader("⚡ Energía")
        r_e = [
            st.slider(q, 1, 5, 1)
            for q in [
                "¿Tienes insomnio con frecuencia?",
                "¿Tienes dificultad para concentrarte?",
                "¿Sientes falta de aire frecuentemente?",
                "¿Te dan infecciones respiratorias con frecuencia?"
            ]
        ]

        st.subheader("🌊 Regulación")
        r_r = [
            st.slider(q, 1, 5, 1)
            for q in [
                "¿Sientes dolor de espalda?",
                "¿Tienes problemas estomacales?",
                "¿Experimentas ataques de pánico?",
                "¿Tienes dolores de cabeza?",
                "¿Suspiros frecuentemente?",
                "¿Ignoras la tensión física hasta que es severa?",
                "¿Te distraes de las sensaciones de malestar?",
                "¿Te preocupas apenas sientes una molestia?"
            ]
        ]

        st.subheader("🧘 Somática")
        r_s = [
            st.slider(q, 1, 5, 1)
            for q in [
                "¿Notas cuando te sientes incómodo en tu cuerpo?",
                "¿Notas cambios en tu respiración?",
                "¿Puedes prestar atención a tu respiración sin distraerte?",
                "¿Puedes mantener consciencia interna aunque haya movimiento alrededor?",
                "¿Al conversar, puedes prestar atención a tu postura?",
                "¿Puedes volver a concentrarte en tu cuerpo si te distraes?",
                "¿Puedes redirigir tu atención de pensamientos a sensaciones?",
                "¿Mantienes consciencia del cuerpo aunque una parte duela?",
                "¿Eres capaz de enfocarte en tu cuerpo como un todo?",
                "¿Notas cómo cambia tu cuerpo cuando estás enojado?",
                "¿Notas que tu cuerpo se siente diferente tras una experiencia pacífica?",
                "¿Notas que tu respiración se libera cuando estás cómodo?",
                "¿Al sentirte abrumado, encuentras un lugar de calma dentro de ti?",
                "¿Al sentirte tenso, usas tu respiración para reducir tensión?",
                "¿Cuando estás estresado, sabes relajarte físicamente?",
                "¿Respetas lo que tu cuerpo pide (descanso, comida)?",
                "¿Al tomar decisiones, consultas tus sensaciones corporales?"
            ]
        ]

        st.markdown("---")

        ya_acepto = verificar_privacidad(email) if email else False
        acepto_check = True
        priv_val = "SI"

        if ya_acepto:
            st.success("Hola de nuevo. Términos verificados.")
        else:
            st.warning("⚠️ Aviso de Privacidad")
            with st.expander("📄 Leer Aviso Legal"):
                st.markdown(AVISO_LEGAL_COMPLETO)
            acepto_check = st.checkbox("He leído y acepto el Aviso de Privacidad.")
            priv_val = "SI" if acepto_check else "NO"

        enviar = st.form_submit_button("🏁 OBTENER INDICE S.E.R.")

    # ================================
    # PROCESAMIENTO
    # ================================
    if enviar:

        if not nombre or not email:
            st.error("Por favor completa nombre y email.")

        elif not ya_acepto and not acepto_check:
            st.error("Debes aceptar el Aviso de Privacidad.")

        else:
            todas = r_e + r_r + r_s
            s, e, r, idx = calcular_ser(todas)
            tit, desc = interpretar(idx)

            fecha = datetime.now(
                pytz.timezone("America/Mexico_City")
            ).strftime("%Y-%m-%d")

            datos = [fecha, email, nombre, s, e, r, idx, tit] + todas + [priv_val]
            guardar_completo(datos)

            st.session_state.resultado_listo = True
            st.session_state.res_datos = (nombre, s, e, r, idx, tit, desc)

    # ================================
    # RESULTADOS
    # ================================
    if st.session_state.resultado_listo:

        nombre, s, e, r, idx, tit, desc = st.session_state.res_datos

        st.markdown("### 🗺️ Mapa de Niveles S.E.R.")

        st.markdown(f"""
<table style="width:100%; border-collapse: collapse;">
  <thead>
    <tr>
      <th style="background-color:{COLOR_MORADO}; padding: 12px; text-align: left; border: 1px solid #eee;">
        <span style="color: white !important; font-weight: bold;">Nivel</span>
      </th>
      <th style="background-color:{COLOR_MORADO}; padding: 12px; text-align: left; border: 1px solid #eee;">
        <span style="color: white !important; font-weight: bold;">Descripción</span>
      </th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="padding: 12px; border: 1px solid #eee;">🟣 <b>ALTA SINTERGIA</b><br>(4.6 - 5.0)</td>
      <td style="padding: 12px; border: 1px solid #eee;">Existe una coherencia total entre cerebro y corazón. Tu energía fluye sin obstáculos, permitiendo un estado de presencia absoluta y máxima expansión creativa.</td>
    </tr>
    <tr>
      <td style="padding: 12px; border: 1px solid #eee;">🟢 <b>ZONA DE PRESENCIA</b><br>(4.0 - 4.5)</td>
      <td style="padding: 12px; border: 1px solid #eee;">Posees la flexibilidad interna para sentir la intensidad de la vida y retornar a tu centro mediante la práctica consciente.</td>
    </tr>
    <tr>
      <td style="padding: 12px; border: 1px solid #eee;">🟡 <b>MODO RESISTENCIA</b><br>(3.0 - 3.9)</td>
      <td style="padding: 12px; border: 1px solid #eee;">Tu sistema mantiene la funcionalidad a través del esfuerzo. Hay signos de agotamiento, pero conservas capacidad de regreso.</td>
    </tr>
    <tr>
      <td style="padding: 12px; border: 1px solid #eee;">🟠 <b>ZONA REACTIVA</b><br>(2.0 - 2.9)</td>
      <td style="padding: 12px; border: 1px solid #eee;">Química de defensa y alerta perpetua. El sistema está saturado y cuesta regresar al centro.</td>
    </tr>
    <tr>
      <td style="padding: 12px; border: 1px solid #eee;">🔴 <b>ZONA DE DESCONEXIÓN</b><br>(1.0 - 1.9)</td>
      <td style="padding: 12px; border: 1px solid #eee;">Estado profundo de Burnout con sobreactivación constante. Se recomienda ayuda profesional.</td>
    </tr>
  </tbody>
</table>
""", unsafe_allow_html=True)


        st.divider()

        df_com = obtener_datos_comunidad()
        prom_total = df_com["Calculado_Total"].mean() if not df_com.empty else 0

        c1, c2 = st.columns(2)

        with c1:
            st.markdown(
                f"""
                <div class='kpi-container'>
                    <div class='kpi-label'>TU ÍNDICE S.E.R.</div>
                    <div class='big-score'>{idx}</div>
                    <div class='community-score'>Promedio Comunidad: {prom_total:.1f}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c2:
            st.markdown(
                f"<h3 style='color:{COLOR_MORADO};'>{tit}</h3>",
                unsafe_allow_html=True
            )
            st.info(desc)


        st.markdown("##### 📊 Desglose por Dimensión")

        df_bar = pd.DataFrame({'Dim':['Somática','Energía','Regulación'], 'Puntaje':[s,e,r], 'Color':[COLOR_MORADO, COLOR_DORADO, COLOR_AZUL]})

        fig_bar = px.bar(df_bar, x='Puntaje', y='Dim', orientation='h', color='Dim', color_discrete_map={'Somática':COLOR_MORADO, 'Energía':COLOR_DORADO, 'Regulación':COLOR_AZUL})

        fig_bar.update_layout(height=180, xaxis=dict(range=[0,5.5]), margin=dict(t=0,b=0,l=0,r=0), showlegend=False)

        st.plotly_chart(fig_bar, use_container_width=True)

        st.caption("Nota: Un puntaje mayor (cercano a 5) indica mayor integración y salud.")



        st.markdown("##### 🆚 Radar Comparativo")

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(r=[s,e,r,s], theta=['SOM','ENE','REG','SOM'], fill='toself', name='TÚ', line_color='#4B0082'))

        

        if not df_com.empty:

             prom_s = df_com['Score_Somatica'].mean()

             prom_e = df_com['Score_Energia'].mean()

             prom_r = df_com['Score_Regulacion'].mean()

             # RADAR OSCURO (OPACITY 0.7)

             fig.add_trace(go.Scatterpolar(r=[prom_s,prom_e,prom_r,prom_s], theta=['SOM','ENE','REG','SOM'], fill='toself', name='COMUNIDAD', line_color='#444444', opacity=0.7))

        

        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,5])), height=250, margin=dict(t=20,b=20))

        st.plotly_chart(fig, use_container_width=True)

        

        if not df_com.empty and 'Email' in df_com.columns:

             mis_datos = df_com[df_com['Email'].astype(str).str.lower() == email]

             if not mis_datos.empty and 'Fecha' in mis_datos.columns:

                 mis_datos['Fecha'] = pd.to_datetime(mis_datos['Fecha'], errors='coerce')

                 mis_datos = mis_datos.sort_values('Fecha')

                 if len(mis_datos) > 1:

                     st.markdown("##### 📈 Tu Evolución en el Tiempo")

                     fig_line = px.line(mis_datos, x='Fecha', y='Calculado_Total', markers=True)

                     fig_line.update_traces(line_color=COLOR_MORADO)

                     fig_line.update_layout(yaxis=dict(range=[1,5.5]), height=250)

                     st.plotly_chart(fig_line, use_container_width=True)



        st.markdown("---")

        pdf_bytes = generar_pdf(nombre, s, e, r, idx, tit, desc)

        

        # NOMBRE DE ARCHIVO CORRECTO (Reemplaza espacios con guiones)

        safe_name = nombre.replace(" ", "_")

        

        c_d1, c_d2 = st.columns(2)

        with c_d1:

            st.download_button("📥 Descargar Reporte (PDF)", pdf_bytes, f"Indice_SER_{safe_name}.pdf", "application/pdf")

        with c_d2:

            # WHATSAPP WARM

            msg = f"Hola, soy {nombre}. Acabo de recibir mi Índice S.E.R. de {idx} ({tit}). Me gustaría saber cómo puedo subir mi indice s.e.r y aumentar mi bienestar."

            link_wa = f"https://wa.me/{WHATSAPP}?text={urllib.parse.quote(msg)}"

            st.link_button("🟢 Quiero mejorar mi ÍNDICE S.E.R.", link_wa, type="primary")



elif modo == "🧘 Aula Virtual":

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
                    url_video = row['Link'].replace("youtu.be/", "www.youtube.com/embed/").replace("watch?v=", "embed/")
                    st.video(url_video)
                    

        else: st.info("No hay clases cargadas aún.")

    else: st.warning("🔒 Ingresa tu clave en la barra lateral.")
