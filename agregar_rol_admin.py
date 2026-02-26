"""
Script de Migración: Agregar rol 'administrador' a la tabla usuarios

Este script modifica el CHECK constraint de la tabla usuarios
para permitir el rol 'administrador' además de 'curador' y 'comite'

Ejecutar: python agregar_rol_admin.py
"""
import sqlite3
import logging
from pathlib import Path
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar el directorio raíz al path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.config import config

def crear_backup():
    """Crea un backup de la base de datos"""
    from datetime import datetime
    import shutil
    
    db_path = Path(config.db_path)
    if not db_path.exists():
        logger.error(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"curaduria_backup_{timestamp}.db"
    
    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"✅ Backup creado: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Error creando backup: {e}")
        return False

def agregar_rol_administrador():
    """Agrega el rol 'administrador' a la tabla usuarios"""
    
    logger.info("="*70)
    logger.info("🔧 AGREGANDO ROL 'ADMINISTRADOR'")
    logger.info("="*70)
    
    # Crear backup
    logger.info("\n📦 Creando backup de seguridad...")
    if not crear_backup():
        logger.error("❌ No se pudo crear backup. Abortando.")
        return False
    
    try:
        conn = sqlite3.connect(config.db_path)
        cursor = conn.cursor()
        
        # SQLite no permite modificar CHECK constraints directamente
        # Necesitamos recrear la tabla
        
        logger.info("\n📋 Paso 1: Creando tabla temporal...")
        
        # 1. Crear tabla temporal con el nuevo constraint
        cursor.execute("""
            CREATE TABLE usuarios_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                rol TEXT CHECK(rol IN ('curador', 'comite', 'administrador')) NOT NULL,
                activo INTEGER DEFAULT 1,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                
                CHECK(length(username) >= 3)
            )
        """)
        logger.info("✅ Tabla temporal creada")
        
        # 2. Copiar datos existentes
        logger.info("\n📋 Paso 2: Copiando datos existentes...")
        cursor.execute("""
            INSERT INTO usuarios_temp (id, username, password_hash, rol, activo, fecha_creacion)
            SELECT id, username, password_hash, rol, activo, fecha_creacion
            FROM usuarios
        """)
        
        rows_copied = cursor.rowcount
        logger.info(f"✅ {rows_copied} usuarios copiados")
        
        # 3. Eliminar tabla antigua
        logger.info("\n📋 Paso 3: Eliminando tabla antigua...")
        cursor.execute("DROP TABLE usuarios")
        logger.info("✅ Tabla antigua eliminada")
        
        # 4. Renombrar tabla temporal
        logger.info("\n📋 Paso 4: Renombrando tabla temporal...")
        cursor.execute("ALTER TABLE usuarios_temp RENAME TO usuarios")
        logger.info("✅ Tabla renombrada")
        
        # 5. Recrear índices
        logger.info("\n📋 Paso 5: Recreando índices...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON usuarios(rol)")
        logger.info("✅ Índices recreados")
        
        # Commit
        conn.commit()
        
        # Verificación
        logger.info("\n🔍 Verificando cambios...")
        
        # Verificar constraint
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='usuarios'")
        table_sql = cursor.fetchone()[0]
        
        if 'administrador' in table_sql:
            logger.info("✅ Constraint actualizado correctamente")
        else:
            logger.warning("⚠️  No se pudo verificar el constraint")
        
        # Contar usuarios por rol
        cursor.execute("SELECT rol, COUNT(*) FROM usuarios GROUP BY rol")
        roles = cursor.fetchall()
        
        logger.info("\n📊 Usuarios por rol:")
        for rol, count in roles:
            logger.info(f"   • {rol}: {count}")
        
        conn.close()
        
        logger.info("\n" + "="*70)
        logger.info("✅ ROL 'ADMINISTRADOR' AGREGADO EXITOSAMENTE")
        logger.info("="*70)
        
        logger.info("\n📋 Próximos pasos:")
        logger.info("1. Crear un usuario administrador: python crear_usuario_admin.py")
        logger.info("2. Actualizar el código para manejar el rol 'administrador'")
        logger.info("3. Reiniciar la aplicación: streamlit run main.py")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Error durante la migración: {e}")
        logger.error("💡 Restaura el backup si es necesario")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔧 AGREGAR ROL 'ADMINISTRADOR'")
    print("="*70)
    print("\nEste script va a:")
    print("✓ Crear backup de la base de datos")
    print("✓ Modificar la tabla usuarios")
    print("✓ Agregar 'administrador' como rol válido")
    print("✓ Preservar TODOS los datos existentes")
    print("\n⚠️  IMPORTANTE:")
    print("• Se creará un backup automático")
    print("• No se perderán datos")
    print("• Este proceso es irreversible (sin restaurar backup)")
    
    respuesta = input("\n¿Continuar? (s/n): ")
    
    if respuesta.lower() != 's':
        print("❌ Operación cancelada")
        sys.exit(0)
    
    exito = agregar_rol_administrador()
    
    if exito:
        print("\n✅ ¡Rol agregado exitosamente!")
        sys.exit(0)
    else:
        print("\n❌ La operación falló")
        sys.exit(1)
