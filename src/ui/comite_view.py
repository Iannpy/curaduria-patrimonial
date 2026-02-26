"""
Vista de la interfaz para el Comité
ACTUALIZADO: Análisis corregido para evaluaciones por aspecto
"""
import streamlit as st
import pandas as pd
import altair as alt
import logging
from io import BytesIO
from src.config import config
from src.database.models import EvaluacionModel, AspectoModel, FichaModel, FichaDimensionModel
from src.auth.authentication import crear_boton_logout
from streamlit_option_menu import option_menu
from .comite.congos_oro_view import mostrar_congos_oro
from .comite.utils import estado_patrimonial, estado_patrimonial_texto
from .comite.exports import generar_pdf_grupo, crear_backup_zip
from .comite.dashboard import mostrar_dashboard, color_gradiente, barra_gradiente, cuadrado_color_estado

logger = logging.getLogger(__name__)

import numpy as np




def mostrar_informe_grupo(df_eval: pd.DataFrame, codigo_grupo: str):
    """Muestra un informe detallado de un grupo específico"""

    # Buscar grupo en evaluaciones
    df_grupo = df_eval[df_eval['codigo_grupo'].str.upper() == codigo_grupo.upper()]

    if df_grupo.empty:
        st.error(f"❌ Grupo '{codigo_grupo}' no encontrado en las evaluaciones")
        # Mostrar sugerencias
        st.info("💡 Grupos disponibles:")
        grupos_disponibles = df_eval['codigo_grupo'].unique()
        st.dataframe(pd.DataFrame({'Códigos disponibles': sorted(grupos_disponibles)}), use_container_width=False)
        return

    # Información básica del grupo
    grupo_info = df_grupo.iloc[0]
    st.success(f"✅ Informe encontrado para: **{grupo_info['nombre_propuesta']}** ({codigo_grupo})")

    # Métricas principales del grupo
    col1, col2, col3, col4 = st.columns(4)
   
    promedio_grupo = df_grupo['resultado'].mean()
    color = color_gradiente(promedio_grupo)
    evaluaciones_total = len(df_grupo)
    curadores_unicos = df_grupo['curador'].nunique()
    aspectos_evaluados = df_grupo['aspecto'].nunique()

    with col1:
        st.markdown(f"{cuadrado_color_estado(promedio_grupo)}", unsafe_allow_html=True)
    with col2:
        st.metric("Total Evaluaciones", evaluaciones_total)
    with col3:
        st.metric("Curadores", curadores_unicos)
    with col4:
        st.metric("Aspectos Evaluados", aspectos_evaluados)



    st.markdown("---")
    st.markdown(barra_gradiente(promedio_grupo), unsafe_allow_html=True)

    # Desempeño por dimensión
    st.subheader("📊 Desempeño por Dimensión")


    df_dim_grupo = (df_grupo
        .groupby('dimension', as_index=False)
        .agg(
            promedio=('resultado', 'mean'),
            evaluaciones=('resultado', 'count'),
            curadores=('curador', 'nunique')
        )
        .sort_values('promedio', ascending=False)
    )
    color_gradiente

    def estilo_estado_dimension(row):
        color = color_gradiente(row['promedio'])
        return [
            f'background-color: {color}'
            if col == 'resultado_emoji' else ''
            for col in row.index
        ]
    df_dim_grupo['resultado_emoji'] = df_dim_grupo['promedio'].apply(lambda x: '')
    st.dataframe(
        df_dim_grupo
            .style
            .apply(estilo_estado_dimension, axis=1)
            .format({'promedio': '{:.2f}'}),
        use_container_width=False,
        hide_index=True,
        column_config={
            'promedio': None,
            'evaluaciones': None,
            'curadores': None,
            'resultado_emoji': st.column_config.TextColumn('Estado'),
        }
    )
    

    # Desempeño por aspecto
    st.subheader("✅ Detalle por Aspecto")


    df_aspecto_grupo = (df_grupo
        .groupby(['dimension', 'aspecto'], as_index=False)
        .agg(
            promedio=('resultado', 'mean'),
            evaluaciones=('resultado', 'count')
        )
        .sort_values(['dimension', 'promedio'], ascending=[True, False])
    )
    def estilo_estado_aspecto(row):
        color = color_gradiente(row['promedio'])
        return [
            f'background-color: {color}; text-align: center; font-weight: bold'
            if col == 'resultado_emoji' else ''
            for col in row.index
        ]

    # Mapear resultados a emojis
    df_aspecto_grupo['resultado_emoji'] = df_aspecto_grupo['promedio'].apply(lambda x: '')

    st.dataframe(
        df_aspecto_grupo[['dimension', 'aspecto', 'resultado_emoji', 'evaluaciones', 'promedio']]
            .style
            .apply(estilo_estado_aspecto, axis=1)
            .format({'promedio': '{:.2f}'}),
        use_container_width=True,
        hide_index=True,
        column_config={
            'promedio': None,
            'evaluaciones': None,
            'resultado_emoji': st.column_config.TextColumn('Estado'),
        }
    )
    
    """
    # Evaluaciones detalladas
    st.subheader("📋 Evaluaciones Detalladas")

    df_detalle = df_grupo[[
        'curador',
        'dimension',
        'aspecto',
        'observacion',
        'fecha_registro'
    ]].copy()

    # Emoji basado en resultado (se calcula antes)
    df_detalle['resultado_emoji'] = df_grupo['resultado'].map({2: '🟢', 1: '🟡', 0: '🔴'})

    st.dataframe(
        df_detalle.sort_values('fecha_registro', ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            'resultado_emoji': st.column_config.TextColumn('Estado'),
            'fecha_registro': st.column_config.DatetimeColumn('Fecha', format='DD/MM/YYYY HH:mm')
        }
    )
    """
    
    # Observaciones cualitativas
    st.subheader("💬 Observaciones Cualitativas")

    # Obtener UNA observación por curador
    observaciones_unicas = (df_grupo[df_grupo['observacion'].notna() & (df_grupo['observacion'].str.strip() != "")]
        .drop_duplicates(subset=['curador'], keep='first')
        .sort_values('fecha_registro', ascending=False)
    )
    
    if not observaciones_unicas.empty:
        for _, row in observaciones_unicas.iterrows():
            st.markdown(f"* {row['observacion']}")
    else:
        st.info("No hay observaciones cualitativas registradas para este grupo")

