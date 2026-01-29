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
from .comite.utils import estado_patrimonial, estado_patrimonial_texto
from .comite.exports import generar_pdf_grupo, crear_backup_zip
from .comite.dashboard import mostrar_dashboard, color_gradiente

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
        st.markdown(f"""**Estado Patrimonial**:<div style="
                width: 40px;
                height: 40px;
                background-color: {color};
                border-radius: 6px
            "></div>""", unsafe_allow_html=True)
    with col2:
        st.metric("Total Evaluaciones", evaluaciones_total)
    with col3:
        st.metric("Curadores", curadores_unicos)
    with col4:
        st.metric("Aspectos Evaluados", aspectos_evaluados)



    st.markdown("---")

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
        pagina = option_menu(
            "📂 Menú de Análisis",
            [
                "Dashboard General",
                "Evaluaciones Detalladas",
                "Análisis por Grupos",
                "Análisis por Ficha",
                "Análisis por Dimensión",
                "Análisis por Aspecto",
                "Análisis por Curador",
                "Gestión de Fichas",
                "Administración",
                "Gestión de Usuarios"
            ],
            icons=[
                "bar-chart-fill",
                "table",
                "people-fill",
                "layers-fill",
                "layers-fill",
                "layers-fill",
                "check2-square",
                "person-badge-fill",
                "gear-fill",
                "people"
            ],
            menu_icon="clipboard-data-fill",
            default_index=0,
            orientation="vertical",
        )
        
        crear_boton_logout()
    
    paginas_sin_evaluaciones = ["Administración", "Gestión de Usuarios","Gestión de Fichas"]
    
    # Si la página requiere evaluaciones y no hay, mostrar aviso
    if pagina not in paginas_sin_evaluaciones and df_eval.empty:
        st.warning("⚠️ No hay evaluaciones registradas todavía")
        st.info("Las evaluaciones aparecerán aquí una vez que los curadores comiencen a registrarlas")
        st.markdown("---")
        st.markdown("💡 **Mientras tanto, puedes:**")
        st.markdown("- Ir a **⚙️ Administración** para sincronizar grupos")
        st.markdown("- Ir a **👥 Gestión de Usuarios** para crear curadores")
        return
    
    # Routing según página seleccionada
    if pagina == "Dashboard General":
        mostrar_dashboard(df_eval)
    elif pagina == "Evaluaciones Detalladas":
        mostrar_evaluaciones_detalladas(df_eval)
    elif pagina == "Análisis por Grupos":
        mostrar_analisis_grupos(df_eval)
    elif pagina == "Análisis por Dimensión":
        mostrar_analisis_dimensiones(df_eval)
    elif pagina == "Análisis por Aspecto":
        mostrar_analisis_aspectos(df_eval)
    elif pagina == "Análisis por Curador":
        mostrar_analisis_curadores(df_eval)
    elif pagina == "Administración":
        mostrar_panel_admin()
    elif pagina == "Gestión de Usuarios":
        mostrar_gestion_usuarios(df_eval)
    elif pagina == "Análisis por Ficha":
        mostrar_analisis_por_ficha(df_eval)
    elif pagina == "Gestión de Fichas":
        from src.ui.admin_fichas_view import mostrar_gestion_fichas
        mostrar_gestion_fichas()



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
        st.markdown("<br>", unsafe_allow_html=True)
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
            'observacion', 'fecha_registro'
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


def mostrar_analisis_dimensiones(df_eval: pd.DataFrame):
    """Análisis por dimensiones patrimoniales - Mejorado"""

    st.header("📊 Análisis por Dimensión")
    st.caption("Desempeño consolidado en cada dimensión patrimonial")

    if df_eval.empty:
        st.warning("⚠️ No hay evaluaciones para analizar por dimensión")
        return

    # Promedio por dimensión con más métricas
    df_dim = (df_eval
        .groupby('dimension', as_index=False)
        .agg(
            promedio=('resultado', 'mean'),
            mediana=('resultado', 'median'),
            desviacion=('resultado', 'std'),
            evaluaciones=('resultado', 'count'),
            grupos=('codigo_grupo', 'nunique'),
            fortalezas=('resultado', lambda x: (x == 2).sum()),
            oportunidades=('resultado', lambda x: (x == 1).sum()),
            riesgos=('resultado', lambda x: (x == 0).sum())
        )
        .sort_values('promedio', ascending=False)
    )
    
    # KPIs generales
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    with col_kpi1:
        st.metric("Total Dimensiones", len(df_dim))
    
    with col_kpi2:
        mejor_dim = df_dim.nlargest(1, 'promedio')
        if not mejor_dim.empty:
            st.metric("Mejor Dimensión", mejor_dim.iloc[0]['dimension'], f"{mejor_dim.iloc[0]['promedio']:.2f}")
    
    with col_kpi3:
        promedio_general_dim = df_dim['promedio'].mean()
        st.metric("Promedio General", f"{promedio_general_dim:.2f}")
    
    with col_kpi4:
        total_eval_dim = df_dim['evaluaciones'].sum()
        st.metric("Total Evaluaciones", total_eval_dim)
    
    st.markdown("---")
    
    # Gráfico mejorado con más información
    chart = alt.Chart(df_dim).mark_bar().encode(
        y=alt.Y('dimension:N', title='Dimensión', sort='-x'),
        x=alt.X('promedio:Q', title='Promedio', scale=alt.Scale(domain=[0, 2])),
        color=alt.Color(
            'promedio:Q',
            scale=alt.Scale(
                domain=[0, config.umbrales.riesgo_max, config.umbrales.mejora_max, 2],
                range=['#d73027', '#fee08b', '#b3ef8b', '#1a9850']
            ),
            legend=None
        ),
        tooltip=[
            'dimension', 
            alt.Tooltip('promedio:Q', format='.2f', title='Promedio'),
            alt.Tooltip('mediana:Q', format='.2f', title='Mediana'),
            alt.Tooltip('desviacion:Q', format='.2f', title='Desv. Est.'),
            alt.Tooltip('evaluaciones:Q', title='Evaluaciones'),
            alt.Tooltip('grupos:Q', title='Grupos'),
            alt.Tooltip('fortalezas:Q', title='🟢 Fortalezas'),
            alt.Tooltip('oportunidades:Q', title='🟡 Oportunidades'),
            alt.Tooltip('riesgos:Q', title='🔴 Riesgos')
        ]
    ).properties(height=max(300, len(df_dim) * 40))
    
    st.altair_chart(chart, use_container_width=True)
    
    # Tabla detallada mejorada
    st.subheader("📋 Detalle por Dimensión")
    st.dataframe(
        df_dim.style.format({
            'promedio': '{:.2f}',
            'mediana': '{:.2f}',
            'desviacion': '{:.2f}'
        }),
        use_container_width=True,
        hide_index=True,
        column_config={
            'dimension': 'Dimensión',
            'promedio': st.column_config.NumberColumn('Promedio', format='%.2f'),
            'mediana': st.column_config.NumberColumn('Mediana', format='%.2f'),
            'desviacion': st.column_config.NumberColumn('Desv. Est.', format='%.2f'),
            'evaluaciones': st.column_config.NumberColumn('Evaluaciones', format='%d'),
            'grupos': st.column_config.NumberColumn('Grupos', format='%d'),
            'fortalezas': st.column_config.NumberColumn('🟢', format='%d'),
            'oportunidades': st.column_config.NumberColumn('🟡', format='%d'),
            'riesgos': st.column_config.NumberColumn('🔴', format='%d')
        }
    )
    
    # Análisis de distribución por dimensión
    st.markdown("---")
    st.subheader("📈 Distribución de Resultados por Dimensión")
    
    # Crear gráfico de distribución (violin o box plot)
    chart_dist = alt.Chart(df_eval).mark_boxplot(extent='min-max').encode(
        x=alt.X('dimension:N', title='Dimensión', sort='-y'),
        y=alt.Y('resultado:Q', title='Resultado', scale=alt.Scale(domain=[0, 2])),
        color=alt.value('#1f77b4')
    ).properties(height=400)
    
    st.altair_chart(chart_dist, use_container_width=True)
    
    # Top y Bottom dimensiones
    st.markdown("---")
    col_top, col_bottom = st.columns(2)
    
    with col_top:
        st.subheader("🟢 Top 3 Dimensiones")
        top3 = df_dim.nlargest(3, 'promedio')[['dimension', 'promedio', 'grupos', 'evaluaciones']]
        st.dataframe(
            top3.style.format({'promedio': '{:.2f}'}),
            use_container_width=True,
            hide_index=True
        )
    
    with col_bottom:
        st.subheader("🔴 Dimensiones que Requieren Atención")
        bottom3 = df_dim.nsmallest(3, 'promedio')[['dimension', 'promedio', 'grupos', 'evaluaciones']]
        st.dataframe(
            bottom3.style.format({'promedio': '{:.2f}'}),
            use_container_width=True,
            hide_index=True
        )


