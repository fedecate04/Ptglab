import streamlit as st import pandas as pd import numpy as np from fpdf import FPDF import io from datetime import datetime

Configuración general

st.set_page_config(page_title="LTS Lab Analyzer", layout="wide") st.title("Laboratorio de Planta LTS - Selección de Análisis")

Página principal con selector

st.subheader("¿Qué análisis desea realizar?")

opcion = st.selectbox("Seleccioná el tipo de análisis:", [ "-- Seleccionar --", "Propiedades del Gas Natural", "Gasolina Estabilizada", "MEG", "Agua Desmineralizada" ])

Función base para exportar PDF

class PDF(FPDF): def header(self): self.set_font('Arial', 'B', 12) self.cell(0, 10, 'Informe de Análisis de Muestra', 0, 1, 'C') self.ln(5) def add_sample(self, nombre, resultados): self.set_font('Arial', '', 10) self.cell(0, 10, f"Muestra: {nombre}", 0, 1) for k, v in resultados.items(): self.cell(0, 8, f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}", 0, 1) self.ln(3)

Análisis de propiedades del gas natural

if opcion == "Propiedades del Gas Natural": st.subheader("Cálculo de Propiedades del Gas Natural")

PM = {
    'CH4': 16.04, 'C2H6': 30.07, 'C3H8': 44.10,
    'i-C4H10': 58.12, 'n-C4H10': 58.12, 'i-C5H12': 72.15, 'n-C5H12': 72.15,
    'C6+': 86.00, 'N2': 28.01, 'CO2': 44.01, 'H2S': 34.08, 'O2': 32.00
}
HHV = {
    'CH4': 39.82, 'C2H6': 70.6, 'C3H8': 101.0,
    'i-C4H10': 131.6, 'n-C4H10': 131.6,
    'i-C5H12': 161.0, 'n-C5H12': 161.0,
    'C6+': 190.0
}
R = 8.314
PM_aire = 28.96
T_std = 288.15
P_std = 101325

def analizar_composicion(composicion):
    composicion = {k: float(v) for k, v in composicion.items() if k in PM}
    total = sum(composicion.values())
    fracciones = {k: v / total for k, v in composicion.items()}
    pm_muestra = sum(fracciones[k] * PM[k] for k in fracciones)
    densidad = (pm_muestra * P_std) / (R * T_std)
    hhv_total = sum(fracciones.get(k, 0) * HHV.get(k, 0) for k in HHV)
    gamma = PM_aire / pm_muestra
    wobbe = hhv_total / np.sqrt(pm_muestra / PM_aire)
    dew_point = -30 if fracciones.get('C6+', 0) > 0.01 else -60
    api_h2s_ppm = composicion.get('H2S', 0) * 1e4
    carga_h2s = (api_h2s_ppm * PM['H2S'] / 1e6) / (pm_muestra * 1e3)
    ingreso = hhv_total * 2.25
    return {
        'PM': pm_muestra,
        'PCS (MJ/m3)': hhv_total,
        'PCS (kcal/m3)': hhv_total * 239.006,
        'Gamma': gamma,
        'Wobbe': wobbe,
        'Densidad (kg/m3)': densidad,
        'Dew Point estimado (°C)': dew_point,
        'CO2 (%)': composicion.get('CO2', 0),
        'H2S ppm': api_h2s_ppm,
        'Carga H2S (kg/kg)': carga_h2s,
        'Ingreso estimado (USD/m3)': ingreso
    }

st.markdown("**Ingresá la composición molar (%):**")
composicion = {}
for comp in PM:
    composicion[comp] = st.number_input(f"{comp}", min_value=0.0, max_value=100.0, step=0.01)

if st.button("Calcular propiedades del gas"):
    suma = sum(composicion.values())
    if abs(suma - 100) > 1:
        st.warning(f"La suma de fracciones molares es {suma:.2f}%. Verificá los valores.")
    else:
        resultados = analizar_composicion(composicion)
        st.success("Resultados del análisis")
        st.dataframe(pd.DataFrame.from_dict(resultados, orient='index', columns=['Valor']))

        operador = st.text_input("Nombre del operador")
        if st.button("Descargar informe PDF"):
            pdf = PDF()
            pdf.add_page()
            pdf.add_sample(f"Gas Natural - {operador}", resultados)
            buffer = io.BytesIO()
            pdf.output(buffer)
            buffer.seek(0)
            st.download_button(
                label="Descargar informe",
                data=buffer,
                file_name=f"Informe_Gas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )

Placeholder para próximos análisis

elif opcion == "Gasolina Estabilizada": st.subheader("Análisis de Gasolina Estabilizada") st.info("Módulo en desarrollo. Próximamente podrás cargar TVR, sales, densidad y apariencia.")

elif opcion == "MEG": st.subheader("Análisis de MEG") st.info("Módulo en desarrollo. Se podrán ingresar pH, concentración y temperatura.")

elif opcion == "Agua Desmineralizada": st.subheader("Análisis de Agua Desmineralizada") st.info("Módulo en desarrollo. Incluirá pH, conductividad, cloruros y otros parámetros.")

