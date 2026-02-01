import random
from app.db.session import SessionLocal
from app.models.user import User
from app.models.profile import Profile
from app.models.offer import Offer
# Importar modelos relacionados para evitar errores de Mapper
from app.models.rating import Rating
from app.models.interest import Interest

# Categorías de venta
SALES_CATEGORIES = [
    "Inmobiliaria (Pisos/Locales)",
    "Vehículos y Motor",
    "Electrónica y Móviles",
    "Moda y Accesorios",
    "Hogar y Muebles",
    "Deportes y Ocio",
    "Coleccionismo",
    "Otros Productos"
]

# Datos de prueba (Fotos de placeholder públicas)
IMAGES = [
    "https://images.unsplash.com/photo-1550989460-0adf9ea622e2?q=80&w=300&auto=format&fit=crop", # Ropa/Tienda
    "https://images.unsplash.com/photo-1542281286-9e0a56eafeff?q=80&w=300&auto=format&fit=crop", # Coche
    "https://images.unsplash.com/photo-1593642702821-c8da6771f0c6?q=80&w=300&auto=format&fit=crop", # Tech
    "https://images.unsplash.com/photo-1556906781-9a412961d28c?q=80&w=300&auto=format&fit=crop", # Zapatillas
    "https://images.unsplash.com/photo-1524758631624-e2822e304c36?q=80&w=300&auto=format&fit=crop", # Muebles
    "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?q=80&w=300&auto=format&fit=crop", # Ordenador
]

# Títulos y descripciones generados
ITEMS = [
    ("iPhone 13 casi nuevo", "Vendo iPhone 13 en perfecto estado, siempre con funda.", "Electrónica y Móviles", 600),
    ("Sofá de piel 3 plazas", "Sofá muy cómodo, color beige. Transporte no incluido.", "Hogar y Muebles", 250),
    ("Bicicleta de Montaña Orbea", "Bici talla M, suspensión delantera. Poco uso.", "Deportes y Ocio", 350),
    ("BMW Serie 1 2018", "Coche diesel, 120.000km, todas las revisiones al día.", "Vehículos y Motor", 18500),
    ("Colección de sellos antiguos", "Sellos de España y colonias, años 50-80.", "Coleccionismo", 100),
    ("Vestido de fiesta Zara", "Talla M, usado una vez para una boda.", "Moda y Accesorios", 45),
    ("Mesa de comedor extensible", "Madera maciza, se abre hasta 2.5m.", "Hogar y Muebles", 180),
    ("PlayStation 5 con 2 mandos", "Consola en caja original, funciona perfecta.", "Electrónica y Móviles", 450),
    ("Botas de esquí Salomon", "Talla 42, modelo X-Pro. Bastante uso pero funcionales.", "Deportes y Ocio", 80),
    ("Piso en Centro, 2 habs", "Alquiler temporal o venta. Reformado.", "Inmobiliaria (Pisos/Locales)", 250000),
]

def populate():
    db = SessionLocal()
    try:
        # Asegurar usuario vendedor
        user_email = "vendedor@test.com"
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"Creando usuario {user_email}...")
            user = User(name="Vendedor Test", email=user_email)
            db.add(user)
            db.commit()
            db.refresh(user)

        # Asegurar perfil
        profile = user.profile
        if not profile:
            print("Creando perfil de vendedor...")
            profile = Profile(
                user_id=user.id,
                profile_type="PARTICULAR",
                description="Vendo cosas que ya no uso.",
                phone="600123456",
                available_now=True
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)

        print("Generando 20 ofertas de venta...")
        
        for i in range(20):
            # Elegir item aleatorio o generar variantes
            base_item = random.choice(ITEMS)
            
            # Variar precios y titulos ligeramente para no duplicar exacto
            price_var = base_item[3] + random.randint(-20, 20)
            if price_var < 5: price_var = 5
            
            offer = Offer(
                profile_id=profile.id,
                offer_kind="PRODUCTO",
                category=base_item[2],
                title=f"{base_item[0]} #{i+1}",
                description=base_item[1] + " ¡Preguntar sin compromiso!",
                price=float(price_var),
                currency="EUR",
                available_now=True,
                status="PUBLISHED",
                video_path=random.choice(IMAGES) # Usamos video_path como foto principal de momento
            )
            db.add(offer)
        
        db.commit()
        print("¡20 Ofertas creadas con éxito!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    populate()