def mostrar_analisis_aspectos(df_eval: pd.DataFrame):
    """Análisis detallado por aspectos individuales - Mejorado"""
    
    st.header("✅ Análisis por Aspecto")
    st.caption("Desempeño detallado en cada aspecto evaluado")
    
    # Promedio por dimensión y aspecto con más métricas
    df_aspecto = (df_eval
        .groupby(['dimension', 'aspecto'], as_index=False)
        .agg(
            promedio=('resultado', 'mean'),
            mediana=('resultado', 'median'),
            desviacion=('resultado', 'std'),
            evaluaciones=('resultado', 'count'),
            grupos=('codigo_grupo', 'nunique'),
            fortaleza=('resultado', lambda x: (x == 2).sum()),
            oportunidad=('resultado', lambda x: (x == 1).sum()),
            riesgo=('resultado', lambda x: (x == 0).sum())
        )
        .sort_values(['dimension', 'promedio'], ascending=[True, False])
    )
    
    # Calcular porcentajes
    df_aspecto['%_fortaleza'] = (df_aspecto['fortaleza'] / df_aspecto['evaluaciones'] * 100).round(1)
    df_aspecto['%_oportunidad'] = (df_aspecto['oportunidad'] / df_aspecto['evaluaciones'] * 100).round(1)
    df_aspecto['%_riesgo'] = (df_aspecto['riesgo'] / df_aspecto['evaluaciones'] * 100).round(1)
    
    # KPIs generales
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    
    with col_kpi1:
        st.metric("Total Aspectos", len(df_aspecto))
    
    with col_kpi2:
        mejor_asp = df_aspecto.nlargest(1, 'promedio')
        if not mejor_asp.empty:
            st.metric("Mejor Aspecto", mejor_asp.iloc[0]['aspecto'][:30] + "...", f"{mejor_asp.iloc[0]['promedio']:.2f}")
    
    with col_kpi3:
        promedio_general_asp = df_aspecto['promedio'].mean()
        st.metric("Promedio General", f"{promedio_general_asp:.2f}")
    
    st.markdown("---")
    
    # Selector de dimensión
    dimensiones = ['Todas'] + sorted(list(df_aspecto['dimension'].unique()))
    dim_sel = st.selectbox("Filtrar por dimensión:", dimensiones, help="Seleccione una dimensión para filtrar aspectos")
    
    if dim_sel != 'Todas':
        df_mostrar = df_aspecto[df_aspecto['dimension'] == dim_sel].copy()
        st.info(f"Mostrando {len(df_mostrar)} aspectos de la dimensión '{dim_sel}'")
    else:
        df_mostrar = df_aspecto.copy()
    
    # Gráfico mejorado de aspectos
    chart = alt.Chart(df_mostrar).mark_bar().encode(
        y=alt.Y('aspecto:N', title='Aspecto', sort='-x'),
        x=alt.X('promedio:Q', title='Promedio', scale=alt.Scale(domain=[0, 2])),
        color=alt.Color(
            'promedio:Q',
            scale=alt.Scale(
                domain=[0, config.umbrales.riesgo_max, config.umbrales.mejora_max, 2],
                range=['#d73027', '#fee08b', '#b3ef8b', '#1a9850']
            ),
            legend=None
        ),
        tooltip=[
            'aspecto',
            'dimension',
            alt.Tooltip('promedio:Q', format='.2f', title='Promedio'),
            alt.Tooltip('mediana:Q', format='.2f', title='Mediana'),
            alt.Tooltip('desviacion:Q', format='.2f', title='Desv. Est.'),
            alt.Tooltip('evaluaciones:Q', title='Evaluaciones'),
            alt.Tooltip('grupos:Q', title='Grupos'),
            alt.Tooltip('fortaleza:Q', title='🟢 Fortalezas'),
            alt.Tooltip('oportunidad:Q', title='🟡 Oportunidades'),
            alt.Tooltip('riesgo:Q', title='🔴 Riesgos')
        ]
    ).properties(height=max(400, len(df_mostrar) * 30))
    
    st.altair_chart(chart, use_container_width=True)
    
    # Tabla detallada mejorada
    st.subheader("📋 Detalle por Aspecto")
    st.dataframe(
        df_mostrar[['dimension', 'aspecto', 'promedio', 'mediana', 'desviacion', 
                   'evaluaciones', 'grupos', 'fortaleza', 'oportunidad', 'riesgo',
                   '%_fortaleza', '%_oportunidad', '%_riesgo']].style.format({
            'promedio': '{:.2f}',
            'mediana': '{:.2f}',
            'desviacion': '{:.2f}',
            '%_fortaleza': '{:.1f}',
            '%_oportunidad': '{:.1f}',
            '%_riesgo': '{:.1f}'
        }),
        use_container_width=True,
        hide_index=True,
        column_config={
            'dimension': 'Dimensión',
            'aspecto': 'Aspecto',
            'promedio': st.column_config.NumberColumn('Promedio', format='%.2f'),
            'mediana': st.column_config.NumberColumn('Mediana', format='%.2f'),
            'desviacion': st.column_config.NumberColumn('Desv. Est.', format='%.2f'),
            'evaluaciones': st.column_config.NumberColumn('Evaluaciones', format='%d'),
            'grupos': st.column_config.NumberColumn('Grupos', format='%d'),
            'fortaleza': st.column_config.NumberColumn('🟢', format='%d'),
            'oportunidad': st.column_config.NumberColumn('🟡', format='%d'),
            'riesgo': st.column_config.NumberColumn('🔴', format='%d'),
            '%_fortaleza': st.column_config.NumberColumn('% 🟢', format='%.1f'),
            '%_oportunidad': st.column_config.NumberColumn('% 🟡', format='%.1f'),
            '%_riesgo': st.column_config.NumberColumn('% 🔴', format='%.1f')
        }
    )
    
    # Top y Bottom aspectos mejorados
    st.markdown("---")
    
    col_top, col_bottom = st.columns(2)
    
    with col_top:
        st.subheader("🟢 Top 5 Aspectos Más Fuertes")
        top5 = df_aspecto.nlargest(5, 'promedio')[['aspecto', 'dimension', 'promedio', 'evaluaciones', '%_fortaleza']]
        st.dataframe(
            top5.style.format({
                'promedio': '{:.2f}',
                '%_fortaleza': '{:.1f}'
            }),
            use_container_width=True,
            hide_index=True,
            column_config={
                'aspecto': 'Aspecto',
                'dimension': 'Dimensión',
                'promedio': st.column_config.NumberColumn('Promedio', format='%.2f'),
                'evaluaciones': st.column_config.NumberColumn('Evaluaciones', format='%d'),
                '%_fortaleza': st.column_config.NumberColumn('% Fortalezas', format='%.1f')
            }
        )
    
    with col_bottom:
        st.subheader("🔴 Top 5 Aspectos que Requieren Atención")
        bottom5 = df_aspecto.nsmallest(5, 'promedio')[['aspecto', 'dimension', 'promedio', 'evaluaciones', '%_riesgo']]
        st.dataframe(
            bottom5.style.format({
                'promedio': '{:.2f}',
                '%_riesgo': '{:.1f}'
            }),
            use_container_width=True,
            hide_index=True,
            column_config={
                'aspecto': 'Aspecto',
                'dimension': 'Dimensión',
                'promedio': st.column_config.NumberColumn('Promedio', format='%.2f'),
                'evaluaciones': st.column_config.NumberColumn('Evaluaciones', format='%d'),
                '%_riesgo': st.column_config.NumberColumn('% Riesgos', format='%.1f')
            }
        )
    
    # Análisis de distribución
    st.markdown("---")
    st.subheader("📊 Distribución de Resultados por Aspecto")
    
    if dim_sel != 'Todas':
        df_dist = df_eval[df_eval['dimension'] == dim_sel]
    else:
        df_dist = df_eval
    
    chart_dist = alt.Chart(df_dist).mark_boxplot(extent='min-max').encode(
        x=alt.X('aspecto:N', title='Aspecto', sort='-y'),
        y=alt.Y('resultado:Q', title='Resultado', scale=alt.Scale(domain=[0, 2])),
        color=alt.value('#1f77b4')
    ).properties(height=max(400, len(df_dist['aspecto'].unique()) * 20))
    
    st.altair_chart(chart_dist, use_container_width=True)

