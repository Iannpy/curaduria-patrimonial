# Sistema de Curaduría Patrimonial 🎭

Este sistema es una plataforma diseñada para la evaluación, gestión y seguimiento de propuestas artísticas y culturales en eventos patrimoniales. Permite a curadores y comités técnicos evaluar dimensiones críticas del rigor tradicional, sentido cultural e innovación pertinente.

## 🚀 Características Principales

- **Gestión de Autenticación:** Sistema de login seguro con roles diferenciados (Curador y Comité).
- **Evaluación Multidimensional:**
  - `Dimensión 1`: Rigor en la ejecución tradicional.
  - `Dimensión 2`: Transmisión del sentido cultural.
  - `Dimensión 3`: Vitalidad e innovación con pertinencia.
- **Visualización de Datos:** Dashboards interactivos para el seguimiento de métricas y estados de las propuestas.
- **Exportación y Sincronización:** Herramientas para manejar bases de datos en SQLite y sincronizar con archivos Excel.
- **Interfaz Intuitiva:** Desarrollada con Streamlit para una experiencia de usuario fluida y moderna.

## 🛠️ Tecnologías Utilizadas

- **Lenguaje:** Python 3.x
- **Frontend/UI:** [Streamlit](https://streamlit.io/)
- **Base de Datos:** SQLite
- **Librerías Clave:**
  - `pandas`: Procesamiento de datos.
  - `bcrypt`: Seguridad y hash de contraseñas.
  - `openpyxl`: Integración con Excel.
  - `python-dotenv`: Gestión de variables de entorno.
  - `altair`: Visualizaciones interactivas.

## 📁 Estructura del Proyecto

```text
curaduria_patrimonial/
├── assets/             # Recursos estáticos (logos, imágenes)
├── data/               # Base de datos y archivos Excel
├── logs/               # Registros de eventos de la aplicación
├── scripts/            # Utilidades de mantenimiento y configuración
│   ├── gen_password.py
│   ├── limpiar_y_sincronizar.py
│   └── recrear_env.py
├── src/                # Código fuente principal
│   ├── auth/           # Lógica de autenticación y sesiones
│   ├── database/       # Conexiones y modelos de datos
│   ├── ui/             # Componentes de la interfaz de usuario
│   ├── utils/          # Funciones auxiliares
│   └── config.py       # Configuración global
├── main.py             # Punto de entrada de la aplicación
├── requirements.txt    # Dependencias de Python
└── .env                # Variables de entorno (Configuración)
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
   Si es la primera vez que se usa, ejecuta los scripts necesarios en `src/database/init_db.py` o utiliza las herramientas en `scripts/`.

## 🖥️ Uso

Para iniciar la aplicación, ejecuta:

```bash
streamlit run main.py
```

La aplicación se abrirá automáticamente en tu navegador predeterminado (usualmente en `http://localhost:8501`).

## 🛡️ Seguridad

El sistema utiliza `bcrypt` para el manejo de contraseñas. Nunca guarde contraseñas en texto plano en el archivo `.env` o en la base de datos sin el proceso de hashing adecuado.

---
© 2026 - Sistema de Curaduría Patrimonial
