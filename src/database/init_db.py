"""
Inicialización y creación de la base de datos
ACTUALIZADO: Sistema completo con fichas dinámicas
"""
import logging
import os
from src.database.connection import ejecutar_script, get_db_connection
from src.config import config

logger = logging.getLogger(__name__)


SCHEMA_SQL = """
-- =====================================================
-- TABLA: usuarios
-- Gestión de curadores y miembros del comité
-- =====================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol TEXT CHECK(rol IN ('curador', 'comite')) NOT NULL,
    activo INTEGER DEFAULT 1,
    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
    
    CHECK(length(username) >= 3)
);

CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username);
CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON usuarios(rol);


-- =====================================================
-- TABLA: fichas
-- Tipos de fichas de evaluación
-- =====================================================
CREATE TABLE IF NOT EXISTS fichas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    
    CHECK(length(codigo) > 0)
);

CREATE INDEX IF NOT EXISTS idx_fichas_codigo ON fichas(codigo);


-- =====================================================
-- TABLA: dimensiones
-- Catálogo de dimensiones patrimoniales
-- =====================================================
CREATE TABLE IF NOT EXISTS dimensiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    orden INTEGER NOT NULL,
    
    CHECK(orden > 0)
);

CREATE INDEX IF NOT EXISTS idx_dimensiones_orden ON dimensiones(orden);
CREATE INDEX IF NOT EXISTS idx_dimensiones_codigo ON dimensiones(codigo);


-- =====================================================
-- TABLA: ficha_dimensiones
-- Relación entre fichas y dimensiones
-- =====================================================
CREATE TABLE IF NOT EXISTS ficha_dimensiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ficha_id INTEGER NOT NULL,
    dimension_id INTEGER NOT NULL,
    orden INTEGER NOT NULL,

    FOREIGN KEY (ficha_id) REFERENCES fichas(id) ON DELETE CASCADE,
    FOREIGN KEY (dimension_id) REFERENCES dimensiones(id) ON DELETE CASCADE,
    UNIQUE (ficha_id, dimension_id),
    CHECK (orden > 0)
);

CREATE INDEX IF NOT EXISTS idx_ficha_dimensiones_ficha ON ficha_dimensiones(ficha_id);
CREATE INDEX IF NOT EXISTS idx_ficha_dimensiones_dimension ON ficha_dimensiones(dimension_id);


-- =====================================================
-- TABLA: aspectos
-- Aspectos evaluables dentro de cada dimensión
-- =====================================================
CREATE TABLE IF NOT EXISTS aspectos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dimension_id INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    orden INTEGER NOT NULL,

    FOREIGN KEY (dimension_id) REFERENCES dimensiones(id) ON DELETE CASCADE,
    UNIQUE (dimension_id, nombre),
    CHECK (orden > 0)
);

CREATE INDEX IF NOT EXISTS idx_aspectos_dimension ON aspectos(dimension_id);
CREATE INDEX IF NOT EXISTS idx_aspectos_orden ON aspectos(orden);


-- =====================================================
-- TABLA: grupos
-- Catálogo de grupos participantes
-- =====================================================
CREATE TABLE IF NOT EXISTS grupos (
    codigo TEXT PRIMARY KEY,
    nombre_propuesta TEXT NOT NULL,
    modalidad TEXT NOT NULL,
    tipo TEXT NOT NULL,
    tamano TEXT,
    naturaleza TEXT,
    ano_evento INTEGER NOT NULL,
    ficha_id INTEGER,
    
    FOREIGN KEY (ficha_id) REFERENCES fichas(id) ON DELETE SET NULL,
    CHECK(length(codigo) > 0 AND length(codigo) <= 50),
    CHECK(length(nombre_propuesta) >= 3)
);

CREATE INDEX IF NOT EXISTS idx_grupos_modalidad ON grupos(modalidad);
CREATE INDEX IF NOT EXISTS idx_grupos_ano ON grupos(ano_evento);
CREATE INDEX IF NOT EXISTS idx_grupos_ficha ON grupos(ficha_id);


-- =====================================================
-- TABLA: evaluaciones
-- Evaluaciones por ficha y aspecto
-- =====================================================
CREATE TABLE IF NOT EXISTS evaluaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    codigo_grupo TEXT NOT NULL,
    ficha_id INTEGER NOT NULL,
    aspecto_id INTEGER NOT NULL,
    resultado INTEGER CHECK (resultado IN (0,1,2)) NOT NULL,
    observacion TEXT NOT NULL,
    fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (codigo_grupo) REFERENCES grupos(codigo) ON DELETE CASCADE,
    FOREIGN KEY (ficha_id) REFERENCES fichas(id) ON DELETE CASCADE,
    FOREIGN KEY (aspecto_id) REFERENCES aspectos(id) ON DELETE CASCADE,

    UNIQUE (usuario_id, codigo_grupo, ficha_id, aspecto_id),
    CHECK (length(observacion) >= 5)
);

CREATE INDEX IF NOT EXISTS idx_evaluaciones_usuario ON evaluaciones(usuario_id);
CREATE INDEX IF NOT EXISTS idx_evaluaciones_grupo ON evaluaciones(codigo_grupo);
CREATE INDEX IF NOT EXISTS idx_evaluaciones_ficha ON evaluaciones(ficha_id);
CREATE INDEX IF NOT EXISTS idx_evaluaciones_aspecto ON evaluaciones(aspecto_id);


-- =====================================================
-- TABLA: logs_sistema
-- Auditoría de acciones importantes
-- =====================================================
CREATE TABLE IF NOT EXISTS logs_sistema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    accion TEXT NOT NULL,
    detalle TEXT,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_logs_fecha ON logs_sistema(fecha);
CREATE INDEX IF NOT EXISTS idx_logs_usuario ON logs_sistema(usuario);
"""


