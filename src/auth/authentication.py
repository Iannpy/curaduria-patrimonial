"""
Sistema de autenticación y gestión de sesiones
"""
import os
import logging
import bcrypt
import streamlit as st
from typing import Optional, Tuple
from src.database.models import UsuarioModel, LogModel
import base64

logger = logging.getLogger(__name__)


class AuthManager:
    """Gestor de autenticación de usuarios"""
    @staticmethod
    def _obtener_hash_env(username: str) -> Optional[str]:
        """
        Obtiene el hash de contraseña desde variables de entorno.
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Hash de contraseña o None si no existe
        """
        username_upper = username.upper()
        hash_var = f"{username_upper}_HASH"
        return os.getenv(hash_var)
    
    

    @staticmethod
    def verificar_credenciales(username: str, password: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Verifica las credenciales de un usuario (ahora desde BD).
        
        Args:
            username: Nombre de usuario
            password: Contraseña en texto plano
            
        Returns:
            Tupla (autenticado, rol, mensaje_error)
        """
        # Validaciones básicas
        if not username or not password:
            return False, None, "Usuario y contraseña son obligatorios"
        
        username = username.strip()
        
        try:
            # Obtener usuario de la base de datos
            usuario = UsuarioModel.obtener_por_username(username)
            
            if not usuario:
                logger.warning(f"Intento de acceso con usuario inexistente: {username}")
                return False, None, "Credenciales incorrectas"
            
            # Verificar que esté activo
            if not usuario['activo']:
                logger.warning(f"Intento de acceso con usuario inactivo: {username}")
                return False, None, "Usuario desactivado. Contacte al administrador"
            
            # Verificar contraseña con bcrypt
            password_bytes = password.encode('utf-8')
            hash_bytes = usuario['password_hash'].encode('utf-8')
            
            if bcrypt.checkpw(password_bytes, hash_bytes):
                rol = usuario['rol']
                logger.info(f"Autenticación exitosa: {username} ({rol})")
                
                # Registrar en logs
                LogModel.registrar_log(
                    usuario=username,
                    accion="LOGIN",
                    detalle=f"Ingreso exitoso - Rol: {rol}"
                )
                
                return True, rol, None
            else:
                logger.warning(f"Contraseña incorrecta para usuario: {username}")
                return False, None, "Credenciales incorrectas"
                
        except Exception as e:
            logger.exception(f"Error verificando credenciales: {e}")
            return False, None, "Error en el proceso de autenticación"
    @staticmethod
    def inicializar_sesion():
        """
        Inicializa las variables de sesión de Streamlit.
        """
        if "autenticado" not in st.session_state:
            st.session_state.autenticado = False
        
        if "usuario" not in st.session_state:
            st.session_state.usuario = None
        
        if "rol" not in st.session_state:
            st.session_state.rol = None
        
        if "usuario_id" not in st.session_state:
            st.session_state.usuario_id = None
    
    @staticmethod
    def login(username: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        Realiza el proceso de login y actualiza el estado de sesión.
        
        Args:
            username: Nombre de usuario
            password: Contraseña
            
        Returns:
            Tupla (exito, mensaje_error)
        """
        autenticado, rol, error = AuthManager.verificar_credenciales(username, password)
        
        if autenticado:
            # Obtener o crear usuario en BD
            usuario_db = UsuarioModel.obtener_por_username(username)
            
            if not usuario_db:
                # Crear usuario en BD si no existe
                hash_password = AuthManager._obtener_hash_env(username)
                usuario_id = UsuarioModel.crear_usuario(username, hash_password, rol)
            else:
                usuario_id = usuario_db['id']
            
            # Actualizar sesión
            st.session_state.autenticado = True
            st.session_state.usuario = username
            st.session_state.rol = rol
            st.session_state.usuario_id = usuario_id
            
            return True, None
        else:
            return False, error
    
    @staticmethod
    def logout():
        """
        Cierra la sesión del usuario actual.
        """
        if st.session_state.usuario:
            LogModel.registrar_log(
                usuario=st.session_state.usuario,
                accion="LOGOUT",
                detalle="Sesión cerrada"
            )
        
        st.session_state.autenticado = False
        st.session_state.usuario = None
        st.session_state.rol = None
        st.session_state.usuario_id = None
    
    @staticmethod
    def es_curador() -> bool:
        """
        Verifica si el usuario actual es curador.
        
        Returns:
            True si es curador, False en caso contrario
        """
        return st.session_state.get("rol") == "curador"
    
    @staticmethod
    def es_comite() -> bool:
        """
        Verifica si el usuario actual es del comité.
        
        Returns:
            True si es comité, False en caso contrario
        """
        return st.session_state.get("rol") == "comite"
    
    @staticmethod
    def requiere_autenticacion():
        """
        Verifica que el usuario esté autenticado, de lo contrario muestra login.
        Usar como guard al inicio de cada página.
        """
        AuthManager.inicializar_sesion()
        
        if not st.session_state.autenticado:
            AuthManager._mostrar_pantalla_login()
            st.stop()

    @staticmethod
    def _mostrar_pantalla_login():
        """
        Muestra la pantalla de login.
        """


        def set_background(image_file):
            with open(image_file, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()

            st.markdown(
                f"""
                <style>
                .stApp {{
                    background-image: url("data:image/jpg;base64,{encoded}");
                    background-size: cover;
                    background-position: center;
                    background-repeat: no-repeat;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )

        set_background("assets/login_background.jpg")

        
        # 1. Inyectar CSS que apunte al contenedor con una key concreta
        st.markdown(
            """
            <style>
            div.st-key-form_blanco {
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        col1, col2, col3 = st.columns([2, 3, 2])
        with col2:
            with st.container(key="form_blanco"):

                with st.form("login_form", border=True):
                    # Logo
                    col1_logo, col2_logo, col3_logo = st.columns([1, 1, 1])
                    with col2_logo:
                        st.image("assets/CDB_EMPRESA_ASSETS.svg", use_container_width=False)

                    st.markdown("<h3 style='text-align: center;'>Sistema de Curaduría<br>Patrimonial</h3>", unsafe_allow_html=True)
                    st.markdown(
                    "<div style='text-align: center; font-size: 16px; color: gray;'>"
                    "Carnaval de Barranquilla" 
                    "</div>", unsafe_allow_html=True
                    )
                    usuario = st.text_input(label="", placeholder="Usuario")
                    password = st.text_input(label="", placeholder="Contraseña", type="password")
                    # Botón de submit
                    submit = st.form_submit_button("Ingresar", use_container_width=True, type="primary", width="stretch")
                    
                    if submit:
                        if not usuario or not password:
                            st.error("⚠️ Complete todos los campos")
                        else:
                            exito, error = AuthManager.login(usuario, password)
                            
                            if exito:
                                st.success("✅ Ingreso exitoso")
                                st.rerun()
                            else:
                                st.error(f"❌ {error}")


def crear_boton_logout():
    """
    Crea un botón de logout en el sidebar al final.
    """
    with st.sidebar:
        # Separador
        st.markdown("---")
        
        # Info del usuario
        st.markdown(f"**👤 Usuario:** {st.session_state.usuario}")
        st.markdown(f"**🎭 Rol:** {st.session_state.rol.title()}")
        
        # Botón de logout
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="primary"):
            AuthManager.logout()
            st.rerun()  