"""
Vista de la interfaz para Curadores
ACTUALIZADO: Evaluación dinámica por fichas
"""
import streamlit as st
import pandas as pd
import logging
from datetime import datetime
from src.config import config
from src.database.models import GrupoModel, EvaluacionModel, LogModel, AspectoModel
from src.utils.validators import validar_codigo_grupo, validar_observacion

logger = logging.getLogger(__name__)


@st.cache_data
def cargar_grupos_excel():
    """Carga el catálogo de grupos desde Excel con cache"""
    try:
        df = pd.read_excel(config.excel_path)
        logger.info(f"Grupos cargados desde Excel: {len(df)}")
        return df
    except FileNotFoundError:
        st.error(f"⚠️ Archivo no encontrado: {config.excel_path}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error cargando Excel: {e}")
        st.error(f"❌ Error cargando datos: {str(e)}")
        return pd.DataFrame()


def bloque_aspecto(dimension_nombre: str, aspecto_nombre: str, key_prefix: str):
    """
    Renderiza un bloque de evaluación para un aspecto individual
    
    Args:
        dimension_nombre: Nombre de la dimensión padre
        aspecto_nombre: Nombre del aspecto a evaluar
        key_prefix: Prefijo único para las claves de widgets
        
    Returns:
        Tupla (resultado, observacion)
    """
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
        <p style="margin: 0; color: #666; font-size: 13px;"><b>{dimension_nombre}</b></p>
        <p style="margin: 5px 0 0 0; font-size: 16px; font-weight: bold;">{aspecto_nombre}</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_resultado, col_obs = st.columns([1, 3])
    
    # Columna 1: Resultado
    with col_resultado:
        st.markdown("**Calificación:**")
        resultado = st.selectbox(
            "Seleccione",
            [2, 1, 0],
            key=f"res_{key_prefix}",
            format_func=lambda x: {
                2: "🟢 Fortaleza",
                1: "🟡 Oportunidad",
                0: "🔴 Riesgo"
            }[x],
            label_visibility="collapsed"
        )
    
    # Columna 2: Observación
    with col_obs:
        st.markdown("**Observación cualitativa:**")
        observacion = st.text_area(
            "",
            height=50,
            key=f"obs_{key_prefix}",
            placeholder=f"Describa lo observado específicamente para '{aspecto_nombre}'...",
            label_visibility="collapsed"
        )
        
        # Validación en tiempo real
        if observacion:
            valido, error = validar_observacion(observacion)
            if not valido:
                st.error(f"⚠️ {error}")
            else:
                st.success(f"✓ {len(observacion)} caracteres")
    
    return resultado, observacion


