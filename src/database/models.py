"""
Modelos de datos y operaciones CRUD
ACTUALIZADO: Sistema completo con fichas dinámicas
"""
import logging
import pandas as pd
import bcrypt
import re
from typing import Optional, List, Dict, Tuple
from src.database.connection import get_db_connection, ejecutar_insert
from src.utils.validators import validar_codigo_grupo, validar_observacion

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# MODELO: Usuarios
# ═══════════════════════════════════════════════════════════════════

class UsuarioModel:
    """Operaciones sobre la tabla usuarios"""
    
    @staticmethod
    def crear_usuario(username: str, password_hash: str, rol: str) -> Optional[int]:
        """Crea un nuevo usuario en el sistema."""
        try:
            query = """
                INSERT INTO usuarios (username, password_hash, rol)
                VALUES (?, ?, ?)
            """
            user_id = ejecutar_insert(query, (username, password_hash, rol))
            logger.info(f"Usuario creado: {username} (ID: {user_id})")
            return user_id
        except Exception as e:
            logger.error(f"Error creando usuario: {e}")
            return None
    
    @staticmethod
    def obtener_por_username(username: str) -> Optional[Dict]:
        """Obtiene un usuario por su username."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM usuarios WHERE username = ? AND activo = 1",
                    (username,)
                )
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Error obteniendo usuario: {e}")
            return None
    
    @staticmethod
    def obtener_por_id(user_id: int) -> Optional[Dict]:
        """Obtiene un usuario por su ID."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Error obteniendo usuario por ID: {e}")
            return None
    
    @staticmethod
    def obtener_todos(incluir_inactivos: bool = False) -> List[Dict]:
        """Obtiene todos los usuarios del sistema."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if incluir_inactivos:
                    cursor.execute("SELECT * FROM usuarios ORDER BY username")
                else:
                    cursor.execute("SELECT * FROM usuarios WHERE activo = 1 ORDER BY username")
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error obteniendo usuarios: {e}")
            return []
    
    @staticmethod
    def obtener_dataframe() -> pd.DataFrame:
        """Obtiene todos los usuarios en formato DataFrame."""
        try:
            with get_db_connection() as conn:
                query = """
                    SELECT 
                        id,
                        username,
                        rol,
                        activo,
                        fecha_creacion
                    FROM usuarios
                    ORDER BY username
                """
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            logger.error(f"Error obteniendo DataFrame de usuarios: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def validar_password_strength(password: str) -> Tuple[bool, Optional[str]]:
        """Valida la fortaleza de una contraseña."""
        if not password or len(password) < 4:
            return False, "La contraseña debe tener al menos 4 caracteres"
        
        return True, None
    
    @staticmethod
    def crear_usuario_completo(username: str, password: str, rol: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """Crea un usuario con validaciones completas."""
        if not username or len(username) < 3:
            return False, "El nombre de usuario debe tener al menos 3 caracteres", None
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "El nombre de usuario solo puede contener letras, números y guión bajo", None
        
        if UsuarioModel.obtener_por_username(username):
            return False, "El nombre de usuario ya existe", None
        
        valido, error = UsuarioModel.validar_password_strength(password)
        if not valido:
            return False, error, None
        
        if rol not in ['curador', 'comite']:
            return False, "Rol inválido. Debe ser 'curador' o 'comite'", None
        
        try:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user_id = UsuarioModel.crear_usuario(username, password_hash, rol)
            
            if user_id:
                logger.info(f"Usuario creado exitosamente: {username}")
                return True, None, user_id
            else:
                return False, "Error al crear el usuario en la base de datos", None
                
        except Exception as e:
            logger.exception(f"Error creando usuario: {e}")
            return False, f"Error: {str(e)}", None
    
    @staticmethod
    def actualizar_nombre_usuario(username: str, nuevo_name: str) -> Tuple[bool, Optional[str]]:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE usuarios SET username = ? WHERE username = ?",
                    (nuevo_name, username)
                )

                if cursor.rowcount > 0:
                    logger.info(f"Nombre de usuario actualizado: {username}")
                    return True, None
                else:
                    return False, "Usuario no encontrado"

        except Exception as e:
            logger.error(f"Error actualizando nombre de usuario: {e}")
            return False, f"Error: {str(e)}"

    @staticmethod
    def actualizar_password(username: str, nueva_password: str) -> Tuple[bool, Optional[str]]:
        """Actualiza la contraseña de un usuario."""
        valido, error = UsuarioModel.validar_password_strength(nueva_password)
        if not valido:
            return False, error
        
        try:
            nuevo_hash = bcrypt.hashpw(nueva_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE usuarios SET password_hash = ? WHERE username = ?",
                    (nuevo_hash, username)
                )
                
                if cursor.rowcount > 0:
                    logger.info(f"Contraseña actualizada para usuario: {username}")
                    return True, None
                else:
                    return False, "Usuario no encontrado"
                    
        except Exception as e:
            logger.error(f"Error actualizando contraseña: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def activar_desactivar_usuario(username: str, activo: bool) -> Tuple[bool, Optional[str]]:
        """Activa o desactiva un usuario."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE usuarios SET activo = ? WHERE username = ?",
                    (1 if activo else 0, username)
                )
                
                if cursor.rowcount > 0:
                    estado = "activado" if activo else "desactivado"
                    logger.info(f"Usuario {estado}: {username}")
                    return True, None
                else:
                    return False, "Usuario no encontrado"
                    
        except Exception as e:
            logger.error(f"Error activando/desactivando usuario: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def eliminar_usuario(username: str) -> Tuple[bool, Optional[str]]:
        """Elimina un usuario del sistema."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COUNT(*) FROM evaluaciones e
                    JOIN usuarios u ON e.usuario_id = u.id
                    WHERE u.username = ?
                """, (username,))
                
                num_evaluaciones = cursor.fetchone()[0]
                cursor.execute("DELETE FROM usuarios WHERE username = ?", (username,))
                
                if cursor.rowcount > 0:
                    logger.warning(f"Usuario eliminado: {username} (tenía {num_evaluaciones} evaluaciones)")
                    return True, None
                else:
                    return False, "Usuario no encontrado"
                    
        except Exception as e:
            logger.error(f"Error eliminando usuario: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def contar_evaluaciones_usuario(username: str) -> int:
        """Cuenta cuántas evaluaciones ha realizado un usuario."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM evaluaciones e
                    JOIN usuarios u ON e.usuario_id = u.id
                    WHERE u.username = ?
                """, (username,))
                
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error contando evaluaciones: {e}")
            return 0


