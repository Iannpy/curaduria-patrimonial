"""
Vista de la interfaz para el Comité
"""
import streamlit as st
import pandas as pd
import altair as alt
import logging
from src.config import config
from src.database.models import EvaluacionModel
from src.auth.authentication import crear_boton_logout
from streamlit_option_menu import option_menu

logger = logging.getLogger(__name__)


def estado_patrimonial(promedio: float) -> str:
    """
    Determina el estado patrimonial según el promedio
    
    Args:
        promedio: Promedio de calificaciones
        
    Returns:
        String con emoji y texto del estado
    """
    if promedio < config.umbrales.riesgo_max:
        return f"{config.umbrales.emoji_riesgo}"
    elif promedio < config.umbrales.mejora_max:
        return f"{config.umbrales.emoji_mejora}"
    else:
        return f"{config.umbrales.emoji_fortalecimiento}"
def mostrar_vista_comite():
    """Renderiza la vista completa del comité"""
    # Cargar evaluaciones
    df_eval = EvaluacionModel.obtener_todas_dataframe()
    

    
    # Sidebar - Navegación (ANTES del botón logout)
    with st.sidebar:
        pagina = option_menu(
            "📂 Menú de Análisis",
            [
                "Dashboard General",
                "Evaluaciones Detalladas",
                "Análisis por Grupos",
                "Análisis por Dimensión",
                "Análisis por Curador",
                "Administración",
                "Gestión de Usuarios"
            ],
            icons=[
                "bar-chart-fill",
                "table",
                "people-fill",
                "graph-up-arrow",
                "person-badge-fill",
                "gear-fill",
                "people"
            ],
            menu_icon="case-gear-fill",
            default_index=0,
            orientation="vertical",
        )
        
        crear_boton_logout()

    
    paginas_sin_evaluaciones = ["Administración", "Gestión de Usuarios"]
    
    # Si la página requiere evaluaciones y no hay, mostrar aviso
    if pagina not in paginas_sin_evaluaciones and df_eval.empty:
        st.warning("⚠️ No hay evaluaciones registradas todavía")
        st.info("Las evaluaciones aparecerán aquí una vez que los curadores comiencen a registrarlas")
        st.markdown("---")
        st.markdown("💡 **Mientras tanto, puedes:**")
        st.markdown("- Ir a **⚙️ Administración** para sincronizar grupos")
        st.markdown("- Ir a **👥 Gestión de Usuarios** para crear curadores")
        return  # ← Cambio: return en lugar de st.stop() para que el sidebar siga funcionando   
    



    # Routing según página seleccionada
    if pagina == "Dashboard General":
        mostrar_dashboard(df_eval)

    elif pagina == "Evaluaciones Detalladas":
        mostrar_evaluaciones_detalladas(df_eval)

    elif pagina == "Análisis por Grupos":
        mostrar_analisis_grupos(df_eval)

    elif pagina == "Análisis por Dimensión":
        mostrar_analisis_dimensiones(df_eval)

    elif pagina == "Análisis por Curador":
        mostrar_analisis_curadores(df_eval)

    elif pagina == "Administración":
        mostrar_panel_admin()
    elif pagina == "Gestión de Usuarios":
        mostrar_gestion_usuarios(df_eval)

