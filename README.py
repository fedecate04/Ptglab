import streamlit as st import pandas as pd import numpy as np from fpdf import FPDF import io from datetime import datetime

Datos base para cálculos de gas natural

PM = { 'CH4': 16.04, 'C2H6': 30.07, 'C3H8': 44.10, 'i-C4H10': 58.12, 'n-C4H10': 58.12, 'i-C5H12': 72.15, 'n-C5H12': 72.15, 'C6+': 86.00, 'N2': 28.01, 'CO2': 44.01, 'H2S': 34.08, 'O2': 32.00 } HHV = { 'CH4': 39.82, 'C2H6': 70.6, 'C3H8': 101.0, 'i-C4H10': 131.6, 'n-C4H10': 131.6, 'i-C5H12': 161.0, 'n-C5H12': 161.0, 'C6+': 190.0 } R = 8.314 PM_aire = 28.96 T_std = 288.15 P_std = 101325

def analizar_composicion(composicion): composicion = {k: float(v) for k, v in composicion.items() if k in PM} total = sum(composicion.values()) if total == 0: return {} fracciones = {k: v / total for k, v in composicion.items()} pm_muestra = sum(fracciones[k] * PM[k] for k in fracciones) densidad = (pm_muestra * P_std) / (R * T_std) hhv_total = sum(fracciones.get(k, 0) * HHV.get(k, 0) for k in HHV) gamma = PM_aire / pm_muestra wobbe = hhv_total / np.sqrt(pm_muestra / PM_aire) dew_point = -30 if fracciones.get('C6+', 0) > 0.01 else -60 api_h2s_ppm = composicion.get('H2S', 0) * 1e4 carga_h2s = (api_h2s_ppm * PM['H2S'] / 1e6) / (pm_muestra * 1e3) ingreso = hhv_total * 2.25 validacion = { 'CO2 (%)': (composicion.get('CO2', 0), ('<', 2, '% molar')), 'Inertes totales': (sum(composicion.get(k, 0) for k in ['N2', 'CO2', 'O2']), ('<', 4, '% molar')), 'O2 (%)': (composicion.get('O2', 0), ('<', 0.2, '% molar')), 'H2S (ppm)': (api_h2s_ppm, ('<', 2, 'ppm')), 'PCS (kcal/m3)': (hhv_total * 239.006, ('>=', (8850, 12200), 'Kcal/Sm3')) } return { 'PM': pm_muestra, 'PCS (MJ/m3)': hhv_total, 'PCS (kcal/m3)': hhv_total * 239.006, 'Gamma': gamma, 'Wobbe': wobbe, 'Densidad (kg/m3)': densidad, 'Dew Point estimado (°C)': dew_point, 'CO2 (%)': composicion.get('CO2', 0), 'H2S ppm': api_h2s_ppm, 'Carga H2S (kg/kg)': carga_h2s, 'Ingreso estimado (USD/m3)': ingreso, 'Validacion': validacion }

def mostrar_validacion(resultados): st.subheader("Validación de parámetros") for param, (valor, (op, ref, unidad)) in resultados['Validacion'].items(): if op == '<': cumple = valor < ref espec = f"< {ref} {unidad}" else: cumple = ref[0] <= valor <= ref[1] espec = f"{ref[0]}–{ref[1]} {unidad}" color = "✅" if cumple else "❌" st.markdown(f"{color} {param}: {valor:.2f} ({espec})")

class PDF(FPDF): def header(self): self.set_font('Arial', 'B', 12) self.cell(0, 10, 'Informe de Análisis de Muestra', 0, 1, 'C') self.ln(5)

def add_sample(self, nombre, resultados):
    self.set_font('Arial', '', 10)
    self.cell(0, 10, f"Muestra: {nombre}", 0, 1)
    for k, v in resultados.items():
        if isinstance(v, dict):
            continue
        self.cell(0, 8, f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}", 0, 1)
    self.ln(3)

App principal con pestañas

st.set_page_config(page_title="App de Laboratorio LTS", layout="wide") st.title("Laboratorio de Planta LTS - Análisis de Muestras")

tabs = st.tabs([ "Dashboard", "Cálculo de Propiedades", "Análisis de Gasolina", "Carga de Muestras", "Resultados de Análisis", "Procedimientos de Ensayo", "Informes y Exportación", "Historial y Trazabilidad", "Herramientas Técnicas", "Biblioteca Técnica", "Configuración" ])

TAB 1: Dashboard

with tabs[0]: st.subheader("Resumen Diario") st.metric("Muestras del día", 12) st.metric("Parámetros fuera de especificación", "2") st.metric("Último análisis", "Scrubber - Gas 05/05 08:30")

TAB 2: Cálculo de propiedades de gas

with tabs[1]: st.subheader("Cálculo de Propiedades del Gas Natural")

