"""
Vista del Dashboard General del comité
"""

import streamlit as st
import pandas as pd
import altair as alt
from .utils import estado_patrimonial


def mostrar_dashboard(df_eval: pd.DataFrame):
    """Dashboard general con KPIs y gráficos principales"""

    st.header("📊 Dashboard General")
    st.markdown("Resumen Ejecutivo de Evaluaciones Patrimoniales")

    if df_eval.empty:
        st.warning("⚠️ No hay evaluaciones registradas todavía")
        st.info("Las métricas aparecerán aquí una vez que los curadores comiencen a evaluar grupos")
        return

    # Calcular promedios por grupo (promedio de TODOS los aspectos evaluados)
    df_promedios = (df_eval
        .groupby(['codigo_grupo', 'nombre_propuesta', 'modalidad'], as_index=False)
        .agg(promedio_final=('resultado', 'mean'))
        .dropna(subset=['promedio_final'])  # Eliminar filas con promedio NaN
    )

    if df_promedios.empty:
        st.warning("⚠️ No hay evaluaciones completas para calcular promedios")
        return

    df_promedios['estado'] = df_promedios['promedio_final'].apply(estado_patrimonial)

    # KPIs principales
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    total_evaluaciones = len(df_eval)
    curadores_activos = df_eval['curador'].nunique()
    aspectos_evaluados = df_eval['aspecto'].nunique()
    promedio_general = df_promedios['promedio_final'].mean()

    with col1:
        grupos_evaluados = df_promedios['codigo_grupo'].nunique()
        st.markdown(f"""
            <div class="metric-card">
            <div class="dimension-title">Grupos Evaluados</div>
            <div class="metric-value">{grupos_evaluados}</div>
            </div>""",
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(f"""
            <div class="metric-card">
            <div class="dimension-title">Total Evaluaciones</div>
            <div class="metric-value">{total_evaluaciones}</div>
            </div>""",
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(f"""
            <div class="metric-card">
            <div class="dimension-title">Curadores Activos</div>
            <div class="metric-value">{curadores_activos}</div>
            </div>""",
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(f"""
            <div class="metric-card">
            <div class="dimension-title">Promedio General</div>
            <div class="metric-value">{promedio_general:.2f}</div>
            </div>""",
            unsafe_allow_html=True
        )

    with col5:
        from src.config import config
        en_riesgo = (df_promedios['promedio_final'] < config.umbrales.riesgo_max).sum()
        st.markdown(f"""
            <div class="metric-card">
            <div class="dimension-title">🔴 En Riesgo</div>
            <div class="metric-value">{en_riesgo}</div>
            </div>""",
            unsafe_allow_html=True
        )

    with col6:
        fortalecidos = (df_promedios['promedio_final'] >= config.umbrales.mejora_max).sum()
        st.markdown(f"""
            <div class="metric-card">
            <div class="dimension-title">🟢 Fortalecidos</div>
            <div class="metric-value">{fortalecidos}</div>
            </div>""",
            unsafe_allow_html=True
        )

    # Estado de evaluación general
    estado_general = estado_patrimonial(promedio_general)
    st.info(f"**Estado Patrimonial General:** {estado_general}")

    # Insights y recomendaciones
    st.markdown("---")
    st.subheader("💡 Insights y Recomendaciones")

    col_ins1, col_ins2 = st.columns(2)

    with col_ins1:
        if en_riesgo > 0:
            porcentaje_riesgo = (en_riesgo / grupos_evaluados) * 100
            st.warning(f"⚠️ **{en_riesgo} grupos en riesgo** ({porcentaje_riesgo:.1f}%) requieren atención inmediata")
            st.markdown("**Recomendaciones:**")
            st.markdown("- Revisar evaluaciones detalladas")
            st.markdown("- Identificar fortalezas y debilidades")
            st.markdown("- Planificar intervenciones específicas")

    with col_ins2:
        if fortalecidos > 0:
            porcentaje_fort = (fortalecidos / grupos_evaluados) * 100
            st.success(f"✅ **{fortalecidos} grupos fortalecidos** ({porcentaje_fort:.1f}%) son modelos a seguir")
            st.markdown("**Acciones:**")
            st.markdown("- Documentar buenas prácticas")
            st.markdown("- Compartir conocimientos")
            st.markdown("- Reconocer logros")

    if curadores_activos > 0:
        evaluaciones_por_curador = total_evaluaciones / curadores_activos
        st.info(f"📊 **Productividad:** {evaluaciones_por_curador:.1f} evaluaciones por curador activo")

    st.markdown("---")

    # Gráfico: Promedio por Modalidad
    st.subheader("📊 Promedio por Modalidad")

    df_modalidad = (df_promedios
        .groupby('modalidad', as_index=False)
        .agg(
            promedio=('promedio_final', 'mean'),
            cantidad=('codigo_grupo', 'count')
        )
        .sort_values('promedio', ascending=False)
    )

    import altair as alt

    chart_modalidad = alt.Chart(df_modalidad).mark_bar().encode(
        x=alt.X('promedio:Q', title='Promedio', scale=alt.Scale(domain=[0, 2])),
        y=alt.Y('modalidad:N', title='Modalidad', sort='-x'),
        color=alt.Color(
            'promedio:Q',
            scale=alt.Scale(
                domain=[0, 0.8, 1, 1.79, 2],
                range=['#d73027', "#febf8b", "#fefc8b", "#b3ef8b", '#1a9850']
            ),
            legend=None
        ),
        tooltip=[
            'modalidad',
            alt.Tooltip('promedio:Q', format='.2f', title='Promedio'),
            alt.Tooltip('cantidad:Q', title='Grupos')
        ]
    ).properties(height=250)

    st.altair_chart(chart_modalidad, use_container_width=True)

    # Mostrar tabla de modalidades
    st.dataframe(
        df_modalidad.style.format({'promedio': '{:.2f}'}),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # Distribución de Estados
    st.subheader("📈 Distribución de Estados Patrimoniales")

    estado_counts = df_promedios['estado'].value_counts().reset_index()
    estado_counts.columns = ['estado', 'cantidad']

    # Mapear emojis a nombres
    estado_map = {
        config.umbrales.emoji_riesgo: '🔴 Riesgo',
        config.umbrales.emoji_mejora: '🟡 Oportunidad',
        config.umbrales.emoji_fortalecimiento: '🟢 Fortaleza'
    }
    estado_counts['estado_nombre'] = estado_counts['estado'].map(estado_map)

    chart_estados = alt.Chart(estado_counts).mark_arc(innerRadius=50).encode(
        theta=alt.Theta('cantidad:Q'),
        color=alt.Color(
            'estado_nombre:N',
            scale=alt.Scale(
                domain=['🔴 Riesgo', '🟡 Oportunidad', '🟢 Fortaleza'],
                range=['#d73027', '#fee08b', '#1a9850']
            ),
            legend=alt.Legend(title="Estado")
        ),
        tooltip=['estado_nombre', 'cantidad']
    ).properties(height=300)

    st.altair_chart(chart_estados, use_container_width=True)

    st.markdown("---")

    # Congos de Oro
    st.subheader("🏆 Entrega de Congos de Oro")

    if df_promedios.empty:
        st.info("No hay datos suficientes para calcular congos de oro")
        return

    seleccion_modalidad = st.selectbox(
        "Seleccionar Modalidad:",
        sorted(df_promedios['modalidad'].dropna().unique())
    )

    df_filtrado = df_promedios[df_promedios['modalidad'] == seleccion_modalidad]
    cantidad_modalidad = df_filtrado.shape[0]

    import math
    cantidad_congos = int(math.ceil(cantidad_modalidad * 0.15))

    if cantidad_modalidad == 0:
        st.warning(f"⚠️ No hay grupos en la modalidad '{seleccion_modalidad}'")
    else:
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.metric("Grupos en modalidad", cantidad_modalidad)
        with col_info2:
            st.metric("Congos de Oro (15%)", cantidad_congos)

        if cantidad_congos <= 0:
            st.info("No hay congos asignables para esta modalidad (cantidad insuficiente).")
        else:
            top_modalidad = df_filtrado.nlargest(cantidad_congos, 'promedio_final')[
                ['nombre_propuesta', 'codigo_grupo', 'promedio_final', 'estado']
            ]

            st.dataframe(
                top_modalidad.style.format({'promedio_final': '{:.2f}'}),
                use_container_width=True,
                hide_index=True
            )

    # Grupos que requieren atención
    with st.expander("⚠️ Ver grupos que requieren atención"):
        st.subheader("Grupos en Riesgo Patrimonial")
        grupos_riesgo = df_promedios[
            df_promedios['promedio_final'] < config.umbrales.riesgo_max
        ].sort_values('promedio_final')[
            ['nombre_propuesta', 'codigo_grupo', 'modalidad', 'promedio_final', 'estado']
        ]

        if grupos_riesgo.empty:
            st.success("✅ No hay grupos en riesgo patrimonial")
        else:
            st.dataframe(
                grupos_riesgo.style.format({'promedio_final': '{:.2f}'}),
                use_container_width=True,
                hide_index=True
            )