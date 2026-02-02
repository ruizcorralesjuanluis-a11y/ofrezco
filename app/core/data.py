
# Categorías y Subcategorías del sistema
# Se usa para poblar los selects en frontend

CATEGORIES = {
    "Hogar y Mantenimiento": [
        "Electricidad",
        "Fontanería",
        "Limpieza del hogar",
        "Jardinería",
        "Pintura",
        "Mudanzas",
        "Carpintería",
        "Albañilería",
        "Climatización (Aire Acondicionado)",
        "Reparación de electrodomésticos"
    ],
    "Tecnología e Informática": [
        "Soporte Técnico PC/Mac",
        "Instalación de Redes/WiFi",
        "Desarrollo Web",
        "Reparación de Móviles",
        "Configuración Smart Home"
    ],
    "Clases y Formación": [
        "Idiomas (Inglés, Francés...)",
        "Matemáticas y Ciencias",
        "Música e Instrumentos",
        "Entrenamiento Personal",
        "Yoga y Pilates"
    ],
    "Eventos y Ocio": [
        "Fotografía",
        "DJ y Música en vivo",
        "Catering y Cocina",
        "Animación infantil",
        "Organización de eventos"
    ],
    "Belleza y Bienestar": [
        "Peluquería a domicilio",
        "Manicura/Pedicura",
        "Masajes",
        "Maquillaje"
    ],
    "Transporte y Recados": [
        "Chófer privado",
        "Mensajería urgente",
        "Compras y recados",
        "Paseo de perros"
    ],
    "Cuidado de Personas": [
        "Cuidado de niños (Babysitter)",
        "Cuidado de mayores",
        "Enfermería a domicilio"
    ],
    "Otros Servicios": [
        "Traducción y textos",
        "Gestoría y trámites",
        "Otros"
    ],
    "Mercadillo y Segunda Mano": [
        "Venta de cosas",
        "Ropa y Accesorios",
        "Muebles y Deco",
        "Electrónica"
    ]
}

def get_flattened_categories():
    """Retorna una lista plana de todas las subcategorías para selects simples"""
    flat = []
    for cat, subs in CATEGORIES.items():
        flat.extend(subs)
    return sorted(list(set(flat)))
