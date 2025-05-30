
import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

st.set_page_config(page_title="Dashboard Bancos Españoles", layout="wide")
st.title("Dashboard - Impacto contable de la Taxonomia de la UE en los bancos del IBEX35")

@st.cache_data
def cargar_datos():
    cotizaciones = pd.read_csv("cotizaciones_diarias_ajustadas_2022_2024 (1).csv", sep=';', decimal=',', parse_dates=['Fecha'])
    cotizaciones.set_index('Fecha', inplace=True)

    datos_financieros = pd.read_csv("datosfinancieros.csv", sep=';', decimal=',')
    emisiones = pd.read_csv("emisiones.csv", sep=';', decimal=',')
    ratings = pd.read_csv("ratings.csv", sep=';', decimal=',')
    riesgos = pd.read_csv("gestionriesgos.csv", sep=';', decimal=',')
    riesgos["Valor"] = riesgos["Valor"].replace("ND", np.nan).str.replace(",", ".").astype(float)
    volatilidad = pd.read_csv("volatilidadmensual.csv", sep=';', decimal=',')
    gar_raw = pd.read_csv("gar.csv", sep=';', decimal=',')

    gar_raw['GAR'] = gar_raw['GAR'].str.replace('%', '').str.replace(',', '.').astype(float)
    gar_raw['Cobertura'] = gar_raw['Cobertura'].str.replace('%', '').str.replace(',', '.').astype(float)
    gar = gar_raw.groupby(['Banco', 'Año']).agg({'GAR': 'mean'}).reset_index()
    gar.rename(columns={'GAR': 'GAR Ponderado'}, inplace=True)

    return cotizaciones, datos_financieros, emisiones, ratings, riesgos, volatilidad, gar, gar_raw

cotizaciones, datos_financieros, emisiones, ratings, riesgos, volatilidad, gar, gar_raw = cargar_datos()

colors_bancos = {
    'Santander': '#ec0000',
    'BBVA': '#003366',
    'CaixaBank': '#00529b',
    'Sabadell': '#00adef',
    'Bankinter': '#ff6600',
    'Unicaja': '#417d3c'
}

st.sidebar.title("📌 Navegación")
seccion = st.sidebar.radio("Selecciona una sección", ["Cotizaciones", "Financieros", "ESG", "Comparativa", "Riesgos"])
banco = st.sidebar.selectbox("Selecciona un banco", cotizaciones.columns)



if seccion == "Cotizaciones":
    st.subheader(f"📈 Cotización diaria de {banco}")
    df_cot = cotizaciones[[banco]].reset_index().rename(columns={banco: "Precio"})
    chart = alt.Chart(df_cot).mark_line(color=colors_bancos.get(banco, "gray")).encode(
        x='Fecha:T', y='Precio:Q'
    ).properties(width=800, height=400)
    st.altair_chart(chart, use_container_width=True)

elif seccion == "Financieros":
    st.subheader(f"📊 Indicadores Financieros de {banco}")
    df_banco = datos_financieros[datos_financieros["Banco"] == banco]

    for indicador in ["ROE", "Beneficio Neto", "Ingresos"]:
        chart = alt.Chart(df_banco).mark_bar(color=colors_bancos.get(banco, "gray")).encode(
            x="Año:O", y=alt.Y(indicador + ":Q"), tooltip=["Año", indicador]
        ).properties(title=f"Evolución de {indicador}", width=700, height=300)
        st.altair_chart(chart, use_container_width=True)

elif seccion == "ESG":
    st.subheader(f"🌱 Indicadores ESG de {banco}")

    # === GAR por tipo ===
    st.markdown("#### GAR por tipo y año (visualización)")

    df_gar_viz = gar_raw[(gar_raw["Banco"] == banco) & (~gar_raw["GAR"].isna())].copy()
    df_gar_viz = df_gar_viz.sort_values(["Tipo de GAR", "Año"])
    tipos_gar = df_gar_viz["Tipo de GAR"].unique()

    for tipo in tipos_gar:
        st.markdown(f"##### {tipo}")
        df_tipo = df_gar_viz[df_gar_viz["Tipo de GAR"] == tipo]
        cols = st.columns(len(df_tipo))

        for idx, (_, row) in enumerate(df_tipo.iterrows()):
            with cols[idx]:
                st.markdown(f"""
                    <div style="text-align:center; padding: 20px 10px;">
                        <h4 style="font-size: 1rem; margin-bottom: 0.3rem;">GAR</h4>
                        <div style="font-size: 50px; font-weight: bold; color: {colors_bancos.get(banco, 'black')}">
                            {row['GAR']:.1f}%
                        </div>
                        <div style="font-size: 16px;">Año: {row['Año']}</div>
                    </div>
                """, unsafe_allow_html=True)

    # === Ratings ESG ===
    st.markdown("#### Ratings ESG")

    proveedores = ratings['Rating'].dropna().unique()
    proveedor = st.selectbox("Selecciona el proveedor de rating ESG", sorted(proveedores))

    df_ratings = ratings[(ratings["Banco"] == banco) & (ratings["Rating"] == proveedor)].copy()

    if df_ratings.empty:
        st.warning("No hay datos disponibles para este banco y proveedor.")
    else:
        df_ratings_sorted = df_ratings.sort_values("Año")
        cols = st.columns(len(df_ratings_sorted))

        for idx, (_, row) in enumerate(df_ratings_sorted.iterrows()):
            with cols[idx]:
                st.markdown(f"""
                    <div style="text-align:center; padding: 20px 10px;">
                        <h3 style="font-size: 1rem; margin-bottom: 0.3rem;">{proveedor} ESG Score</h3>
                        <div style="font-size: 60px; font-weight: bold; color: {colors_bancos.get(banco, 'black')}">
                            {row['Nota']}
                        </div>
                        <div style="font-size: 16px;">Año: {row['Año']}</div>
                    </div>
                """, unsafe_allow_html=True)

    # === Emisiones de GEI ===
    st.markdown("#### Emisiones de Gases de Efecto Invernadero (GEI)")

    df_emisiones_banco = emisiones[emisiones["Banco"] == banco].copy()

    if df_emisiones_banco.empty:
        st.info("No hay datos de emisiones disponibles para este banco.")
    else:
        df_emisiones_banco["Emisión"] = pd.to_numeric(df_emisiones_banco["Emisión"], errors="coerce")
        df_emisiones_banco["Emisión"] = df_emisiones_banco["Emisión"].map("{:,.0f}".format)

        años = sorted(df_emisiones_banco["Año"].unique())
        cols = st.columns(len(años))

        for i, año in enumerate(años):
            df_año = df_emisiones_banco[df_emisiones_banco["Año"] == año][["Tipo de emisión", "Emisión"]].reset_index(drop=True)
            table_html = df_año.to_html(index=False, escape=False)

            styled_html = f"""
                <div style="color: #ffffff; font-size: 14px; text-align: center;">
                    <h4 style="margin-bottom: 10px;"> Año {año}</h4>
                    <div style="display: inline-block; text-align: left; max-width: 300px;">
                    {table_html}
                </div>
            """

            with cols[i]:
                st.markdown(styled_html, unsafe_allow_html=True)

