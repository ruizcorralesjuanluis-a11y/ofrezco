from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.offer import Offer
from app.models.profile import Profile
from app.models.user import User
from app.core.data import CATEGORIES, get_flattened_categories, get_sales_categories

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def format_price(value):
    try:
        # Convertir a entero para quitar el .0
        num = int(float(value)) if value else 0
        # Formatear con puntos para miles (estilo ES)
        return "{:,}".format(num).replace(",", ".")
    except:
        return value

templates.env.filters["format_price"] = format_price

def get_user_context(request: Request):
    return {
        "id": request.session.get("user_id"),
        "name": request.session.get("user_name"),
        "email": request.session.get("user_email"),
        "picture": request.session.get("user_picture"),
        "profile_id": request.session.get("profile_id"),
    }




# -------------------------
# HOME (usa home.html)
# -------------------------
@router.get("/", response_class=HTMLResponse)
@router.get("/ui", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "title": "Ofrezco",
            "page_title": "Inicio",
            "user": get_user_context(request),
        },
    )


# -------------------------
# PUBLICAR NECESIDAD
# -------------------------
@router.get("/ui/need/new", response_class=HTMLResponse)
def ui_need_new(request: Request):
    return templates.TemplateResponse(
        "ui_need_new.html",
        {
            "request": request,
            "title": "Ofrezco · Publicar necesidad",
            "page_title": "Publicar Necesidad",
            "back_url": "/ui",
            "user": get_user_context(request),
            "categories": CATEGORIES,
            "mode": request.query_params.get("mode", ""),
        },
    )


# -------------------------
# RESULTADOS (búsqueda)
# -------------------------
# -------------------------
# RESULTADOS (búsqueda)
# -------------------------
@router.get("/ui/results", response_class=HTMLResponse)
def ui_results(
    request: Request,
    q: str = "",
    cat: str = "",
    mode: str = "",
    urg: str = "",
    db: Session = Depends(get_db)  # Inyección de DB
):
    sales_cats = get_sales_categories()

    # 1. Determinar si es búsqueda de productos (Mercadillo, Inmo, Motor)
    is_product_search = False
    mosaic_cats = [
        "Mercado de Segunda Mano (Venta)",
        "Inmobiliaria (Pisos/Locales)",
        "Vehículos y Motor",
        "Moda y Accesorios",
        "Electrónica y Móviles",
        "Hogar y Muebles"
    ]
    if cat in mosaic_cats or mode == "sales":
        is_product_search = True
        view_mode = "mosaic"
    else:
        view_mode = "list"

    # Siempre usamos el modelo Offer en esta versión del proyecto
    query = select(Offer).where(Offer.status == "PUBLISHED").order_by(Offer.id.desc())

    # 2. Lógica de filtrado estricto
    if cat == "Inmobiliaria (Pisos/Locales)":
        query = query.where(Offer.category == "Inmobiliaria (Pisos/Locales)")
    elif cat == "Vehículos y Motor":
        query = query.where(Offer.category == "Vehículos y Motor")
    elif cat == "Mercado de Segunda Mano (Venta)":
        # Todo el mercadillo EXCEPTO Inmo y Motor
        query = query.where(Offer.category.in_(sales_cats))
        query = query.where(Offer.category.notin_(["Inmobiliaria (Pisos/Locales)", "Vehículos y Motor"]))
    elif mode == "service":
        # Solo servicios: excluir TODAS las de venta
        query = query.where(Offer.category.notin_(sales_cats))
    
    # Si hay una categoría específica manual (ej. "Electricidad")
    if cat and cat not in ["Todas", "Mercado de Segunda Mano (Venta)", "Inmobiliaria (Pisos/Locales)", "Vehículos y Motor"]:
        query = query.where(Offer.category == cat)
    
    if q:
        query = query.where(Offer.title.contains(q))

    items = db.execute(query).scalars().all()
    results = []

    for o in items:
        prof = db.get(Profile, o.profile_id)
        u = db.get(User, prof.user_id) if prof else None
        
        results.append({
            "id": o.profile_id,
            "title": o.title,
            "role": o.title, # Retrocompatibilidad con la card de listado
            "name": u.name if u else "Usuario",
            "category": o.category,
            "offer_cat": o.category, # Retrocompatibilidad
            "price": o.price or 0,
            "video": o.video_path or "", # Path al video
            "photo": o.photo_path or "https://via.placeholder.com/56", 
            "distance_km": 1.2,
            "status": "Disponible" if o.available_now else "Consultar",
            "desc": o.description or "",
            "phone": prof.phone or "",
            "extra": o.extra_info or {}
        })

    return templates.TemplateResponse(
        "ui_results.html",
        {
            "request": request,
            "title": "Ofrezco · Resultados",
            "page_title": "Resultados",
            "back_url": "/ui",

            "results": results, 
            "flat_categories": get_flattened_categories(),
            "q": q, "cat": cat,
            "view_mode": view_mode
        },
    )

