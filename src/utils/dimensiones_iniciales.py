# ═══════════════════════════════════════════════════════════════════
# DATOS INICIALES - FICHAS
# ═══════════════════════════════════════════════════════════════════


FICHAS_INICIALES = [
    {
        'codigo': 'CONGO',
        'nombre': 'Ficha Congo',
        'descripcion': 'Modalidad Danza Tradicional - Congo'
    },
    {
        'codigo': 'GARABATO',
        'nombre': 'Ficha Garabato',
        'descripcion': 'Modalidad Danza Tradicional - Garabato'
    },
    {
        'codigo': 'CUMBIA',
        'nombre': 'Ficha Cumbia',
        'descripcion': 'Modalidad Cumbia'
    },
    {
        'codigo': 'MAPALE',
        'nombre': 'Ficha Mapalé',
        'descripcion': 'Modalidad Danza Tradicional - Mapalé'
    },
    {
        'codigo': 'SON_NEGRO',
        'nombre': 'Ficha Son de Negro',
        'descripcion': 'Modalidad Danza Tradicional - Son de Negro'
    },
    {
        'codigo': 'COMPARSA_TRAD',
        'nombre': 'Ficha Comparsa de Tradición',
        'descripcion': 'Naturaleza Tradición Popular'
    },
    {
        'codigo': 'COMPARSA_FANT',
        'nombre': 'Ficha Comparsa de Fantasía',
        'descripcion': 'Naturaleza Fantasía'
    },
    {
        'codigo': 'DANZAS_ESP',
        'nombre': 'Ficha Danzas Especiales',
        'descripcion': 'Danzas de Relación, Danzas Especiales y Expresiones Invitadas'
    }
]


# ═══════════════════════════════════════════════════════════════════
# DATOS INICIALES - DIMENSIONES Y ASPECTOS
# ═══════════════════════════════════════════════════════════════════