elif seccion == "Comparativa":
    st.subheader("📊 Comparativa entre Bancos")

    st.markdown("### Evolución del GAR Ponderado (2022-2024)")
    chart_gar = alt.Chart(gar).mark_line(point=True).encode(
        x='Año:O',
        y='GAR Ponderado:Q',
        color=alt.Color('Banco:N', scale=alt.Scale(domain=list(colors_bancos.keys()), range=list(colors_bancos.values())))
    ).properties(width=700, height=400)
    st.altair_chart(chart_gar, use_container_width=True)

    st.markdown("### Evolución del ROE (2022-2024)")
    df_roe = datos_financieros.groupby(['Banco', 'Año'])['ROE'].mean().reset_index()
    chart_roe = alt.Chart(df_roe).mark_line(point=True).encode(
        x='Año:O',
        y='ROE:Q',
        color=alt.Color('Banco:N', scale=alt.Scale(domain=list(colors_bancos.keys()), range=list(colors_bancos.values())))
    ).properties(width=700, height=400)
    st.altair_chart(chart_roe, use_container_width=True)

    st.markdown("### Rentabilidad Bursátil anual (2022-2024)")
    cotizaciones_dt = cotizaciones.copy()
    cotizaciones_dt.index = pd.to_datetime(cotizaciones_dt.index)
    rentabilidades = []

    for banco_ in cotizaciones.columns:
        precios = cotizaciones_dt[banco_].resample('Y').last()
        rentabilidad = precios.pct_change().dropna()
        for i, val in enumerate(rentabilidad.values):
            rentabilidades.append({
                'Banco': banco_,
                'Año': 2023 + i,
                'Rentabilidad': val
            })

    rent_df = pd.DataFrame(rentabilidades)
    chart_rent = alt.Chart(rent_df).mark_line(point=True).encode(
        x='Año:O',
        y='Rentabilidad:Q',
        color=alt.Color('Banco:N', scale=alt.Scale(domain=list(colors_bancos.keys()), range=list(colors_bancos.values())))
    ).properties(width=700, height=400)
    st.altair_chart(chart_rent, use_container_width=True)

elif seccion == "Riesgos":
    st.subheader("🧯 Mapa de Calor de Riesgos ESG")

    horizonte = st.selectbox("Selecciona horizonte temporal", ["CP", "MP", "LP"])
    riesgos_filtrado = riesgos[riesgos["Horizonte"] == horizonte]

    st.markdown("#### Riesgos Físicos")
    fisico = riesgos_filtrado[riesgos_filtrado["Riesgo"].str.lower().str.contains("fisico")]
    heatmap_fisico = alt.Chart(fisico).mark_rect().encode(
        x=alt.X("Tipo de riesgo:N", title="Tipo de Riesgo"),
        y=alt.Y("Banco:N", title="Banco"),
        color=alt.Color("Valor:Q", scale=alt.Scale(scheme="blues"), title="Intensidad"),
        tooltip=["Banco", "Tipo de riesgo", "Valor"]
    ).properties(width=700, height=300)
    st.altair_chart(heatmap_fisico, use_container_width=True)

    st.markdown("#### Riesgos de Transición")
    transicion = riesgos_filtrado[riesgos_filtrado["Riesgo"].str.lower().str.contains("transición")]
    heatmap_trans = alt.Chart(transicion).mark_rect().encode(
        x=alt.X("Tipo de riesgo:N", title="Tipo de Riesgo"),
        y=alt.Y("Banco:N", title="Banco"),
        color=alt.Color("Valor:Q", scale=alt.Scale(scheme="orangered"), title="Intensidad"),
        tooltip=["Banco", "Tipo de riesgo", "Valor"]
    ).properties(width=700, height=300)
    st.altair_chart(heatmap_trans, use_container_width=True)
