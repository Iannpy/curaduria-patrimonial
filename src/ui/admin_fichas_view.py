"""
Vista de administración de fichas, dimensiones y aspectos
Sistema CRUD completo para gestión patrimonial
"""
import streamlit as st
import pandas as pd
import logging
from typing import List, Dict
from src.database.models import (
    FichaModel, DimensionModel, AspectoModel, 
    FichaDimensionModel, LogModel
)

logger = logging.getLogger(__name__)


def mostrar_gestion_fichas():
    """Punto de entrada principal para la gestión de fichas"""
    
    st.header("🎭 Gestión de Fichas de Evaluación")
    st.caption("Administración completa del sistema de fichas patrimoniales")
    
    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Fichas",
        "📐 Dimensiones", 
        "✅ Aspectos",
        "🔗 Configurar Fichas"
    ])
    
    with tab1:
        gestionar_fichas()
    
    with tab2:
        gestionar_dimensiones()
    
    with tab3:
        gestionar_aspectos()
    
    with tab4:
        configurar_ficha_dimensiones()


# ═══════════════════════════════════════════════════════════════════
# TAB 1: GESTIÓN DE FICHAS
# ═══════════════════════════════════════════════════════════════════

def gestionar_fichas():
    """Gestión CRUD de fichas"""
    
    st.subheader("Gestión de Fichas")
    
    # Cargar fichas existentes
    fichas = FichaModel.obtener_todas()
    
    # Mostrar fichas existentes
    if fichas:
        st.markdown("### 📋 Fichas Existentes")
        
        for ficha in fichas:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
                
                with col1:
                    st.markdown(f"**`{ficha['codigo']}`**")
                
                with col2:
                    st.markdown(f"{ficha['nombre']}")
                
                with col3:
                    # Contar dimensiones asignadas
                    dims = FichaDimensionModel.obtener_dimensiones_de_ficha(ficha['id'])
                    st.caption(f"📐 {len(dims)} dims")
                
                with col4:
                    if st.button("🗑️", key=f"del_ficha_{ficha['id']}", help="Eliminar ficha"):
                        exito, error = FichaModel.eliminar_ficha(ficha['id'])
                        if exito:
                            LogModel.registrar_log(
                                st.session_state.usuario,
                                "FICHA_ELIMINADA",
                                f"Ficha: {ficha['codigo']}"
                            )
                            st.success("Ficha eliminada")
                            st.rerun()
                        else:
                            st.error(f"Error: {error}")
                
                # Mostrar descripción si existe
                if ficha.get('descripcion'):
                    st.caption(f"💬 {ficha['descripcion']}")
                
                st.markdown("---")
    else:
        st.info("No hay fichas registradas todavía")
    
    # Formulario para crear nueva ficha
    st.markdown("### ➕ Crear Nueva Ficha")
    
    with st.form("crear_ficha_form", clear_on_submit=True):
        col_form1, col_form2 = st.columns(2)
        
        with col_form1:
            nuevo_codigo = st.text_input(
                "Código de Ficha",
                placeholder="Ej: CUMBIA",
                help="Código único para identificar la ficha (sin espacios, mayúsculas)"
            )
        
        with col_form2:
            nuevo_nombre = st.text_input(
                "Nombre de Ficha",
                placeholder="Ej: Ficha Cumbia",
                help="Nombre descriptivo de la ficha"
            )
        
        nueva_descripcion = st.text_area(
            "Descripción (opcional)",
            placeholder="Describe el propósito o alcance de esta ficha...",
            height=80
        )
        
        submitted = st.form_submit_button("➕ Crear Ficha", type="primary", use_container_width=True)
        
        if submitted:
            if not nuevo_codigo or not nuevo_nombre:
                st.error("⚠️ El código y el nombre son obligatorios")
            else:
                # Validar código (solo mayúsculas, números y guion bajo)
                import re
                if not re.match(r'^[A-Z0-9_]+$', nuevo_codigo):
                    st.error("⚠️ El código solo puede contener letras mayúsculas, números y guión bajo")
                else:
                    ficha_id = FichaModel.crear_ficha(nuevo_codigo, nuevo_nombre, nueva_descripcion)
                    
                    if ficha_id:
                        LogModel.registrar_log(
                            st.session_state.usuario,
                            "FICHA_CREADA",
                            f"Ficha: {nuevo_codigo} - {nuevo_nombre}"
                        )
                        st.success(f"✅ Ficha '{nuevo_nombre}' creada exitosamente")
                        st.rerun()
                    else:
                        st.error("❌ Error al crear la ficha (posiblemente el código ya existe)")


# ═══════════════════════════════════════════════════════════════════
# TAB 2: GESTIÓN DE DIMENSIONES
# ═══════════════════════════════════════════════════════════════════

