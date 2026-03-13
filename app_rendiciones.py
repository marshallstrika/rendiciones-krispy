import streamlit as st
from fpdf import FPDF
from datetime import datetime
import tempfile
import os

# --- ESTILOS WEB CORPORATIVOS ---
st.set_page_config(page_title="Portal de Rendiciones", page_icon="🍩", layout="wide")
st.markdown("""
<style>
    div[data-testid="stMetricValue"] { color: #00704A; font-weight: bold; }
    .stButton>button { border: 2px solid #00704A; color: #00704A; font-weight: bold; }
    .stButton>button:hover { background-color: #00704A; color: white; }
</style>
""", unsafe_allow_html=True)

# --- MOTOR DE PDF: DISEÑO DASHBOARD KRISPY KREME ---
class ReportePDF(FPDF):
    def __init__(self):
        super().__init__(orientation='L', unit='mm', format='A4')
        self.set_auto_page_break(auto=True, margin=20)
        
        self.kk_green = (0, 112, 74)
        self.kk_red = (209, 35, 42)
        self.kk_light_grey = (245, 245, 245)
        self.kk_dark_grey = (50, 50, 50)
        
    def header(self):
        self.set_fill_color(*self.kk_red)
        self.rect(0, 0, 297, 6, 'F')
        
        self.set_fill_color(*self.kk_green)
        self.rect(15, 6, 65, 22, 'F')
        
        # Logo sin texto inferior
        self.set_xy(15, 12)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.cell(65, 10, 'KRISPY KREME', align='C', ln=1)
        
        self.set_xy(90, 12)
        self.set_font('Arial', 'B', 24)
        self.set_text_color(*self.kk_green)
        self.cell(192, 10, 'REPORTE DE RENDICION', align='R', ln=1)
        
        # Procesamiento manual de fecha en español
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        mes_actual = meses[datetime.now().month - 1]
        fecha_esp = f'Generado el: {datetime.now().day} de {mes_actual}, {datetime.now().year} | {datetime.now().strftime("%H:%M")}'
        
        self.set_x(90)
        self.set_font('Arial', '', 10)
        self.set_text_color(120, 120, 120)
        self.cell(192, 6, fecha_esp, align='R')
        self.ln(22)

    def footer(self):
        self.set_y(-18)
        self.set_draw_color(*self.kk_red)
        self.set_line_width(0.5)
        self.line(15, self.get_y(), 282, self.get_y())
        
        self.set_y(-14)
        self.set_font('Arial', 'B', 8)
        self.set_text_color(*self.kk_green)
        self.cell(100, 10, 'CONFIDENCIAL - KRISPY KREME CHILE', align='L')
        
        self.set_text_color(150, 150, 150)
        self.set_font('Arial', '', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', align='R')

# --- LÓGICA DE MONTOS Y AUTO-LIMPIEZA ---
if 'lista_montos' not in st.session_state:
    st.session_state.lista_montos = []
if 'monto_reset_key' not in st.session_state:
    st.session_state.monto_reset_key = 0

def agregar_monto_y_limpiar():
    clave_actual = f"monto_temp_{st.session_state.monto_reset_key}"
    valor_texto = st.session_state.get(clave_actual, "")
    if valor_texto:
        try:
            valor_num = int(valor_texto.replace(".", "").replace(",", "").strip())
            if valor_num > 0:
                st.session_state.lista_montos.append(valor_num)
        except ValueError:
            pass
    st.session_state.monto_reset_key += 1

# --- INTERFAZ WEB ---
st.title("🍩 Portal de Rendiciones")

with st.expander("💰 Panel de Carga Rápida", expanded=True):
    st.text_input(
        "Ingresa el monto de la boleta y presiona ENTER", 
        placeholder="Ejemplo: 4500",
        key=f"monto_temp_{st.session_state.monto_reset_key}", 
        on_change=agregar_monto_y_limpiar
    )
    if st.session_state.lista_montos:
        total = sum(st.session_state.lista_montos)
        st.info(f"**Historial de la sesión:** {' + '.join([f'${m:,}' for m in st.session_state.lista_montos])}")
        st.metric("TOTAL RENDICIÓN", f"${total:,}")
        if st.button("Limpiar Registros"):
            st.session_state.lista_montos = []
            st.rerun()

st.divider()

col_a, col_b = st.columns(2)
with col_a:
    fecha = st.date_input("Fecha del Gasto", datetime.now())
    categoria = st.selectbox("Categoría de Gasto", ["Insumos Tecnicos", "Auditoria Mystery Shopper", "Logistica", "Otros"])
with col_b:
    fotos = st.file_uploader("Adjuntar Boletas (Capturas)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

detalle = st.text_area("Justificación Técnica del Gasto", height=100)

# --- GENERADOR DEL PDF ---
if st.button("🚀 Emitir reporte"):
    if not fotos or not st.session_state.lista_montos:
        st.error("Datos incompletos. Asegúrate de cargar montos y fotografías.")
    else:
        try:
            pdf = ReportePDF()
            pdf.add_page()
            
            total_f = sum(st.session_state.lista_montos)
            desglose_f = " + ".join([f"${m:,}" for m in st.session_state.lista_montos])
            y_start = pdf.get_y()
            
            pdf.set_fill_color(*pdf.kk_light_grey)
            pdf.rect(15, y_start, 60, 22, 'F')
            pdf.set_xy(15, y_start + 4)
            pdf.set_font('Arial', 'B', 8)
            pdf.set_text_color(*pdf.kk_green)
            pdf.cell(60, 5, '  FECHA DEL GASTO', align='L', ln=1)
            pdf.set_x(15)
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color(*pdf.kk_dark_grey)
            pdf.cell(60, 8, f'  {fecha}', align='L')
            
            pdf.rect(80, y_start, 90, 22, 'F')
            pdf.set_xy(80, y_start + 4)
            pdf.set_font('Arial', 'B', 8)
            pdf.set_text_color(*pdf.kk_green)
            pdf.cell(90, 5, '  CATEGORIA', align='L', ln=1)
            pdf.set_x(80)
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color(*pdf.kk_dark_grey)
            pdf.cell(90, 8, f'  {categoria.upper()}', align='L')
            
            pdf.rect(175, y_start, 107, 22, 'F')
            pdf.set_xy(175, y_start + 4)
            pdf.set_font('Arial', 'B', 8)
            pdf.set_text_color(*pdf.kk_red)
            pdf.cell(102, 5, 'MONTO TOTAL', align='R', ln=1)
            pdf.set_x(175)
            pdf.set_font('Arial', 'B', 22)
            pdf.set_text_color(*pdf.kk_dark_grey)
            pdf.cell(102, 9, f'${total_f:,}', align='R')
            
            pdf.set_y(y_start + 28)
            
            pdf.set_fill_color(*pdf.kk_light_grey)
            pdf.rect(15, pdf.get_y(), 267, 16, 'F')
            pdf.set_xy(15, pdf.get_y() + 2)
            pdf.set_font('Arial', 'B', 8)
            pdf.set_text_color(*pdf.kk_green)
            pdf.cell(267, 5, '  DESGLOSE MATEMATICO', align='L', ln=1)
            pdf.set_x(15)
            pdf.set_font('Arial', '', 11)
            pdf.set_text_color(*pdf.kk_dark_grey)
            pdf.cell(267, 7, f'  {desglose_f}', align='L')
            
            pdf.ln(12)
            
            y_just = pdf.get_y()
            pdf.set_font('Arial', 'B', 9)
            pdf.set_text_color(*pdf.kk_green)
            pdf.cell(267, 6, 'JUSTIFICACION TECNICA DEL GASTO', ln=1)
            
            y_texto = pdf.get_y()
            pdf.set_font('Arial', '', 11)
            pdf.set_text_color(*pdf.kk_dark_grey)
            
            pdf.set_x(20)
            pdf.multi_cell(257, 6, f'{detalle}', border=0)
            
            h_barra = pdf.get_y() - y_texto
            pdf.set_fill_color(*pdf.kk_red)
            pdf.rect(15, y_texto, 2, h_barra, 'F')
            
            pdf.ln(15)
            
            pdf.set_font('Arial', 'B', 14)
            pdf.set_text_color(*pdf.kk_green)
            pdf.cell(0, 10, 'REPORTE FOTOGRAFICO', ln=1)
            
            pdf.set_draw_color(220, 220, 220)
            pdf.set_line_width(0.3)
            pdf.line(15, pdf.get_y(), 282, pdf.get_y())
            pdf.ln(8)

            for foto in fotos:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(foto.getvalue())
                    ruta = tmp.name
                
                if pdf.get_y() > 140:
                    pdf.add_page()
                
                pdf.image(ruta, x=15, w=110)
                pdf.ln(8)
                os.remove(ruta)

            out_bytes = pdf.output()
            st.success("✅ Reporte corporativo generado.")
            st.download_button("📥 Generar informe", data=bytes(out_bytes), file_name=f"Reporte_KK_{fecha}.pdf")
            
        except Exception as e:
            st.error(f"Error técnico crítico: {e}")