"""
Modelos de datos y operaciones CRUD
ACTUALIZADO: Incluye gestión completa de usuarios
"""
import logging
import pandas as pd
import bcrypt
import re
from typing import Optional, List, Dict, Tuple
from src.database.connection import get_db_connection, ejecutar_insert
from src.utils.validators import validar_codigo_grupo, validar_observacion

logger = logging.getLogger(__name__)


class UsuarioModel:
    """Operaciones sobre la tabla usuarios"""
    
    @staticmethod
    def crear_usuario(username: str, password_hash: str, rol: str) -> Optional[int]:
        """
        Crea un nuevo usuario en el sistema.
        
        Args:
            username: Nombre de usuario único
            password_hash: Hash bcrypt de la contraseña
            rol: 'curador' o 'comite'
            
        Returns:
            ID del usuario creado o None si falla
        """
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
        """
        Obtiene un usuario por su username.
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Diccionario con datos del usuario o None
        """
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
        """
        Obtiene un usuario por su ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Diccionario con datos del usuario o None
        """
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
        """
        Obtiene todos los usuarios del sistema.
        
        Args:
            incluir_inactivos: Si True, incluye usuarios inactivos
            
        Returns:
            Lista de diccionarios con datos de usuarios
        """
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
        """
        Obtiene todos los usuarios en formato DataFrame.
        
        Returns:
            DataFrame con usuarios
        """
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
        """
        Valida la fortaleza de una contraseña.
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Tupla (es_valida, mensaje_error)
        """
        if not password or len(password) < 4:
            return False, "La contraseña debe tener al menos 4 caracteres"
        
        # Opcional: Validaciones más estrictas (descomentarlas si se requiere)
        # if not re.search(r'[A-Z]', password):
        #     return False, "La contraseña debe contener al menos una mayúscula"
        # if not re.search(r'[a-z]', password):
        #     return False, "La contraseña debe contener al menos una minúscula"
        # if not re.search(r'[0-9]', password):
        #     return False, "La contraseña debe contener al menos un número"
        
        return True, None
    
    @staticmethod
    def crear_usuario_completo(username: str, password: str, rol: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Crea un usuario con validaciones completas.
        
        Args:
            username: Nombre de usuario
            password: Contraseña en texto plano
            rol: Rol del usuario
            
        Returns:
            Tupla (exito, mensaje_error, user_id)
        """
        # Validar username
        if not username or len(username) < 3:
            return False, "El nombre de usuario debe tener al menos 3 caracteres", None
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "El nombre de usuario solo puede contener letras, números y guión bajo", None
        
        # Verificar que no exista
        if UsuarioModel.obtener_por_username(username):
            return False, "El nombre de usuario ya existe", None
        
        # Validar contraseña
        valido, error = UsuarioModel.validar_password_strength(password)
        if not valido:
            return False, error, None
        
        # Validar rol
        if rol not in ['curador', 'comite']:
            return False, "Rol inválido. Debe ser 'curador' o 'comite'", None
        
        try:
            # Generar hash
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Crear usuario
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
        """
        Actualiza la contraseña de un usuario.
        
        Args:
            username: Nombre de usuario
            nueva_password: Nueva contraseña en texto plano
            
        Returns:
            Tupla (exito, mensaje_error)
        """
        # Validar contraseña
        valido, error = UsuarioModel.validar_password_strength(nueva_password)
        if not valido:
            return False, error
        
        try:
            # Generar nuevo hash
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
        """
        Activa o desactiva un usuario.
        
        Args:
            username: Nombre de usuario
            activo: True para activar, False para desactivar
            
        Returns:
            Tupla (exito, mensaje_error)
        """
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
        """
        Elimina un usuario del sistema.
        NOTA: Esto también eliminará todas sus evaluaciones (CASCADE).
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Tupla (exito, mensaje_error)
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Primero verificar si tiene evaluaciones
                cursor.execute("""
                    SELECT COUNT(*) FROM evaluaciones e
                    JOIN usuarios u ON e.usuario_id = u.id
                    WHERE u.username = ?
                """, (username,))
                
                num_evaluaciones = cursor.fetchone()[0]
                
                # Eliminar usuario (CASCADE eliminará evaluaciones automáticamente)
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
        """
        Cuenta cuántas evaluaciones ha realizado un usuario.
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Cantidad de evaluaciones
        """
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


# ═══════════════════════════════════════════════════════════
# RESTO DE MODELOS (sin cambios)
# ═══════════════════════════════════════════════════════════

class GrupoModel:
    """Operaciones sobre la tabla grupos"""
    
    @staticmethod
    def crear_grupo(codigo: str, nombre_propuesta: str, modalidad: str, 
                   tipo: str, tamano: str, naturaleza: str, ano_evento: int) -> bool:
        """Crea un nuevo grupo en el catálogo."""
        try:
            valido, codigo_limpio, error = validar_codigo_grupo(codigo)
            if not valido:
                logger.error(f"Código inválido: {error}")
                return False
            
            query = """
                INSERT INTO grupos (codigo, nombre_propuesta, modalidad, tipo, tamano, naturaleza, ano_evento)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (codigo_limpio, nombre_propuesta, modalidad, tipo, tamano, naturaleza, ano_evento))
            
            logger.info(f"Grupo creado: {codigo_limpio}")
            return True
            
        except Exception as e:
            logger.error(f"Error creando grupo: {e}")
            return False
    
    @staticmethod
    def obtener_por_codigo(codigo: str) -> Optional[Dict]:
        """Obtiene un grupo por su código."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM grupos WHERE codigo = ?", (codigo,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Error obteniendo grupo: {e}")
            return None
    
    @staticmethod
    def cargar_desde_excel(ruta_excel: str, ano_evento: int) -> Tuple[int, int]:
        """Carga grupos desde archivo Excel."""
        insertados = 0
        errores = 0
        
        try:
            df = pd.read_excel(ruta_excel)
            
            columnas_requeridas = ['Codigo', 'Nombre_Propuesta', 'Modalidad', 'Tipo', 'Tamaño', 'Naturaleza']
            if not all(col in df.columns for col in columnas_requeridas):
                logger.error("Columnas faltantes en Excel")
                return 0, len(df)
            
            for _, row in df.iterrows():
                try:
                    if GrupoModel.crear_grupo(
                        codigo=row['Codigo'],
                        nombre_propuesta=row['Nombre_Propuesta'],
                        modalidad=row['Modalidad'],
                        tipo=row['Tipo'],
                        tamano=row['Tamaño'],
                        naturaleza=row['Naturaleza'],
                        ano_evento=ano_evento
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


class DimensionModel:
    """Operaciones sobre la tabla dimensiones"""
    
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


class EvaluacionModel:
    """Operaciones sobre la tabla evaluaciones"""
    
    @staticmethod
    def crear_evaluacion(usuario_id: int, codigo_grupo: str, dimension_id: int,
                        resultado: int, observacion: str) -> Optional[int]:
        """Crea una nueva evaluación."""
        try:
            valido, error = validar_observacion(observacion)
            if not valido:
                logger.error(f"Observación inválida: {error}")
                return None
            
            query = """
                INSERT INTO evaluaciones (usuario_id, codigo_grupo, dimension_id, resultado, observacion)
                VALUES (?, ?, ?, ?, ?)
            """
            
            eval_id = ejecutar_insert(query, (usuario_id, codigo_grupo, dimension_id, resultado, observacion))
            logger.info(f"Evaluación creada: ID {eval_id}")
            return eval_id
            
        except Exception as e:
            logger.error(f"Error creando evaluación: {e}")
            return None
    
    @staticmethod
    def evaluacion_existe(usuario_id: int, codigo_grupo: str) -> bool:
        """Verifica si ya existe una evaluación completa del usuario para el grupo."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COUNT(DISTINCT dimension_id)
                    FROM evaluaciones
                    WHERE usuario_id = ? AND codigo_grupo = ?
                """, (usuario_id, codigo_grupo))
                
                count = cursor.fetchone()[0]
                return count >= 3
                
        except Exception as e:
            logger.error(f"Error verificando evaluación: {e}")
            return False
    
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
                        d.nombre as dimension,
                        e.resultado,
                        e.observacion,
                        e.fecha_registro
                    FROM evaluaciones e
                    LEFT JOIN usuarios u ON e.usuario_id = u.id
                    LEFT JOIN grupos g ON e.codigo_grupo = g.codigo
                    JOIN dimensiones d ON e.dimension_id = d.id
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
                        d.nombre as dimension,
                        e.resultado,
                        e.observacion,
                        e.fecha_registro
                    FROM evaluaciones e
                    JOIN usuarios u ON e.usuario_id = u.id
                    JOIN dimensiones d ON e.dimension_id = d.id
                    WHERE e.codigo_grupo = ?
                    ORDER BY d.orden, u.username
                """
                
                df = pd.read_sql_query(query, conn, params=(codigo_grupo,))
                return df
                
        except Exception as e:
            logger.error(f"Error obteniendo evaluaciones del grupo: {e}")
            return pd.DataFrame()


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