@router.get("/ui/feed", response_class=HTMLResponse)
def ui_feed(
    request: Request,
    cat: str = "",
    q: str = "",
    start_id: int = None,
    db: Session = Depends(get_db)
):
    from app.core.data import get_sales_categories
    sales_cats = get_sales_categories()

    query = select(Offer).where(Offer.status == "PUBLISHED").order_by(Offer.id.desc())
    
    # Filtrado similar a ui_results pero enfocado a productos/motor/inmo
    if cat == "Inmobiliaria (Pisos/Locales)":
        query = query.where(Offer.category == "Inmobiliaria (Pisos/Locales)")
    elif cat == "Vehículos y Motor":
        query = query.where(Offer.category == "Vehículos y Motor")
    elif cat == "Mercado de Segunda Mano (Venta)":
        query = query.where(Offer.category.in_(sales_cats))
        query = query.where(Offer.category.notin_(["Inmobiliaria (Pisos/Locales)", "Vehículos y Motor"]))
    elif cat:
         query = query.where(Offer.category == cat)
    
    if q:
        query = query.where(Offer.title.contains(q))

    items = db.execute(query).scalars().all()
    results = []

    for o in items:
        prof = db.get(Profile, o.profile_id)
        u = db.get(User, prof.user_id) if prof else None
        
        results.append({
            "id": o.profile_id,
            "title": o.title,
            "name": u.name if u else "Usuario",
            "category": o.category,
            "price": o.price or 0,
            "video": o.video_path or "",
            "photo": o.photo_path or "https://via.placeholder.com/56", 
            "desc": o.description or "",
            "phone": prof.phone or "",
            "extra": o.extra_info or {}
        })

    return templates.TemplateResponse(
        "ui_item_feed.html",
        {
            "request": request,
            "items": results,
            "back_url": f"/ui/results?cat={cat}&q={q}" if cat or q else "/ui"
        }
    )


# -------------------------
# PERFIL
# -------------------------
@router.get("/ui/profile/{profile_id}", response_class=HTMLResponse)
def ui_profile(request: Request, profile_id: int, db: Session = Depends(get_db)):
    # 1. Obtener perfil
    prof = db.get(Profile, profile_id)
    if not prof:
        return HTMLResponse("<h1>404 - Perfil no encontrado</h1>", status_code=404)
    
    # 2. Obtener usuario asociado
    user_owner = db.get(User, prof.user_id)
    
    # 3. Obtener ofertas del perfil
    offers_q = select(Offer).where(Offer.profile_id == profile_id).where(Offer.status == "PUBLISHED").order_by(Offer.id.desc())
    offers = db.execute(offers_q).scalars().all()

    # Prepara datos para la vista
    profile_data = {
        "id": prof.id,
        "type": prof.profile_type,
        "desc": prof.description,
        "available": prof.available_now,
        "user_name": user_owner.name if user_owner else "Usuario",
        "user_photo": prof.photo if prof.photo else "https://via.placeholder.com/80", # Ahora leemos de la DB
        "photo": prof.photo, # Raw photo path
        "phone": prof.phone or ""
    }

    return templates.TemplateResponse(
        "ui_profile.html",
        {
            "request": request,
            "title": f"Ofrezco · {profile_data['user_name']}",
            "page_title": "Perfil",
            "back_url": "javascript:history.back()",
            "p": profile_data,
            "offers": offers,
            "user": get_user_context(request), 
        },
    )