DIMENSIONES_INICIALES = [
    # Grupo 1
    {"codigo": "DIM1",
     "nombre": "Puesta en escena - Congo",
     "orden": 1,
     "aspectos": [
         "Danza guerrera, alegre y colorida: Movimientos fuertes, enérgicos,con pasos cadenciosos y marcados, imitando gestos de combate."]
    },
    {"codigo": "DIM2",
     "nombre": "Coreografía - Congo",
     "orden": 2,
     "aspectos": [
         "Baile de casa",
         "Paso de marca"]
    },
    {"codigo": "DIM3",
     "nombre": "Vestuario y Parafernalia - Congo",
     "orden": 3,
     "aspectos": [
         "Mujeres",
         "Hombres",
         "Fauna"]
    },
    {"codigo": "DIM4",
     "nombre": "Marcación del ritmo - Congo",
     "orden": 4,
     "aspectos": [
         "Movimientos de marcación: cuatro tiempos hacia la derecha y hacia la izquierda alternativamente",
         "Las mujeres bailan desplazándose hacia la derecha y hacia la izquierda, mueven los hombros y sujetan la falda con las manos para moverla."]
    },
    {"codigo": "DIM5",
     "nombre": "Música - Congo",
     "orden": 5,
     "aspectos": [
         "El grupo musical está compuesto por tambor alegre, la guacharaca tradicional del Congo",
         "Golpe de tambor"]
    },

    # Grupo 2
    {"codigo": "DIM6",
     "nombre": "Puesta en escena - Garabato",
     "orden": 6,
     "aspectos": [
         "Representación de la lucha entre la vida y la muerte, protagonizada por un caporal (la vida) que coquetea con una mujer mientras la Muerte intenta separarlos, pero el hombre, con su garabato (bastón), triunfa y demuestra la perpetuidad de la vida"]
    },
    {"codigo": "DIM7",
     "nombre": "Coreografía - Garabato",
     "orden": 7,
     "aspectos": [
         "Desplazamiento al ritmo del toque del tambor, en cuadrillas o en figuras de caracoles, culebras, abanicos, túneles o representando el movimiento de las olas",
         "La mujer no puede hacer faldeo en el baile",
         "La danza incluye teatro popular representando la lucha de la vida con la muerte sin incluir elementos de comicidad."]
    },
    {"codigo": "DIM8",
     "nombre": "Vestuario y Parafernalia - Garabato",
     "orden": 8,
     "aspectos": [
         "Mujeres",
         "Hombres",
         "Muerte"]
    },
    {"codigo": "DIM9",
     "nombre": "Marcación del ritmo - Garabato",
     "orden": 9,
     "aspectos": [
         "El ritmo se marca de acuerdo a la música tradicional de la danza al igual que los desplazamientos y acentos: paso básico (izquierda adelante, derecha atrás), la acentuación de los 4 tiempos con un balanceo cadencioso y la escucha activa de la música para coordinar pies y hombros, usando el garabato como guía rítmica"]
    },
    {"codigo": "DIM10",
     "nombre": "Música - Garabato",
     "orden": 10,
     "aspectos": [
         "El grupo musical que acompaña a la danza está compuesto por un cantador y un coro, una tambora y tambores de un solo parche, acompañado de guache, maracas, flauta e 'millo y palmas o tablitas. Puede o no llevar clarinete"]
    },

    # Grupo 3
    {"codigo": "DIM11",
     "nombre": "Expresión dancística - Cumbiamba",
     "orden": 11,
     "aspectos": [
         "El Sonido de la Flauta se interioriza y eleva la expresividad generando la altivez corporal y elegancia de la mujer",
         "En el hombre se muestran sentimientos de alegría expresados en comportamientos de Cortejo y conquista para con la mujer",
         "Manejo del contacto visual (gestos, miradas y sonrisas) en pareja indicando el coqueteo y galanteo. Evita que supareja la toque",
         "Gritos/Güiros y expresiones de júbilo por parte de los participantes de la rueda para llamar la atención del momento vivido"]
    },
    {"codigo": "DIM12",
     "nombre": "Coreografía - Cumbiamba",
     "orden": 12,
     "aspectos": [
         "Momentos escénicos y planimetría o ubicación espacial",
         "Baile de parejas y conservación del círculo en sentidoc ontrario a las manecillas del reloj"]
    },
    {"codigo": "DIM13",
     "nombre": "Vestuario y Parafernalia - Cumbiamba",
     "orden": 13,
     "aspectos": [
         "Mujeres",
         "Hombres"]
    },
    {"codigo": "DIM14",
     "nombre": "Marcación del ritmo + interpretación musical",
     "orden": 14,
     "aspectos": [
         "La mujer marca con oscilaciones laterales (pendular) de la cadera en forma natural, sin exagerar y su posición es serena y erguida",
         "Estabilidad rítmica",
         "La pollera se levanta en forma pausada, elegante mostrando señorío, sin movimientos bruscos",
         "La mujer desliza los pies sobre el piso con pasos cortos",
         "El Hombre tiene libertad de movimiento y marca el ritmo con los dos pies, se apoya levantando uno",
         "Música: El grupo musical típico que acompaña a la cumbia está compuesto por tambor alegre, llamador, tambora, guache, maracas y flauta de millo o gaita, que interpreta sones de cumbia"]
    },
    {"codigo": "DIM15",
     "nombre": "Música",
     "orden": 15,
     "aspectos": [
         "Riqueza sonora",
         "Respeto por la tradición"]
    },

    # Grupo 4
    {"codigo": "DIM16",
     "nombre": "Puesta en escena - Mapalé",
     "orden": 16,
     "aspectos": [
         "La percusión es uno de sus elementos distintivos, características propias de la etnia de este continente, al igual que los movimientos fuertes"]
    },
    {"codigo": "DIM17",
     "nombre": "Coreografía - Mapalé",
     "orden": 17,
     "aspectos": [
         "La coreografía es libre y va de acuerdo al baile y al ritmo musical denominado “Mapalé”",
         "En el baile tradicional no se presentan figuras ni elementos circenses."]
    },
    {"codigo": "DIM18",
     "nombre": "Vestuario y Parafernalia",
     "orden": 18,
     "aspectos": [
         "Mujeres",
         "Hombres"]
    },
    {"codigo": "DIM19",
     "nombre": "Marcación del ritmo - Mapalé",
     "orden": 19,
     "aspectos": [
         "Baile de los Hombres; los movimientos del cuerpo son rápidos y fuertes, se representan con contorciones, brincos y desplazamientos horizontales, en el paso del caimán tradicional de la danza, se apoyan sobre manos y pies",
         "En el Baile de las mujeres, los sensuales movimientos de las caderas, la pelvis, los glúteos y la cintura pueden ser rápidos o lentos"]
    },
    {"codigo": "DIM20",
     "nombre": "Música - Mapalé",
     "orden": 20,
     "aspectos": [
         "El grupo musical que acompaña a la danza está compuesto por un cantador y un coro, una tambora y tambores de un solo parche, acompañado de guache, maracas, flauta e' millo y palmas o tablitas. Puede o no llevar clarinete"]
    },

    # Grupo 5
    {"codigo": "DIM21",
     "nombre": "Expresiones corporales y faciales de burla exagerada",
     "orden": 21,
     "aspectos": [
         "Seguridad en la interpretación",
         "Comunicación escénica"]
    },
    {"codigo": "DIM22",
     "nombre": "Coreografía - Son de Negro",
     "orden": 22,
     "aspectos": [
         "Estructura del baile",
         "Precisión en los movimientos"]
    },
    {"codigo": "DIM23",
     "nombre": "Vestuario y Parafernalia - Son de Negro",
     "orden": 23,
     "aspectos": [
         "Mujeres",
         "Hombres",
         "Parafernalia y maquillaje"]
    },
    {"codigo": "DIM24",
     "nombre": "Marcación del ritmo - Son de Negro",
     "orden": 24,
     "aspectos": [
         "El baile de los hombres semeja convulsiones que se mezclan con expresiones rígidas",
         "El baile de la mujer tiene movimientos de caderas y con los glúteos buscan golpear al hombre, este trata de evitar el contacto"]
    },
    {"codigo": "DIM25",
     "nombre": "Música",
     "orden": 25,
     "aspectos": [
         "Integración instrumental",
         'El tema distintivo de la danza del son de negro es la canción "La Rama de Tamarindo". Se interpreta con Tambor alegre, guacharaca o guache, claves, tablas o palmas']
    }
]



# ═══════════════════════════════════════════════════════════════════
# MAPEO: FICHAS → DIMENSIONES
# ═══════════════════════════════════════════════════════════════════

# Por defecto, todas las fichas tendrán las 3 dimensiones básicas
# Puedes modificar esto según las necesidades específicas de cada ficha

FICHA_DIMENSIONES_MAP = {
    'CONGO': ['DIM1', 'DIM2', 'DIM3', 'DIM4', 'DIM5'],
    'GARABATO': ['DIM6', 'DIM7', 'DIM8', 'DIM9', 'DIM10'],
    'CUMBIA': ['DIM11', 'DIM12', 'DIM13', 'DIM14'],
    'MAPALE': ['DIM16', 'DIM17', 'DIM18', 'DIM19', 'DIM20'],
    'SON_DE_NEGRO': ['DIM21', 'DIM22', 'DIM23', 'DIM24', 'DIM25'],
    'COMPARSA_TRAD': ['DIM1', 'DIM2', 'DIM3'],
    'COMPARSA_FANT': ['DIM1', 'DIM2', 'DIM3'],
    'DANZAS_ESP': ['DIM2', 'DIM3']  # Ejemplo: esta ficha no tiene DIM1
}