# ═══════════════════════════════════════════════════════════════════
# DATOS INICIALES - FICHAS
# ═══════════════════════════════════════════════════════════════════

FICHAS_INICIALES = [
    {
        'codigo': 'CONGO',
        'nombre': 'Ficha Congo',
        'descripcion': 'Modalidad Danza Tradicional - Congo'
    },
    {
        'codigo': 'GARABATO',
        'nombre': 'Ficha Garabato',
        'descripcion': 'Modalidad Danza Tradicional - Garabato'
    },
    {
        'codigo': 'CUMBIA',
        'nombre': 'Ficha Cumbia',
        'descripcion': 'Modalidad Cumbia'
    },
    {
        'codigo': 'MAPALE',
        'nombre': 'Ficha Mapalé',
        'descripcion': 'Modalidad Danza Tradicional - Mapalé'
    },
    {
        'codigo': 'SON_NEGRO',
        'nombre': 'Ficha Son de Negro',
        'descripcion': 'Modalidad Danza Tradicional - Son de Negro'
    },
    {
        'codigo': 'COMPARSA_TRAD',
        'nombre': 'Ficha Comparsa de Tradición',
        'descripcion': 'Naturaleza Tradición Popular'
    },
    {
        'codigo': 'COMPARSA_FANT',
        'nombre': 'Ficha Comparsa de Fantasía',
        'descripcion': 'Naturaleza Fantasía'
    },
    {
        'codigo': 'DANZAS_ESP',
        'nombre': 'Ficha Danzas Especiales',
        'descripcion': 'Danzas de Relación, Danzas Especiales y Expresiones Invitadas'
    }
]


# ═══════════════════════════════════════════════════════════════════
# DATOS INICIALES - DIMENSIONES Y ASPECTOS
# ═══════════════════════════════════════════════════════════════════

DIMENSIONES_INICIALES = [
    {
        'codigo': 'DIM1',
        'nombre': 'Dimensión 1 – Rigor en la ejecución tradicional',
        'orden': 1,
        'aspectos': [
            'Coreografía / pasos básicos',
            'Expresión dancística',
            'Relación música – danza',
            'Vestuario apropiado (incluye parafernalia)',
            'Marcación del ritmo'
        ]
    },
    {
        'codigo': 'DIM2',
        'nombre': 'Dimensión 2 – Transmisión del sentido cultural',
        'orden': 2,
        'aspectos': [
            'Su identidad',
            'Su narrativa',
            'Su historia',
            'El valor simbólico'
        ]
    },
    {
        'codigo': 'DIM3',
        'nombre': 'Dimensión 3 – Vitalidad e innovación con pertinencia',
        'orden': 3,
        'aspectos': [
            'Creatividad con respeto',
            'Adaptaciones pertinentes',
            'Renovación generacional o estética sin perder esencia'
        ]
    }
]


# ═══════════════════════════════════════════════════════════════════
# MAPEO: FICHAS → DIMENSIONES
# ═══════════════════════════════════════════════════════════════════

# Por defecto, todas las fichas tendrán las 3 dimensiones básicas
# Puedes modificar esto según las necesidades específicas de cada ficha

FICHA_DIMENSIONES_MAP = {
    'CONGO': ['DIM1', 'DIM2', 'DIM3'],
    'GARABATO': ['DIM1', 'DIM2', 'DIM3'],
    'CUMBIA': ['DIM1', 'DIM2', 'DIM3'],
    'MAPALE': ['DIM1', 'DIM2', 'DIM3'],
    'SON_NEGRO': ['DIM1', 'DIM2', 'DIM3'],
    'COMPARSA_TRAD': ['DIM1', 'DIM2', 'DIM3'],
    'COMPARSA_FANT': ['DIM1', 'DIM2', 'DIM3'],
    'DANZAS_ESP': ['DIM2', 'DIM3']  # Ejemplo: esta ficha no tiene DIM1
}


