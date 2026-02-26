"""
Sistema de Curaduría Patrimonial
Punto de entrada principal de la aplicación
"""
import logging
import streamlit as st
from src.auth.authentication import AuthManager, crear_boton_logout
from src.config import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Curaduría Patrimonial",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado
st.markdown("""
<style>
.header-box {
    border: 2px solid #ddd;
    padding: 20px;
    border-radius: 10px;
    background-color: #f8f9fa;
    margin-bottom: 20px;
}
.gradient-bar {
    height: 8px;
    background: linear-gradient(to right, #d7191c, #fdae61, #1a9641, #00a600, #006837, #0066cc);
    
}
.dimension-box {
    border: 2px solid #e0e0e0;
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
    background-color: #ffffff;
    font-size: 32px;
    font-weight: 700;
    color: #27ae60;
}
.dimension-title {
    font-weight: 700;
    font-size: 18px;
    color: #2c3e50;
    margin-bottom: 15px;
}
.metric-card {
    background-color: white;
    padding: 10px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    text-align: left;
    margin-bottom: 20px;
    font-size: 18px;
    color: #2c3e50;
}

.metric-value {
    font-size: 32px;
    color: black;
</style>
""", unsafe_allow_html=True)


def main():
    """Función principal de la aplicación"""
    
    # Requerir autenticación
    AuthManager.requiere_autenticacion()
    
    # Botón de logout en sidebar
    
    
    # Routing según rol
    if AuthManager.es_curador():
        from src.ui.curador_view import mostrar_vista_curador
        crear_boton_logout()
        mostrar_vista_curador()
        
    
    elif AuthManager.es_comite():
        from src.ui.comite_view import mostrar_vista_comite
        mostrar_vista_comite()
    
    elif AuthManager.es_admin():
        from src.ui.administrador_view import mostrar_vista_comite
        mostrar_vista_comite()
    
    else:
        st.error("⚠️ Rol no reconocido")
        if st.button("Cerrar Sesión"):
            AuthManager.logout()
            st.rerun()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Error en la aplicación: {e}")
        st.error(f"❌ Error en la aplicación: {str(e)}")
        st.info("💡 Contacte al administrador del sistema si el error persiste")