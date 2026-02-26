"""
Vista de Congos de Oro 
Usa rutas configurables desde config.py y detecta archivos automáticamente
"""
import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
from src.config import DATA_DIR
from .dashboard import color_gradiente

# ═══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN - Rutas dinámicas
# ═══════════════════════════════════════════════════════════════════

def obtener_rutas_bds():
    """
    Detecta automáticamente las rutas de las bases de datos
    Busca en DATA_DIR los archivos .db disponibles
    """
    data_path = Path(DATA_DIR)
    
    # Buscar archivos .db
    archivos_db = list(data_path.glob("*.db"))
    
    # Intentar identificar las BDs por nombre
    db_fin = None
    db_gran = None
    
    for archivo in archivos_db:
        nombre = archivo.stem.lower()
        if 'fin' in nombre or 'finde' in nombre or 'semana' in nombre:
            db_fin = str(archivo)
        elif 'gran' in nombre or 'parada' in nombre:
            db_gran = str(archivo)
    
    # Si no se encuentran con esos nombres, usar los dos primeros .db
    if db_fin is None or db_gran is None:
        if len(archivos_db) >= 2:
            db_fin = str(archivos_db[0])
            db_gran = str(archivos_db[1])
        elif len(archivos_db) == 1:
            # Solo hay una BD, usarla para ambos
            db_fin = str(archivos_db[0])
            db_gran = str(archivos_db[0])
    
    return db_fin, db_gran


# Obtener rutas dinámicamente
DB_FIN_SEMANA, DB_GRAN_PARADA = obtener_rutas_bds()

# Configuración de ponderaciones
PONDERACIONES = {
    "CONGO": {"fin_semana": 0.60, "gran_parada": 0.40},
    "CUMBIA": {"fin_semana": 0.60, "gran_parada": 0.40},
    "GARABATO": {"fin_semana": 0.50, "gran_parada": 0.50},
    "MAPALÉ": {"fin_semana": 0.60, "gran_parada": 0.40},
    "MAPALE": {"fin_semana": 0.60, "gran_parada": 0.40},
    "SON_DE_NEGRO": {"fin_semana": 1.00, "gran_parada": 0.00},
    "COMPARSA_TRAD": {"fin_semana": 0.60, "gran_parada": 0.40},
    "COMPARSA_FANT": {"fin_semana": 0.60, "gran_parada": 0.40},
    "DANZAS_ESP": {"fin_semana": 1.00, "gran_parada": 0.00},
    "DANZAS_REL": {"fin_semana": 1.00, "gran_parada": 0.00},
    "EXPRESIONES_I": {"fin_semana": 1.00, "gran_parada": 0.00},
}

UMBRAL_RIESGO = 0.8
UMBRAL_MEJORA = 1.6


# ═══════════════════════════════════════════════════════════════════
# FUNCIONES
# ═══════════════════════════════════════════════════════════════════

