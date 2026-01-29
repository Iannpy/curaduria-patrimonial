# Sistema de Curaduría Patrimonial 🎭

Este sistema es una plataforma diseñada para la evaluación, gestión y seguimiento de propuestas artísticas y culturales en eventos patrimoniales. Permite a curadores y comités técnicos evaluar dimensiones críticas del rigor tradicional, sentido cultural e innovación pertinente.

## 🚀 Características Principales

- **Gestión de Autenticación:** Sistema de login seguro con roles diferenciados (Curador y Comité).
- **Evaluación por Ficha Dinámica:** Los grupos son evaluados según fichas personalizadas, cada una con sus propias dimensiones y aspectos.
- **Dashboard y Análisis Avanzado (Módulo Comité):**
  - **KPIs Profesionales:** Métricas clave con desviaciones estándar y porcentajes.
  - **Análisis Estadístico:** Distribuciones de promedios (mediana, cuartiles, rango, box plots).
  - **Insights y Recomendaciones:** Mensajes proactivos basados en el desempeño de los grupos.
  - **Entrega de Congos de Oro:** Cálculo del 25% superior de grupos por **ficha** (no por modalidad), con ranking y visualización.
  - **Análisis Detallados:** Vistas por Grupos, Fichas, Dimensiones, Aspectos y Curadores con tablas interactivas y gráficos Altair.
  - **Exportación Flexible:** Datos exportables a Excel y CSV en Evaluaciones Detalladas y Análisis por Grupos.
- **Interfaz Intuitiva:** Desarrollada con Streamlit para una experiencia de usuario fluida y moderna.

## 🛠️ Tecnologías Utilizadas

- **Lenguaje:** Python 3.x
- **Frontend/UI:** [Streamlit](https://streamlit.io/)
- **Base de Datos:** SQLite
- **Librerías Clave:**
  - `pandas`: Procesamiento y análisis de datos.
  - `bcrypt`: Seguridad y hash de contraseñas.
  - `openpyxl`: Integración con Excel.
  - `python-dotenv`: Gestión de variables de entorno.
  - `altair`: Visualizaciones interactivas y declarativas.

## 📁 Estructura del Proyecto

```text
curaduria_patrimonial/
├── assets/             # Recursos estáticos (logos, imágenes)
├── data/               # Base de datos y archivos Excel
├── logs/               # Registros de eventos de la aplicación
├── scripts/            # Utilidades de mantenimiento y configuración
│   ├── gen_password.py
│   ├── limpiar_y_sincronizar.py
│   ├── recrear_env.py
│   ├── asignar_fichas_grupos.py        # Nuevo: Asigna fichas a grupos desde Excel
│   ├── eliminar_evaluaciones_grupo_curador.py # Nuevo: Elimina evaluaciones de un grupo/curador
│   └── restablecer_evaluaciones.py     # Resetea evaluaciones (ejemplo)
├── src/                # Código fuente principal
│   ├── auth/           # Lógica de autenticación y sesiones
│   ├── database/       # Conexiones y modelos de datos
│   ├── ui/             # Componentes de la interfaz de usuario
│   │   ├── comite/     # Módulos específicos del comité (dashboard, utils, etc.)
│   │   └── admin_fichas_view.py # Gestión de fichas y dimensiones
│   ├── utils/          # Funciones auxiliares (validadores, dimensiones iniciales)
│   └── config.py       # Configuración global
├── main.py             # Punto de entrada de la aplicación
├── requirements.txt    # Dependencias de Python
├── .env                # Variables de entorno (Configuración)
└── REFACTORING_NOTES.md # Notas sobre optimizaciones y mejoras
```

## ⚙️ Instalación y Configuración

1. **Clonar el repositorio:**
   ```bash
   git clone <url-del-repositorio>
   cd curaduria_patrimonial
   ```

2. **Crear un entorno virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**
   Crea un archivo `.env` basado en `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Ajusta los valores según sea necesario (rutas de DB, nombres de eventos, etc.).

5. **Inicializar la Base de Datos:**
   Es crucial inicializar la base de datos y cargar las fichas y dimensiones.
   Ejecuta: `python src/database/init_db.py`
   Luego, si tienes un Excel con grupos, puedes sincronizarlos: `python scripts/asignar_fichas_grupos.py`
   Para crear usuarios iniciales, puedes usar `scripts/crear_usuario.py`.

## 🖥️ Uso

Para iniciar la aplicación, ejecuta:

```bash
streamlit run main.py
```

La aplicación se abrirá automáticamente en tu navegador predeterminado (usualmente en `http://localhost:8501`).

## ✨ Refactorización y Mejoras Recientes

Durante un reciente proceso de auditoría y mejora, se realizaron las siguientes optimizaciones:

### Dashboard y Análisis del Comité:
- **Dashboard General:** Se mejoró con KPIs más detallados, análisis estadísticos (mediana, cuartiles), y una sección de "Congos de Oro" que ahora considera el 25% superior de grupos por **Ficha** (previamente era por modalidad).
- **Análisis por Grupos:** Se refactorizó con una interfaz de dos pestañas: una para búsqueda individual por código y otra para análisis consolidado con filtros avanzados (por ficha, por estado y ordenamiento), y exportación a Excel/CSV.
- **Análisis por Dimensión y Aspecto:** Se enriquecieron con más métricas estadísticas (mediana, desviación estándar), gráficos de distribución, y la identificación de los aspectos más fuertes y los que requieren atención.
- **Análisis por Curador:** Se amplió con métricas de productividad, consistencia y una comparativa de promedios otorgados.
- **Exportación:** La sección de "Evaluaciones Detalladas" ahora incluye un botón para exportar los datos a Excel, además de CSV.

### Optimización de Código General:
- **Queries SQL:** Optimizada `EvaluacionModel.evaluacion_existe()` para un rendimiento superior.
- **Manejo de Transacciones:** Scripts de mantenimiento (`asignar_fichas_grupos.py`) fueron refactorizados para usar un context manager, garantizando consistencia y mejor manejo de errores.
- **Validaciones:** Se centralizó y mejoró la consistencia de las validaciones de datos en los modelos de la base de datos.
- **Script de Eliminación de Evaluaciones:** Se agregó un nuevo script `scripts/eliminar_evaluaciones_grupo_curador.py` para facilitar la eliminación específica de evaluaciones por grupo y curador.

## 🛡️ Seguridad

El sistema utiliza `bcrypt` para el manejo de contraseñas. Nunca guarde contraseñas en texto plano en el archivo `.env` o en la base de datos sin el proceso de hashing adecuado.

---
© 2026 - Sistema de Curaduría Patrimonial