tipo_entrada = st.radio("Tipo de ingreso", ["Desde archivo CSV", "Manual"])
resultados = {}

if tipo_entrada == "Desde archivo CSV":
    archivo = st.file_uploader("Subí un archivo CSV con una muestra", type="csv")
    if archivo:
        df = pd.read_csv(archivo)
        indice = st.number_input("Selecciona la fila de muestra", min_value=0, max_value=len(df)-1, value=0)
        fila = df.iloc[indice]
        composicion = {k: fila[k] for k in PM if k in fila}
        resultados = analizar_composicion(composicion)

elif tipo_entrada == "Manual":
    st.markdown("**Ingresá la composición molar (%):**")
    composicion = {}
    for comp in PM:
        composicion[comp] = st.number_input(f"{comp}", min_value=0.0, max_value=100.0, step=0.01)
    suma_fracciones = sum(composicion.values())
    st.markdown(f"**Suma de fracciones:** {suma_fracciones:.2f}%")
    if abs(suma_fracciones - 100) > 1:
        st.warning("La suma no es 100%. Revisá los valores.")
    if st.button("Calcular propiedades"):
        resultados = analizar_composicion(composicion)

if resultados:
    st.success("Resultados del análisis")
    st.dataframe(pd.DataFrame.from_dict(resultados, orient='index', columns=['Valor']))
    mostrar_validacion(resultados)

    st.subheader("Descargar informe")
    operador = st.text_input("Nombre del operador")
    if st.button("Generar PDF"):
        pdf = PDF()
        pdf.add_page()
        pdf.add_sample(f"Muestra - {operador}", resultados)
        buffer = io.BytesIO()
        pdf.output(buffer)
        buffer.seek(0)
        st.download_button(
            label="Descargar informe PDF",
            data=buffer,
            file_name=f"Informe_Gas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf"
        )

TAB 3: Análisis de Gasolina

with tabs[2]: st.subheader("Análisis de Gasolina Estabilizada")

with st.form("form_gasolina"):
    tvr = st.number_input("Tensión de vapor Reid (TVR) [psi]", min_value=0.0)
    sales = st.number_input("Contenido de sales [mg/L]", min_value=0.0)
    densidad = st.number_input("Densidad a 15 °C [kg/m³]", min_value=600.0, max_value=800.0)
    apariencia = st.selectbox("Apariencia", ["Limpia", "Turbia", "Sedimentos"])
    operador_g = st.text_input("Nombre del operador")
    enviado = st.form_submit_button("Analizar muestra")

if enviado:
    validaciones = {
        "TVR (psi)": (tvr, ('>=', (8, 15))),
        "Sales (mg/L)": (sales, ('<', 5)),
        "Densidad (kg/m³)": (densidad, ('>=', (700, 750))),
        "Apariencia": (apariencia, ('==', 'Limpia'))
    }

    st.subheader("Validación de Parámetros")
    for param, (valor, regla) in validaciones.items():
        op, ref = regla
        cumple = False
        if op == '<':
            cumple = valor < ref
            espec = f"< {ref}"
        elif op == '>=':
            cumple = ref[0] <= valor <= ref[1]
            espec = f"{ref[0]} – {ref[1]}"
        elif op == '==':
            cumple = valor == ref
            espec = f"Debe ser: {ref}"

        color = '✅' if cumple else '❌'
        st.markdown(f"**{color} {param}:** {valor} ({espec})")

    # Exportar a PDF
    if st.button("Generar informe de gasolina"):
        pdf = PDF()
        pdf.add_page()
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, f"Muestra de Gasolina - Operador: {operador_g}", 0, 1)
        pdf.cell(0, 8, f"TVR: {tvr} psi", 0, 1)
        pdf.cell(0, 8, f"Sales: {sales} mg/L", 0, 1)
        pdf.cell(0, 8, f"Densidad: {densidad} kg/m³", 0, 1)
        pdf.cell(0, 8, f"Apariencia: {apariencia}", 0, 1)
        pdf.ln(4)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 8, "Validaciones:", 0, 1)
        pdf.set_font('Arial', '', 10)
        for param, (valor, regla) in validaciones.items():
            op, ref = regla
            if op == '<':
                cumple = valor < ref
                espec = f"< {ref}"
            elif op == '>=':
                cumple = ref[0] <= valor <= ref[1]
                espec = f"{ref[0]} – {ref[1]}"
            elif op == '==':
                cumple = valor == ref
                espec = f"Debe ser: {ref}"
            estado = 'CUMPLE' if cumple else 'NO CUMPLE'
            pdf.cell(0, 8, f"{estado} {param}: {valor} ({espec})", 0, 1)

        buffer = io.BytesIO()
        pdf.output(buffer)
        buffer.seek(0)
        st.download_button(
            label="Descargar informe PDF",
            data=buffer,
            file_name=f"Informe_Gasolina_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf"
        )