"""
Agregar esta función a comite_view.py
Insertar después de mostrar_analisis_aspectos()
"""

def mostrar_analisis_por_ficha(df_eval: pd.DataFrame):
    """Análisis detallado por tipo de ficha"""
    
    st.header("🎭 Análisis por Ficha")
    st.caption("Desempeño consolidado por tipo de ficha de evaluación")
    
    # Verificar que haya columna ficha
    if 'ficha' not in df_eval.columns:  
        st.warning("⚠️ No hay información de fichas en las evaluaciones")
        return
    
    # Estadísticas generales por ficha
    from src.database.models import EvaluacionModel
    df_stats_ficha = EvaluacionModel.obtener_estadisticas_por_ficha()
    
    if df_stats_ficha.empty:
        st.info("No hay evaluaciones registradas por ficha todavía")
        return
    
    # KPIs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_fichas = len(df_stats_ficha)
        st.metric("Total Fichas Activas", total_fichas)
    
    with col2:
        ficha_mejor = df_stats_ficha.nlargest(1, 'promedio_general')
        if not ficha_mejor.empty:
            st.metric(
                "Ficha con Mejor Desempeño",
                ficha_mejor.iloc[0]['ficha'],
                #f"{ficha_mejor.iloc[0]['promedio_general']:.2f}"
            )
    
    with col3:
        total_grupos = df_stats_ficha['grupos_evaluados'].sum()
        st.metric("Total Grupos Evaluados", int(total_grupos))
    
    st.markdown("---")
    
    # Gráfico comparativo de fichas
    st.subheader("📊 Comparativa de Fichas")
    
    chart = alt.Chart(df_stats_ficha).mark_bar().encode(
        y=alt.Y('ficha:N', title='Ficha', sort='-x'),
        x=alt.X('promedio_general:Q', title='Estado General', scale=alt.Scale(domain=[0, 2]), axis=alt.Axis(labels=False)),
        color=alt.Color(
            'promedio_general:Q',
            scale=alt.Scale(
                    domain=[0, config.umbrales.riesgo_max,1, config.umbrales.mejora_max, 2],
                    range=['#DA0024', "#feb98b", '#FFCA00', '#b3ef8b', '#00AD1B']
                ),
            legend=None
        ),
        tooltip=[
            'ficha',
            #alt.Tooltip('promedio_general:Q', format='.2f', title='Promedio'),
            alt.Tooltip('grupos_evaluados:Q', title='Grupos'),
            alt.Tooltip('total_evaluaciones:Q', title='Evaluaciones')
        ]
    ).properties(height=max(300, len(df_stats_ficha) * 40))
    
    st.altair_chart(chart, use_container_width=True)
    
    # Tabla detallada
    st.subheader("📋 Detalle por Ficha")
    
    # Formatear columnas
    df_display = df_stats_ficha.copy()

    def estilo_estado_ficha(row):
                color = color_gradiente(row['promedio_general'])
                return [
                    f'background-color: {color}'
                    if col == 'resultado_emoji' else ''
                    for col in row.index
                ]
    df_display['resultado_emoji'] = df_display['promedio_general'].apply(lambda x:"")
    
    
    st.dataframe(
        df_display.style.apply(estilo_estado_ficha, axis=1),
        use_container_width=True,
        hide_index=True,
        column_config={
            'ficha_id': None,
            'ficha': 'Ficha',
            'grupos_evaluados': st.column_config.NumberColumn('Grupos', format='%d'),
            'curadores': None,
            #'curadores': st.column_config.NumberColumn('Curadores', format='%d'),
            'total_evaluaciones': st.column_config.NumberColumn('Evaluaciones', format='%d'),
            'promedio_general': None,
            'resultado_emoji': 'Estado',
            'fortalezas': st.column_config.NumberColumn('🟢 Fortalezas', format='%d'),
            'oportunidades': st.column_config.NumberColumn('🟡 Oportunidades', format='%d'),
            'riesgos': st.column_config.NumberColumn('🔴 Riesgos', format='%d')
        }
    )
    
    st.markdown("---")
    
    # Análisis detallado por ficha seleccionada
    st.subheader("📇 Análisis Detallado por Ficha")
    
    fichas_disponibles = df_stats_ficha['ficha'].tolist()
    ficha_seleccionada = st.selectbox("Seleccionar ficha:", fichas_disponibles)
    
    if ficha_seleccionada:
        # Filtrar evaluaciones de esta ficha
        df_ficha = df_eval[df_eval['ficha'] == ficha_seleccionada]
        
        if df_ficha.empty:
            st.warning(f"No hay evaluaciones para la ficha '{ficha_seleccionada}'")
        

        total_evaluaciones = len(df_eval)
        curadores_activos = df_eval['curador'].nunique()
        grupos_evaluados = df_ficha['codigo_grupo'].nunique()
        promedio_general = df_ficha['resultado'].mean()
        desviacion_std = df_ficha['resultado'].std()

        color_estado_general = color_gradiente(promedio_general)

        

        
        # Calcular estados
        en_riesgo = (df_ficha['resultado'] < config.umbrales.riesgo_max).sum()
        por_mejorar = ((df_ficha['resultado'] >= config.umbrales.riesgo_max) & 
                    (df_ficha['resultado'] < config.umbrales.mejora_max)).sum()
        fortalecidos = (df_ficha['resultado'] >= config.umbrales.mejora_max).sum()
        
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
            
        # Análisis por dimensión dentro de la ficha
        st.markdown("**Desempeño por Dimensión:**")
        
        df_dim_ficha = (df_ficha
            .groupby('dimension', as_index=False)
            .agg(
                promedio=('resultado', 'mean'),
                evaluaciones=('resultado', 'count')
            )
            .sort_values('promedio', ascending=False)
        )
            
        chart_dim = alt.Chart(df_dim_ficha).mark_bar().encode(
            y=alt.Y('dimension:N', title='Dimensión'),
            x=alt.X('promedio:Q', title='Estado', scale=alt.Scale(domain=[0, 2]), axis=alt.Axis(labels=False)),
            color=alt.Color(
                'promedio:Q',
                scale=alt.Scale(
                    domain=[0, config.umbrales.riesgo_max,1, config.umbrales.mejora_max, 2],
                    range=['#DA0024', "#feb98b", '#FFCA00', '#b3ef8b', '#00AD1B']
                ),
                legend=None
            ),
            tooltip=[
                'dimension',
                #alt.Tooltip('promedio:Q', format='.2f'),
                'evaluaciones'
            ]
        ).properties(height=250)
        
        st.altair_chart(chart_dim, use_container_width=True)
        
        # Top grupos de esta ficha
        st.markdown("**🏆 Top 5 Grupos de esta Ficha:**")
        
        df_grupos_ficha = (df_ficha
            .groupby(['codigo_grupo', 'nombre_propuesta'], as_index=False)
            .agg(promedio=('resultado', 'mean'))
            .nlargest(5, 'promedio')
        )
    
        df_grupos_ficha['resultado_emoji'] = df_grupos_ficha['promedio'].apply(estado_patrimonial)
        st.dataframe(
            df_grupos_ficha.style.format({'promedio': '{:.2f}'}),
            use_container_width=True,
            hide_index=True,
            column_config={
                'codigo_grupo': 'Código',
                'nombre_propuesta': 'Grupo',
                'resultado_emoji': 'Estado',
                #'promedio': st.column_config.NumberColumn('Promedio', format='%.2f')
                'promedio': None
            }
        )
        
        # Aspectos más fuertes y débiles de esta ficha
        col_asp1, col_asp2 = st.columns(2)
        
        with col_asp1:
            st.markdown("**🟢 Aspectos Más Fuertes:**")
            df_asp_fuerte = (df_ficha
                .groupby('aspecto', as_index=False)
                .agg(promedio=('resultado', 'mean'))
                .nlargest(5, 'promedio')
            )
            df_asp_fuerte['resultado_emoji'] = df_asp_fuerte['promedio'].apply(estado_patrimonial)
            st.dataframe(
                df_asp_fuerte.style.format({'promedio': '{:.2f}'}),
                use_container_width=True,
                hide_index=True,
                column_config={
                    'aspecto': 'Aspecto',
                    'resultado_emoji': 'Estado',
                    'promedio': None
                }
            )
        
        with col_asp2:
            st.markdown("**🔴 Aspectos a Fortalecer:**")
            df_asp_debil = (df_ficha
                .groupby('aspecto', as_index=False)
                .agg(promedio=('resultado', 'mean'))
                .nsmallest(5, 'promedio')
            )
            df_asp_debil['resultado_emoji'] = df_asp_debil['promedio'].apply(estado_patrimonial)
            st.dataframe(
                df_asp_debil.style.format({'promedio': '{:.2f}'}),
                use_container_width=True,
                hide_index=True,
                column_config={
                    'aspecto': 'Aspecto',
                    'resultado_emoji': 'Estado',
                    'promedio': None
                }
            )

