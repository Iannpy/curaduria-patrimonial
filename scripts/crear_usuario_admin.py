"""
Script para Crear Usuario Administrador

Ejecutar DESPUÉS de agregar_rol_admin.py

Ejecutar: python crear_usuario_admin.py
"""
import sqlite3
import bcrypt
import logging
import sys
import getpass
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.config import config

def crear_usuario_administrador():
    """Crea un usuario con rol administrador"""
    
    logger.info("="*70)
    logger.info("👤 CREAR USUARIO ADMINISTRADOR")
    logger.info("="*70)
    
    # Solicitar datos
    print("\n📝 Ingresa los datos del administrador:")
    print("-" * 50)
    
    username = input("Username: ").strip()
    
    if len(username) < 3:
        logger.error("❌ El username debe tener al menos 3 caracteres")
        return False
    
    # Solicitar contraseña (oculta)
    password = getpass.getpass("Password: ")
    password_confirm = getpass.getpass("Confirmar password: ")
    
    if password != password_confirm:
        logger.error("❌ Las contraseñas no coinciden")
        return False
    
    if len(password) < 6:
        logger.error("❌ La contraseña debe tener al menos 6 caracteres")
        return False
    
    nombre_completo = input("Nombre completo (opcional): ").strip()
    
    try:
        conn = sqlite3.connect(config.db_path)
        cursor = conn.cursor()
        
        # Verificar que el rol 'administrador' existe
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='usuarios'")
        table_sql = cursor.fetchone()[0]
        
        if 'administrador' not in table_sql:
            logger.error("❌ El rol 'administrador' no está disponible")
            logger.info("💡 Ejecuta primero: python agregar_rol_admin.py")
            conn.close()
            return False
        
        # Verificar si el usuario ya existe
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
        if cursor.fetchone():
            logger.error(f"❌ El usuario '{username}' ya existe")
            conn.close()
            return False
        
        # Hashear contraseña
        logger.info("\n🔐 Hasheando contraseña...")
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insertar usuario
        logger.info("💾 Creando usuario...")
        
        # Si hay columna nombre_completo
        try:
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, rol, nombre_completo, activo)
                VALUES (?, ?, 'administrador', ?, 1)
            """, (username, password_hash, nombre_completo if nombre_completo else username))
        except sqlite3.OperationalError:
            # Si no existe la columna nombre_completo
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, rol, activo)
                VALUES (?, ?, 'administrador', 1)
            """, (username, password_hash))
        
        conn.commit()
        
        user_id = cursor.lastrowid
        
        logger.info(f"\n✅ Usuario administrador creado exitosamente!")
        logger.info(f"   • ID: {user_id}")
        logger.info(f"   • Username: {username}")
        logger.info(f"   • Rol: administrador")
        
        # Mostrar resumen de usuarios
        logger.info("\n📊 Resumen de usuarios:")
        cursor.execute("SELECT rol, COUNT(*) FROM usuarios WHERE activo = 1 GROUP BY rol")
        for rol, count in cursor.fetchall():
            logger.info(f"   • {rol}: {count}")
        
        conn.close()
        
        logger.info("\n" + "="*70)
        logger.info("✅ USUARIO ADMINISTRADOR CREADO")
        logger.info("="*70)
        
        logger.info("\n📋 Próximos pasos:")
        logger.info("1. Inicia sesión con las credenciales creadas")
        logger.info("2. Verifica que el rol 'administrador' funcione correctamente")
        logger.info("3. Agrega la lógica para el panel de administrador")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Error creando usuario: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print("👤 CREAR USUARIO ADMINISTRADOR")
    print("="*70)
    print("\nEste script crea un usuario con rol 'administrador'")
    print("\n⚠️  IMPORTANTE:")
    print("• Debes haber ejecutado 'agregar_rol_admin.py' primero")
    print("• La contraseña debe tener al menos 6 caracteres")
    print("• El username debe ser único")
    
    respuesta = input("\n¿Continuar? (s/n): ")
    
    if respuesta.lower() != 's':
        print("❌ Operación cancelada")
        sys.exit(0)
    
    exito = crear_usuario_administrador()
    
    if exito:
        print("\n✅ ¡Usuario creado exitosamente!")
        print("Ya puedes iniciar sesión con las credenciales ingresadas")
        sys.exit(0)
    else:
        print("\n❌ No se pudo crear el usuario")
        sys.exit(1)