# ═══════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL DE INICIALIZACIÓN
# ═══════════════════════════════════════════════════════════════════

def inicializar_base_datos() -> bool:
    """
    Crea las tablas e inicializa datos básicos si no existen.
    
    Returns:
        True si se inicializó correctamente, False en caso contrario
    """
    try:
        logger.info("Inicializando base de datos...")
        
        # 1. Crear esquema
        ejecutar_script(SCHEMA_SQL)
        logger.info("Esquema de base de datos creado")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 2. Insertar DIMENSIONES y ASPECTOS
            cursor.execute("SELECT COUNT(*) FROM dimensiones")
            count_dimensiones = cursor.fetchone()[0]
            
            if count_dimensiones == 0:
                logger.info("Insertando dimensiones y aspectos iniciales...")
                
                dimensiones_ids = {}
                
                for dim in DIMENSIONES_INICIALES:
                    # Insertar dimensión
                    cursor.execute(
                        """INSERT INTO dimensiones (codigo, nombre, orden)
                        VALUES (?, ?, ?)""",
                        (dim['codigo'], dim['nombre'], dim['orden'])
                    )
                    dimension_id = cursor.lastrowid
                    dimensiones_ids[dim['codigo']] = dimension_id
                    
                    # Insertar aspectos de esta dimensión
                    for orden, nombre_aspecto in enumerate(dim['aspectos'], start=1):
                        cursor.execute(
                            """INSERT INTO aspectos (dimension_id, nombre, orden)
                            VALUES (?, ?, ?)""",
                            (dimension_id, nombre_aspecto, orden)
                        )
                    
                    logger.info(f"Dimensión '{dim['nombre']}' insertada con {len(dim['aspectos'])} aspectos")
                
                conn.commit()
                logger.info("Dimensiones y aspectos iniciales insertados correctamente")
            else:
                logger.info(f"Las dimensiones ya existen ({count_dimensiones} registros)")
                # Obtener IDs existentes
                cursor.execute("SELECT id, codigo FROM dimensiones")
                dimensiones_ids = {codigo: id_ for id_, codigo in cursor.fetchall()}
            
            # 3. Insertar FICHAS
            cursor.execute("SELECT COUNT(*) FROM fichas")
            count_fichas = cursor.fetchone()[0]
            
            if count_fichas == 0:
                logger.info("Insertando fichas iniciales...")
                
                fichas_ids = {}
                
                for ficha in FICHAS_INICIALES:
                    cursor.execute(
                        """INSERT INTO fichas (codigo, nombre, descripcion)
                        VALUES (?, ?, ?)""",
                        (ficha['codigo'], ficha['nombre'], ficha['descripcion'])
                    )
                    ficha_id = cursor.lastrowid
                    fichas_ids[ficha['codigo']] = ficha_id
                    
                    logger.info(f"Ficha '{ficha['nombre']}' insertada (ID: {ficha_id})")
                
                conn.commit()
                logger.info(f"{len(FICHAS_INICIALES)} fichas iniciales insertadas")
            else:
                logger.info(f"Las fichas ya existen ({count_fichas} registros)")
                # Obtener IDs existentes
                cursor.execute("SELECT id, codigo FROM fichas")
                fichas_ids = {codigo: id_ for id_, codigo in cursor.fetchall()}
            
            # 4. Insertar relación FICHA-DIMENSIONES
            cursor.execute("SELECT COUNT(*) FROM ficha_dimensiones")
            count_fd = cursor.fetchone()[0]
            
            if count_fd == 0:
                logger.info("Creando relaciones ficha-dimensiones...")
                
                for ficha_codigo, dim_codigos in FICHA_DIMENSIONES_MAP.items():
                    if ficha_codigo not in fichas_ids:
                        logger.warning(f"Ficha no encontrada: {ficha_codigo}")
                        continue
                    
                    ficha_id = fichas_ids[ficha_codigo]
                    
                    for orden, dim_codigo in enumerate(dim_codigos, start=1):
                        if dim_codigo not in dimensiones_ids:
                            logger.warning(f"Dimensión no encontrada: {dim_codigo}")
                            continue
                        
                        dimension_id = dimensiones_ids[dim_codigo]
                        
                        cursor.execute(
                            """INSERT INTO ficha_dimensiones (ficha_id, dimension_id, orden)
                            VALUES (?, ?, ?)""",
                            (ficha_id, dimension_id, orden)
                        )
                    
                    logger.info(f"Relaciones creadas para ficha '{ficha_codigo}': {len(dim_codigos)} dimensiones")
                
                conn.commit()
                logger.info("Relaciones ficha-dimensiones creadas correctamente")
            else:
                logger.info(f"Las relaciones ficha-dimensiones ya existen ({count_fd} registros)")
        
        logger.info("✅ Base de datos inicializada correctamente")
        return True
        
    except Exception as e:
        logger.exception(f"❌ Error inicializando base de datos: {e}")
        return False


