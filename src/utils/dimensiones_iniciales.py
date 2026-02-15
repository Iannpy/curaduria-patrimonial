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
        'codigo': 'SON_DE_NEGRO',
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
        'codigo': 'DANZAS_REL',
        'nombre': 'Ficha Danzas de Relación',
        'descripcion': 'Danzas de Relación'
    },
    {
        'codigo': 'DANZAS_ESP',
        'nombre': 'Ficha Danzas Especiales',
        'descripcion': 'Danzas Especiales'
    },
    {
        'codigo': 'EXPRESIONES_I',
        'nombre': 'Ficha Expresiones Invitadas',
        'descripcion': 'Expresiones Invitadas'
    }
    
]


# ═══════════════════════════════════════════════════════════════════
# DATOS INICIALES - DIMENSIONES Y ASPECTOS
# ═══════════════════════════════════════════════════════════════════

DIMENSIONES_INICIALES = [
    # Grupo 1
    {"codigo": "DIM1",
     "nombre": "Gran Parada de Tradición - Congo",
     "orden": 1,
     "aspectos": [
         "Puesta en escena.",
         "Vestuario del hombre, la mujer y la fauna, si la tiene.",
         "Marcación del ritmo.",
         "Coreografía paso de marcha.",
         "Música."]
    },
    {"codigo": "DIM2",
     "nombre": "Gran Parada de Tradición - Garabato",
     "orden": 2,
     "aspectos": [
         "Coreografía libre de acuerdo a la tradición de la danza."]
    },
    {"codigo": "DIM3",
     "nombre": "Gran Parada de Tradición - Cumbiamba",
     "orden": 3,
     "aspectos": [
         "Coreografía.",
         "Expresión dancística de la Cumbia.",
         "Vestuario y parafernalia.",
         "Marcación del ritmo e interpretación musical."]
    },
    {"codigo": "DIM4",
     "nombre": "Gran Parada de Tradición - Mapalé",
     "orden": 4,
     "aspectos": [
         "Coreografía libre de acuerdo a la tradición de la danza."]
    },
    {"codigo": "DIM5",
     "nombre": "Gran Parada de Fantasía - Comparsa de Tradición Popular",
     "orden": 5,
     "aspectos": [
         "Interpretación dancística",
         "Puesta en escena",
         "Coreografía.",
         "Vestuario y parafernalia.",
         "Musica y ritmo."]
    },

    # Grupo 2
    {"codigo": "DIM6",
     "nombre": "Gran Parada de Fantasía - Comparsa de Fantasía",
     "orden": 6,
     "aspectos": [
         "Propuesta escénica.",
         "Proyección artística.",
         "Coreografía.",
         "Música.",
         "Vestuario y parafernalia."]
    },

    {"codigo": "DIM7",
     "nombre": "No es calificable",
     "orden": 7,
     "aspectos": [
         "No es calificable"]
            },
]





# ═══════════════════════════════════════════════════════════════════
# MAPEO: FICHAS → DIMENSIONES
# ═══════════════════════════════════════════════════════════════════

# Por defecto, todas las fichas tendrán las 3 dimensiones básicas
# Puedes modificar esto según las necesidades específicas de cada ficha

FICHA_DIMENSIONES_MAP = {
    'CONGO': ['DIM1'],
    'GARABATO': ['DIM2'],
    'CUMBIA': ['DIM3'],
    'MAPALE': ['DIM4'],
    'SON_DE_NEGRO': ['DIM7'],
    'COMPARSA_TRAD': ['DIM5'],
    'COMPARSA_FANT': ['DIM6'],
    'DANZAS_REL' : ['DIM7'],
    'DANZAS_ESP': ['DIM7'],
    'EXPRESIONES_I' : ['DIM7']
}
