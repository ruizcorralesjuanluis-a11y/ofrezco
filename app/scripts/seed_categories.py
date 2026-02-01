from app.db.session import SessionLocal, engine
from app.db.base import Base

# IMPORTANTÍSIMO: importar el modelo para que SQLAlchemy lo registre
from app.models.category import Category  # noqa: F401


CATEGORIES = [
    # Padres
    ("hogar", "Hogar", None),
    ("clases", "Clases particulares", None),
    ("tecnologia", "Tecnología", None),
    ("eventos", "Eventos", None),
    ("comida", "Comida", None),
    ("mascotas", "Mascotas", None),
    ("otros", "Otros", None),

    # Hogar -> Subcategorías principales
    ("reparaciones", "Reparaciones", "hogar"),
    ("instalaciones", "Instalaciones", "hogar"),
    ("limpieza", "Limpieza", "hogar"),
    ("mudanzas", "Mudanzas y portes", "hogar"),
    ("jardineria", "Jardinería", "hogar"),
    ("pintura", "Pintura", "hogar"),
    ("bricolaje", "Bricolaje / Montaje", "hogar"),

    # Reparaciones
    ("electricidad", "Electricidad", "reparaciones"),
    ("fontaneria", "Fontanería", "reparaciones"),
    ("cerrajeria", "Cerrajería", "reparaciones"),
    ("electrodomesticos", "Electrodomésticos", "reparaciones"),
    ("climatizacion", "Aire acondicionado / Calefacción", "reparaciones"),

    # Instalaciones
    ("antenas", "Antenas y TV", "instalaciones"),
    ("paneles_solares", "Paneles solares", "instalaciones"),
    ("alarmas", "Alarmas y seguridad", "instalaciones"),
    ("cocinas", "Cocinas", "instalaciones"),

    # Limpieza
    ("limpieza_hogar", "Limpieza del hogar", "limpieza"),
    ("limpieza_oficinas", "Limpieza de oficinas", "limpieza"),
    ("limpieza_fin_obra", "Limpieza fin de obra", "limpieza"),

    # Clases
    ("clases_mates", "Clases de matemáticas", "clases"),
    ("clases_ingles", "Clases de inglés", "clases"),
    ("clases_musica", "Clases de música", "clases"),
    ("clases_informatica", "Clases de informática", "clases"),

    # Tecnología
    ("reparacion_movil", "Reparación de móviles", "tecnologia"),
    ("reparacion_pc", "Reparación de ordenadores", "tecnologia"),
    ("wifi_redes", "WiFi y redes", "tecnologia"),

    # Eventos
    ("fotografia", "Fotografía", "eventos"),
    ("dj", "DJ", "eventos"),
    ("catering", "Catering", "eventos"),

    # Comida
    ("comida_casera", "Comida casera", "comida"),
    ("reposteria", "Repostería", "comida"),

    # Mascotas
    ("paseador_perros", "Paseador de perros", "mascotas"),
    ("cuidador_mascotas", "Cuidador de mascotas", "mascotas"),
]


def run():
    # ✅ crea tablas faltantes
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # mapa parent slug -> id
    slug_to_id = {c.slug: c.id for c in db.query(Category).all()}

    created = 0
    for slug, name, parent_slug in CATEGORIES:
        exists = db.query(Category).filter(Category.slug == slug).first()
        if exists:
            continue

        parent_id = slug_to_id.get(parent_slug)

        cat = Category(
            slug=slug,
            name=name,
            parent_id=parent_id,
            active=True,
        )
        db.add(cat)
        db.flush()
        slug_to_id[slug] = cat.id
        created += 1

    db.commit()
    db.close()
    print(f"✅ Categorías creadas: {created}")


if __name__ == "__main__":
    run()
