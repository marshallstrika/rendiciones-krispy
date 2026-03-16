import streamlit as st
from fpdf import FPDF
from datetime import datetime
import tempfile
import os
from PIL import Image  # Nueva librería para procesar fotos correctamente

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Rendición de Gastos", page_icon="donut", layout="wide")
st.markdown("""
<style>
    div[data-testid="stMetricValue"] { color: #00704A; font-weight: bold; }
    .stButton>button { border: 2px solid #00704A; color: #00704A; font-weight: bold; width: 100%; }
</style>
""", unsafe_allow_html=True)

class ReportePDF(FPDF):
    def __init__(self):
        super().__init__(orientation='L', unit='mm', format='A4')
        self.kk_green, self.kk_red = (0, 112, 74), (209, 35, 42)
        
    def header(self):
        self.set_fill_color(*self.kk_red); self.rect(0, 0, 297, 6, 'F')
        self.set_fill_color(*self.kk_green); self.rect(15, 6, 65, 20, 'F')
        self.set_xy(15, 11); self.set_font('Arial', 'B', 16); self.set_text_color(255, 255, 255)
        self.cell(65, 10, 'KRISPY KREME', align='C', ln=1)
        self.set_xy(90, 10); self.set_font('Arial', 'B', 22); self.set_text_color(*self.kk_green)
        self.cell(192, 10, 'RENDICION DE GASTOS', align='R', ln=1)
        self.ln(15)

    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8); self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Página {self.page_no()} | Soporte Administrativo', align='R')

# --- LÓGICA DE DATOS ---
if 'lista_montos' not in st.session_state: st.session_state.lista_montos = []
if 'monto_reset_key' not in st.session_state: st.session_state.monto_reset_key = 0

def agregar_monto():
    key = f"monto_temp_{st.session_state.monto_reset_key}"
    valor = st.session_state.get(key, "")
    if valor:
        try:
            num = int(valor.replace(".", "").replace(",", "").strip())
            if num > 0: st.session_state.lista_montos.append(num)
        except: pass
    st.session_state.monto_reset_key += 1

# --- INTERFAZ ---
st.title("Rendición de Gastos")

with st.sidebar:
    st.header("Identificación")
    responsable = st.text_input("Responsable del Gasto", placeholder="Nombre y Apellido")
    st.divider()
    if st.button("🔄 Reiniciar"):
        st.session_state.lista_montos = []
        st.rerun()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("💰 Montos")
    st.text_input("Monto + ENTER", key=f"monto_temp_{st.session_state.monto_reset_key}", on_change=agregar_monto)
    if st.session_state.lista_montos:
        total = sum(st.session_state.lista_montos)
        st.metric("TOTAL ACUMULADO", f"${total:,}")
        st.write("**Detalle de montos:**")
        for i, m in enumerate(st.session_state.lista_montos, 1):
            st.text(f"Boleta {i}: ${m:,}")

with col2:
    st.subheader("📝 Detalles")
    c_gasto, f_gasto = st.columns(2)
    categoria = c_gasto.selectbox("Categoría", ["Insumos Técnicos", "Auditoría Mystery Shopper", "Logística", "Mantenimiento", "Otros"])
    fecha_gasto = f_gasto.date_input("Fecha del Gasto", datetime.now())
    detalle = st.text_area("Justificación", placeholder="Motivo del gasto...")
    fotos = st.file_uploader("Adjuntar Boletas", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

st.divider()

if fotos and st.session_state.lista_montos and responsable:
    pdf = ReportePDF()
    pdf.add_page()
    
    # Bloque Resumen
    pdf.set_fill_color(245, 245, 245); pdf.rect(15, 35, 267, 25, 'F')
    pdf.set_xy(20, 38); pdf.set_font('Arial', 'B', 9); pdf.set_text_color(*pdf.kk_green)
    pdf.cell(89, 5, 'RESPONSABLE'); pdf.cell(89, 5, 'CATEGORÍA'); pdf.cell(89, 5, 'TOTAL ACUMULADO', ln=1)
    
    pdf.set_x(20); pdf.set_font('Arial', '', 12); pdf.set_text_color(50, 50, 50)
    pdf.cell(89, 8, responsable.upper()); pdf.cell(89, 8, categoria.upper())
    pdf.set_font('Arial', 'B', 14); pdf.set_text_color(*pdf.kk_red)
    pdf.cell(89, 8, f'${sum(st.session_state.lista_montos):,}', ln=1)

    pdf.ln(12)
    pdf.set_font('Arial', 'B', 10); pdf.set_text_color(*pdf.kk_green)
    pdf.cell(0, 6, 'DESGLOSE DE MONTOS:', ln=1)
    pdf.set_font('Arial', '', 10); pdf.set_text_color(50, 50, 50)
    montos_str = [f"Bol. {i+1}: ${m:,}" for i, m in enumerate(st.session_state.lista_montos)]
    pdf.multi_cell(267, 5, " | ".join(montos_str), border=0)

    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10); pdf.set_text_color(*pdf.kk_green)
    pdf.cell(0, 6, 'JUSTIFICACIÓN TÉCNICA:', ln=1)
    pdf.set_font('Arial', '', 11); pdf.multi_cell(267, 6, detalle if detalle else "Sin descripción.", border=0)

    # Anexo Fotográfico Mejorado
    for i, foto in enumerate(fotos):
        if i % 2 == 0:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14); pdf.set_text_color(*pdf.kk_green)
            pdf.cell(0, 10, f'ANEXO FOTOGRÁFICO - LÁMINA {(i//2) + 1}', ln=1)
            pdf.line(15, pdf.get_y(), 282, pdf.get_y())

        # TRATAMIENTO DE IMAGEN SEGURO
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            img = Image.open(foto)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB") # Evita error de transparencia
            img.save(tmp.name, format="JPEG", quality=85)
            ruta = tmp.name
        
        pdf.image(ruta, x=(15 if i % 2 == 0 else 155), y=45, w=125)
        os.remove(ruta)

    fecha_emision = datetime.now().strftime("%d-%m-%Y")
    nombre_archivo = f"{responsable.replace(' ', '_')}_{fecha_emision}.pdf"
    
    st.download_button(
        label="🚀 Generar y Descargar Reporte",
        data=bytes(pdf.output()),
        file_name=nombre_archivo,
        mime="application/pdf"
    )
else:
    st.info("💡 Complete los datos para habilitar la descarga.")