# ═══════════════════════════════════════════════════════════════════
# MODELO: Fichas
# ═══════════════════════════════════════════════════════════════════

class FichaModel:
    """Operaciones sobre la tabla fichas"""
    
    @staticmethod
    def crear_ficha(codigo: str, nombre: str, descripcion: str = None) -> Optional[int]:
        """Crea una nueva ficha de evaluación."""
        try:
            query = """
                INSERT INTO fichas (codigo, nombre, descripcion)
                VALUES (?, ?, ?)
            """
            ficha_id = ejecutar_insert(query, (codigo, nombre, descripcion))
            logger.info(f"Ficha creada: {codigo} (ID: {ficha_id})")
            return ficha_id
        except Exception as e:
            logger.error(f"Error creando ficha: {e}")
            return None
    
    @staticmethod
    def obtener_todas() -> List[Dict]:
        """Obtiene todas las fichas."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM fichas ORDER BY nombre")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error obteniendo fichas: {e}")
            return []
    
    @staticmethod
    def obtener_por_id(ficha_id: int) -> Optional[Dict]:
        """Obtiene una ficha por su ID."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM fichas WHERE id = ?", (ficha_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Error obteniendo ficha: {e}")
            return None
    
    @staticmethod
    def obtener_por_codigo(codigo: str) -> Optional[Dict]:
        """Obtiene una ficha por su código."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM fichas WHERE codigo = ?", (codigo,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Error obteniendo ficha por código: {e}")
            return None
    
    @staticmethod
    def actualizar_ficha(ficha_id: int, nombre: str, descripcion: str = None) -> Tuple[bool, Optional[str]]:
        """Actualiza una ficha existente."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE fichas 
                    SET nombre = ?, descripcion = ?
                    WHERE id = ?
                """, (nombre, descripcion, ficha_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"Ficha actualizada: ID {ficha_id}")
                    return True, None
                else:
                    return False, "Ficha no encontrada"
                    
        except Exception as e:
            logger.error(f"Error actualizando ficha: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def eliminar_ficha(ficha_id: int) -> Tuple[bool, Optional[str]]:
        """Elimina una ficha (y sus relaciones CASCADE)."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM fichas WHERE id = ?", (ficha_id,))
                
                if cursor.rowcount > 0:
                    logger.warning(f"Ficha eliminada: ID {ficha_id}")
                    return True, None
                else:
                    return False, "Ficha no encontrada"
                    
        except Exception as e:
            logger.error(f"Error eliminando ficha: {e}")
            return False, f"Error: {str(e)}"