def mostrar_analisis_curadores(df_eval: pd.DataFrame):
    """Análisis por curadores - Mejorado"""
    
    st.header("👥 Análisis por Curador")
    st.caption("Estadísticas detalladas de evaluación por curador")
    
    # Estadísticas por curador mejoradas
    df_cur = (df_eval
        .groupby('curador', as_index=False)
        .agg(
            grupos_evaluados=('codigo_grupo', 'nunique'),
            total_evaluaciones=('resultado', 'count'),
            promedio_otorgado=('resultado', 'mean'),
            mediana_otorgada=('resultado', 'median'),
            desviacion=('resultado', 'std'),
            fortaleza=('resultado', lambda x: (x == 2).sum()),
            oportunidad=('resultado', lambda x: (x == 1).sum()),
            riesgo=('resultado', lambda x: (x == 0).sum()),
            fichas_evaluadas=('ficha', 'nunique')
        )
        .sort_values('grupos_evaluados', ascending=False)
    )
    
    # Calcular porcentajes y métricas adicionales
    df_cur['%_fortaleza'] = (df_cur['fortaleza'] / df_cur['total_evaluaciones'] * 100).round(1)
    df_cur['%_oportunidad'] = (df_cur['oportunidad'] / df_cur['total_evaluaciones'] * 100).round(1)
    df_cur['%_riesgo'] = (df_cur['riesgo'] / df_cur['total_evaluaciones'] * 100).round(1)
    df_cur['eval_por_grupo'] = (df_cur['total_evaluaciones'] / df_cur['grupos_evaluados']).round(1)
    
    # KPIs mejorados
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Curadores", len(df_cur))
    
    with col2:
        st.metric("Promedio Evaluaciones/Curador", f"{df_cur['total_evaluaciones'].mean():.0f}")
    
    with col3:
        st.metric("Promedio General Otorgado", f"{df_cur['promedio_otorgado'].mean():.2f}")
    
    with col4:
        st.metric("Desviación Estándar", f"{df_cur['promedio_otorgado'].std():.2f}")
    
    st.markdown("---")
    
    

    
    
    st.subheader("📊 Grupos Evaluados por Curador")
    chart1 = alt.Chart(df_cur).mark_bar().encode(
        x=alt.X('curador:N', title='Curador', sort='-y'),
        y=alt.Y('grupos_evaluados:Q', title='Grupos Evaluados'),
        color=alt.Color(
            'grupos_evaluados:Q',
            scale=alt.Scale(scheme='greens'),
            legend=None
        ),
        tooltip=[
            'curador', 
            'grupos_evaluados',
            alt.Tooltip('promedio_otorgado:Q', format='.2f', title='Promedio'),
            'total_evaluaciones'
        ]
    ).properties(height=300)
    
    st.altair_chart(chart1, use_container_width=True)
    
    
    st.subheader("📈 Promedio Otorgado por Curador")
    chart2 = alt.Chart(df_cur).mark_bar().encode(
        x=alt.X('curador:N', title='Curador', sort='-y'),
        y=alt.Y('promedio_otorgado:Q', title='Promedio', scale=alt.Scale(domain=[0, 2])),
        color=alt.Color(
            'promedio_otorgado:Q',
            scale=alt.Scale(
                domain=[0, config.umbrales.riesgo_max, config.umbrales.mejora_max, 2],
                range=['#d73027', '#fee08b', '#b3ef8b', '#1a9850']
            ),
            legend=None
        ),
        tooltip=[
            'curador', 
            alt.Tooltip('promedio_otorgado:Q', format='.2f', title='Promedio'),
            alt.Tooltip('mediana_otorgada:Q', format='.2f', title='Mediana'),
            alt.Tooltip('desviacion:Q', format='.2f', title='Desv. Est.'),
            'total_evaluaciones'
        ]
    ).properties(height=300)
    
    st.altair_chart(chart2, use_container_width=True)
    
    # Gráfico de distribución de calificaciones
    st.markdown("---")
    st.subheader("📊 Distribución de Calificaciones por Curador")
    
    chart_dist = alt.Chart(df_eval).mark_boxplot(extent='min-max').encode(
        x=alt.X('curador:N', title='Curador', sort='-y'),
        y=alt.Y('resultado:Q', title='Resultado', scale=alt.Scale(domain=[0, 2])),
        color=alt.value('#1f77b4')
    ).properties(height=400)
    
    st.altair_chart(chart_dist, use_container_width=True)
    
    # Tabla detallada mejorada
    st.markdown("---")
    st.subheader("📋 Detalle por Curador")
    st.dataframe(
        df_cur[['curador', 'grupos_evaluados', 'total_evaluaciones', 'eval_por_grupo',
               'promedio_otorgado', 'mediana_otorgada', 'desviacion',
               'fichas_evaluadas', 'fortaleza', 'oportunidad', 'riesgo',
               '%_fortaleza', '%_oportunidad', '%_riesgo']].style.format({
            'promedio_otorgado': '{:.2f}',
            'mediana_otorgada': '{:.2f}',
            'desviacion': '{:.2f}',
            'eval_por_grupo': '{:.1f}',
            '%_fortaleza': '{:.1f}',
            '%_oportunidad': '{:.1f}',
            '%_riesgo': '{:.1f}'
        }),
        use_container_width=True,
        hide_index=True,
        column_config={
            'curador': 'Curador',
            'grupos_evaluados': st.column_config.NumberColumn('Grupos', format='%d'),
            'total_evaluaciones': st.column_config.NumberColumn('Evaluaciones', format='%d'),
            'eval_por_grupo': st.column_config.NumberColumn('Eval/Grupo', format='%.1f'),
            'promedio_otorgado': st.column_config.NumberColumn('Promedio', format='%.2f'),
            'mediana_otorgada': st.column_config.NumberColumn('Mediana', format='%.2f'),
            'desviacion': st.column_config.NumberColumn('Desv. Est.', format='%.2f'),
            'fichas_evaluadas': st.column_config.NumberColumn('Fichas', format='%d'),
            'fortaleza': st.column_config.NumberColumn('🟢', format='%d'),
            'oportunidad': st.column_config.NumberColumn('🟡', format='%d'),
            'riesgo': st.column_config.NumberColumn('🔴', format='%d'),
            '%_fortaleza': st.column_config.NumberColumn('% 🟢', format='%.1f'),
            '%_oportunidad': st.column_config.NumberColumn('% 🟡', format='%.1f'),
            '%_riesgo': st.column_config.NumberColumn('% 🔴', format='%.1f')
        }
    )
    
    # Análisis comparativo
    st.markdown("---")
    st.subheader("🔍 Análisis Comparativo")
    
    col_comp1, col_comp2 = st.columns(2)
    
    with col_comp1:
        st.markdown("**📊 Curadores Más Productivos**")
        top_productivos = df_cur.nlargest(5, 'total_evaluaciones')[
            ['curador', 'total_evaluaciones', 'grupos_evaluados', 'eval_por_grupo']
        ]
        st.dataframe(
            top_productivos.style.format({'eval_por_grupo': '{:.1f}'}),
            use_container_width=True,
            hide_index=True
        )
    
    with col_comp2:
        st.markdown("**⭐ Curadores Más Generosos (Mayor Promedio)**")
        top_generosos = df_cur.nlargest(5, 'promedio_otorgado')[
            ['curador', 'promedio_otorgado', 'total_evaluaciones', '%_fortaleza']
        ]
        st.dataframe(
            top_generosos.style.format({
                'promedio_otorgado': '{:.2f}',
                '%_fortaleza': '{:.1f}'
            }),
            use_container_width=True,
            hide_index=True
        )
    
    # Análisis de consistencia
    st.markdown("---")
    st.subheader("📏 Análisis de Consistencia")
    
    col_cons1, col_cons2 = st.columns(2)
    
    with col_cons1:
        st.markdown("**🎯 Curadores Más Consistentes (Menor Desviación)**")
        mas_consistentes = df_cur.nsmallest(5, 'desviacion')[
            ['curador', 'desviacion', 'promedio_otorgado', 'total_evaluaciones']
        ]
        st.dataframe(
            mas_consistentes.style.format({
                'desviacion': '{:.2f}',
                'promedio_otorgado': '{:.2f}'
            }),
            use_container_width=True,
            hide_index=True
        )
    
    with col_cons2:
        st.markdown("**📊 Estadísticas Generales**")
        st.metric("Promedio de Grupos/Curador", f"{df_cur['grupos_evaluados'].mean():.1f}")
        st.metric("Promedio de Evaluaciones/Curador", f"{df_cur['total_evaluaciones'].mean():.1f}")
        st.metric("Desviación Estándar de Promedios", f"{df_cur['promedio_otorgado'].std():.2f}")