def mostrar_vista_curador():
    """Renderiza la vista completa del curador"""
    # ============================================================
    # Encabezado
    # ============================================================
    col1, col2, col3 = st.columns([0.8, 4, 1])
    with col1:
        st.image("assets/CDB_EMPRESA_ASSETS.svg", width=200, clamp=True)
    with col2:
        st.markdown(f"""
            <div>
                <h1 style="font-size:24px;">Ficha de Observación Cualitativa 2026</h1>
                <p style=" padding: 0; margin: 0;">
                    <b>Evento:</b> {config.nombre_evento}
                </p>
            </div>
            """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div>  
                <p style="text-align:center; padding: 20px; margin: 0;">
                    <b>Curador:</b> {st.session_state.usuario}
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="gradient-bar"></div>', unsafe_allow_html=True) 
    st.markdown("<div style='margin:0;'>" \
    "<p style='text-align:right; font-size:14px; color: gray; margin: 0;'>" \
    "Fecha de acceso: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + \
    "</p></div>", unsafe_allow_html=True)
    
    col1_global, col2_global, col3_global = st.columns([1, 6, 1])
    with col2_global:
        # Cargar catálogo de grupos
        df_grupos = cargar_grupos_excel()
        
        if df_grupos.empty:
            st.warning("⚠️ No se pudo cargar el catálogo de grupos. Contacte al administrador.")
            st.stop()
        
        # Sección: Búsqueda de grupo
        st.subheader("🔍 Búsqueda de Grupo")
        
        col_busq1, col_busq2 = st.columns([2, 1])
        
        with col_busq1:
            id_busqueda = st.text_input(
                "Ingrese el código del grupo:",
                placeholder="P123",
                help="Ingrese el código tal como aparece en su listado"
            )
        
        with col_busq2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔍 Buscar", type="primary", use_container_width=True):
                if id_busqueda:
                    st.rerun()
        
        # Buscar grupo
        grupo = None
        if id_busqueda:
            # Validar código
            valido, codigo_limpio, error = validar_codigo_grupo(id_busqueda)
            
            if not valido:
                st.error(f"❌ {error}")
                st.stop()
            
            # Buscar en el dataframe
            resultado = df_grupos[df_grupos['Codigo'].astype(str).str.upper() == codigo_limpio]
            
            # Si no encuentra, intentar búsqueda parcial
            if resultado.empty:
                resultado = df_grupos[df_grupos['Codigo'].astype(str).str.contains(codigo_limpio, case=False, na=False)]
            
            if resultado.empty:
                st.error(f"❌ Grupo no encontrado: {codigo_limpio}")
                st.info("💡 Verifique que el código sea correcto")
                
                # Mostrar sugerencias
                with st.expander("Ver todos los códigos disponibles"):
                    st.dataframe(
                        df_grupos[['Codigo', 'Nombre_Propuesta']],
                        use_container_width=True
                    )
                st.stop()
            else:
                grupo = resultado.iloc[0]
                st.success(f"✅ Grupo encontrado: {grupo['Nombre_Propuesta']}")
        else:
            st.info("👆 Ingrese un código de grupo para comenzar la evaluación")
            st.stop()
        
        # ============================================================
        # NUEVO: Obtener información completa del grupo incluyendo ficha
        # ============================================================
        grupo_db = GrupoModel.obtener_por_codigo(str(grupo['Codigo']))
        
        if not grupo_db:
            st.error("❌ Grupo no encontrado en la base de datos")
            st.info("💡 El grupo debe estar sincronizado desde Administración")
            st.stop()
        
        # Verificar que el grupo tenga ficha asignada
        if not grupo_db.get('ficha_id'):
            st.error("❌ Este grupo no tiene una ficha de evaluación asignada")
            st.info("💡 Contacte al administrador para asignar una ficha a este grupo")
            
            with st.expander("ℹ️ Más información"):
                st.markdown("""
                **¿Qué significa esto?**
                
                Cada grupo debe tener asignada una ficha de evaluación que determina 
                qué dimensiones y aspectos se deben evaluar.
                
                **¿Cómo se soluciona?**
                
                1. El administrador debe ir a: **Administración → Sincronizar Grupos**
                2. Asegurarse de que el archivo Excel tenga la columna "Ficha" con el código correcto
                3. Ejecutar sincronización
                
                **Fichas disponibles:**
                - CONGO, GARABATO, CUMBIA, MAPALE, SON_NEGRO
                - COMPARSA_TRAD, COMPARSA_FANT, DANZAS_ESP
                """)
            st.stop()
        
        ficha_id = grupo_db['ficha_id']
        ficha_nombre = grupo_db.get('ficha_nombre', 'Desconocida')
        
        # Mostrar información de la ficha
        st.info(f"📋 **Ficha asignada:** {ficha_nombre}")
        
        # ============================================================
        # NUEVO: Verificar si ya evaluó este grupo con esta ficha
        # ============================================================
        if EvaluacionModel.evaluacion_existe(st.session_state.usuario_id, str(grupo['Codigo']), ficha_id):
            st.error(f"⚠️ Ya evaluó este grupo anteriormente")
            st.info("No puede evaluar el mismo grupo más de una vez")
            
            with st.expander("Ver evaluación registrada"):
                evaluaciones_previas = EvaluacionModel.obtener_evaluacion_grupo_usuario(
                    st.session_state.usuario_id,
                    str(grupo['Codigo'])
                )
                
                if evaluaciones_previas:
                    st.markdown(f"**Fecha:** {evaluaciones_previas[0]['fecha_registro']}")
                    st.markdown(f"**Total aspectos evaluados:** {len(evaluaciones_previas)}")
                    
                    for eval in evaluaciones_previas:
                        resultado_emoji = {0: '🔴', 1: '🟡', 2: '🟢'}[eval['resultado']]
                        st.markdown(f"- {resultado_emoji} **{eval['aspecto_nombre']}**: {eval['observacion'][:50]}...")
            
            st.stop()
        
        st.markdown("---")
        
        # Datos del grupo
        st.subheader("📋 Datos del Grupo")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.text_input("Código", value=grupo['Codigo'], disabled=True)
            st.text_input("Modalidad", value=grupo['Modalidad'], disabled=True)
        
        with col2:
            st.text_input("Tipo", value=grupo['Tipo'], disabled=True)
            st.text_input("Tamaño", value=grupo.get('Tamaño', 'N/A'), disabled=True)
        
        with col3:
            st.text_input("Naturaleza", value=grupo['Naturaleza'], disabled=True)
            st.text_input("Nombre de la Propuesta", value=grupo['Nombre_Propuesta'], disabled=True)
        
        st.info(f"🎭 **Ahora se presenta:** '{grupo['Nombre_Propuesta']}'")
        
        st.markdown("---")
        
        # Formulario de evaluación
        st.subheader("📝 Evaluación de la Ficha")
        
        # ============================================================
        # NUEVO: Obtener aspectos según la ficha del grupo
        # ============================================================
        aspectos_por_dimension = AspectoModel.obtener_por_ficha(ficha_id)
        
        if not aspectos_por_dimension:
            st.error("❌ No se pudieron cargar los aspectos de evaluación para esta ficha")
            st.info("💡 Contacte al administrador para configurar las dimensiones de esta ficha")
            
            with st.expander("ℹ️ Información técnica"):
                st.markdown(f"""
                **Ficha ID:** {ficha_id}  
                **Ficha Nombre:** {ficha_nombre}
                
                El administrador debe ir a:
                **Gestión de Fichas → Configurar Fichas** y asignar dimensiones a esta ficha.
                """)
            st.stop()
        
        # Contar total de aspectos a evaluar
        total_aspectos = sum(len(d['aspectos']) for d in aspectos_por_dimension.values())
        st.caption(f"📊 Esta ficha requiere evaluar **{total_aspectos} aspectos** distribuidos en **{len(aspectos_por_dimension)} dimensiones**")
        
        with st.form("formulario_evaluacion", clear_on_submit=False):
            evaluaciones = []  # Lista de tuplas (aspecto_id, resultado, observacion)
            
            # Iterar sobre cada dimensión de la ficha
            for dim_id, dim_data in sorted(aspectos_por_dimension.items(), key=lambda x: x[1]['dimension']['orden']):
                dimension = dim_data['dimension']
                aspectos = dim_data['aspectos']
                
                if not aspectos:
                    continue  # Saltar dimensiones sin aspectos
                
                # Mostrar título de dimensión
                st.markdown(f"""
                <div class="dimension-box" style="background: linear-gradient(135deg, #FCAB60 0%, #08A114 100%); 
                     color: white; padding: 15px; border-radius: 10px; margin: 20px 0 15px 0;">
                    <h3 style="margin: 0; font-size: 18px;">{dimension['nombre']}</h3>
                    <p style="margin: 5px 0 0 0; font-size: 13px; opacity: 0.9;">{len(aspectos)} aspectos a evaluar</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Evaluar cada aspecto de esta dimensión
                for aspecto in aspectos:
                    resultado, observacion = bloque_aspecto(
                        dimension_nombre=dimension['nombre'],
                        aspecto_nombre=aspecto['nombre'],
                        key_prefix=f"asp_{aspecto['id']}"
                    )
                    evaluaciones.append((aspecto['id'], resultado, observacion))
            
            st.markdown("---")
            
            # Información de resumen antes de guardar
            st.info(f"📝 Está a punto de registrar **{len(evaluaciones)} evaluaciones** para el grupo **{grupo['Nombre_Propuesta']}**")
            
            # Botones
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            
            with col_btn2:
                submitted = st.form_submit_button(
                    "✅ REGISTRAR EVALUACIÓN",
                    type="primary",
                    use_container_width=True
                )
            
            if submitted:
                # Validar que todas las observaciones estén completas
                errores = []
                
                for i, (aspecto_id, resultado, observacion) in enumerate(evaluaciones):
                    valido, error = validar_observacion(observacion)
                    if not valido:
                        # Obtener nombre del aspecto para el mensaje
                        aspecto_nombre = None
                        for dim_data in aspectos_por_dimension.values():
                            for asp in dim_data['aspectos']:
                                if asp['id'] == aspecto_id:
                                    aspecto_nombre = asp['nombre']
                                    break
                            if aspecto_nombre:
                                break
                        
                        errores.append(f"**{aspecto_nombre}:** {error}")
                
                if errores:
                    st.error("❌ Complete correctamente todas las observaciones:")
                    for error in errores:
                        st.markdown(f"• {error}")
                else:
                    # Guardar evaluaciones
                    try:
                        exito = True
                        evaluaciones_guardadas = 0
                        
                        # Mostrar progreso
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for idx, (aspecto_id, resultado, observacion) in enumerate(evaluaciones):
                            # Actualizar progreso
                            progress = (idx + 1) / len(evaluaciones)
                            progress_bar.progress(progress)
                            status_text.text(f"Guardando evaluación {idx + 1} de {len(evaluaciones)}...")
                            
                            # ============================================================
                            # NUEVO: Incluir ficha_id al crear evaluación
                            # ============================================================
                            eval_id = EvaluacionModel.crear_evaluacion(
                                usuario_id=st.session_state.usuario_id,
                                codigo_grupo=str(grupo['Codigo']),
                                ficha_id=ficha_id,  # ← NUEVO PARÁMETRO
                                aspecto_id=aspecto_id,
                                resultado=resultado,
                                observacion=observacion
                            )
                            
                            if eval_id:
                                evaluaciones_guardadas += 1
                            else:
                                exito = False
                                logger.error(f"Error guardando evaluación para aspecto {aspecto_id}")
                                break
                        
                        # Limpiar barra de progreso
                        progress_bar.empty()
                        status_text.empty()
                        
                        if exito:
                            # Registrar log
                            LogModel.registrar_log(
                                usuario=st.session_state.usuario,
                                accion="EVALUACION_CREADA",
                                detalle=f"Grupo: {grupo['Codigo']} - {grupo['Nombre_Propuesta']} | Ficha: {ficha_nombre} | {evaluaciones_guardadas} aspectos"
                            )
                            
                            st.success(f"✅ Evaluación guardada exitosamente")
                            st.info(f"📊 Se registraron **{evaluaciones_guardadas} aspectos** evaluados para el grupo **{grupo['Nombre_Propuesta']}**")
                            st.balloons()
                            st.session_state.evaluacion_guardada = True
                        else:
                            st.error(f"❌ Error al guardar la evaluación. Se guardaron {evaluaciones_guardadas} de {len(evaluaciones)} aspectos.")
                            st.warning("⚠️ Contacte al administrador con este mensaje de error")
                            
                    except Exception as e:
                        logger.exception(f"Error guardando evaluación: {e}")
                        st.error(f"❌ Error crítico: {str(e)}")
                        st.info("💡 Intente nuevamente. Si el problema persiste, contacte al administrador.")
        
        # Botón para evaluar otro grupo (FUERA del formulario)
        if 'evaluacion_guardada' in st.session_state and st.session_state.evaluacion_guardada:
            st.markdown("---")
            
            col_nuevo1, col_nuevo2, col_nuevo3 = st.columns([1, 2, 1])
            
            with col_nuevo2:
                if st.button("➡️ Evaluar otro grupo", type="primary", use_container_width=True):
                    st.session_state.evaluacion_guardada = False
                    st.rerun()
        
        # Información adicional
        with st.expander("ℹ️ Guía de Evaluación"):
            st.markdown("""
            ### 🎯 Criterios de Calificación
            
            **🟢 Fortaleza Patrimonial (2 puntos)**
            - Cumplimiento sobresaliente del aspecto evaluado
            - Evidencia clara, consistente y bien ejecutada
            - Práctica consolidada y culturalmente pertinente
            - Transmite efectivamente el valor patrimonial
            
            **🟡 Oportunidad de Mejora (1 punto)**
            - Cumplimiento parcial del aspecto
            - Evidencia de intención pero con elementos por fortalecer
            - Práctica en proceso de consolidación
            - Requiere ajustes para alcanzar su potencial patrimonial
            
            **🔴 Riesgo Patrimonial (0 puntos)**
            - Incumplimiento del aspecto evaluado
            - Ausencia de elementos fundamentales
            - Práctica que requiere intervención urgente
            - Riesgo de pérdida o distorsión del valor patrimonial
            
            ---
            
            ### 📝 Guía para Observaciones
            
            Las observaciones deben ser:
            
            - **Específicas:** Mencione qué observó concretamente en este aspecto
            - **Descriptivas:** Describa la situación sin juicios de valor excesivos
            - **Constructivas:** Oriente sobre qué mantener o mejorar
            - **Enfocadas:** Cada observación debe referirse únicamente al aspecto que está evaluando
            - **Fundamentadas:** Base sus observaciones en evidencia concreta de la presentación
            
            **Requisitos técnicos:**
            - Mínimo: 5 caracteres por observación
            - Recomendado: 50-200 caracteres para una evaluación completa
            - Evite observaciones genéricas como "bien", "mal", "regular"
            
            ---
            
            ### 💡 Consejos Prácticos
            
            1. **Tome notas durante la presentación** de cada aspecto específico
            2. **Sea objetivo** y base sus evaluaciones en criterios patrimoniales
            3. **Sea coherente** en sus calificaciones entre diferentes grupos
            4. **Documente lo positivo y lo mejorable** en sus observaciones
            5. **Revise antes de guardar** que todas las observaciones estén completas
            
            ---
            
            ### 🎭 Sobre las Fichas de Evaluación
            
            Cada grupo tiene asignada una ficha específica según su modalidad y tipo.
            Las fichas determinan qué dimensiones y aspectos se evalúan, adaptándose
            a las características particulares de cada expresión cultural.
            
            **Ficha actual:** {ficha_nombre}  
            **Aspectos a evaluar:** {total_aspectos}  
            
            """.format(
                ficha_nombre=ficha_nombre,
                total_aspectos=total_aspectos,
                len=len
            ))