def gestionar_dimensiones():
    """Gestión CRUD de dimensiones"""
    
    st.subheader("Gestión de Dimensiones")
    
    # Cargar dimensiones existentes
    dimensiones = DimensionModel.obtener_todas()
    
    # Mostrar dimensiones existentes
    if dimensiones:
        st.markdown("### 📐 Dimensiones Existentes")
        
        for dim in dimensiones:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([1, 2, 4, 1, 1])
                
                with col1:
                    st.markdown(f"**`{dim['codigo']}`**")
                
                with col2:
                    st.caption(f"Orden: {dim['orden']}")
                
                with col3:
                    st.markdown(f"{dim['nombre']}")
                
                with col4:
                    # Contar aspectos
                    aspectos = AspectoModel.obtener_por_dimension(dim['id'])
                    st.caption(f"✅ {len(aspectos)} asp.")
                
                with col5:
                    if st.button("🗑️", key=f"del_dim_{dim['id']}", help="Eliminar dimensión"):
                        exito, error = DimensionModel.eliminar_dimension(dim['id'])
                        if exito:
                            LogModel.registrar_log(
                                st.session_state.usuario,
                                "DIMENSION_ELIMINADA",
                                f"Dimensión: {dim['codigo']}"
                            )
                            st.success("Dimensión eliminada")
                            st.rerun()
                        else:
                            st.error(f"Error: {error}")
                
                # Mostrar descripción si existe
                if dim.get('descripcion'):
                    st.caption(f"💬 {dim['descripcion']}")
                
                # Mostrar aspectos
                aspectos = AspectoModel.obtener_por_dimension(dim['id'])
                if aspectos:
                    with st.expander(f"Ver aspectos de {dim['codigo']} ({len(aspectos)})"):
                        for asp in aspectos:
                            st.markdown(f"• {asp['nombre']}")
                
                st.markdown("---")
    else:
        st.info("No hay dimensiones registradas todavía")
    
    # Formulario para crear nueva dimensión
    st.markdown("### ➕ Crear Nueva Dimensión")
    
    with st.form("crear_dimension_form", clear_on_submit=True):
        col_form1, col_form2, col_form3 = st.columns([2, 3, 1])
        
        with col_form1:
            nuevo_codigo_dim = st.text_input(
                "Código",
                placeholder="Ej: DIM4",
                help="Código único (ej: DIM4, DIM5)"
            )
        
        with col_form2:
            nuevo_nombre_dim = st.text_input(
                "Nombre",
                placeholder="Ej: Dimensión 4 - Impacto Social"
            )
        
        with col_form3:
            nuevo_orden = st.number_input(
                "Orden",
                min_value=1,
                value=len(dimensiones) + 1 if dimensiones else 1,
                help="Orden de aparición"
            )
        
        nueva_descripcion_dim = st.text_area(
            "Descripción (opcional)",
            height=60
        )
        
        submitted_dim = st.form_submit_button("➕ Crear Dimensión", type="primary", use_container_width=True)
        
        if submitted_dim:
            if not nuevo_codigo_dim or not nuevo_nombre_dim:
                st.error("⚠️ El código y el nombre son obligatorios")
            else:
                import re
                if not re.match(r'^[A-Z0-9_]+$', nuevo_codigo_dim):
                    st.error("⚠️ El código solo puede contener letras mayúsculas, números y guión bajo")
                else:
                    dim_id = DimensionModel.crear_dimension(
                        nuevo_codigo_dim, 
                        nuevo_nombre_dim, 
                        nueva_descripcion_dim,
                        nuevo_orden
                    )
                    
                    if dim_id:
                        LogModel.registrar_log(
                            st.session_state.usuario,
                            "DIMENSION_CREADA",
                            f"Dimensión: {nuevo_codigo_dim} - {nuevo_nombre_dim}"
                        )
                        st.success(f"✅ Dimensión '{nuevo_nombre_dim}' creada exitosamente")
                        st.rerun()
                    else:
                        st.error("❌ Error al crear la dimensión")


# ═══════════════════════════════════════════════════════════════════
# TAB 3: GESTIÓN DE ASPECTOS
# ═══════════════════════════════════════════════════════════════════

