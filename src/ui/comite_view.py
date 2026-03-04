"""
Vista de la interfaz para el Comité
ACTUALIZADO: Análisis corregido para evaluaciones por aspecto
"""
import streamlit as st
import logging
from src.config import config
from src.database.models import EvaluacionModel, AspectoModel, FichaModel, FichaDimensionModel
from src.auth.authentication import crear_boton_logout
from streamlit_option_menu import option_menu
from .comite.congos_oro_view import mostrar_congos_oro
from .comite.dashboard import mostrar_dashboard
from .administrador_view import mostrar_evaluaciones_detalladas, mostrar_analisis_grupos
logger = logging.getLogger(__name__)

import numpy as np

# Configuración de la página    
def mostrar_vista_comite():
    """Renderiza la vista completa del comité"""
    # Cargar evaluaciones
    df_eval = EvaluacionModel.obtener_todas_dataframe()
    
    # Sidebar - Navegación
    with st.sidebar:
        icons = [
        "speedometer2",        # Dashboard General
        "trophy",             # Congos de Oro
        "clipboard-data",      # Evaluaciones Detalladas
        "people",              # Análisis por Grupos
        ]
        pagina = option_menu(
            "Menú de Análisis",
            [
                "Dashboard General",
                "Gala de premios",
                "Evaluaciones Detalladas",
                "Análisis por Grupos",
                
            ],
            icons=icons,
            menu_icon="clipboard-data",
            default_index=0,
            orientation="vertical",
        )
        
        crear_boton_logout()
    
    
    
    # Routing según página seleccionada
    if pagina == "Dashboard General":
        mostrar_dashboard(df_eval)
    elif pagina == "Gala de premios":
        mostrar_congos_oro()
    elif pagina == "Evaluaciones Detalladas":
        mostrar_evaluaciones_detalladas(df_eval)
    elif pagina == "Análisis por Grupos":
        mostrar_analisis_grupos(df_eval)
 