"""
Vista del Dashboard General del comité
ACTUALIZADO: Dashboard mejorado con análisis profundo y corrección de Congos por Ficha
"""
import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from .utils import estado_patrimonial
from src.config import config

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return np.array([int(hex_color[i:i+2], 16) for i in (0, 2, 4)])

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb.astype(int))

def color_gradiente(valor, min_val=0, max_val=2):
    """
    Gradiente continuo tipo Altair
    """
    # Colores ancla (puedes cambiarlos)
    colores = [
        '#DA0024',  # rojo
        '#FFCA00',  # amarillo
        '#1a9850'   # verde fuerte
    ]

    # Normalizar valor
    t = np.clip((valor - min_val) / (max_val - min_val), 0, 1)

    # Posición en la escala
    idx = t * (len(colores) - 1)
    i = int(np.floor(idx))
    frac = idx - i

    if i >= len(colores) - 1:
        return colores[-1]

    c1 = hex_to_rgb(colores[i])
    c2 = hex_to_rgb(colores[i + 1])

    rgb = c1 + frac * (c2 - c1)
    return rgb_to_hex(rgb)



def mostrar_dashboard(df_eval: pd.DataFrame):
    """Dashboard general con KPIs y gráficos principales mejorados"""

    
    st.header("📊 Dashboard General")
   
    
    if df_eval.empty:
        st.warning("⚠️ No hay evaluaciones registradas todavía")
        st.info("Las métricas aparecerán aquí una vez que los curadores comiencen a evaluar grupos")
        return
    
    # Verificar que existe la columna 'ficha' o 'ficha_grupo'
    if 'ficha' not in df_eval.columns and 'ficha_grupo' in df_eval.columns:
        df_eval['ficha'] = df_eval['ficha_grupo']
    
    # Calcular promedios por grupo (promedio de TODOS los aspectos evaluados)
    # Usar 'ficha' en lugar de 'modalidad'
    df_promedios = (df_eval
        .groupby(['codigo_grupo', 'nombre_propuesta', 'ficha'], as_index=False)
        .agg(promedio_final=('resultado', 'mean'))
        .dropna(subset=['promedio_final'])
    )
    
    if df_promedios.empty:
        st.warning("⚠️ No hay evaluaciones completas para calcular promedios")
        return
    
    df_promedios['estado'] = df_promedios['promedio_final'].apply(estado_patrimonial)
    
    # ============================================================
    # KPIs PRINCIPALES - Mejorados
    # ============================================================
    st.markdown("---")
    st.subheader("📈 Métricas Clave")
    
    total_evaluaciones = len(df_eval)
    curadores_activos = df_eval['curador'].nunique()
    grupos_evaluados = df_promedios['codigo_grupo'].nunique()
    promedio_general = df_promedios['promedio_final'].mean()
    desviacion_std = df_promedios['promedio_final'].std()

    color_estado_general = color_gradiente(promedio_general)

    

    
    # Calcular estados
    en_riesgo = (df_promedios['promedio_final'] < config.umbrales.riesgo_max).sum()
    por_mejorar = ((df_promedios['promedio_final'] >= config.umbrales.riesgo_max) & 
                   (df_promedios['promedio_final'] < config.umbrales.mejora_max)).sum()
    fortalecidos = (df_promedios['promedio_final'] >= config.umbrales.mejora_max).sum()
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric(
            "Grupos Evaluados",
            grupos_evaluados,
            help="Total de grupos únicos evaluados"
        )
    
    with col2:
        st.metric(
            "Total Observaciones",
            total_evaluaciones,
            help="Total de observaciones registradas"
        )
    
    with col3:
        st.markdown(f"""<p style="font-size: 15px; font-type:normal; margin-bottom: 0px;">
                    Estado Patrimonial General</p>
            <div style="
                width: 40px;
                margin-top: 5px;
                height: 40px;
                background-color: {color_estado_general};
                border-radius: 5px;
            "></div>""", unsafe_allow_html=True)
        
    
    with col4:
        st.metric(
            "🔴 En Riesgo",
            en_riesgo,
            delta=f"{(en_riesgo/grupos_evaluados*100):.1f}%" if grupos_evaluados > 0 else None,
            delta_color="inverse",
            help="Grupos con promedio < 0.8"
        )
    
    with col5:
        st.metric(
            "🟡 Por Mejorar",
            por_mejorar,
            delta=f"{(por_mejorar/grupos_evaluados*100):.1f}%" if grupos_evaluados > 0 else None,
            help="Grupos con promedio entre 0.8 y 1.6"
        )
    
    with col6:
        st.metric(
            "🟢 Fortalecidos",
            fortalecidos,
            delta=f"{(fortalecidos/grupos_evaluados*100):.1f}%" if grupos_evaluados > 0 else None,
            help="Grupos con promedio ≥ 1.6"
        )



    # Estado patrimonial general
    
    

    """
    # ============================================================
    # ANÁLISIS ESTADÍSTICO PROFUNDO
    # ============================================================
    st.markdown("---")
    st.subheader("📊 Análisis Estadístico")
    
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    with col_stat1:
        mediana = df_promedios['promedio_final'].median()
        st.metric("Mediana", f"{mediana:.2f}")
    
    with col_stat2:
        q25 = df_promedios['promedio_final'].quantile(0.25)
        st.metric("Q1 (25%)", f"{q25:.2f}")
    
    with col_stat3:
        q75 = df_promedios['promedio_final'].quantile(0.75)
        st.metric("Q3 (75%)", f"{q75:.2f}")
    
    with col_stat4:
        rango = df_promedios['promedio_final'].max() - df_promedios['promedio_final'].min()
        st.metric("Rango", f"{rango:.2f}")
    
    # Box plot de distribución
    st.markdown("**Distribución de Promedios:**")
    chart_box = alt.Chart(df_promedios).mark_boxplot(extent='min-max').encode(
        y=alt.Y('promedio_final:Q', title='Promedio', scale=alt.Scale(domain=[0, 2])),
        color=alt.value('#1f77b4')
    ).properties(height=150)
    
    st.altair_chart(chart_box, use_container_width=True)
    
    
    
    if curadores_activos > 0:
        evaluaciones_por_curador = total_evaluaciones / curadores_activos
        aspectos_por_grupo = total_evaluaciones / grupos_evaluados if grupos_evaluados > 0 else 0
        st.info(f"📊 **Productividad:** {evaluaciones_por_curador:.1f} observaciones/curador | {aspectos_por_grupo:.1f} aspectos/grupo")
    """
    # ============================================================
    # ANÁLISIS POR FICHA 
    # ============================================================
    st.markdown("---")
    st.subheader("📊 Análisis por Ficha de Evaluación")
    
    if 'ficha' in df_promedios.columns and df_promedios['ficha'].notna().any():
        df_ficha = (df_promedios
            .groupby('ficha', as_index=False)
            .agg(
                promedio=('promedio_final', 'mean'),
                cantidad=('codigo_grupo', 'count'),
                #desviacion=('promedio_final', 'std'),
                #min_promedio=('promedio_final', 'min'),
                #max_promedio=('promedio_final', 'max')
            )
            .sort_values('promedio', ascending=False)
        )
        
        # Gráfico mejorado
        chart_ficha = alt.Chart(df_ficha).mark_bar().encode(
            x=alt.X('promedio:Q', title='Estado', scale=alt.Scale(domain=[0, 2]), axis=alt.Axis(labels=False)),
            y=alt.Y('ficha:N', title='Ficha', sort='-x'),
            color=alt.Color(
                'promedio:Q',
                scale=alt.Scale(
                    domain=[0, config.umbrales.riesgo_max,1, config.umbrales.mejora_max, 2],
                    range=['#DA0024', "#feb98b", '#FFCA00', '#b3ef8b', '#00AD1B']
                ),
                legend=None
            ),
            tooltip=[
                'ficha',
                # alt.Tooltip('promedio:Q', format='.2f', title='Promedio'),
                alt.Tooltip('cantidad:Q', title='Grupos'),
                # alt.Tooltip('desviacion:Q', format='.2f', title='Desv. Est.'),
                # alt.Tooltip('min_promedio:Q', format='.2f', title='Mínimo'),
                # alt.Tooltip('max_promedio:Q', format='.2f', title='Máximo')
            ]
        ).properties(height=max(300, len(df_ficha) * 40))
        
        st.altair_chart(chart_ficha, use_container_width=True)
        """"""
        def estilo_estado_ficha(row):
            color = color_gradiente(row['promedio'])
            return [
                f'background-color: {color}'
                if col == 'resultado_emoji' else ''
                for col in row.index
            ]
        df_ficha['resultado_emoji'] = df_ficha['promedio'].apply(lambda x:"")
            
        st.dataframe(
            df_ficha
                .style
                .apply(estilo_estado_ficha, axis=1)
                .format({'promedio': '{:.2f}'}),
            use_container_width=False,
            hide_index=True,
            column_config={
                'promedio': None,
                'ficha': 'Ficha',
                'resultado_emoji': st.column_config.TextColumn('Estado'),
                'cantidad': st.column_config.NumberColumn('Grupos', format='%d'),
                
            }
        )
        """
        # Tabla detallada con más métricas
        st.dataframe(
            df_ficha.style.format({
                'promedio': '{:.2f}',
                #'desviacion': '{:.2f}',
                #'min_promedio': '{:.2f}',
                #'max_promedio': '{:.2f}'
            }),
            use_container_width=True,
            hide_index=True,
            column_config={
                'ficha': 'Ficha',
                'promedio': st.column_config.NumberColumn('Promedio', format='%.2f'),
                'cantidad': st.column_config.NumberColumn('Grupos', format='%d'),
               # 'desviacion': st.column_config.NumberColumn('Desv. Est.', format='%.2f'),
               # 'min_promedio': st.column_config.NumberColumn('Mínimo', format='%.2f'),
               # 'max_promedio': st.column_config.NumberColumn('Máximo', format='%.2f')
            }
        )
        """
    else:
        st.warning("⚠️ No hay información de fichas disponible en los datos")
    
    # ============================================================
    # DISTRIBUCIÓN DE ESTADOS PATRIMONIALES
    # ============================================================
    st.markdown("---")
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
    estado_counts['porcentaje'] = (estado_counts['cantidad'] / estado_counts['cantidad'].sum() * 100).round(1)
    
    col_chart, col_table = st.columns([2, 1])
    
    with col_chart:
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
            tooltip=['estado_nombre', 'cantidad', alt.Tooltip('porcentaje:Q', format='.1f', title='%')]
        ).properties(height=300)
        
        st.altair_chart(chart_estados, use_container_width=True)
    
    with col_table:
        st.dataframe(
            estado_counts[['estado_nombre', 'cantidad', 'porcentaje']],
            use_container_width=True,
            hide_index=True,
            column_config={
                'estado_nombre': 'Estado',
                'cantidad': st.column_config.NumberColumn('Cantidad', format='%d'),
                'porcentaje': st.column_config.NumberColumn('%', format='%.1f')
            }
        )

    # ============================================================
    # ENTREGA DE CONGOS DE ORO (CORREGIDO - POR FICHA)
    # ============================================================
    st.markdown("---")
    st.subheader("🏆 Entrega de Congos de Oro")
    st.caption("Los Congos de Oro se asignan al 25% superior de cada **Ficha** (no por modalidad)")
    
    if df_promedios.empty:
        st.info("No hay datos suficientes para calcular congos de oro")
        return
    
    # Verificar que existe la columna 'ficha'
    if 'ficha' not in df_promedios.columns or df_promedios['ficha'].isna().all():
        st.warning("⚠️ No hay información de fichas disponible. Los grupos deben tener fichas asignadas.")
        return
    
    fichas_disponibles = sorted(df_promedios['ficha'].dropna().unique())
    
    if not fichas_disponibles:
        st.warning("⚠️ No hay fichas disponibles para calcular congos")
        return
    
    # Selector de ficha
    seleccion_ficha = st.selectbox(
        "Seleccionar Ficha:",
        fichas_disponibles,
        help="Seleccione la ficha para ver los grupos candidatos a Congos de Oro"
    )
    
    df_filtrado = df_promedios[df_promedios['ficha'] == seleccion_ficha].copy()
    cantidad_ficha = len(df_filtrado)
    
    import math
    cantidad_congos = max(1, int(math.ceil(cantidad_ficha * 0.25)))  # Mínimo 1 congo
    
    if cantidad_ficha == 0:
        st.warning(f"⚠️ No hay grupos evaluados con la ficha '{seleccion_ficha}'")
    else:
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            st.metric("Grupos en Ficha", cantidad_ficha)
        
        with col_info2:
            st.metric("Congos de Oro (25%)", cantidad_congos)
        
        with col_info3:
            promedio_ficha = df_filtrado['promedio_final'].mean()
            color_estdo_ficha = color_gradiente(promedio_ficha)
            #st.metric("Promedio de Ficha", f"{promedio_ficha:.2f}")
            st.markdown(f"""<p style="font-size: 15px; font-type:normal; margin-bottom: 0px;">
                                Estado Patrimonial General</p>
                        <div style="
                            width: 40px;
                            margin-top: 5px;
                            height: 40px;
                            background-color: {color_estdo_ficha};
                            border-radius: 5px;
                        "></div>""", unsafe_allow_html=True)
            
        
        if cantidad_congos <= 0:
            st.info("No hay congos asignables para esta ficha (cantidad insuficiente).")
        else:
            # Obtener top grupos
            top_ficha = df_filtrado.nlargest(cantidad_congos, 'promedio_final')[
                ['nombre_propuesta', 'codigo_grupo', 'promedio_final', 'estado']
            ].copy()
            
            # Agregar ranking
            top_ficha.insert(0, 'Ranking', range(1, len(top_ficha) + 1))
            
            st.success(f"🏆 ***{len(top_ficha)} grupos candidatos a Congos de Oro para la ficha*** **{seleccion_ficha}**")
            
            # Gráfico de barras de los candidatos
            chart_congos = alt.Chart(top_ficha).mark_bar().encode(
                x=alt.X('promedio_final:Q', title='Promedio', scale=alt.Scale(domain=[0, 2])),
                y=alt.Y('nombre_propuesta:N', title='Grupo', sort='-x'),
                color=alt.Color(
                    'promedio_final:Q',
                    scale=alt.Scale(
                        domain=[0, config.umbrales.riesgo_max, config.umbrales.mejora_max, 2],
                        range=['#d73027', '#fee08b', '#b3ef8b', '#1a9850']
                    ),
                    legend=None
                ),
                tooltip=[
                    'nombre_propuesta',
                    'codigo_grupo',
                    alt.Tooltip('promedio_final:Q', format='.2f', title='Promedio'),
                    'estado'
                ]
            ).properties(height=max(200, len(top_ficha) * 30))
            
            st.altair_chart(chart_congos, use_container_width=True)
            
            # Tabla detallada
            st.dataframe(
                top_ficha.style.format({'promedio_final': '{:.2f}'}),
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Ranking': st.column_config.NumberColumn('Ranking', format='%d'),
                    'nombre_propuesta': 'Grupo',
                    'codigo_grupo': 'Código',
                    'promedio_final': None,
                    #'promedio_final': st.column_config.NumberColumn('Promedio', format='%.2f'),
                    'estado': 'Estado'
                }
            )
            
            # Información adicional
            if len(top_ficha) > 0:
                promedio_minimo = top_ficha['promedio_final'].min()
                promedio_maximo = top_ficha['promedio_final'].max()
                #st.caption(f"📊 Rango de promedios: {promedio_minimo:.2f} - {promedio_maximo:.2f}")
    
    # ============================================================
    # GRUPOS QUE REQUIEREN ATENCIÓN
    # ============================================================
    st.markdown("---")
    st.subheader("⚠️ Grupos que Requieren Atención")
    
    grupos_riesgo = df_promedios[df_promedios['promedio_final'] < config.umbrales.riesgo_max].nsmallest(
        10, 'promedio_final'
    )[['nombre_propuesta', 'codigo_grupo', 'ficha', 'promedio_final', 'estado']]
    
    if len(grupos_riesgo) > 0:
        st.warning(f"**{len(grupos_riesgo)} grupos con mayor necesidad de atención:**")
        st.dataframe(
            grupos_riesgo.style.format({'promedio_final': '{:.2f}'}),
            use_container_width=True,
            hide_index=True,
            column_config={
                'ficha': 'Ficha',
                'nombre_propuesta': 'Grupo',
                'codigo_grupo': 'Código',
                'promedio_final': None,
                'estado': 'Estado'
            }
        )
    else:
        st.success("✅ No hay grupos en riesgo crítico")
    
    # ============================================================
    # TOP GRUPOS POR FICHA
    # ============================================================
    st.markdown("---")
    st.subheader("🌟 Top 5 Grupos por Ficha")
    
    if 'ficha' in df_promedios.columns:
        top_por_ficha = (df_promedios
            .groupby('ficha', group_keys=False)
            .apply(lambda x: x.nlargest(5, 'promedio_final'))
            .reset_index(drop=True)
        )
        
        if len(top_por_ficha) > 0:
            st.dataframe(
                top_por_ficha[['ficha', 'nombre_propuesta', 'codigo_grupo', 'promedio_final', 'estado']]
                    .style.format({'promedio_final': '{:.2f}'}),
                use_container_width=True,
                hide_index=True,
                column_config={
                'ficha': 'Ficha',
                'nombre_propuesta': 'Grupo',
                'codigo_grupo': 'Código',
                'promedio_final': None,
                'estado': 'Estado'
                
                }
            )
        else:
            st.info("No hay datos suficientes para mostrar top grupos")