def gestionar_aspectos():
    """Gestión CRUD de aspectos"""
    
    st.subheader("Gestión de Aspectos")
    
    # Cargar dimensiones para el selector
    dimensiones = DimensionModel.obtener_todas()
    
    if not dimensiones:
        st.warning("⚠️ Primero debes crear dimensiones antes de crear aspectos")
        return
    
    # Selector de dimensión
    dim_seleccionada = st.selectbox(
        "Filtrar por dimensión:",
        ["Todas"] + [f"{d['codigo']} - {d['nombre']}" for d in dimensiones]
    )
    
    # Mostrar aspectos
    st.markdown("### ✅ Aspectos Existentes")
    
    if dim_seleccionada == "Todas":
        aspectos = AspectoModel.obtener_todos()
    else:
        dim_codigo = dim_seleccionada.split(" - ")[0]
        dim = next((d for d in dimensiones if d['codigo'] == dim_codigo), None)
        if dim:
            aspectos = AspectoModel.obtener_por_dimension(dim['id'])
        else:
            aspectos = []
    
    if aspectos:
        for asp in aspectos:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 5, 1, 1])
                
                with col1:
                    if 'dimension_codigo' in asp:
                        st.caption(f"📐 {asp['dimension_codigo']}")
                    else:
                        # Buscar dimensión
                        dim = next((d for d in dimensiones if d['id'] == asp['dimension_id']), None)
                        if dim:
                            st.caption(f"📐 {dim['codigo']}")
                
                with col2:
                    st.markdown(f"**{asp['nombre']}**")
                
                with col3:
                    st.caption(f"Orden: {asp['orden']}")
                
                with col4:
                    if st.button("🗑️", key=f"del_asp_{asp['id']}", help="Eliminar aspecto"):
                        exito, error = AspectoModel.eliminar_aspecto(asp['id'])
                        if exito:
                            LogModel.registrar_log(
                                st.session_state.usuario,
                                "ASPECTO_ELIMINADO",
                                f"Aspecto: {asp['nombre']}"
                            )
                            st.success("Aspecto eliminado")
                            st.rerun()
                        else:
                            st.error(f"Error: {error}")
                
                if asp.get('descripcion'):
                    st.caption(f"💬 {asp['descripcion']}")
                
                st.markdown("---")
    else:
        st.info("No hay aspectos para mostrar")
    
    # Formulario para crear nuevo aspecto
    st.markdown("### ➕ Crear Nuevo Aspecto")
    
    with st.form("crear_aspecto_form", clear_on_submit=True):
        # Selector de dimensión
        dim_opciones = {f"{d['codigo']} - {d['nombre']}": d['id'] for d in dimensiones}
        dim_seleccion = st.selectbox(
            "Dimensión",
            list(dim_opciones.keys()),
            help="Selecciona la dimensión a la que pertenece este aspecto"
        )
        
        col_asp1, col_asp2 = st.columns([4, 1])
        
        with col_asp1:
            nuevo_nombre_asp = st.text_input(
                "Nombre del Aspecto",
                placeholder="Ej: Coreografía / pasos básicos"
            )
        
        with col_asp2:
            # Contar aspectos existentes de esa dimensión para sugerir orden
            dim_id_seleccionada = dim_opciones[dim_seleccion]
            aspectos_existentes = AspectoModel.obtener_por_dimension(dim_id_seleccionada)
            
            nuevo_orden_asp = st.number_input(
                "Orden",
                min_value=1,
                value=len(aspectos_existentes) + 1
            )
        
        nueva_descripcion_asp = st.text_area(
            "Descripción (opcional)",
            placeholder="Describe qué se evalúa en este aspecto...",
            height=60
        )
        
        submitted_asp = st.form_submit_button("➕ Crear Aspecto", type="primary", use_container_width=True)
        
        if submitted_asp:
            if not nuevo_nombre_asp:
                st.error("⚠️ El nombre del aspecto es obligatorio")
            else:
                asp_id = AspectoModel.crear_aspecto(
                    dim_id_seleccionada,
                    nuevo_nombre_asp,
                    nueva_descripcion_asp,
                    nuevo_orden_asp
                )
                
                if asp_id:
                    LogModel.registrar_log(
                        st.session_state.usuario,
                        "ASPECTO_CREADO",
                        f"Aspecto: {nuevo_nombre_asp} (Dimensión: {dim_seleccion.split(' - ')[0]})"
                    )
                    st.success(f"✅ Aspecto '{nuevo_nombre_asp}' creado exitosamente")
                    st.rerun()
                else:
                    st.error("❌ Error al crear el aspecto")


# ═══════════════════════════════════════════════════════════════════
# TAB 4: CONFIGURAR FICHAS (Asignar dimensiones a fichas)
# ═══════════════════════════════════════════════════════════════════