def mostrar_panel_admin():
    """Panel de administración para sincronización de datos"""
    
    st.header("⚙️ Panel de Administración")
    
    st.warning("⚠️ Esta sección permite modificar la base de datos. Úsala con precaución.")
    
    tab1, tab2, tab3 = st.tabs(["📥 Sincronizar Grupos", "💾 Backups", "📊 Estadísticas"])
    
    with tab1:
        st.subheader("Sincronizar Grupos desde Excel")
        
        st.info(f"📂 Archivo configurado: {config.excel_path}")
        
        # Opción de sincronización
        sync_option = st.radio(
            "Tipo de sincronización:",
            [
                "Actualizar grupos existentes (mantiene evaluaciones)",
                "Agregar solo grupos nuevos",
                "Sincronización completa (actualiza + agrega)",
                "🗑️ Eliminar SOLO evaluaciones (mantiene grupos)",
                "⚠️ Eliminar todo y recargar (BORRA EVALUACIONES)"
            ]
        )
        
        if st.button("🔄 Ejecutar Sincronización", type="primary"):
            try:
                with st.spinner("Sincronizando..."):
                    # Cargar Excel
                    df_excel = pd.read_excel(config.excel_path)
                    
                    # Conectar a BD
                    from src.database.connection import get_db_connection
                    
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        
                        if "Actualizar grupos existentes" in sync_option:
                            actualizados = 0
                            for _, row in df_excel.iterrows():
                                cursor.execute("""
                                    UPDATE grupos 
                                    SET nombre_propuesta = ?,
                                        modalidad = ?,
                                        tipo = ?,
                                        tamano = ?,
                                        naturaleza = ?
                                    WHERE codigo = ?
                                """, (
                                    row['Nombre_Propuesta'],
                                    row['Modalidad'],
                                    row['Tipo'],
                                    row.get('Tamaño', 'N/A'),
                                    row['Naturaleza'],
                                    str(row['Codigo']).strip().upper()
                                ))
                                if cursor.rowcount > 0:
                                    actualizados += 1
                            
                            st.success(f"✅ {actualizados} grupos actualizados")
                        
                        elif "solo grupos nuevos" in sync_option:
                            # Agregar solo nuevos
                            cursor.execute("SELECT codigo FROM grupos")
                            existentes = {row[0] for row in cursor.fetchall()}
                            
                            nuevos = 0
                            for _, row in df_excel.iterrows():
                                codigo = str(row['Codigo']).strip().upper()
                                if codigo not in existentes:
                                    try:
                                        cursor.execute("""
                                            INSERT INTO grupos 
                                            (codigo, nombre_propuesta, modalidad, tipo, tamano, naturaleza, ano_evento)
                                            VALUES (?, ?, ?, ?, ?, ?, ?)
                                        """, (
                                            codigo,
                                            row['Nombre_Propuesta'],
                                            row['Modalidad'],
                                            row['Tipo'],
                                            row.get('Tamaño', 'N/A'),
                                            row['Naturaleza'],
                                            config.ano_evento
                                        ))
                                        nuevos += 1
                                    except:
                                        pass
                            
                            st.success(f"✅ {nuevos} grupos nuevos agregados")
                        
                        elif "Sincronización completa" in sync_option:
                            # Actualizar + agregar
                            cursor.execute("SELECT codigo FROM grupos")
                            existentes = {row[0] for row in cursor.fetchall()}
                            
                            actualizados = 0
                            nuevos = 0
                            
                            for _, row in df_excel.iterrows():
                                codigo = str(row['Codigo']).strip().upper()
                                
                                if codigo in existentes:
                                    cursor.execute("""
                                        UPDATE grupos 
                                        SET nombre_propuesta = ?,
                                            modalidad = ?,
                                            tipo = ?,
                                            tamano = ?,
                                            naturaleza = ?
                                        WHERE codigo = ?
                                    """, (
                                        row['Nombre_Propuesta'],
                                        row['Modalidad'],
                                        row['Tipo'],
                                        row.get('Tamaño', 'N/A'),
                                        row['Naturaleza'],
                                        codigo
                                    ))
                                    actualizados += 1
                                else:
                                    try:
                                        cursor.execute("""
                                            INSERT INTO grupos 
                                            (codigo, nombre_propuesta, modalidad, tipo, tamano, naturaleza, ano_evento)
                                            VALUES (?, ?, ?, ?, ?, ?, ?)
                                        """, (
                                            codigo,
                                            row['Nombre_Propuesta'],
                                            row['Modalidad'],
                                            row['Tipo'],
                                            row.get('Tamaño', 'N/A'),
                                            row['Naturaleza'],
                                            config.ano_evento
                                        ))
                                        nuevos += 1
                                    except:
                                        pass
                            
                            st.success(f"✅ {actualizados} grupos actualizados, {nuevos} grupos nuevos")
                        elif "Eliminar SOLO evaluaciones" in sync_option:
                            # ============================================================
                            # OPCIÓN: ELIMINAR SOLO EVALUACIONES (SIMPLIFICADO)
                            # ============================================================
                            st.error("⚠️ ADVERTENCIA: Esta opción eliminará TODAS las evaluaciones")
                            st.info("✅ Los grupos NO serán eliminados")
                            
                            # Mostrar estadísticas
                            try:
                                cursor.execute("SELECT COUNT(*) FROM evaluaciones")
                                total_evaluaciones = cursor.fetchone()[0]
                                
                                cursor.execute("SELECT COUNT(DISTINCT codigo_grupo) FROM evaluaciones")
                                grupos_evaluados = cursor.fetchone()[0]
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Total Evaluaciones", total_evaluaciones)
                                with col2:
                                    st.metric("Grupos Evaluados", grupos_evaluados)
                                
                            except Exception as e:
                                st.warning(f"Error obteniendo estadísticas: {e}")
                                total_evaluaciones = 0
                            
                            st.markdown("---")
                            
                            # UN SOLO BOTÓN CON CONFIRMACIÓN
                            if st.button(
                                f"🗑️ ELIMINAR TODAS LAS EVALUACIONES ({total_evaluaciones})", 
                                type="primary", 
                                use_container_width=True,
                                key="btn_eliminar_eval"
                            ):
                                try:
                                    # Eliminar evaluaciones
                                    cursor.execute("DELETE FROM evaluaciones")
                                    evaluaciones_eliminadas = cursor.rowcount
                                    
                                    # Verificar
                                    cursor.execute("SELECT COUNT(*) FROM evaluaciones")
                                    verificacion = cursor.fetchone()[0]
                                    
                                    if verificacion == 0:
                                        st.success(f"✅ Se eliminaron {evaluaciones_eliminadas} evaluaciones")
                                        
                                        cursor.execute("SELECT COUNT(*) FROM grupos")
                                        grupos_restantes = cursor.fetchone()[0]
                                        st.info(f"ℹ️ Los {grupos_restantes} grupos permanecen intactos")
                                        
                                        # Log
                                        from src.database.models import LogModel
                                        LogModel.registrar_log(
                                            usuario=st.session_state.usuario,
                                            accion="ELIMINACION_EVALUACIONES",
                                            detalle=f"Eliminadas: {evaluaciones_eliminadas} evaluaciones"
                                        )
                                        
                                        st.cache_data.clear()
                                        st.balloons()
                                    else:
                                        st.error(f"❌ Error: Quedan {verificacion} evaluaciones")
                                        
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                                    logger.exception("Error eliminando evaluaciones")
                        else:
                            # Eliminar todo
                            st.error("Esta opción eliminará TODAS las evaluaciones")
                            if st.checkbox("Confirmo que quiero eliminar todo"):
                                cursor.execute("DELETE FROM evaluaciones")
                                cursor.execute("DELETE FROM grupos")
                                
                                insertados = 0
                                for _, row in df_excel.iterrows():
                                    try:
                                        cursor.execute("""
                                            INSERT INTO grupos 
                                            (codigo, nombre_propuesta, modalidad, tipo, tamano, naturaleza, ano_evento)
                                            VALUES (?, ?, ?, ?, ?, ?, ?)
                                        """, (
                                            str(row['Codigo']).strip().upper(),
                                            row['Nombre_Propuesta'],
                                            row['Modalidad'],
                                            row['Tipo'],
                                            row.get('Tamaño', 'N/A'),
                                            row['Naturaleza'],
                                            config.ano_evento
                                        ))
                                        insertados += 1
                                    except:
                                        pass
                                
                                st.success(f"✅ Base de datos recreada con {insertados} grupos")
                    
                    # Limpiar caché
                    st.cache_data.clear()
                    
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    with tab2:
        st.subheader("💾 Sistema de Backups")

        st.info("💡 Se crea un backup comprimido de la base de datos completa")

        if st.button("📦 Crear Backup Ahora", type="primary"):
            try:
                # Crear backup usando la función modular
                zip_data = crear_backup_zip()

                # Descargar el ZIP
                st.download_button(
                    label="⬇️ Descargar Backup",
                    data=zip_data,
                    file_name=f"backup_curaduria_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip",
                    type="secondary"
                )

                st.success("✅ Backup creado exitosamente")

            except Exception as e:
                st.error(f"❌ Error al crear backup: {e}")
    
    with tab3:
        st.subheader("📊 Estadísticas del Sistema")
        
        from src.database.connection import get_db_connection
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM grupos")
            total_grupos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM evaluaciones")
            total_eval = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT usuario_id) FROM evaluaciones")
            curadores_activos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM aspectos")
            total_aspectos = cursor.fetchone()[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Grupos", total_grupos)
        
        with col2:
            st.metric("Total Aspectos", total_aspectos)
        
        with col3:
            st.metric("Total Evaluaciones", total_eval)
        
        with col4:
            st.metric("Curadores Activos", curadores_activos)


def mostrar_gestion_usuarios(df_eval: pd.DataFrame):
    """Panel de gestión completa de usuarios"""
    from src.database.models import UsuarioModel, LogModel
    
    st.header("👥 Gestión de Usuarios")
    st.caption("Administración de curadores y miembros del comité")
    
    # Botón para refrescar
    if st.button("🔄️ Actualizar Lista"):
        st.rerun()
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Lista de Usuarios", 
        "➕ Crear Usuario", 
        "🔑 Cambiar Contraseña", 
        "✏️ Editar Usuario"
    ])
    
    # ═══════════════════════════════════════════════════════════════
    # TAB 1: LISTA DE USUARIOS
    # ═══════════════════════════════════════════════════════════════
    with tab1:
        st.subheader("Usuarios del Sistema")
        
        # Cargar usuarios
        usuarios = UsuarioModel.obtener_todos(incluir_inactivos=True)
        
        if not usuarios:
            st.info("No hay usuarios registrados")
        else:
            # Crear DataFrame para mejor visualización
            usuarios_df = pd.DataFrame(usuarios)
            
            # Calcular evaluaciones por usuario
            for idx, user in usuarios_df.iterrows():
                num_eval = UsuarioModel.contar_evaluaciones_usuario(user['username'])
                usuarios_df.at[idx, 'num_evaluaciones'] = num_eval
            
            # Mostrar tabla resumen
            st.dataframe(
                usuarios_df[['username', 'rol', 'activo', 'num_evaluaciones', 'fecha_creacion']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    'username': 'Usuario',
                    'rol': st.column_config.TextColumn('Rol'),
                    'activo': st.column_config.CheckboxColumn('Activo'),
                    'num_evaluaciones': st.column_config.NumberColumn('Evaluaciones', format='%d'),
                    'fecha_creacion': 'Fecha Creación'
                }
            )
            
            st.markdown("---")
            st.subheader("Acciones")
            
            # Tabla de usuarios con acciones
            for user in usuarios:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
                    
                    with col1:
                        estado_emoji = "✅" if user['activo'] else "❌"
                        st.markdown(f"**{estado_emoji} {user['username']}**")
                    
                    with col2:
                        rol_badge = "🎭 Curador" if user['rol'] == 'curador' else "🏛️ Comité"
                        st.text(rol_badge)
                    
                    with col3:
                        num_eval = UsuarioModel.contar_evaluaciones_usuario(user['username'])
                        st.text(f"📝 {num_eval} eval.")
                    
                    with col4:
                        if user['activo']:
                            if st.button("🚫 Desactivar", key=f"deact_{user['id']}", use_container_width=True):
                                exito, error = UsuarioModel.activar_desactivar_usuario(user['username'], False)
                                if exito:
                                    LogModel.registrar_log(
                                        st.session_state.usuario,
                                        "USUARIO_DESACTIVADO",
                                        f"Usuario: {user['username']}"
                                    )
                                    st.success(f"Usuario {user['username']} desactivado")
                                    st.rerun()
                                else:
                                    st.error(error)
                        else:
                            if st.button("✅ Activar", key=f"act_{user['id']}", use_container_width=True):
                                exito, error = UsuarioModel.activar_desactivar_usuario(user['username'], True)
                                if exito:
                                    LogModel.registrar_log(
                                        st.session_state.usuario,
                                        "USUARIO_ACTIVADO",
                                        f"Usuario: {user['username']}"
                                    )
                                    st.success(f"Usuario {user['username']} activado")
                                    st.rerun()
                                else:
                                    st.error(error)
                    
                    with col5:
                        # No puede eliminarse a sí mismo
                        if user['username'] != st.session_state.usuario:
                            if st.button("🗑️ Eliminar", key=f"del_{user['id']}", type="secondary", use_container_width=True):
                                # Confirmación
                                if 'confirmar_eliminacion' not in st.session_state:
                                    st.session_state.confirmar_eliminacion = user['username']
                                    st.warning(f"⚠️ ¿Eliminar a {user['username']}? Haz clic nuevamente para confirmar.")
                                elif st.session_state.confirmar_eliminacion == user['username']:
                                    exito, error = UsuarioModel.eliminar_usuario(user['username'])
                                    if exito:
                                        LogModel.registrar_log(
                                            st.session_state.usuario,
                                            "USUARIO_ELIMINADO",
                                            f"Usuario: {user['username']}"
                                        )
                                        st.success("Usuario eliminado")
                                        del st.session_state.confirmar_eliminacion
                                        st.rerun()
                                    else:
                                        st.error(error)
                        else:
                            st.text("(No permitido)")
                    
                    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════
    # TAB 2: CREAR USUARIO
    # ═══════════════════════════════════════════════════════════════
    with tab2:
        st.subheader("Crear Nuevo Usuario")
        
        with st.form("crear_usuario_form", clear_on_submit=True):
            col_form1, col_form2 = st.columns(2)
            
            with col_form1:
                nuevo_username = st.text_input(
                    "Nombre de usuario",
                    placeholder="Ej: curador6",
                    help="Solo letras, números y guión bajo. Mínimo 3 caracteres"
                )
                
                nuevo_password = st.text_input(
                    "Contraseña",
                    type="password",
                    placeholder="Mínimo 4 caracteres",
                    help="La contraseña debe tener al menos 4 caracteres"
                )
            
            with col_form2:
                confirmar_password = st.text_input(
                    "Confirmar contraseña",
                    type="password"
                )
                
                nuevo_rol = st.selectbox(
                    "Rol",
                    ["curador", "comite"],
                    format_func=lambda x: "🎭 Curador" if x == "curador" else "🏛️ Comité"
                )
            
            submitted = st.form_submit_button("➕ Crear Usuario", type="primary", use_container_width=True)
            
            if submitted:
                # Validaciones
                if not nuevo_username or not nuevo_password:
                    st.error("⚠️ Complete todos los campos")
                elif nuevo_password != confirmar_password:
                    st.error("⚠️ Las contraseñas no coinciden")
                else:
                    # Crear usuario
                    exito, error, user_id = UsuarioModel.crear_usuario_completo(
                        nuevo_username,
                        nuevo_password,
                        nuevo_rol
                    )
                    
                    if exito:
                        LogModel.registrar_log(
                            st.session_state.usuario,
                            "USUARIO_CREADO",
                            f"Nuevo usuario: {nuevo_username} (Rol: {nuevo_rol})"
                        )
                        st.success(f"✅ Usuario '{nuevo_username}' creado exitosamente")
                        st.balloons()
                    else:
                        st.error(f"❌ {error}")
    
    # ═══════════════════════════════════════════════════════════════
    # TAB 3: CAMBIAR CONTRASEÑA
    # ═══════════════════════════════════════════════════════════════
    with tab3:
        st.subheader("Cambiar Contraseña de Usuario")
        
        usuarios_activos = UsuarioModel.obtener_todos(incluir_inactivos=False)
        
        if not usuarios_activos:
            st.warning("No hay usuarios activos")
        else:
            with st.form("cambiar_password_form"):
                usuario_seleccionado = st.selectbox(
                    "Seleccionar usuario",
                    [u['username'] for u in usuarios_activos]
                )
                
                col_pass1, col_pass2 = st.columns(2)
                
                with col_pass1:
                    nueva_password = st.text_input(
                        "Nueva contraseña",
                        type="password",
                        placeholder="Mínimo 4 caracteres"
                    )
                
                with col_pass2:
                    confirmar_nueva = st.text_input(
                        "Confirmar nueva contraseña",
                        type="password"
                    )
                
                submitted_pass = st.form_submit_button("🔑 Cambiar Contraseña", type="primary", use_container_width=True)
                
                if submitted_pass:
                    if not nueva_password:
                        st.error("⚠️ Ingrese la nueva contraseña")
                    elif nueva_password != confirmar_nueva:
                        st.error("⚠️ Las contraseñas no coinciden")
                    else:
                        exito, error = UsuarioModel.actualizar_password(
                            usuario_seleccionado,
                            nueva_password
                        )
                        
                        if exito:
                            LogModel.registrar_log(
                                st.session_state.usuario,
                                "PASSWORD_CAMBIADA",
                                f"Usuario: {usuario_seleccionado}"
                            )
                            st.success(f"✅ Contraseña actualizada para '{usuario_seleccionado}'")
                            st.balloons()
                        else:
                            st.error(f"❌ {error}")
    
    # ═══════════════════════════════════════════════════════════════
    # TAB 4: EDITAR USUARIO
    # ═══════════════════════════════════════════════════════════════
    with tab4:
        st.subheader("Editar Nombre de Usuario")
        
        usuarios_todos = UsuarioModel.obtener_todos(incluir_inactivos=True)
        
        if not usuarios_todos:
            st.warning("No hay usuarios registrados")
        else:
            with st.form("actualizar_usuarios_form"):
                usuario_seleccionado = st.selectbox(
                    "Seleccionar usuario",
                    [u['username'] for u in usuarios_todos]
                )
                
                nuevo_name = st.text_input(
                    "Nuevo nombre de usuario",
                    placeholder="Ej: curador_nuevo",
                    help="Solo letras, números y guión bajo. Mínimo 3 caracteres"
                )
                
                submitted_update = st.form_submit_button("✏️ Actualizar Usuario", type="primary", use_container_width=True)
                
                if submitted_update:
                    if not nuevo_name:
                        st.error("⚠️ Ingrese el nuevo nombre de usuario")
                    elif nuevo_name == usuario_seleccionado:
                        st.warning("⚠️ El nuevo nombre es igual al actual")
                    else:
                        exito, error = UsuarioModel.actualizar_nombre_usuario(
                            usuario_seleccionado,
                            nuevo_name
                        )
                        
                        if exito:
                            LogModel.registrar_log(
                                st.session_state.usuario,
                                "USUARIO_ACTUALIZADO",
                                f"Usuario: {usuario_seleccionado} → {nuevo_name}"
                            )
                            st.success(f"✅ Usuario '{usuario_seleccionado}' actualizado a '{nuevo_name}'")
                            st.balloons()
                        else:
                            st.error(f"❌ {error}")