def mostrar_dashboard(df_eval: pd.DataFrame):
    """Dashboard general con KPIs y gráficos principales"""
    
    st.header("📊 Dashboard General")
    st.markdown("Resumen de Evaluaciones Patrimoniales")
    
    # Calcular métricas
    df_promedios = (df_eval
        .groupby(['codigo_grupo', 'nombre_propuesta', 'modalidad'], as_index=False)
        .agg(promedio_final=('resultado', 'mean'))
    )
    
    df_promedios['estado'] = df_promedios['promedio_final'].apply(estado_patrimonial)
    
    # KPIs principales
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        grupo_evaluados = df_promedios['codigo_grupo'].nunique()

        st.markdown(f"""
            <div class="metric-card">
            <div class="dimension-title">Grupos Evaluados</div>
            <div class="metric-value">{grupo_evaluados}</div>
            </div>""",
            unsafe_allow_html=True
        )
        
    with col2:
        promedio_general = df_promedios['promedio_final'].mean()
        st.markdown(f"""
            <div class="metric-card">
            <div class="dimension-title">Promedio General</div>
            <div class="metric-value">{promedio_general:.2f}</div>
            </div>""",
            unsafe_allow_html=True
        )
    
    with col3:
        en_riesgo = (df_promedios['promedio_final'] < config.umbrales.riesgo_max).sum()
        st.markdown(f"""
            <div class="metric-card">
            <div class="dimension-title">🔴 En Riesgo</div>
            <div class="metric-value">{en_riesgo}</div>
            </div>""",
            unsafe_allow_html=True
        )
    
    with col4:
        en_mejora = ((df_promedios['promedio_final'] >= config.umbrales.riesgo_max) & 
                      (df_promedios['promedio_final'] < config.umbrales.mejora_max)).sum()
        st.markdown(f"""
            <div class="metric-card">
            <div class="dimension-title">🟡 Por mejorar</div>
            <div class="metric-value">{en_mejora}</div>
            </div>""",
            unsafe_allow_html=True
        )

    with col5:
        fortalecidos = (df_promedios['promedio_final'] >= config.umbrales.mejora_max).sum()
        st.markdown(f"""
            <div class="metric-card">
            <div class="dimension-title">🟢 Fortalecidos</div>
            <div class="metric-value">{fortalecidos}</div>
            </div>""",
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    # Gráficos principales
    
    
    """
    st.subheader("Estado Patrimonial de Grupos")
    
    estado_counts = df_promedios['estado'].value_counts().reset_index()
    estado_counts.columns = ['estado', 'cantidad']
    
    chart_estado = alt.Chart(estado_counts).mark_bar().encode(
        x=alt.X('estado:N', title='Estado Patrimonial', sort=None),
        y=alt.Y('cantidad:Q', title='Cantidad de Grupos'),
        color=alt.Color('estado:N', legend=None),
        tooltip=['estado', 'cantidad']
    ).properties(height=300)
    st.altair_chart(chart_estado, use_container_width=True)
    """
    
    st.subheader("Promedio por Modalidad")
    
    df_modalidad = (df_promedios
        .groupby('modalidad', as_index=False)
        .agg(promedio=('promedio_final', 'mean'))
        .sort_values('promedio', ascending=False)
    )
    
    chart_modalidad = alt.Chart(df_modalidad).mark_bar().encode(
        x=alt.X('promedio:Q', title='Promedio', scale=alt.Scale(domain=[0, 2])),
        y=alt.Y('modalidad:N', title='Modalidad', sort='-x'),
        color=alt.Color('promedio:Q', scale=alt.Scale(scheme='redyellowgreen'), legend=None),
        tooltip=['modalidad', alt.Tooltip('promedio:Q', format='.2f')]
    ).properties(height=200)

    st.altair_chart(chart_modalidad, use_container_width=True)  
    
    st.markdown("---")
    
    st.subheader("Entrega de congos de oro")
    seleccion_modalidad = st.selectbox("Seleccionar Modalidad:", df_promedios['modalidad'].unique())
    # usar el valor tal cual para filtrar
    seleccion_raw = seleccion_modalidad
    cantidad_modalidad = df_promedios[df_promedios['modalidad'] == seleccion_raw].shape[0]
        
    import math
    cantidad_congos = math.ceil(cantidad_modalidad * 0.15)
    
    if cantidad_modalidad == 0:
        st.warning(f"⚠️ No hay grupos en la modalidad '{seleccion_raw}'")
    else:
        seleccion_display = seleccion_raw.lower().title()
        st.subheader(f"🏆 Ganadores de Congos de Oro Modalidad {seleccion_display}")
        df_filtrado = df_promedios[df_promedios['modalidad'] == seleccion_raw]
        if cantidad_congos <= 0:
            st.info("No hay congos asignables para esta modalidad (cantidad insuficiente).")
        else:
            top_modalidad = df_filtrado.nlargest(cantidad_congos, 'promedio_final')[['nombre_propuesta', 'promedio_final', 'estado']]
            st.dataframe(
                top_modalidad.style.format({'promedio_final': '{:.2f}'}),
                hide_index=True
            )

    with st.expander("Ver todos los grupos que requieren atención ⚠️"):
        st.subheader("⚠️ Grupos que Requieren Atención")
        bottom5 = df_promedios.nsmallest(5, 'promedio_final')[['nombre_propuesta', 'promedio_final', 'estado']]
        st.dataframe(
            bottom5.style.format({'promedio_final': '{:.2f}'}),
            hide_index=True
        )


def mostrar_evaluaciones_detalladas(df_eval: pd.DataFrame):
    """Tabla detallada de todas las evaluaciones"""
    
    st.header("📋 Evaluaciones Detalladas")
    
    # Opciones de visualización
    col_opt1, col_opt2 = st.columns([3, 1])
    
    with col_opt1:
        buscar = st.text_input("🔍 Buscar", placeholder="Buscar por grupo, curador o dimensión...")
    
    with col_opt2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📥 Exportar a Excel"):
            st.info("🚧 Funcionalidad de exportación en desarrollo")
    
    # Filtrar
    df_mostrar = df_eval.copy()
    if buscar:
        df_mostrar = df_mostrar[
            df_mostrar['nombre_propuesta'].str.contains(buscar, case=False, na=False) |
            df_mostrar['curador'].str.contains(buscar, case=False, na=False) |
            df_mostrar['dimension'].str.contains(buscar, case=False, na=False)
        ]
    
    # Mostrar tabla
    st.dataframe(
        df_mostrar[[
            'curador', 'codigo_grupo', 'nombre_propuesta', 
            'modalidad', 'dimension', 'resultado', 'observacion', 'fecha_registro'
        ]].sort_values('fecha_registro', ascending=False),
        use_container_width=True,
        hide_index=True
    )
    
    st.caption(f"Total de registros: {len(df_mostrar)}")


def mostrar_analisis_grupos(df_eval: pd.DataFrame):
    """Análisis consolidado por grupos"""
    
    st.header("🎭 Análisis por Grupos")
    
    # Calcular consolidado por grupo y dimensión
    df_pivot = (df_eval
        .groupby(['codigo_grupo', 'nombre_propuesta', 'modalidad', 'dimension'], as_index=False)
        .agg(promedio_dimension=('resultado', 'mean'))
    )
    
    # Crear tabla pivote
    df_tabla = df_pivot.pivot_table(
        index=['codigo_grupo', 'nombre_propuesta', 'modalidad'],
        columns='dimension',
        values='promedio_dimension'
    ).reset_index()
    
    # Calcular promedio final
    dim_cols = [c for c in df_tabla.columns if c.startswith('Dimensión')]
    df_tabla['Promedio Final'] = df_tabla[dim_cols].mean(axis=1)
    df_tabla['Estado'] = df_tabla['Promedio Final'].apply(estado_patrimonial)
    
    # Ordenar por promedio
    df_tabla = df_tabla.sort_values('Promedio Final', ascending=False)
    
    # Mostrar tabla
    st.dataframe(
        df_tabla.style.format({
            **{col: '{:.2f}' for col in dim_cols},
            'Promedio Final': '{:.2f}'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Análisis por modalidad
    st.markdown("---")
    st.subheader("📊 Resumen por Modalidad")
    
    df_resumen_mod = (df_tabla
        .groupby('modalidad', as_index=False)
        .agg({
            'codigo_grupo': 'count',
            'Promedio Final': 'mean'
        })
        .rename(columns={'codigo_grupo': 'Cantidad', 'Promedio Final': 'Promedio'})
    )
    
    chart = alt.Chart(df_resumen_mod).mark_bar().encode(
        x=alt.X('modalidad:N', title='Modalidad'),
        y=alt.Y('Promedio:Q', title='Promedio', scale=alt.Scale(domain=[0, 2])),
        color=alt.Color('Promedio:Q', scale=alt.Scale(scheme='redyellowgreen')),
        tooltip=['modalidad', alt.Tooltip('Promedio:Q', format='.2f'), 'Cantidad']
    ).properties(height=300)
        
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(
        df_resumen_mod.style.format({'Promedio': '{:.2f}'}),
        use_container_width=True,
        hide_index=True
    )


def mostrar_analisis_dimensiones(df_eval: pd.DataFrame):
    """Análisis por dimensiones patrimoniales"""
    
    st.header("📈 Análisis por Dimensión")
    
    # Promedio por dimensión
    df_dim = (df_eval
        .groupby('dimension', as_index=False)
        .agg(
            promedio=('resultado', 'mean'),
            evaluaciones=('resultado', 'count')
        )
        .sort_values('promedio', ascending=False)
    )
    
    # Gráfico
    chart = alt.Chart(df_dim).mark_bar().encode(
        y=alt.Y('dimension:N', title='Dimensión', sort='-x'),
        x=alt.X('promedio:Q', title='Promedio', scale=alt.Scale(domain=[0, 2])),
        color=alt.Color('promedio:Q', scale=alt.Scale(scheme='redyellowgreen'), legend=None),
        tooltip=['dimension', alt.Tooltip('promedio:Q', format='.2f'), 'evaluaciones']
    ).properties(height=300)
    
    st.altair_chart(chart, use_container_width=True)
    
    # Tabla detallada
    st.dataframe(
        df_dim.style.format({'promedio': '{:.2f}'}),
        use_container_width=True,
        hide_index=True
    )


def mostrar_analisis_curadores(df_eval: pd.DataFrame):
    """Análisis por curadores"""
    
    st.header("👥 Análisis por Curador")
    
    # Estadísticas por curador
    df_cur = (df_eval
        .groupby('curador', as_index=False)
        .agg(
            grupos_evaluados=('codigo_grupo', 'nunique'),
            total_evaluaciones=('resultado', 'count'),
            promedio_otorgado=('resultado', 'mean')
        )
        .sort_values('grupos_evaluados', ascending=False)
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        chart = alt.Chart(df_cur).mark_bar().encode(
            x=alt.X('curador:N', title='Curador'),
            y=alt.Y('grupos_evaluados:Q', title='Grupos Evaluados'),
            color=alt.value('#1a9641'),
            tooltip=['curador', 'grupos_evaluados', alt.Tooltip('promedio_otorgado:Q', format='.2f')]
        ).properties(height=300)
        
        st.altair_chart(chart, use_container_width=True)
    
    with col2:
        st.dataframe(
            df_cur.style.format({'promedio_otorgado': '{:.2f}'}),
            use_container_width=True,
            hide_index=True
        )
# Agregar esta función en src/ui/comite_view.py

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
                            # Actualizar solo existentes
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
        
        if st.button("Crear Backup Ahora"):
            # Crear backup
            st.info("🚧 Funcionalidad en desarrollo")
    
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
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Grupos", total_grupos)
        
        with col2:
            st.metric("Total Evaluaciones", total_eval)
        
        with col3:
            st.metric("Curadores Activos", curadores_activos)

# ═══════════════════════════════════════════════════════════
# AGREGAR ESTA FUNCIÓN A src/ui/comite_view.py
# ═══════════════════════════════════════════════════════════

def mostrar_gestion_usuarios(df_eval: pd.DataFrame):
    """Panel de gestión completa de usuarios"""
    from src.database.models import UsuarioModel, LogModel
    import bcrypt
    
    st.header("👥 Gestión de Usuarios")
    st.caption("Administración de curadores y miembros del comité")
    st.button("🔄️ Actualizar")
    st.dataframe(df_eval.head())


    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Lista de Usuarios", "➕ Crear Usuario", "🔑 Cambiar Contraseña", "🧑‍🎨 Actualizar usuarios"])
    
    # ═══════════════════════════════════════════════════════════
    # TAB 1: LISTA DE USUARIOS
    # ═══════════════════════════════════════════════════════════
    with tab1:
        st.subheader("Usuarios del Sistema")
        
        # Cargar usuarios
        usuarios = UsuarioModel.obtener_todos(incluir_inactivos=True)
        
        if not usuarios:
            st.info("No hay usuarios registrados")
        else:
            # Tabla de usuarios
            for user in usuarios:
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 3])
                
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
                    if user['username'] != st.session_state.usuario:  # No puede eliminarse a sí mismo
                        if st.button("🗑️ Eliminar", key=f"del_{user['id']}", type="secondary", use_container_width=True):
                            num_eval = UsuarioModel.contar_evaluaciones_usuario(user['username'])
                            if num_eval > 0:
                                st.warning(f"⚠️ Este usuario tiene {num_eval} evaluaciones. ¿Eliminar de todos modos?")
                                if st.button(f"✓ Confirmar eliminación de {user['username']}", key=f"conf_{user['id']}"):
                                    exito, error = UsuarioModel.eliminar_usuario(user['username'])
                                    if exito:
                                        LogModel.registrar_log(
                                            st.session_state.usuario,
                                            "USUARIO_ELIMINADO",
                                            f"Usuario: {user['username']} ({num_eval} evaluaciones eliminadas)"
                                        )
                                        st.success("Usuario eliminado")
                                        st.rerun()
                                    else:
                                        st.error(error)
                            else:
                                exito, error = UsuarioModel.eliminar_usuario(user['username'])
                                if exito:
                                    LogModel.registrar_log(
                                        st.session_state.usuario,
                                        "USUARIO_ELIMINADO",
                                        f"Usuario: {user['username']}"
                                    )
                                    st.success("Usuario eliminado")
                                    st.rerun()
                                else:
                                    st.error(error)
                
                st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════
    # TAB 2: CREAR USUARIO
    # ═══════════════════════════════════════════════════════════
    with tab2:
        st.subheader("Crear Nuevo Usuario")
        
        with st.form("crear_usuario_form", clear_on_submit=True):
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
    
    # ═══════════════════════════════════════════════════════════
    # TAB 3: CAMBIAR CONTRASEÑA
    # ═══════════════════════════════════════════════════════════
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
                
                nueva_password = st.text_input(
                    "Nueva contraseña",
                    type="password",
                    placeholder="Mínimo 4 caracteres"
                )
                
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

    # ═══════════════════════════════════════════════════════════
    # TAB 4: ACTUALIZAR USUARIOS
    # =══════════════════════════════════════════════════════════
    with tab4:
        st.subheader("Actualizar Usuarios")

        usuarios_activos = UsuarioModel.obtener_todos(incluir_inactivos=True)

        if not usuarios_activos:
            st.warning("No hay usuarios registrados")
        else:
            with st.form("actualizar_usuarios_form"):
                usuario_seleccionado = st.selectbox(
                    "Seleccionar usuario",
                    [u['username'] for u in usuarios_activos]
                )

                nuevo_name: str = st.text_input(
                    "Nuevo nombre de usuario",
                    placeholder="Ej: curador_nuevo",
                    help="Solo letras, números y guión bajo. Mínimo 3 caracteres"
                )
                

                submitted_update = st.form_submit_button("🧑‍🎨 Actualizar Usuario", type="primary", use_container_width=True)

                if submitted_update:
                    if not nuevo_name:
                        st.error("⚠️ Ingrese el nuevo nombre de usuario")
                    else:
                        exito, error = UsuarioModel.actualizar_nombre_usuario(
                            usuario_seleccionado,
                            nuevo_name
                        )

                        if exito:
                            LogModel.registrar_log(
                                st.session_state.usuario,
                                "USUARIO_ACTUALIZADO",
                                f"Usuario: {usuario_seleccionado} a {nuevo_name}"
                            )
                            st.success(f"✅ Usuario '{usuario_seleccionado}' actualizado a '{nuevo_name}'")
                            st.balloons()
                        else:
                            st.error(f"❌ {error}")