def configurar_ficha_dimensiones():
    """Configuración de dimensiones por ficha"""
    
    st.subheader("🔗 Configurar Dimensiones por Ficha")
    st.caption("Asigna qué dimensiones se evaluarán en cada tipo de ficha")
    
    # Cargar fichas y dimensiones
    fichas = FichaModel.obtener_todas()
    dimensiones = DimensionModel.obtener_todas()
    
    if not fichas:
        st.warning("⚠️ Primero debes crear fichas")
        return
    
    if not dimensiones:
        st.warning("⚠️ Primero debes crear dimensiones")
        return
    
    # Selector de ficha
    ficha_opciones = {f"{f['codigo']} - {f['nombre']}": f for f in fichas}
    ficha_seleccion = st.selectbox(
        "Seleccionar Ficha:",
        list(ficha_opciones.keys())
    )
    
    ficha = ficha_opciones[ficha_seleccion]
    
    st.markdown(f"### Configuración de: **{ficha['nombre']}**")
    
    # Obtener dimensiones actuales de esta ficha
    dims_actuales = FichaDimensionModel.obtener_dimensiones_de_ficha(ficha['id'])
    dims_ids_actuales = [d['dimension_id'] for d in dims_actuales]
    
    # Mostrar dimensiones actuales
    if dims_actuales:
        st.markdown("**📐 Dimensiones Actuales:**")
        
        for dim_rel in dims_actuales:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"• {dim_rel['dimension_codigo']} - {dim_rel['dimension_nombre']}")
            
            with col2:
                st.caption(f"Orden: {dim_rel['orden']}")
            
            with col3:
                if st.button("🗑️", key=f"del_fd_{ficha['id']}_{dim_rel['dimension_id']}"):
                    exito, error = FichaDimensionModel.eliminar_dimension_de_ficha(
                        ficha['id'], 
                        dim_rel['dimension_id']
                    )
                    if exito:
                        LogModel.registrar_log(
                            st.session_state.usuario,
                            "FICHA_DIMENSION_ELIMINADA",
                            f"Ficha: {ficha['codigo']}, Dimensión: {dim_rel['dimension_codigo']}"
                        )
                        st.success("Dimensión eliminada de la ficha")
                        st.rerun()
                    else:
                        st.error(f"Error: {error}")
        
        st.markdown("---")
    else:
        st.info("Esta ficha no tiene dimensiones asignadas todavía")
    
    # Formulario para agregar dimensión a ficha
    st.markdown("### ➕ Agregar Dimensión a esta Ficha")
    
    # Filtrar dimensiones que NO están asignadas
    dims_disponibles = [d for d in dimensiones if d['id'] not in dims_ids_actuales]
    
    if not dims_disponibles:
        st.success("✅ Todas las dimensiones ya están asignadas a esta ficha")
    else:
        with st.form("agregar_dim_ficha_form", clear_on_submit=True):
            col_form1, col_form2 = st.columns([3, 1])
            
            with col_form1:
                dim_opciones_disp = {
                    f"{d['codigo']} - {d['nombre']}": d['id'] 
                    for d in dims_disponibles
                }
                dim_agregar = st.selectbox(
                    "Dimensión a agregar:",
                    list(dim_opciones_disp.keys())
                )
            
            with col_form2:
                orden_nueva = st.number_input(
                    "Orden",
                    min_value=1,
                    value=len(dims_actuales) + 1
                )
            
            submitted_fd = st.form_submit_button(
                "➕ Agregar Dimensión", 
                type="primary", 
                use_container_width=True
            )
            
            if submitted_fd:
                dim_id_agregar = dim_opciones_disp[dim_agregar]
                
                rel_id = FichaDimensionModel.asignar_dimension_a_ficha(
                    ficha['id'],
                    dim_id_agregar,
                    orden_nueva
                )
                
                if rel_id:
                    LogModel.registrar_log(
                        st.session_state.usuario,
                        "FICHA_DIMENSION_ASIGNADA",
                        f"Ficha: {ficha['codigo']}, Dimensión: {dim_agregar.split(' - ')[0]}"
                    )
                    st.success(f"✅ Dimensión '{dim_agregar}' agregada a la ficha")
                    st.rerun()
                else:
                    st.error("❌ Error al agregar la dimensión")
    
    # Vista previa de la estructura completa
    st.markdown("---")
    st.markdown("### 👁️ Vista Previa de la Ficha")
    
    if dims_actuales:
        # Obtener aspectos por ficha
        aspectos_ficha = AspectoModel.obtener_por_ficha(ficha['id'])
        
        total_aspectos = sum(len(d['aspectos']) for d in aspectos_ficha.values())
        
        st.info(f"📊 Esta ficha tiene **{len(dims_actuales)} dimensiones** con un total de **{total_aspectos} aspectos** a evaluar")
        
        for dim_data in sorted(aspectos_ficha.values(), key=lambda x: x['dimension']['orden']):
            with st.expander(f"📐 {dim_data['dimension']['nombre']} ({len(dim_data['aspectos'])} aspectos)"):
                for asp in dim_data['aspectos']:
                    st.markdown(f"✅ {asp['nombre']}")
    else:
        st.warning("⚠️ Agrega dimensiones a esta ficha para poder usarla en evaluaciones")