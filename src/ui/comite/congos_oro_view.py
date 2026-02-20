"""
Dashboard de Congos de Oro Consolidados
Vista para el Comité Técnico

Coloca este archivo en: src/ui/comite/congos_oro_view.py
O ejecútalo standalone: streamlit run dashboard_congos_oro.py
"""

import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from .dashboard import color_gradiente

# ═══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════

DB_FIN_SEMANA = "data\curaduria_finde.db"
DB_GRAN_PARADA = "data\curaduria_granparada.db"

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
def cargar_datos():
    """Carga y consolida datos de ambos eventos"""
    
    def obtener_evaluaciones(db_path):
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
    
    df_fin = obtener_evaluaciones(DB_FIN_SEMANA)
    df_fin['evento'] = 'Fin de Semana'
    
    df_gran = obtener_evaluaciones(DB_GRAN_PARADA)
    df_gran['evento'] = 'Gran Parada'
    
    # Consolidar
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
            estado = "🔴 Riesgo"
        elif nota_consolidada < UMBRAL_MEJORA:
            estado = "🟡 Mejora"
        else:
            estado = "🟢 Fortalecimiento"
        
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

def calcular_congos_oro(df):
    """Calcula Congos de Oro por ficha"""
    congos = []
    
    for ficha in df['ficha_codigo'].unique():
        df_ficha = df[df['ficha_codigo'] == ficha]
        
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

# ═══════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════

def mostrar_dashboard():
    st.markdown("""
    <style>
    /* ===== IDENTIDAD GENERAL ===== */
    html, body, [class*="css"]  {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    /* Fondo general */
    .main {
        background-color: #F7F8FA;
    }

    /* Títulos principales */
    h1, h2, h3 {
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* Subtítulos */
    h3 {
        color: #1F2937;
    }

    /* ===== TARJETAS KPI ===== */
    div[data-testid="metric-container"] {
        background-color: white;
        border-radius: 12px;
        padding: 12px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }

    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
    }

    /* ===== TABLAS ===== */
    [data-testid="stDataFrame"] {
        background-color: white;
        border-radius: 14px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 6px 16px rgba(0,0,0,0.05);
    }

    /* ===== CABECERAS DE TABLA ===== */
    thead tr th {
        background-color: #F3F4F6 !important;
        font-weight: 600;
        color: #111827;
    }

    /* ===== BOTONES ===== */
    button[kind="primary"] {
        background-color: #111827;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    st.title("🏆 Congos de Oro - Consolidado 2026")
    #st.caption("Evaluaciones consolidadas: Fin de Semana de la Tradición + Gran Parada de Tradición")
    
    # Cargar datos
    with st.spinner("Cargando datos..."):
        df = cargar_datos()
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
        riesgo = len(df[df['estado'] == "🔴 Riesgo"])
        st.metric("🔴 Riesgo", riesgo, 
                 delta=f"{riesgo/len(df)*100:.0f}%")
    with col5:
        mejora = len(df[df['estado'] == "🟡 Mejora"])
        st.metric("🟡 Mejora", mejora, 
                    delta=f"{mejora/len(df)*100:.0f}%")
    
    with col6:
        fortalecimiento = len(df[df['estado'] == "🟢 Fortalecimiento"])
        st.metric("🟢 Fortalecimiento", fortalecimiento,
                 delta=f"{fortalecimiento/len(df)*100:.0f}%")
    
    #espacio en blanco
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🏆 Congos de Oro", "📊 Todos los Grupos", "📈 Análisis por Modalidad"])
    
    with tab1:
        st.markdown("### 🏆 Congos de Oro (Top 25% por Modalidad)")
        
        # Filtro por categoría
        categorias = ['Todas'] + sorted(df_congos['categoria'].unique().tolist())
        categoria_sel = st.selectbox("Filtrar por categoría:", categorias)
        
        if categoria_sel != 'Todas':
            df_mostrar = df_congos[df_congos['categoria'] == categoria_sel]
        else:
            df_mostrar = df_congos
        
        # Tabla
        st.dataframe(
            df_mostrar[[
                'ranking', 'categoria', 'codigo_grupo', 'nombre_propuesta',
                'nota_consolidada', 'promedio_fin', 'promedio_gran', 
                'estado', 'participacion'
            ]],
            height=35 * len(df_mostrar) + 40,
            use_container_width=True,
            hide_index=True,
            column_config={
                'ranking': '🏅',
                'categoria': 'Categoría',
                'codigo_grupo': 'Código',
                'nombre_propuesta': 'Nombre',
                'nota_consolidada': st.column_config.NumberColumn('Nota Final', format="%.3f"),
                'promedio_fin': st.column_config.NumberColumn('Fin de Semana', format="%.3f"),
                'promedio_gran': st.column_config.NumberColumn('Gran Parada', format="%.3f"),
                'estado': 'Estado',
                'participacion': 'Eventos'
            }
        )
        
        # Botón de exportación
        csv = df_mostrar.to_csv(index=False)
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name=f"congos_oro_{categoria_sel.lower().replace(' ', '_')}.csv",
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
                            'Promedio': df_tam['nota_consolidada'].mean(),
                            '🟢' : len(df_tam[df_tam['estado'] == "🟢 Fortalecimiento"]),
                            '🟡' : len(df_tam[df_tam['estado'] == "🟡 Mejora"]),
                            '🔴' : len(df_tam[df_tam['estado'] == "🔴 Riesgo"]),
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
                    'Promedio': df_ficha['nota_consolidada'].mean(),
                    '🟢' : len(df_ficha[df_ficha['estado'] == "🟢 Fortalecimiento"]),
                    '🟡' : len(df_ficha[df_ficha['estado'] == "🟡 Mejora"]),
                    '🔴' : len(df_ficha[df_ficha['estado'] == "🔴 Riesgo"]),
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
                'Promedio': st.column_config.NumberColumn(format="%.3f"),
                #'Máximo': st.column_config.NumberColumn(format="%.3f"),
                #'Mínimo': st.column_config.NumberColumn(format="%.3f"),
                #'Desv. Std': st.column_config.NumberColumn(format="%.3f"),
            }
        )

# ═══════════════════════════════════════════════════════════════════
# EJECUCIÓN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    st.set_page_config(
        page_title="Congos de Oro 2026",
        page_icon="🏆",
        layout="wide"
    )
    
    mostrar_dashboard()