@st.cache_data
def cargar_y_consolidar_datos():
    """Carga y consolida datos de ambos eventos"""
    
    # Verificar que existan las BDs
    if DB_FIN_SEMANA is None or DB_GRAN_PARADA is None:
        st.error("❌ No se encontraron bases de datos en la carpeta data/")
        st.info(f"📂 Buscando en: {DATA_DIR}")
        return pd.DataFrame()
    
    def obtener_evaluaciones(db_path):
        """Obtiene evaluaciones de una BD"""
        if not Path(db_path).exists():
            st.warning(f"⚠️ No se encuentra: {db_path}")
            return pd.DataFrame()
        
        try:
            conn = sqlite3.connect(db_path)
            query = """
                SELECT 
                    e.codigo_grupo,
                    g.nombre_propuesta,
                    g.modalidad,
                    g.tipo,
                    g.tamano,
                    f.codigo as ficha_codigo,
                    f.nombre as ficha_nombre,
                    AVG(e.resultado) as promedio
                FROM evaluaciones e
                JOIN grupos g ON e.codigo_grupo = g.codigo
                JOIN fichas f ON e.ficha_id = f.id
                GROUP BY e.codigo_grupo, f.id
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"❌ Error leyendo {db_path}: {e}")
            return pd.DataFrame()
    
    # Cargar datos
    df_fin = obtener_evaluaciones(DB_FIN_SEMANA)
    df_gran = obtener_evaluaciones(DB_GRAN_PARADA)
    
    # Si alguna está vacía, mostrar info
    if df_fin.empty and df_gran.empty:
        st.error("❌ No se pudieron cargar datos de ninguna base de datos")
        return pd.DataFrame()
    
    if df_fin.empty:
        st.warning(f"⚠️ Base de datos vacía: {Path(DB_FIN_SEMANA).name}")
        # Usar solo Gran Parada
        df_gran['promedio_fin'] = None
        df_gran['promedio_gran'] = df_gran['promedio']
        df_gran['nota_consolidada'] = df_gran['promedio']
        df_gran['participacion'] = "Gran Parada"
        return df_gran
    
    if df_gran.empty:
        st.warning(f"⚠️ Base de datos vacía: {Path(DB_GRAN_PARADA).name}")
        # Usar solo Fin de Semana
        df_fin['promedio_fin'] = df_fin['promedio']
        df_fin['promedio_gran'] = None
        df_fin['nota_consolidada'] = df_fin['promedio']
        df_fin['participacion'] = "Fin de Semana"
        return df_fin
    
    # Consolidar ambas
    todos_codigos = set(df_fin['codigo_grupo'].unique()) | set(df_gran['codigo_grupo'].unique())
    
    resultados = []
    for codigo in todos_codigos:
        grupo_fin = df_fin[df_fin['codigo_grupo'] == codigo]
        grupo_gran = df_gran[df_gran['codigo_grupo'] == codigo]
        
        info = grupo_fin.iloc[0] if len(grupo_fin) > 0 else grupo_gran.iloc[0]
        ficha = info['ficha_codigo']
        ponderaciones = PONDERACIONES.get(ficha, {"fin_semana": 0.5, "gran_parada": 0.5})
        
        prom_fin = grupo_fin['promedio'].iloc[0] if len(grupo_fin) > 0 else None
        prom_gran = grupo_gran['promedio'].iloc[0] if len(grupo_gran) > 0 else None
        
        if prom_fin and prom_gran:
            nota_consolidada = prom_fin * ponderaciones['fin_semana'] + prom_gran * ponderaciones['gran_parada']
            participacion = "Ambos"
        elif prom_fin:
            nota_consolidada = prom_fin * ponderaciones['fin_semana']
            participacion = "Fin de Semana"
        else:
            nota_consolidada = prom_gran * ponderaciones['gran_parada']
            participacion = "Gran Parada"
        
        # Estado patrimonial
        if nota_consolidada < UMBRAL_RIESGO:
            estado = "🔴"
        elif nota_consolidada < UMBRAL_MEJORA:
            estado = "🟡"
        else:
            estado = "🟢"
        
        resultados.append({
            'codigo_grupo': codigo,
            'nombre_propuesta': info['nombre_propuesta'],
            'modalidad': info['modalidad'],
            'tamano': info.get('tamano', ''),
            'ficha_codigo': ficha,
            'ficha_nombre': info['ficha_nombre'],
            'promedio_fin': prom_fin,
            'promedio_gran': prom_gran,
            'nota_consolidada': nota_consolidada,
            'estado': estado,
            'participacion': participacion
        })
    
    return pd.DataFrame(resultados)
def asignar_premio(nota, umbral):
    if pd.isna(nota):
        return "PARTICIPACIÓN"

    if nota >= umbral:
        return "CONGO DE ORO"
    elif nota >= 1.8:
        return "MEDALLA A LA EXCELENCIA"
    elif nota >= 1.0:
        return "HONOR AL FOLCLOR"
    else:
        return "PARTICIPACIÓN"

def calcular_premios(df):
    """
    Calcula premios por modalidad:
    - Asigna categoria
    - Calcula umbral (percentil 75)
    - Asigna premio según nota
    - Genera ranking solo para Congos de Oro
    """

    if df.empty:
        return pd.DataFrame()

    resultados = []

    for ficha in df['ficha_codigo'].unique():
        df_ficha = df[df['ficha_codigo'] == ficha].copy()

        # 🔶 Caso especial: CUMBIA por tamaño
        if ficha == "CUMBIA":
            for tamano in ['GRANDE', 'MEDIANO']:
                df_cat = df_ficha[df_ficha['tamano'] == tamano].copy()
                if df_cat.empty:
                    continue

                categoria = f'Cumbia {tamano.capitalize()}'
                umbral = df_cat['nota_consolidada'].quantile(0.75)

                df_cat['categoria'] = categoria
                df_cat['umbral_congo'] = umbral
                df_cat['premio'] = df_cat.apply(
                    lambda r: asignar_premio(
                        r['nota_consolidada'], umbral
                    ),
                    axis=1
                )

                resultados.append(df_cat)

        # 🔶 Caso general
        else:
            categoria = ficha
            umbral = df_ficha['nota_consolidada'].quantile(0.75)

            df_ficha['categoria'] = categoria
            df_ficha['umbral_congo'] = umbral
            df_ficha['premio'] = df_ficha.apply(
                lambda r: asignar_premio(
                    r['nota_consolidada'], umbral
                ),
                axis=1
            )

            resultados.append(df_ficha)

    df_final = pd.concat(resultados, ignore_index=True)

    # 🔢 Ranking por categoria
    df_final = df_final.sort_values(
        ['categoria', 'nota_consolidada'],
        ascending=[True, False]
    )

    df_final['ranking'] = df_final.groupby('categoria').cumcount() + 1

    return df_final

def calcular_congos_oro(df):
    """Calcula Congos de Oro por modalidad (Top 25%)"""
    if df.empty:
        return pd.DataFrame()
    
    congos = []
    
    for ficha in df['ficha_codigo'].unique():
        df_ficha = df[df['ficha_codigo'] == ficha]
        
        # Caso especial: CUMBIA separada por tamaño
        if ficha == "CUMBIA":
            for tamano in ['GRANDE', 'MEDIANO']:
                df_tam = df_ficha[df_ficha['tamano'] == tamano]
                if len(df_tam) > 0:
                    umbral = df_tam['nota_consolidada'].quantile(0.75)
                    df_oro = df_tam[df_tam['nota_consolidada'] >= umbral].copy()
                    df_oro['categoria'] = f'Cumbia {tamano.capitalize()}'
                    congos.append(df_oro)
        else:
            umbral = df_ficha['nota_consolidada'].quantile(0.75)
            df_oro = df_ficha[df_ficha['nota_consolidada'] >= umbral].copy()
            df_oro['categoria'] = ficha
            congos.append(df_oro)
    
    if congos:
        df_congos = pd.concat(congos, ignore_index=True)
        df_congos = df_congos.sort_values(['categoria', 'nota_consolidada'], ascending=[True, False])
        df_congos['ranking'] = df_congos.groupby('categoria').cumcount() + 1
        return df_congos
    return pd.DataFrame()


def mostrar_congos_oro():
    """Vista principal de Congos de Oro"""
    
    #st.caption("Evaluaciones consolidadas: Fin de Semana de la Tradición + Gran Parada de Tradición")
    
    # Mostrar info de BDs detectadas
    """
    with st.expander("ℹ️ Información de Bases de Datos"):
        if DB_FIN_SEMANA:
            st.success(f"✅ Fin de Semana: {Path(DB_FIN_SEMANA).name}")
        else:
            st.error("❌ No se encontró BD de Fin de Semana")
        
        if DB_GRAN_PARADA:
            st.success(f"✅ Gran Parada: {Path(DB_GRAN_PARADA).name}")
        else:
            st.error("❌ No se encontró BD de Gran Parada")
    """
    st.title("🏆 Congos de Oro - Consolidado 2026")
    st.markdown("---")
    # Cargar datos
    with st.spinner("Cargando datos..."):
        df = cargar_y_consolidar_datos()
        
        if df.empty:
            st.error("❌ No se pudieron cargar datos")
            st.info("💡 Verifica que existan archivos .db en la carpeta data/")
            return
        
        df = calcular_premios(df)
        df_congos = calcular_congos_oro(df)
    
    # KPIs principales
    st.markdown("### 📊 Métricas Generales")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Grupos", len(df))
    
    with col2:
        st.metric("Congos de Oro", len(df_congos), 
                 delta=f"{len(df_congos)/len(df)*100:.1f}%")
    
    promedio_general = df['nota_consolidada'].mean()
    
    
    with col3:
        color = color_gradiente(promedio_general)
        st.markdown(f"""Promedio General:<div style="
                    width: 40px;
                    height: 40px;
                    background-color: {color};
                    border-radius: 6px
                "></div>""", unsafe_allow_html=True)
    with col4:
        riesgo = len(df[df['estado'] == "🔴"])
        st.metric("🔴 Riesgo", riesgo, 
                 delta=f"{riesgo/len(df)*100:.0f}%")
    with col5:
        mejora = len(df[df['estado'] == "🟡"])
        st.metric("🟡 Mejora", mejora, 
                    delta=f"{mejora/len(df)*100:.0f}%")
    
    with col6:
        fortalecimiento = len(df[df['estado'] == "🟢"])
        st.metric("🟢 Fortalecimiento", fortalecimiento,
                 delta=f"{fortalecimiento/len(df)*100:.0f}%")
    
    #espacio en blanco
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🏆 Listado de premios", "📊 Todos los Grupos", "📈 Análisis por Modalidad"])
    
    with tab1:
        st.markdown("### 🏆 Listado de Premios")
        
        if df.empty:
            st.warning("⚠️ No se pudieron calcular Congos de Oro")
            return
        
        # Filtro por categoría

        col_f1, col_f2, colf3 = st.columns(3)
        with col_f1:
            categorias = ['Todas'] + sorted(df['categoria'].unique().tolist())
            categoria_sel = st.selectbox("Filtrar por categoría:", categorias)
        
        if categoria_sel != 'Todas':
            df_mostrar = df[df['categoria'] == categoria_sel]
        else:
            df_mostrar = df
        
        with col_f2:
            premios_list = ['Todos', 'CONGO DE ORO', 'MEDALLA A LA EXCELENCIA', 'HONOR AL FOLCLOR', 'PARTICIPACIÓN']
            premio_sel = st.selectbox("Filtrar por premio:", premios_list) 
        if premio_sel != 'Todos':
            df_mostrar = df_mostrar[df_mostrar['premio'] == premio_sel]
        else:
            df_mostrar = df_mostrar

        with colf3:
            estado_list = ['Todos', '🟢', '🟡', '🔴']
            estado_sel = st.selectbox("Filtrar por estado:", estado_list)
        if estado_sel != 'Todos':
            df_mostrar = df_mostrar[df_mostrar['estado'] == estado_sel]
        else:
            df_mostrar = df_mostrar
        
        premio_display = {
            "CONGO DE ORO": "🏆",
            "MEDALLA A LA EXCELENCIA": "🥇",
            "HONOR AL FOLCLOR": "📜",
            "PARTICIPACIÓN": "🎭"
        }
        
        df_mostrar['premio_display'] = df_mostrar['premio'].apply(
            lambda x: premio_display.get(x, x))
        
        # Tabla
        st.dataframe(
            df_mostrar[[
                'ranking', 'categoria', 'codigo_grupo', 'nombre_propuesta',
                'nota_consolidada', 'promedio_fin', 'promedio_gran', 'premio_display',
                'estado','participacion'
            ]],
            height=35 * len(df_mostrar) + 40,
            use_container_width=True,
            hide_index=True,
            column_config={
                'ranking': '🏅',
                'categoria': 'Categoría',
                'codigo_grupo': 'Código',
                'nombre_propuesta': 'Nombre',
                'premio_display': 'Premio',
                'nota_consolidada': st.column_config.NumberColumn('Nota Final', format="%.2f"),
                'promedio_fin': st.column_config.NumberColumn('Fin de Semana', format="%.2f"),
                'promedio_gran': st.column_config.NumberColumn('Gran Parada', format="%.2f"),
                'estado': 'Estado',
                'participacion': 'Eventos'
            }
        )
        
        # Botón de exportación
        csv = df_mostrar.to_csv(index=False)
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name=f"congos_oro_{categoria_sel.lower().replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with tab2:
            st.markdown("""
            <div style="
                background-color: white;
                padding: 16px;
                border-radius: 14px;
                border: 1px solid #E5E7EB;
                margin-bottom: 12px;
            ">
            <b>📊 Ranking Completo de los Grupos</b>
            </div>
            """, unsafe_allow_html=True)
            

            # ===== OPCIONES SUPERIORES =====
            col_opt1, col_opt2, col_opt3 = st.columns([3, 1, 1])

            with col_opt1:
                buscar = st.text_input(
                    "🔍 Buscar",
                    placeholder="Buscar por código, nombre o ficha..."
                )

            with col_opt2:
                
                ficha_sel = st.selectbox(
                    "Filtrar por modalidad",
                    ["Todas"] + sorted(df['ficha_codigo'].dropna().unique().tolist())
                )

            with col_opt3:
                
                estado_sel = st.selectbox(
                    "Filtrar por estado",
                    ["Todos", "🟢 Fortalecimiento", "🟡 Mejora", "🔴 Riesgo"]
                )

            # ===== FILTRADO =====
            df_mostrar = df.copy()

            # Búsqueda global
            if buscar:
                df_mostrar = df_mostrar[
                    df_mostrar['codigo_grupo'].astype(str).str.contains(buscar, case=False, na=False) |
                    df_mostrar['nombre_propuesta'].str.contains(buscar, case=False, na=False) |
                    df_mostrar['ficha_codigo'].astype(str).str.contains(buscar, case=False, na=False)
                ]

            # Filtro por ficha
            if ficha_sel != "Todas":
                df_mostrar = df_mostrar[df_mostrar['ficha_codigo'] == ficha_sel]

            # Filtro por estado
            if estado_sel != "Todos":
                df_mostrar = df_mostrar[df_mostrar['estado'] == estado_sel]

            # Ordenar por ranking
            df_mostrar = df_mostrar.sort_values(
                'nota_consolidada',
                ascending=False
            )

            # ===== TABLA =====
            st.dataframe(
                df_mostrar[[
                    'codigo_grupo', 'nombre_propuesta', 'ficha_codigo',
                    'nota_consolidada', 'promedio_fin', 'promedio_gran',
                    'estado', 'participacion'
                ]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    'codigo_grupo': 'Código',
                    'nombre_propuesta': 'Nombre',
                    'ficha_codigo': 'Ficha',
                    'nota_consolidada': st.column_config.NumberColumn(
                        'Nota Final', format="%.3f"
                    ),
                    'promedio_fin': st.column_config.NumberColumn(
                        'Fin de Semana', format="%.3f"
                    ),
                    'promedio_gran': st.column_config.NumberColumn(
                        'Gran Parada', format="%.3f"
                    ),
                    'estado': 'Estado',
                    'participacion': 'Eventos'
                }
            )

            st.caption(f"Mostrando {len(df_mostrar)} de {len(df)} grupos")
        
    with tab3:
        st.markdown("### 📈 Análisis por Modalidad")
        
        # Resumen por ficha
        resumen = []
        for ficha in sorted(df['ficha_codigo'].unique()):
            df_ficha = df[df['ficha_codigo'] == ficha]
            
            if ficha == "CUMBIA":
                for tamano in ['GRANDE', 'MEDIANO']:
                    df_tam = df_ficha[df_ficha['tamano'] == tamano]
                    if len(df_tam) > 0:
                        df_oro = df_tam[df_tam['nota_consolidada'] >= df_tam['nota_consolidada'].quantile(0.75)]
                        resumen.append({
                            'Ficha': f'Cumbia {tamano.capitalize()}',
                            'Total': len(df_tam),
                            'Congos de Oro': len(df_oro),
                            'Medalla a la Excelencia': len(df_tam[df_tam['premio'] == "MEDALLA A LA EXCELENCIA"]),
                            'Honor al Folclor': len(df_tam[df_tam['premio'] == "HONOR AL FOLCLOR"]),
                            'Participación': len(df_tam[df_tam['premio'] == "PARTICIPACIÓN"]),
                            #'% Congos de Oro': len(df_oro)/len(df_tam)*100 if len(df_tam) > 0 else 0,
                            'Promedio': df_tam['nota_consolidada'].mean(),
                            'Umbral': df_tam['nota_consolidada'].quantile(0.75),
                            '🟢' : len(df_tam[df_tam['estado'] == "🟢"]),
                            #'🟢%' : len(df_tam[df_tam['estado'] == "🟢 Fortalecimiento"])/len(df_tam)*100 if len(df_tam) > 0 else 0,
                            '🟡' : len(df_tam[df_tam['estado'] == "🟡"]),
                            #'🟡%' : len(df_tam[df_tam['estado'] == "🟡 Mejora"])/len(df_tam)*100 if len(df_tam) > 0 else 0,
                            '🔴' : len(df_tam[df_tam['estado'] == "🔴"]),
                            #'🔴%' : len(df_tam[df_tam['estado'] == "🔴 Riesgo"])/len(df_tam)*100 if len(df_tam) > 0 else 0,
                            #'Máximo': df_tam['nota_consolidada'].max(),
                            #'Mínimo': df_tam['nota_consolidada'].min(),
                            #'Desv. Std': df_tam['nota_consolidada'].std()
                        })
            else:
                df_oro = df_ficha[df_ficha['nota_consolidada'] >= df_ficha['nota_consolidada'].quantile(0.75)]
                resumen.append({
                    'Ficha': ficha,
                    'Total': len(df_ficha),
                    'Congos de Oro': len(df_oro),
                    'Medalla a la Excelencia': len(df_ficha[df_ficha['premio'] == "MEDALLA A LA EXCELENCIA"]),
                    'Honor al Folclor': len(df_ficha[df_ficha['premio'] == "HONOR AL FOLCLOR"]),
                    'Participación': len(df_ficha[df_ficha['premio'] == "PARTICIPACIÓN"]),
                    'Promedio': df_ficha['nota_consolidada'].mean(),
                    'Umbral': df_ficha['nota_consolidada'].quantile(0.75),
                    '🟢' : len(df_ficha[df_ficha['estado'] == "🟢"]),
                    #'🟢%' : len(df_ficha[df_ficha['estado'] == "🟢 Fortalecimiento"])/len(df_ficha)*100 if len(df_ficha) > 0 else 0,
                    '🟡' : len(df_ficha[df_ficha['estado'] == "🟡"]),
                    #'🟡%' : len(df_ficha[df_ficha['estado'] == "🟡 Mejora"])/len(df_ficha)*100 if len(df_ficha) > 0 else 0,
                    '🔴' : len(df_ficha[df_ficha['estado'] == "🔴"]),
                    #'🔴%' : len(df_ficha[df_ficha['estado'] == "🔴 Riesgo"])/len(df_ficha)*100 if len(df_ficha) > 0 else 0,
                    #'Máximo': df_ficha['nota_consolidada'].max(),
                    #'Mínimo': df_ficha['nota_consolidada'].min(),
                    #'Desv. Std': df_ficha['nota_consolidada'].std()
                })
        
        df_resumen = pd.DataFrame(resumen)
        
        st.data_editor(
            df_resumen,
            height=35 * len(df_resumen) + 40,

            use_container_width=True,
            hide_index=True,
            column_config={
                'Promedio': st.column_config.NumberColumn(format="%.2f"),
                'Umbral': st.column_config.NumberColumn(format="%.2f"),
                #'% Congos de Oro': st.column_config.NumberColumn(format="%.0f%%"),
                'Total': st.column_config.NumberColumn(format="%d"),
                'Congos de Oro': st.column_config.NumberColumn(label="🏆", format="%d"),
                'Medalla a la Excelencia': st.column_config.NumberColumn(label="🥇", format="%d"),
                'Honor al Folclor': st.column_config.NumberColumn(label="📜", format="%d"),
                'Participación': st.column_config.NumberColumn(label="🎭", format="%d"),
                '🟢': st.column_config.NumberColumn(format="%d"),
                #'🟢%': st.column_config.NumberColumn(format="%.0f%%"),
                '🟡': st.column_config.NumberColumn(format="%d"),
                #'🟡%': st.column_config.NumberColumn(format="%.0f%%"),
                '🔴': st.column_config.NumberColumn(format="%d"),
                #'🔴%': st.column_config.NumberColumn(format="%.0f%%"),
                #'Máximo': st.column_config.NumberColumn(format="%.3f"),
                #'Mínimo': st.column_config.NumberColumn(format="%.3f"),
                #'Desv. Std': st.column_config.NumberColumn(format="%.3f"),
            }
        )
