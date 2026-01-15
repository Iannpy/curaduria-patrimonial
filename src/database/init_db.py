"""
Inicialización y creación de la base de datos
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
    
    CHECK(length(codigo) > 0 AND length(codigo) <= 50),
    CHECK(length(nombre_propuesta) >= 3)
);

CREATE INDEX IF NOT EXISTS idx_grupos_modalidad ON grupos(modalidad);
CREATE INDEX IF NOT EXISTS idx_grupos_ano ON grupos(ano_evento);

-- =====================================================
-- TABLA: fichas
-- Tipos de fichas de evaluación
-- =====================================================
CREATE TABLE IF NOT EXISTS fichas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT
);

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

-- Agregar columna a la tabla grupos
ALTER TABLE grupos ADD COLUMN ficha_id INTEGER;

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
    CHECK (length(observacion) >= 20)
);


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


# Dimensiones y aspectos iniciales
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

FICHAS_INICIALES = [
    ("CUMBIA", "Ficha Cumbia", "Modalidad Cumbia"),
    ("CONGO_GARABATO", "Ficha Congo y Garabato", "Danza Tradicional"),
    ("SON_NEGRO", "Ficha Son de Negro y Mapalé", "Danza Tradicional"),
    ("COMPARSA", "Ficha Comparsa", "Comparsa"),
    ("DANZAS_EX", "Ficha Danzas ex", "Danza de Relación, Danza Especial y Expresiones Invitadas")
]
FICHA_DIMENSIONES = {
    "CUMBIA": ["DIM1", "DIM2", "DIM3"],
    "CONGO_GARABATO": ["DIM1", "DIM2", "DIM3"],
    "SON_NEGRO": ["DIM1", "DIM2", "DIM3"],
    "COMPARSA": ["DIM1", "DIM2", "DIM3", "DIM4"],
    "DANZAS_EX": ["DIM2", "DIM3", "DIM5"]
}



def inicializar_base_datos() -> bool:
    """
    Crea las tablas e inicializa datos básicos si no existen.
    
    Returns:
        True si se inicializó correctamente, False en caso contrario
    """
    try:
        logger.info("Inicializando base de datos...")
        
        # Crear esquema
        ejecutar_script(SCHEMA_SQL)
        logger.info("Esquema de base de datos creado")
        
        # Insertar dimensiones y aspectos si no existen
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar si ya existen dimensiones
            cursor.execute("SELECT COUNT(*) FROM dimensiones")
            count_dimensiones = cursor.fetchone()[0]
            
            if count_dimensiones == 0:
                logger.info("Insertando dimensiones iniciales...")
                
                for dim in DIMENSIONES_INICIALES:
                    # Insertar dimensión
                    cursor.execute(
                        """INSERT INTO dimensiones (codigo, nombre, orden)
                        VALUES (?, ?, ?)""",
                        (dim['codigo'], dim['nombre'], dim['orden'])
                    )
                    dimension_id = cursor.lastrowid
                    
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
        
            # ---------- FICHAS ----------
            cursor.execute("SELECT COUNT(*) FROM fichas")
            if cursor.fetchone()[0] == 0:
                cursor.executemany(
                    "INSERT INTO fichas (codigo, nombre, descripcion) VALUES (?, ?, ?)",
                    FICHAS_INICIALES
                )
                logger.info("Fichas iniciales insertadas")

            # ---------- FICHA_DIMENSIONES ----------
            cursor.execute("SELECT COUNT(*) FROM ficha_dimensiones")
            if cursor.fetchone()[0] == 0:
                cursor.execute("SELECT id, codigo FROM fichas")
                fichas_map = {codigo: id_ for id_, codigo in cursor.fetchall()}

                cursor.execute("SELECT id, codigo FROM dimensiones")
                dimensiones_map = {codigo: id_ for id_, codigo in cursor.fetchall()}

                for ficha_codigo, dims in FICHA_DIMENSIONES.items():
                    ficha_id = fichas_map[ficha_codigo]
                    for orden, dim_codigo in enumerate(dims, start=1):
                        cursor.execute(
                            """INSERT INTO ficha_dimensiones (ficha_id, dimension_id, orden)
                            VALUES (?, ?, ?)""",
                            (ficha_id, dimensiones_map[dim_codigo], orden)
                        )

                logger.info("Relación ficha-dimensiones creada")

            conn.commit()

        
        
        
        
        
        
        logger.info("Base de datos inicializada correctamente")
        return True
        
    except Exception as e:
        logger.exception(f"Error inicializando base de datos: {e}")
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
            tablas_requeridas = ['usuarios', 'grupos', 'dimensiones', 'aspectos', 'evaluaciones']

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tablas_existentes = [row[0] for row in cursor.fetchall()]
            
            for tabla in tablas_requeridas:
                if tabla not in tablas_existentes:
                    logger.error(f"Tabla faltante: {tabla}")
                    return False
            
            # Verificar que existan dimensiones
            cursor.execute("SELECT COUNT(*) FROM dimensiones")
            count_dim = cursor.fetchone()[0]
            if count_dim == 0:
                logger.warning("No hay dimensiones en la base de datos")
                return False
            
            # Verificar que existan aspectos
            cursor.execute("SELECT COUNT(*) FROM aspectos")
            count_asp = cursor.fetchone()[0]
            if count_asp == 0:
                logger.warning("No hay aspectos en la base de datos")
                return False
            
            logger.info(f"Integridad de base de datos verificada ({count_dim} dimensiones, {count_asp} aspectos)")
            return True
            
    except Exception as e:
        logger.exception(f"Error verificando integridad: {e}")
        return False


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
        else:
            print("❌ Error en la integridad de la base de datos")
    else:
        print("❌ Error inicializando base de datos")