def verificar_integridad_bd() -> bool:
    """
    Verifica que la base de datos tenga la estructura correcta.
    
    Returns:
        True si la estructura es válida, False en caso contrario
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar tablas requeridas
            tablas_requeridas = [
                'usuarios', 'fichas', 'dimensiones', 'ficha_dimensiones',
                'aspectos', 'grupos', 'evaluaciones', 'logs_sistema'
            ]

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tablas_existentes = [row[0] for row in cursor.fetchall()]
            
            for tabla in tablas_requeridas:
                if tabla not in tablas_existentes:
                    logger.error(f"❌ Tabla faltante: {tabla}")
                    return False
            
            # Verificar que existan fichas
            cursor.execute("SELECT COUNT(*) FROM fichas")
            count_fichas = cursor.fetchone()[0]
            if count_fichas == 0:
                logger.warning("⚠️ No hay fichas en la base de datos")
                return False
            
            # Verificar que existan dimensiones
            cursor.execute("SELECT COUNT(*) FROM dimensiones")
            count_dim = cursor.fetchone()[0]
            if count_dim == 0:
                logger.warning("⚠️ No hay dimensiones en la base de datos")
                return False
            
            # Verificar que existan aspectos
            cursor.execute("SELECT COUNT(*) FROM aspectos")
            count_asp = cursor.fetchone()[0]
            if count_asp == 0:
                logger.warning("⚠️ No hay aspectos en la base de datos")
                return False
            
            # Verificar relaciones ficha-dimensiones
            cursor.execute("SELECT COUNT(*) FROM ficha_dimensiones")
            count_fd = cursor.fetchone()[0]
            if count_fd == 0:
                logger.warning("⚠️ No hay relaciones ficha-dimensiones")
                return False
            
            logger.info(f"✅ Integridad verificada: {count_fichas} fichas, {count_dim} dimensiones, {count_asp} aspectos, {count_fd} relaciones")
            return True
            
    except Exception as e:
        logger.exception(f"❌ Error verificando integridad: {e}")
        return False


def mostrar_resumen_bd():
    """Muestra un resumen de la estructura de la base de datos."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            print("\n" + "="*60)
            print("📊 RESUMEN DE LA BASE DE DATOS")
            print("="*60)
            
            # Fichas
            cursor.execute("SELECT codigo, nombre FROM fichas ORDER BY nombre")
            fichas = cursor.fetchall()
            print(f"\n🎭 FICHAS ({len(fichas)}):")
            for codigo, nombre in fichas:
                # Contar dimensiones de esta ficha
                cursor.execute("""
                    SELECT COUNT(*) FROM ficha_dimensiones WHERE ficha_id = (
                        SELECT id FROM fichas WHERE codigo = ?
                    )
                """, (codigo,))
                num_dims = cursor.fetchone()[0]
                print(f"  • {codigo}: {nombre} ({num_dims} dimensiones)")
            
            # Dimensiones
            cursor.execute("SELECT codigo, nombre FROM dimensiones ORDER BY orden")
            dimensiones = cursor.fetchall()
            print(f"\n📐 DIMENSIONES ({len(dimensiones)}):")
            for codigo, nombre in dimensiones:
                # Contar aspectos
                cursor.execute("""
                    SELECT COUNT(*) FROM aspectos WHERE dimension_id = (
                        SELECT id FROM dimensiones WHERE codigo = ?
                    )
                """, (codigo,))
                num_asp = cursor.fetchone()[0]
                print(f"  • {codigo}: {nombre} ({num_asp} aspectos)")
            
            # Estadísticas generales
            cursor.execute("SELECT COUNT(*) FROM grupos")
            num_grupos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            num_usuarios = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM evaluaciones")
            num_eval = cursor.fetchone()[0]
            
            print(f"\n📈 ESTADÍSTICAS:")
            print(f"  • Grupos registrados: {num_grupos}")
            print(f"  • Usuarios: {num_usuarios}")
            print(f"  • Evaluaciones: {num_eval}")
            
            print("\n" + "="*60 + "\n")
            
    except Exception as e:
        logger.exception(f"Error mostrando resumen: {e}")


if __name__ == "__main__":
    # Configurar logging para ejecución directa
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Inicializar base de datos
    if inicializar_base_datos():
        print("✅ Base de datos inicializada correctamente")
        
        if verificar_integridad_bd():
            print("✅ Integridad verificada")
            mostrar_resumen_bd()
        else:
            print("❌ Error en la integridad de la base de datos")
    else:
        print("❌ Error inicializando base de datos")