# Botón de exportación PDF
    st.markdown("---")
    col_exp1, col_exp2, col_exp3 = st.columns([1, 2, 1])

    with col_exp2:
        try:
            pdf_buffer = generar_pdf_grupo(df_grupo)
            st.download_button(
                label="📄 Descargar Informe PDF",
                data=pdf_buffer,
                file_name=f"Informe_{codigo_grupo}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error al generar PDF: {str(e)}")
            
def mostrar_vista_comite():
    """Renderiza la vista completa del comité"""
    # Cargar evaluaciones
    df_eval = EvaluacionModel.obtener_todas_dataframe()
    
    # Sidebar - Navegación
    with st.sidebar:
        icons = [
        "speedometer2",        # Dashboard General
        "trophy",             # Congos de Oro
        "clipboard-data",      # Evaluaciones Detalladas
        "people",              # Análisis por Grupos
        "file-earmark-bar-graph",  # Análisis por Ficha
        "diagram-3",           # Análisis por Dimensión
        "bounding-box",        # Análisis por Aspecto
        "person-check",        # Análisis por Curador
        "folder2-open",        # Gestión de Fichas
        "shield-lock",         # Administración
        "people-fill"          # Gestión de Usuarios
        ]
        pagina = option_menu(
            "Menú de Análisis",
            [
                "Dashboard General",
                "Gala de premios",
                "Evaluaciones Detalladas",
                "Análisis por Grupos",
                
            ],
            icons=icons,
            menu_icon="clipboard-data",
            default_index=0,
            orientation="vertical",
        )
        
        crear_boton_logout()
    
    
    
    # Routing según página seleccionada
    if pagina == "Dashboard General":
        mostrar_dashboard(df_eval)
    elif pagina == "Gala de premios":
        mostrar_congos_oro()
    elif pagina == "Evaluaciones Detalladas":
        mostrar_evaluaciones_detalladas(df_eval)
    elif pagina == "Análisis por Grupos":
        mostrar_analisis_grupos(df_eval)
 