# ═══════════════════════════════════════════════════════════════════
# MODELO: Dimensiones
# ═══════════════════════════════════════════════════════════════════

class DimensionModel:
    """Operaciones sobre la tabla dimensiones"""
    
    @staticmethod
    def crear_dimension(codigo: str, nombre: str, descripcion: str = None, orden: int = 1) -> Optional[int]:
        """Crea una nueva dimensión."""
        try:
            query = """
                INSERT INTO dimensiones (codigo, nombre, descripcion, orden)
                VALUES (?, ?, ?, ?)
            """
            dim_id = ejecutar_insert(query, (codigo, nombre, descripcion, orden))
            logger.info(f"Dimensión creada: {codigo} (ID: {dim_id})")
            return dim_id
        except Exception as e:
            logger.error(f"Error creando dimensión: {e}")
            return None
    
    @staticmethod
    def obtener_todas() -> List[Dict]:
        """Obtiene todas las dimensiones ordenadas."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM dimensiones ORDER BY orden")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error obteniendo dimensiones: {e}")
            return []
    
    @staticmethod
    def obtener_por_id(dimension_id: int) -> Optional[Dict]:
        """Obtiene una dimensión por su ID."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM dimensiones WHERE id = ?", (dimension_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Error obteniendo dimensión: {e}")
            return None
    
    @staticmethod
    def obtener_por_codigo(codigo: str) -> Optional[Dict]:
        """Obtiene una dimensión por su código."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM dimensiones WHERE codigo = ?", (codigo,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Error obteniendo dimensión: {e}")
            return None
    
    @staticmethod
    def actualizar_dimension(dimension_id: int, nombre: str, descripcion: str = None, orden: int = None) -> Tuple[bool, Optional[str]]:
        """Actualiza una dimensión existente."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if orden is not None:
                    cursor.execute("""
                        UPDATE dimensiones 
                        SET nombre = ?, descripcion = ?, orden = ?
                        WHERE id = ?
                    """, (nombre, descripcion, orden, dimension_id))
                else:
                    cursor.execute("""
                        UPDATE dimensiones 
                        SET nombre = ?, descripcion = ?
                        WHERE id = ?
                    """, (nombre, descripcion, dimension_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"Dimensión actualizada: ID {dimension_id}")
                    return True, None
                else:
                    return False, "Dimensión no encontrada"
                    
        except Exception as e:
            logger.error(f"Error actualizando dimensión: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def eliminar_dimension(dimension_id: int) -> Tuple[bool, Optional[str]]:
        """Elimina una dimensión (y sus aspectos CASCADE)."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM dimensiones WHERE id = ?", (dimension_id,))
                
                if cursor.rowcount > 0:
                    logger.warning(f"Dimensión eliminada: ID {dimension_id}")
                    return True, None
                else:
                    return False, "Dimensión no encontrada"
                    
        except Exception as e:
            logger.error(f"Error eliminando dimensión: {e}")
            return False, f"Error: {str(e)}"


# ═══════════════════════════════════════════════════════════════════
# MODELO: Aspectos
# ═══════════════════════════════════════════════════════════════════

class AspectoModel:
    """Operaciones sobre la tabla aspectos"""
    
    @staticmethod
    def crear_aspecto(dimension_id: int, nombre: str, descripcion: str = None, orden: int = 1) -> Optional[int]:
        """Crea un nuevo aspecto."""
        try:
            query = """
                INSERT INTO aspectos (dimension_id, nombre, descripcion, orden)
                VALUES (?, ?, ?, ?)
            """
            aspecto_id = ejecutar_insert(query, (dimension_id, nombre, descripcion, orden))
            logger.info(f"Aspecto creado: {nombre} (ID: {aspecto_id})")
            return aspecto_id
        except Exception as e:
            logger.error(f"Error creando aspecto: {e}")
            return None
    
    @staticmethod
    def obtener_todos() -> List[Dict]:
        """Obtiene todos los aspectos ordenados."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT a.*, d.nombre as dimension_nombre, d.codigo as dimension_codigo
                    FROM aspectos a
                    JOIN dimensiones d ON a.dimension_id = d.id
                    ORDER BY d.orden, a.orden
                """)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error obteniendo aspectos: {e}")
            return []
    
    @staticmethod
    def obtener_por_dimension(dimension_id: int) -> List[Dict]:
        """Obtiene todos los aspectos de una dimensión específica."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM aspectos 
                    WHERE dimension_id = ? 
                    ORDER BY orden
                """, (dimension_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error obteniendo aspectos de dimensión: {e}")
            return []
    
    @staticmethod
    def obtener_agrupados_por_dimension() -> Dict[int, Dict]:
        """Obtiene aspectos agrupados por dimensión."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        d.id as dimension_id,
                        d.codigo as dimension_codigo,
                        d.nombre as dimension_nombre,
                        d.orden as dimension_orden,
                        a.id as aspecto_id,
                        a.nombre as aspecto_nombre,
                        a.orden as aspecto_orden
                    FROM dimensiones d
                    LEFT JOIN aspectos a ON d.id = a.dimension_id
                    ORDER BY d.orden, a.orden
                """)
                rows = cursor.fetchall()
                
                resultado = {}
                for row in rows:
                    dim_id = row['dimension_id']
                    if dim_id not in resultado:
                        resultado[dim_id] = {
                            'dimension': {
                                'id': row['dimension_id'],
                                'codigo': row['dimension_codigo'],
                                'nombre': row['dimension_nombre'],
                                'orden': row['dimension_orden']
                            },
                            'aspectos': []
                        }
                    
                    if row['aspecto_id']:
                        resultado[dim_id]['aspectos'].append({
                            'id': row['aspecto_id'],
                            'nombre': row['aspecto_nombre'],
                            'orden': row['aspecto_orden']
                        })
                
                return resultado
        except Exception as e:
            logger.error(f"Error obteniendo aspectos agrupados: {e}")
            return {}
    
    @staticmethod
    def obtener_por_ficha(ficha_id: int) -> Dict[int, Dict]:
        """Obtiene aspectos agrupados por dimensión para una ficha específica."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        d.id as dimension_id,
                        d.codigo as dimension_codigo,
                        d.nombre as dimension_nombre,
                        fd.orden as dimension_orden,
                        a.id as aspecto_id,
                        a.nombre as aspecto_nombre,
                        a.orden as aspecto_orden
                    FROM ficha_dimensiones fd
                    JOIN dimensiones d ON fd.dimension_id = d.id
                    LEFT JOIN aspectos a ON d.id = a.dimension_id
                    WHERE fd.ficha_id = ?
                    ORDER BY fd.orden, a.orden
                """, (ficha_id,))
                rows = cursor.fetchall()
                
                resultado = {}
                for row in rows:
                    dim_id = row['dimension_id']
                    if dim_id not in resultado:
                        resultado[dim_id] = {
                            'dimension': {
                                'id': row['dimension_id'],
                                'codigo': row['dimension_codigo'],
                                'nombre': row['dimension_nombre'],
                                'orden': row['dimension_orden']
                            },
                            'aspectos': []
                        }
                    
                    if row['aspecto_id']:
                        resultado[dim_id]['aspectos'].append({
                            'id': row['aspecto_id'],
                            'nombre': row['aspecto_nombre'],
                            'orden': row['aspecto_orden']
                        })
                
                return resultado
        except Exception as e:
            logger.error(f"Error obteniendo aspectos por ficha: {e}")
            return {}
    
    @staticmethod
    def actualizar_aspecto(aspecto_id: int, nombre: str, descripcion: str = None, orden: int = None) -> Tuple[bool, Optional[str]]:
        """Actualiza un aspecto existente."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if orden is not None:
                    cursor.execute("""
                        UPDATE aspectos 
                        SET nombre = ?, descripcion = ?, orden = ?
                        WHERE id = ?
                    """, (nombre, descripcion, orden, aspecto_id))
                else:
                    cursor.execute("""
                        UPDATE aspectos 
                        SET nombre = ?, descripcion = ?
                        WHERE id = ?
                    """, (nombre, descripcion, aspecto_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"Aspecto actualizado: ID {aspecto_id}")
                    return True, None
                else:
                    return False, "Aspecto no encontrado"
                    
        except Exception as e:
            logger.error(f"Error actualizando aspecto: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def eliminar_aspecto(aspecto_id: int) -> Tuple[bool, Optional[str]]:
        """Elimina un aspecto."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM aspectos WHERE id = ?", (aspecto_id,))
                
                if cursor.rowcount > 0:
                    logger.warning(f"Aspecto eliminado: ID {aspecto_id}")
                    return True, None
                else:
                    return False, "Aspecto no encontrado"
                    
        except Exception as e:
            logger.error(f"Error eliminando aspecto: {e}")
            return False, f"Error: {str(e)}"


# ═══════════════════════════════════════════════════════════════════
# MODELO: Ficha-Dimensiones (Relación)
# ═══════════════════════════════════════════════════════════════════

class FichaDimensionModel:
    """Operaciones sobre la relación ficha-dimensiones"""
    
    @staticmethod
    def asignar_dimension_a_ficha(ficha_id: int, dimension_id: int, orden: int) -> Optional[int]:
        """Asigna una dimensión a una ficha."""
        try:
            query = """
                INSERT INTO ficha_dimensiones (ficha_id, dimension_id, orden)
                VALUES (?, ?, ?)
            """
            rel_id = ejecutar_insert(query, (ficha_id, dimension_id, orden))
            logger.info(f"Dimensión {dimension_id} asignada a ficha {ficha_id}")
            return rel_id
        except Exception as e:
            logger.error(f"Error asignando dimensión a ficha: {e}")
            return None
    
    @staticmethod
    def obtener_dimensiones_de_ficha(ficha_id: int) -> List[Dict]:
        """Obtiene todas las dimensiones asignadas a una ficha."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        fd.*,
                        d.codigo as dimension_codigo,
                        d.nombre as dimension_nombre
                    FROM ficha_dimensiones fd
                    JOIN dimensiones d ON fd.dimension_id = d.id
                    WHERE fd.ficha_id = ?
                    ORDER BY fd.orden
                """, (ficha_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error obteniendo dimensiones de ficha: {e}")
            return []
    
    @staticmethod
    def eliminar_dimension_de_ficha(ficha_id: int, dimension_id: int) -> Tuple[bool, Optional[str]]:
        """Elimina una dimensión de una ficha."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM ficha_dimensiones 
                    WHERE ficha_id = ? AND dimension_id = ?
                """, (ficha_id, dimension_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"Dimensión {dimension_id} eliminada de ficha {ficha_id}")
                    return True, None
                else:
                    return False, "Relación no encontrada"
                    
        except Exception as e:
            logger.error(f"Error eliminando dimensión de ficha: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def actualizar_orden_dimensiones(ficha_id: int, dimensiones_ordenadas: List[Tuple[int, int]]) -> Tuple[bool, Optional[str]]:
        """
        Actualiza el orden de las dimensiones de una ficha.
        
        Args:
            ficha_id: ID de la ficha
            dimensiones_ordenadas: Lista de tuplas (dimension_id, nuevo_orden)
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for dimension_id, nuevo_orden in dimensiones_ordenadas:
                    cursor.execute("""
                        UPDATE ficha_dimensiones 
                        SET orden = ?
                        WHERE ficha_id = ? AND dimension_id = ?
                    """, (nuevo_orden, ficha_id, dimension_id))
                
                logger.info(f"Orden de dimensiones actualizado para ficha {ficha_id}")
                return True, None
                    
        except Exception as e:
            logger.error(f"Error actualizando orden de dimensiones: {e}")
            return False, f"Error: {str(e)}"
"""
Continuación de models.py - Grupos, Evaluaciones y Logs
"""

# ═══════════════════════════════════════════════════════════════════
# MODELO: Grupos
# ═══════════════════════════════════════════════════════════════════

class GrupoModel:
    """Operaciones sobre la tabla grupos"""
    
    @staticmethod
    def crear_grupo(codigo: str, nombre_propuesta: str, modalidad: str, 
                   tipo: str, tamano: str, naturaleza: str, ano_evento: int,
                   ficha_id: int = None) -> bool:
        """Crea un nuevo grupo en el catálogo."""
        try:
            valido, codigo_limpio, error = validar_codigo_grupo(codigo)
            if not valido:
                logger.error(f"Código inválido: {error}")
                return False
            
            query = """
                INSERT INTO grupos (codigo, nombre_propuesta, modalidad, tipo, tamano, naturaleza, ano_evento, ficha_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (codigo_limpio, nombre_propuesta, modalidad, tipo, tamano, naturaleza, ano_evento, ficha_id))
            
            logger.info(f"Grupo creado: {codigo_limpio}")
            return True
            
        except Exception as e:
            logger.error(f"Error creando grupo: {e}")
            return False
    
    @staticmethod
    def obtener_por_codigo(codigo: str) -> Optional[Dict]:
        """Obtiene un grupo por su código (con información de ficha)."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        g.*,
                        f.codigo as ficha_codigo,
                        f.nombre as ficha_nombre
                    FROM grupos g
                    LEFT JOIN fichas f ON g.ficha_id = f.id
                    WHERE g.codigo = ?
                """, (codigo,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Error obteniendo grupo: {e}")
            return None
    
    @staticmethod
    def obtener_todos() -> List[Dict]:
        """Obtiene todos los grupos con información de ficha."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        g.*,
                        f.codigo as ficha_codigo,
                        f.nombre as ficha_nombre
                    FROM grupos g
                    LEFT JOIN fichas f ON g.ficha_id = f.id
                    ORDER BY g.codigo
                """)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error obteniendo grupos: {e}")
            return []
    
    @staticmethod
    def asignar_ficha_a_grupo(codigo_grupo: str, ficha_id: int) -> Tuple[bool, Optional[str]]:
        """Asigna una ficha a un grupo."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE grupos 
                    SET ficha_id = ?
                    WHERE codigo = ?
                """, (ficha_id, codigo_grupo))
                
                if cursor.rowcount > 0:
                    logger.info(f"Ficha {ficha_id} asignada a grupo {codigo_grupo}")
                    return True, None
                else:
                    return False, "Grupo no encontrado"
                    
        except Exception as e:
            logger.error(f"Error asignando ficha a grupo: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def cargar_desde_excel(ruta_excel: str, ano_evento: int) -> Tuple[int, int]:
        """
        Carga grupos desde archivo Excel.
        Ahora incluye la columna 'Ficha' para asignar automáticamente.
        """
        insertados = 0
        errores = 0
        
        try:
            df = pd.read_excel(ruta_excel)
            
            columnas_requeridas = ['Codigo', 'Nombre_Propuesta', 'Modalidad', 'Tipo', 'Tamaño', 'Naturaleza']
            if not all(col in df.columns for col in columnas_requeridas):
                logger.error("Columnas faltantes en Excel")
                return 0, len(df)
            
            # Verificar si existe columna Ficha
            tiene_columna_ficha = 'Ficha' in df.columns
            
            for _, row in df.iterrows():
                try:
                    # Obtener ficha_id si existe la columna
                    ficha_id = None
                    if tiene_columna_ficha and pd.notna(row.get('Ficha')):
                        # Buscar ficha por código
                        ficha_codigo = str(row['Ficha']).strip().upper()
                        ficha = FichaModel.obtener_por_codigo(ficha_codigo)
                        if ficha:
                            ficha_id = ficha['id']
                    
                    if GrupoModel.crear_grupo(
                        codigo=row['Codigo'],
                        nombre_propuesta=row['Nombre_Propuesta'],
                        modalidad=row['Modalidad'],
                        tipo=row['Tipo'],
                        tamano=row.get('Tamaño', 'N/A'),
                        naturaleza=row['Naturaleza'],
                        ano_evento=ano_evento,
                        ficha_id=ficha_id
                    ):
                        insertados += 1
                    else:
                        errores += 1
                except Exception as e:
                    logger.error(f"Error insertando grupo {row['Codigo']}: {e}")
                    errores += 1
            
            logger.info(f"Carga finalizada: {insertados} insertados, {errores} errores")
            return insertados, errores
            
        except Exception as e:
            logger.exception(f"Error cargando Excel: {e}")
            return 0, 0
    
    @staticmethod
    def actualizar_ficha_masiva_por_mapeo(mapeo_fichas: Dict[str, int]) -> Tuple[int, int]:
        """
        Actualiza fichas masivamente basándose en un mapeo.
        
        Args:
            mapeo_fichas: Dict con estructura {codigo_ficha: [lista_codigos_grupos]}
            
        Returns:
            Tupla (actualizados, errores)
        """
        actualizados = 0
        errores = 0
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for codigo_ficha, codigos_grupos in mapeo_fichas.items():
                    # Obtener ficha_id
                    ficha = FichaModel.obtener_por_codigo(codigo_ficha)
                    if not ficha:
                        logger.warning(f"Ficha no encontrada: {codigo_ficha}")
                        errores += len(codigos_grupos)
                        continue
                    
                    ficha_id = ficha['id']
                    
                    # Actualizar cada grupo
                    for codigo_grupo in codigos_grupos:
                        cursor.execute("""
                            UPDATE grupos 
                            SET ficha_id = ?
                            WHERE codigo = ?
                        """, (ficha_id, codigo_grupo))
                        
                        if cursor.rowcount > 0:
                            actualizados += 1
                        else:
                            errores += 1
                
                logger.info(f"Actualización masiva: {actualizados} actualizados, {errores} errores")
                return actualizados, errores
                
        except Exception as e:
            logger.exception(f"Error en actualización masiva: {e}")
            return actualizados, errores


# ═══════════════════════════════════════════════════════════════════
# MODELO: Evaluaciones
# ═══════════════════════════════════════════════════════════════════

class EvaluacionModel:
    """Operaciones sobre la tabla evaluaciones"""
    
    @staticmethod
    def crear_evaluacion(usuario_id: int, codigo_grupo: str, ficha_id: int, 
                        aspecto_id: int, resultado: int, observacion: str) -> Optional[int]:
        """Crea una nueva evaluación para un aspecto específico."""
        try:
            valido, error = validar_observacion(observacion)
            if not valido:
                logger.error(f"Observación inválida: {error}")
                return None
            
            query = """
                INSERT INTO evaluaciones (usuario_id, codigo_grupo, ficha_id, aspecto_id, resultado, observacion)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
            eval_id = ejecutar_insert(query, (usuario_id, codigo_grupo, ficha_id, aspecto_id, resultado, observacion))
            logger.info(f"Evaluación creada: ID {eval_id} - Ficha {ficha_id}, Aspecto {aspecto_id}")
            return eval_id
            
        except Exception as e:
            logger.error(f"Error creando evaluación: {e}")
            return None
    
    @staticmethod
    def evaluacion_existe(usuario_id: int, codigo_grupo: str, ficha_id: int) -> bool:
        """Verifica si ya existe una evaluación completa del usuario para el grupo con esa ficha."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Contar cuántos aspectos únicos ha evaluado para esta ficha
                cursor.execute("""
                    SELECT COUNT(DISTINCT aspecto_id)
                    FROM evaluaciones
                    WHERE usuario_id = ? AND codigo_grupo = ? AND ficha_id = ?
                """, (usuario_id, codigo_grupo, ficha_id))
                
                count_evaluado = cursor.fetchone()[0]
                
                # Contar cuántos aspectos totales tiene esta ficha
                cursor.execute("""
                    SELECT COUNT(a.id)
                    FROM aspectos a
                    JOIN ficha_dimensiones fd ON a.dimension_id = fd.dimension_id
                    WHERE fd.ficha_id = ?
                """, (ficha_id,))
                
                count_total = cursor.fetchone()[0]
                
                # Si ha evaluado todos los aspectos de la ficha, la evaluación está completa
                return count_evaluado >= count_total
                
        except Exception as e:
            logger.error(f"Error verificando evaluación: {e}")
            return False
    
    @staticmethod
    def obtener_evaluacion_grupo_usuario(usuario_id: int, codigo_grupo: str) -> List[Dict]:
        """Obtiene todas las evaluaciones de un usuario para un grupo específico."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        e.*,
                        a.nombre as aspecto_nombre,
                        d.nombre as dimension_nombre,
                        f.nombre as ficha_nombre
                    FROM evaluaciones e
                    JOIN aspectos a ON e.aspecto_id = a.id
                    JOIN dimensiones d ON a.dimension_id = d.id
                    JOIN fichas f ON e.ficha_id = f.id
                    WHERE e.usuario_id = ? AND e.codigo_grupo = ?
                    ORDER BY d.orden, a.orden
                """, (usuario_id, codigo_grupo))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error obteniendo evaluaciones: {e}")
            return []
    
    @staticmethod
    def obtener_todas_dataframe() -> pd.DataFrame:
        """Obtiene todas las evaluaciones en formato DataFrame."""
        try:
            with get_db_connection() as conn:
                query = """
                    SELECT 
                        e.id,
                        u.username as curador,
                        e.codigo_grupo,
                        g.nombre_propuesta,
                        g.modalidad,
                        g.tipo,
                        g.naturaleza,
                        f.nombre as ficha,
                        d.nombre as dimension,
                        a.nombre as aspecto,
                        e.resultado,
                        e.observacion,
                        e.fecha_registro
                    FROM evaluaciones e
                    LEFT JOIN usuarios u ON e.usuario_id = u.id
                    LEFT JOIN grupos g ON e.codigo_grupo = g.codigo
                    LEFT JOIN fichas f ON e.ficha_id = f.id
                    JOIN aspectos a ON e.aspecto_id = a.id
                    JOIN dimensiones d ON a.dimension_id = d.id
                    ORDER BY e.fecha_registro DESC
                """
                
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            logger.error(f"Error obteniendo evaluaciones: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def obtener_por_grupo(codigo_grupo: str) -> pd.DataFrame:
        """Obtiene todas las evaluaciones de un grupo específico."""
        try:
            with get_db_connection() as conn:
                query = """
                    SELECT 
                        u.username as curador,
                        f.nombre as ficha,
                        d.nombre as dimension,
                        a.nombre as aspecto,
                        e.resultado,
                        e.observacion,
                        e.fecha_registro
                    FROM evaluaciones e
                    JOIN usuarios u ON e.usuario_id = u.id
                    JOIN fichas f ON e.ficha_id = f.id
                    JOIN aspectos a ON e.aspecto_id = a.id
                    JOIN dimensiones d ON a.dimension_id = d.id
                    WHERE e.codigo_grupo = ?
                    ORDER BY d.orden, a.orden, u.username
                """
                
                df = pd.read_sql_query(query, conn, params=(codigo_grupo,))
                return df
                
        except Exception as e:
            logger.error(f"Error obteniendo evaluaciones del grupo: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def obtener_por_ficha(ficha_id: int) -> pd.DataFrame:
        """Obtiene todas las evaluaciones de una ficha específica."""
        try:
            with get_db_connection() as conn:
                query = """
                    SELECT 
                        e.id,
                        u.username as curador,
                        e.codigo_grupo,
                        g.nombre_propuesta,
                        g.modalidad,
                        d.nombre as dimension,
                        a.nombre as aspecto,
                        e.resultado,
                        e.observacion,
                        e.fecha_registro
                    FROM evaluaciones e
                    LEFT JOIN usuarios u ON e.usuario_id = u.id
                    LEFT JOIN grupos g ON e.codigo_grupo = g.codigo
                    JOIN aspectos a ON e.aspecto_id = a.id
                    JOIN dimensiones d ON a.dimension_id = d.id
                    WHERE e.ficha_id = ?
                    ORDER BY e.fecha_registro DESC
                """
                
                df = pd.read_sql_query(query, conn, params=(ficha_id,))
                return df
                
        except Exception as e:
            logger.error(f"Error obteniendo evaluaciones de ficha: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def obtener_estadisticas_por_ficha() -> pd.DataFrame:
        """Obtiene estadísticas agregadas por ficha."""
        try:
            with get_db_connection() as conn:
                query = """
                    SELECT 
                        f.id as ficha_id,
                        f.nombre as ficha,
                        COUNT(DISTINCT e.codigo_grupo) as grupos_evaluados,
                        COUNT(DISTINCT e.usuario_id) as curadores,
                        COUNT(*) as total_evaluaciones,
                        AVG(e.resultado) as promedio_general,
                        SUM(CASE WHEN e.resultado = 2 THEN 1 ELSE 0 END) as fortalezas,
                        SUM(CASE WHEN e.resultado = 1 THEN 1 ELSE 0 END) as oportunidades,
                        SUM(CASE WHEN e.resultado = 0 THEN 1 ELSE 0 END) as riesgos
                    FROM evaluaciones e
                    JOIN fichas f ON e.ficha_id = f.id
                    GROUP BY f.id, f.nombre
                    ORDER BY promedio_general DESC
                """
                
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas por ficha: {e}")
            return pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════
# MODELO: Logs
# ═══════════════════════════════════════════════════════════════════

class LogModel:
    """Operaciones sobre logs del sistema"""
    
    @staticmethod
    def registrar_log(usuario: str, accion: str, detalle: str = None) -> bool:
        """Registra una acción en los logs."""
        try:
            query = """
                INSERT INTO logs_sistema (usuario, accion, detalle)
                VALUES (?, ?, ?)
            """
            ejecutar_insert(query, (usuario, accion, detalle))
            return True
        except Exception as e:
            logger.error(f"Error registrando log: {e}")
            return False
    
    @staticmethod
    def obtener_logs_recientes(limite: int = 100) -> List[Dict]:
        """Obtiene los logs más recientes."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM logs_sistema 
                    ORDER BY fecha DESC 
                    LIMIT ?
                """, (limite,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error obteniendo logs: {e}")
            return []
    
    @staticmethod
    def obtener_logs_por_usuario(username: str, limite: int = 50) -> List[Dict]:
        """Obtiene los logs de un usuario específico."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM logs_sistema 
                    WHERE usuario = ?
                    ORDER BY fecha DESC 
                    LIMIT ?
                """, (username, limite))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error obteniendo logs de usuario: {e}")
            return []
    
    @staticmethod
    def obtener_logs_dataframe(limite: int = 500) -> pd.DataFrame:
        """Obtiene logs en formato DataFrame."""
        try:
            with get_db_connection() as conn:
                query = """
                    SELECT * FROM logs_sistema 
                    ORDER BY fecha DESC 
                    LIMIT ?
                """
                df = pd.read_sql_query(query, conn, params=(limite,))
                return df
        except Exception as e:
            logger.error(f"Error obteniendo DataFrame de logs: {e}")
            return pd.DataFrame()