@router.get("/ui/profile/{profile_id}/edit", response_class=HTMLResponse)
def ui_profile_edit(request: Request, profile_id: int, db: Session = Depends(get_db)):
    # Seguridad básica
    if "user_id" not in request.session: return RedirectResponse("/ui")
    
    prof = db.get(Profile, profile_id)
    if not prof:
        return HTMLResponse("No encontrado", status_code=404)
        
    return templates.TemplateResponse(
        "ui_profile_edit.html",
        {
            "request": request,
            "title": "Editar Perfil",
            "p": prof,
            "back_url": f"/ui/profile/{profile_id}"
        }
    )


# -------------------------
# PUBLICAR OFERTA
# -------------------------
@router.get("/ui/offers/new", response_class=HTMLResponse)
def ui_offer_new(request: Request, type: str = ""):
    if "user_id" not in request.session:
        return RedirectResponse("/ui?login_required=true")
    
    from app.core.data import get_sales_categories

    # Filtrar categorías según el tipo
    filtered_cats = CATEGORIES
    if type == "sales":
        filtered_cats = {k: v for k, v in CATEGORIES.items() if "Venta" in k}
    elif type == "service":
        filtered_cats = {k: v for k, v in CATEGORIES.items() if "Venta" not in k}

    return templates.TemplateResponse(
        "ui_offer_w1.html",
        {
            "request": request,
            "title": "Ofrezco · Nueva oferta (1/4)",
            "user": get_user_context(request),
            "categories": filtered_cats,
            "sales_categories": get_sales_categories(),
            "back_url": "/ui",
            "offer_type": type,
        },
    )



# -------------------------
# WIZARD NUEVA OFERTA (4 pasos)
# -------------------------
@router.get("/ui/offers/new/1", response_class=HTMLResponse)
def ui_offer_w1(request: Request):
    if "user_id" not in request.session: return RedirectResponse("/ui")
    from app.core.data import get_sales_categories
    return templates.TemplateResponse("ui_offer_w1.html", {
        "request": request, 
        "title": "Nueva oferta (1/4)", 
        "page_title": "Paso 1: Info Básica",
        "back_url": "/ui",
        "user": get_user_context(request),
        "categories": CATEGORIES,
        "sales_categories": get_sales_categories(),
    })


@router.get("/ui/offers/new/2", response_class=HTMLResponse)
def ui_offer_w2(request: Request):
    if "user_id" not in request.session: return RedirectResponse("/ui")
    from app.core.data import get_sales_categories
    return templates.TemplateResponse("ui_offer_w2.html", {
        "request": request, 
        "title": "Nueva oferta (2/4)", 
        "page_title": "Paso 2: Ubicación",
        "back_url": "/ui/offers/new/1",
        "user": get_user_context(request),
        "sales_categories": get_sales_categories(),
    })


@router.get("/ui/offers/new/3", response_class=HTMLResponse)
def ui_offer_w3(request: Request):
    if "user_id" not in request.session: return RedirectResponse("/ui")
    from app.core.data import get_sales_categories
    return templates.TemplateResponse("ui_offer_w3.html", {
        "request": request, 
        "title": "Nueva oferta (3/4)", 
        "page_title": "Paso 3: Detalles",
        "back_url": "/ui/offers/new/2",
        "user": get_user_context(request),
        "sales_categories": get_sales_categories(),
    })


@router.get("/ui/offers/new/4", response_class=HTMLResponse)
def ui_offer_w4(request: Request):
    if "user_id" not in request.session: return RedirectResponse("/ui")
    return templates.TemplateResponse("ui_offer_w4.html", {
        "request": request, 
        "title": "Nueva oferta (4/4)", 
        "page_title": "Paso 4: Vídeo",
        "back_url": "/ui/offers/new/3",
        "user": get_user_context(request)
    })

# -------------------------
# LISTADO DE OFERTAS
# -------------------------
@router.get("/ui/offers", response_class=HTMLResponse)
def ui_offers(request: Request):
    return templates.TemplateResponse(
        "ui_offers.html",
        {
            "request": request,
            "title": "Ofrezco · Ofertas",
        },
    )


# -------------------------
# ADMIN
# -------------------------
@router.get("/ui/admin", response_class=HTMLResponse)
def ui_admin(request: Request):
    return templates.TemplateResponse(
        "ui_admin.html",
        {
            "request": request,
            "title": "Ofrezco · Admin",
        },
    )