def mostrar_evaluaciones_detalladas(df_eval: pd.DataFrame) -> None:
    """Tabla detallada de todas las evaluaciones"""
    
    st.header("📋 Evaluaciones Detalladas")
    st.caption("Vista completa de todas las evaluaciones por aspecto")
    
    # Opciones de visualización
    col_opt1, col_opt2, col_opt3 = st.columns([3, 1, 1])
    
    with col_opt1:
        buscar = st.text_input(
            "🔍 Buscar", 
            placeholder="Buscar por grupo, curador, dimensión o aspecto..."
        )
    
    with col_opt2:
        
        filtro_resultado = st.selectbox(
            "Filtrar por resultado",
            ["Todos", "🟢 Fortaleza (2)", "🟡 Oportunidad (1)", "🔴 Riesgo (0)"]
        )
    
    with col_opt3:
        st.markdown("<br>", unsafe_allow_html=True)
        # Placeholder for export button, will be added after filtering
    
    # Filtrar
    df_mostrar = df_eval.copy()
    
    if buscar:
        df_mostrar = df_mostrar[
            df_mostrar['nombre_propuesta'].str.contains(buscar, case=False, na=False) |
            df_mostrar['curador'].str.contains(buscar, case=False, na=False) |
            df_mostrar['dimension'].str.contains(buscar, case=False, na=False) |
            df_mostrar['aspecto'].str.contains(buscar, case=False, na=False) |
            df_mostrar['ficha_grupo'].astype(str).str.contains(buscar, case=False, na=False)
        ]
    
    if filtro_resultado != "Todos":
        resultado_map = {
            "🟢 Fortaleza (2)": 2,
            "🟡 Oportunidad (1)": 1,
            "🔴 Riesgo (0)": 0
        }
        df_mostrar = df_mostrar[df_mostrar['resultado'] == resultado_map[filtro_resultado]]
    
    # Mapear resultados a emojis
    df_mostrar['resultado_emoji'] = df_mostrar['resultado'].map({
        2: '🟢',
        1: '🟡',
        0: '🔴'
    })
    
    # Mostrar tabla
    st.dataframe(
        df_mostrar[[
            'curador', 'codigo_grupo', 'nombre_propuesta', 
            'modalidad', 'dimension', 'aspecto', 'resultado_emoji', 
            'observacion', 'fecha_registro', 'resultado'
        ]].sort_values('fecha_registro', ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            'resultado_emoji': st.column_config.TextColumn('Resultado')
        }
    )
    
    st.caption(f"Total de registros: {len(df_mostrar)}")

    # Exportar datos (después de filtrar)
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        # Exportar a Excel
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_mostrar.to_excel(writer, sheet_name='Evaluaciones', index=False)
        
        st.download_button(
            label="📥 Exportar Excel",
            data=excel_buffer.getvalue(),
            file_name=f"evaluaciones_detalladas_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )

    with col_exp2:
        # Exportar a CSV
        csv_data = df_mostrar.to_csv(index=False)
        st.download_button(
            label="📥 Exportar CSV",
            data=csv_data,
            file_name=f"evaluaciones_detalladas_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            type="secondary",
            use_container_width=True
        )


def mostrar_analisis_grupos(df_eval: pd.DataFrame):
    """Análisis consolidado por grupos - Refactorizado con tabs"""

    st.header("🎭 Análisis por Grupos")
    st.caption("Vista consolidada del desempeño de cada grupo")

    if df_eval.empty:
        st.warning("⚠️ No hay evaluaciones para analizar por grupos")
        return

    # Crear tabs
    tab1, tab2 = st.tabs(["🔍 Búsqueda Individual", "📊 Análisis con Filtros"])

    # ============================================================
    # TAB 1: BÚSQUEDA INDIVIDUAL DE GRUPO
    # ============================================================
    with tab1:
        st.subheader("🔍 Búsqueda de Grupo por Código")
        st.caption("Ingrese el código del grupo para ver su informe detallado")
        
        col_busq1, col_busq2 = st.columns([3, 1])
        
        with col_busq1:
            id_busqueda = st.text_input(
                "Ingrese el código del grupo:",
                placeholder="Ej: P123",
                help="Ingrese el código tal como aparece en la lista",
                key="busqueda_grupo_tab1"
            )
        
        with col_busq2:
            st.markdown("<br>", unsafe_allow_html=True)
            buscar_btn = st.button("🔍 Buscar", type="primary", use_container_width=True, key="btn_buscar_tab1")
        
        if buscar_btn and id_busqueda:
            st.rerun()
        
        # Mostrar informe del grupo si se buscó
        if id_busqueda:
            mostrar_informe_grupo(df_eval, id_busqueda)
        else:
            st.info("👆 Ingrese un código de grupo para ver su informe detallado")
            
            # Mostrar lista de grupos disponibles
            with st.expander("📋 Ver grupos disponibles"):
                grupos_disponibles = sorted(df_eval['codigo_grupo'].unique())
                grupos_df = pd.DataFrame({
                    'Código': grupos_disponibles,
                    'Nombre': [df_eval[df_eval['codigo_grupo'] == cod]['nombre_propuesta'].iloc[0] 
                              if not df_eval[df_eval['codigo_grupo'] == cod].empty else 'N/A' 
                              for cod in grupos_disponibles]
                })
                st.dataframe(grupos_df, use_container_width=True, hide_index=True)

    # ============================================================
    # TAB 2: ANÁLISIS CON FILTROS
    # ============================================================
    with tab2:
        st.subheader("📊 Análisis de Grupos con Filtros")
        st.caption("Filtre y analice grupos por ficha y estado patrimonial")
        
        # Calcular promedios por grupo y dimensión
        df_grupo_dim = (df_eval
            .groupby(['codigo_grupo', 'nombre_propuesta', 'ficha', 'dimension'], as_index=False)
            .agg(promedio_dimension=('resultado', 'mean'))
        )
        
        if df_grupo_dim.empty:
            st.warning("⚠️ No hay datos suficientes para análisis por dimensión")
            return
        
        # Crear tabla pivote
        df_pivot = df_grupo_dim.pivot_table(
            index=['codigo_grupo', 'nombre_propuesta', 'ficha'],
            columns='dimension',
            values='promedio_dimension',
            fill_value=0  # Rellenar NaN con 0 para grupos sin todas las dimensiones
        ).reset_index()
        
        # Calcular promedio final (promedio de todas las dimensiones)
        dim_cols = [c for c in df_pivot.columns if c not in ['codigo_grupo', 'nombre_propuesta', 'ficha']]
        if dim_cols:
            df_pivot['Promedio Final'] = df_pivot[dim_cols].mean(axis=1)
            df_pivot['Estado'] = df_pivot['Promedio Final'].apply(estado_patrimonial)
        else:
            st.warning("⚠️ No se encontraron dimensiones en las evaluaciones")
            return
        
        # Ordenar por promedio
        df_pivot = df_pivot.sort_values('Promedio Final', ascending=False)
        
        # ============================================================
        # FILTROS
        # ============================================================
        st.markdown("---")
        st.subheader("🔽 Filtros de Búsqueda")
        
        col_filt1, col_filt2, col_filt3 = st.columns(3)
        
        with col_filt1:
            fichas_disponibles = ['Todas'] + sorted([f for f in df_pivot['ficha'].unique() if pd.notna(f)])
            ficha_sel = st.selectbox(
                "Filtrar por ficha:",
                fichas_disponibles,
                help="Seleccione una ficha específica o 'Todas' para ver todos"
            )
        
        with col_filt2:
            estados = ['Todos', '🟢 Fortaleza', '🟡 Oportunidad', '🔴 Riesgo']
            estado_sel = st.selectbox(
                "Filtrar por estado:",
                estados,
                help="Seleccione un estado patrimonial específico"
            )
        
        with col_filt3:
            orden_sel = st.selectbox(
                "Ordenar por:",
                ['Promedio (Mayor a Menor)', 'Promedio (Menor a Mayor)', 'Nombre (A-Z)', 'Código (A-Z)'],
                help="Seleccione el criterio de ordenamiento"
            )
        
        # ============================================================
        # OBTENER DIMENSIONES POR FICHA (si se filtra por ficha específica)
        # ============================================================
        dimensiones_ficha = []
        if ficha_sel != 'Todas':
            # Buscar ficha por nombre (el valor en el selectbox es el nombre de la ficha)
            fichas_todas = FichaModel.obtener_todas()
            ficha_obj = None
            
            # Buscar por nombre exacto
            for ficha in fichas_todas:
                if ficha['nombre'] == ficha_sel:
                    ficha_obj = ficha
                    break
            
            if ficha_obj:
                ficha_id = ficha_obj['id']
                # Obtener dimensiones de esta ficha
                dims_ficha = FichaDimensionModel.obtener_dimensiones_de_ficha(ficha_id)
                dimensiones_ficha = [d['dimension_nombre'] for d in dims_ficha]
        
        # Aplicar filtros
        df_filtrado = df_pivot.copy()
        
        if ficha_sel != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['ficha'] == ficha_sel]
            
            # Recalcular promedio final solo con dimensiones de la ficha
            if dimensiones_ficha:
                # Filtrar solo las columnas de dimensiones que pertenecen a esta ficha
                dim_cols_ficha = [col for col in dim_cols if col in dimensiones_ficha]
                if dim_cols_ficha:
                    # Recalcular promedio solo con dimensiones de la ficha
                    # Solo usar columnas que existen en el dataframe
                    dim_cols_ficha_existentes = [col for col in dim_cols_ficha if col in df_filtrado.columns]
                    if dim_cols_ficha_existentes:
                        # Calcular promedio solo con las dimensiones de la ficha
                        df_filtrado['Promedio Final'] = df_filtrado[dim_cols_ficha_existentes].mean(axis=1)
                        # Recalcular estado con el nuevo promedio
                        df_filtrado['Estado'] = df_filtrado['Promedio Final'].apply(estado_patrimonial)
        
        if estado_sel != 'Todos':
            estado_map = {
                '🟢 Fortaleza': config.umbrales.emoji_fortalecimiento,
                '🟡 Oportunidad': config.umbrales.emoji_mejora,
                '🔴 Riesgo': config.umbrales.emoji_riesgo
            }
            df_filtrado = df_filtrado[df_filtrado['Estado'] == estado_map[estado_sel]]
        
        # Aplicar ordenamiento
        if orden_sel == 'Promedio (Mayor a Menor)':
            df_filtrado = df_filtrado.sort_values('Promedio Final', ascending=False)
        elif orden_sel == 'Promedio (Menor a Mayor)':
            df_filtrado = df_filtrado.sort_values('Promedio Final', ascending=True)
        elif orden_sel == 'Nombre (A-Z)':
            df_filtrado = df_filtrado.sort_values('nombre_propuesta', ascending=True)
        elif orden_sel == 'Código (A-Z)':
            df_filtrado = df_filtrado.sort_values('codigo_grupo', ascending=True)
        
        # ============================================================
        # ESTADÍSTICAS DEL FILTRO
        # ============================================================
        st.markdown("---")
        st.subheader("📊 Estadísticas del Filtro Actual")
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            if len(df_filtrado) > 0:
                st.metric("Promedio General", f"{df_filtrado['Promedio Final'].mean():.2f}")
            else:
                st.metric("Promedio General", "N/A")
        
        with col_stat2:
            if len(df_filtrado) > 0:
                st.metric("Mejor Promedio", f"{df_filtrado['Promedio Final'].max():.2f}")
            else:
                st.metric("Mejor Promedio", "N/A")
        
        with col_stat3:
            if len(df_filtrado) > 0:
                st.metric("Peor Promedio", f"{df_filtrado['Promedio Final'].min():.2f}")
            else:
                st.metric("Peor Promedio", "N/A")
        
        with col_stat4:
            st.metric("Grupos Mostrados", len(df_filtrado), delta=f"de {len(df_pivot)} total")
        
        # ============================================================
        # TABLA DE RESULTADOS (con columnas adaptadas)
        # ============================================================
        st.markdown("---")
        st.subheader("📋 Resultados")
        
        if len(df_filtrado) == 0:
            st.warning("⚠️ No hay grupos que coincidan con los filtros seleccionados")
            st.info("💡 Intente ajustar los filtros para ver más resultados")
        else:
            # Determinar qué columnas mostrar
            if ficha_sel == 'Todas':
                # Si es "Todas", mostrar solo: código, grupo, ficha, promedio final y estado
                columnas_mostrar = ['codigo_grupo', 'nombre_propuesta', 'ficha', 'Promedio Final', 'Estado']
                df_mostrar = df_filtrado[columnas_mostrar].copy()
                
                # Configuración de columnas
                column_config = {
                    'codigo_grupo': 'Código',
                    'nombre_propuesta': 'Grupo',
                    'ficha': 'Ficha',
                    'Promedio Final': st.column_config.NumberColumn('Promedio Final', format='%.2f'),
                    'Estado': 'Estado'
                }
                
                # Formato
                formato_dict = {'Promedio Final': '{:.2f}'}
            else:
                # Si se filtra por ficha específica, mostrar dimensiones de esa ficha
                if dimensiones_ficha:
                    # Columnas base + dimensiones de la ficha + promedio final + estado
                    columnas_mostrar = ['codigo_grupo', 'nombre_propuesta', 'ficha'] + dimensiones_ficha + ['Promedio Final', 'Estado']
                    # Filtrar solo las que existen en el dataframe
                    columnas_mostrar = [col for col in columnas_mostrar if col in df_filtrado.columns]
                    df_mostrar = df_filtrado[columnas_mostrar].copy()
                    
                    # Configuración de columnas
                    column_config = {
                        'codigo_grupo': 'Código',
                        'nombre_propuesta': 'Grupo',
                        'ficha': 'Ficha',
                        'Promedio Final': st.column_config.NumberColumn('Promedio Final', format='%.2f'),
                        'Estado': 'Estado'
                    }
                    # Agregar config para dimensiones
                    for dim in dimensiones_ficha:
                        if dim in df_mostrar.columns:
                            column_config[dim] = st.column_config.NumberColumn(dim, format='%.2f')
                    
                    # Formato
                    formato_dict = {col: '{:.2f}' for col in dimensiones_ficha if col in df_mostrar.columns}
                    formato_dict['Promedio Final'] = '{:.2f}'
                else:
                    # Si no se encontraron dimensiones, mostrar solo columnas base
                    columnas_mostrar = ['codigo_grupo', 'nombre_propuesta', 'ficha', 'Promedio Final', 'Estado']
                    df_mostrar = df_filtrado[columnas_mostrar].copy()
                    
                    column_config = {
                        'codigo_grupo': 'Código',
                        'nombre_propuesta': 'Grupo',
                        'ficha': 'Ficha',
                        'Promedio Final': st.column_config.NumberColumn('Promedio Final', format='%.2f'),
                        'Estado': 'Estado'
                    }
                    
                    formato_dict = {'Promedio Final': '{:.2f}'}
            
            # Mostrar tabla con formato mejorado
            st.dataframe(
                df_mostrar.style.format(formato_dict),
                use_container_width=True,
                hide_index=True,
                column_config=column_config
            )
            
            # ============================================================
            # EXPORTACIÓN (usar df_mostrar que tiene las columnas correctas)
            # ============================================================
            st.markdown("---")
            st.subheader("💾 Exportar Datos")
            
            col_exp1, col_exp2 = st.columns(2)
            
            with col_exp1:
                # Exportar a Excel (usar df_mostrar que tiene las columnas filtradas)
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df_mostrar.to_excel(writer, sheet_name='Analisis_Grupos', index=False)
                
                st.download_button(
                    label="📊 Exportar a Excel",
                    data=excel_buffer.getvalue(),
                    file_name=f"analisis_grupos_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )
            
            with col_exp2:
                # Exportar a CSV (usar df_mostrar que tiene las columnas filtradas)
                csv_buffer = df_mostrar.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Exportar a CSV",
                    data=csv_buffer,
                    file_name=f"analisis_grupos_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    type="secondary",
                    use_container_width=True
                )
            
            st.caption(f"📊 Mostrando {len(df_filtrado)} de {len(df_pivot)} grupos totales")
            
            # ============================================================
            # GRÁFICO DE DISTRIBUCIÓN
            # ============================================================
            st.markdown("---")
            st.subheader("📈 Distribución de Promedios")
            
            import altair as alt
            
            chart_dist = alt.Chart(df_filtrado).mark_bar().encode(
                x=alt.X('Promedio Final:Q', title='Promedio Final', bin=alt.Bin(maxbins=20)),
                y=alt.Y('count()', title='Cantidad de Grupos'),
                color=alt.Color(
                    'Promedio Final:Q',
                    scale=alt.Scale(
                        domain=[0, config.umbrales.riesgo_max, config.umbrales.mejora_max, 2],
                        range=['#d73027', '#fee08b', '#b3ef8b', '#1a9850']
                    ),
                    legend=None
                ),
                tooltip=['count()', alt.Tooltip('Promedio Final:Q', format='.2f')]
            ).properties(height=300)
            
            st.altair_chart(chart_dist, use_container_width=True)
