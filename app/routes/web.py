from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.offer import Offer
from app.models.profile import Profile
from app.models.user import User
from app.models.rating import Rating
from app.core.data import CATEGORIES, get_sales_categories

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
# Force Reload Trigger

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
            "categories": CATEGORIES,
        },
    )


# -------------------------
# PUBLICAR NECESIDAD
# -------------------------
@router.get("/ui/need/new", response_class=HTMLResponse)
def ui_need_new(request: Request, mode: str = ""):
    return templates.TemplateResponse(
        "ui_need_new.html",
        {
            "request": request,
            "title": "Ofrezco · Publicar necesidad",
            "page_title": "Publicar Necesidad",
            "back_url": "/ui",
            "user": get_user_context(request),
            "categories": CATEGORIES,
            "mode": mode,
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
    urg: str = "",
    mode: str = "",
    db: Session = Depends(get_db)  # Inyección de DB
):
    from app.core.data import get_flattened_categories
    # Base query: Ofertas publicadas
    query = select(Offer).where(Offer.status == "PUBLISHED").order_by(Offer.id.desc())

    from sqlalchemy import or_

    # Filtros básicos
    if cat and cat != "Todas" and cat != "":
        # Comprobar si es una Categoría Padre (ej. Mercado de Segunda Mano)
        if cat in CATEGORIES:
            subcats = CATEGORIES[cat]
            query = query.where(Offer.category.in_(subcats))
        else:
            # Es una subcategoría específica
            query = query.where(Offer.category == cat)

    if q:
        # Búsqueda más amplia (título o descripción, case-insensitive)
        search_term = f"%{q}%"
        query = query.where(
            or_(
                Offer.title.ilike(search_term),
                Offer.description.ilike(search_term)
            )
        )

    # Filtro por modo (Venta vs Servicio)
    from app.core.data import get_sales_categories
    sales_cats = get_sales_categories()
    if mode == "sales":
        query = query.where(Offer.category.in_(sales_cats))
    elif mode == "service":
        query = query.where(~Offer.category.in_(sales_cats))

    offers = db.execute(query).scalars().all()

    # Formatear para la vista "ui_results.html" (espera objetos 'p')
    results = []
    for o in offers:
        # Cargar perfil/usuario (idealmente con join, aquí lazy loading por simplicidad)
        # Asumimos que profile y user están relacionados en el modelo o los buscamos
        # El modelo Offer tiene profile_id. El Profile tiene user_id. 
        # Vamos a hacer una chapuza rápida para demo: buscar el profile -> user
        
        # Necesitamos la foto y el nombre. 
        # Offer -> relation 'profile' -> relation 'user'
        # Si las relaciones no están definidas en SQLAlchemy Models (lazy='joined'), hay que hacer queries.
        # Revisando user.py y profile.py, definen relaciones?
        # Asumiremos que sí o haremos query manual.
        
        # Query manual rápida para asegurar:
        prof = db.get(Profile, o.profile_id)
        u = db.get(User, prof.user_id) if prof else None
        
        # Calcular valoración del perfil
        stmt_rating = select(func.count(Rating.id), func.avg(Rating.score)).where(Rating.profile_id == o.profile_id)
        r_count, r_avg = db.execute(stmt_rating).one()
        
        results.append({
            "id": o.profile_id, # El enlace va al perfil
            "offer_id": o.id,   # Guardamos el ID de la oferta específica
            "name": u.name if u else "Usuario",
            "role": o.title,    # Mostramos el Título de la oferta como "Rol" principal
            "title": o.title,   # Mapping explicito para vista mosaico
            "category": o.category, # Mapping explicito para vista mosaico
            "photo": (prof.photo if prof and prof.photo else "https://via.placeholder.com/56"), 
            # Priorizamos video de la oferta, si no, del perfil
            "video": getattr(o, "video_path", None) or (prof.video_url if prof else None),
            "distance_km": 1.2, # Fake distance
            "status": "Disponible" if o.available_now else "Consultar",
            "offer_cat": o.category,
            "price": o.price,
            "currency": o.currency,
            "rating_avg": round(r_avg, 1) if r_avg else 0,
            "rating_count": r_count or 0
        })

    # Detectar modo de vista
    view_mode = "list"
    if cat and ("Venta" in cat or "Mercado" in cat or "mercadillo" in cat.lower()):
        view_mode = "mosaic"

    return templates.TemplateResponse(
        "ui_results.html",
        {
            "request": request,
            "title": "Ofrezco · Resultados",
            "page_title": "Resultados",
            "back_url": "/ui/need/new",

            "results": results, 
            "flat_categories": get_flattened_categories(), # Para filtros
            "q": q, "cat": cat, "mode": mode, # Mantener filtros seleccionados
            "view_mode": view_mode,
        },
    )


# -------------------------
# PERFIL
# -------------------------
@router.get("/ui/profile/{profile_id}", response_class=HTMLResponse)
def ui_profile(request: Request, profile_id: int, offer_id: int = None, db: Session = Depends(get_db)):
    # 1. Obtener perfil
    prof = db.get(Profile, profile_id)
    if not prof:
        return HTMLResponse("<h1>404 - Perfil no encontrado</h1>", status_code=404)
    
    # 2. Obtener usuario asociado
    user_owner = db.get(User, prof.user_id)
    
    # 3. Obtener ofertas del perfil
    offers_q = select(Offer).where(Offer.profile_id == profile_id).where(Offer.status == "PUBLISHED")
    
    if offer_id:
        offers_q = offers_q.where(Offer.id == offer_id)
        
    offers_q = offers_q.order_by(Offer.id.desc())
    offers = db.execute(offers_q).scalars().all()

    # Separar por tipo
    sales_cats = get_sales_categories()
    service_offers = [o for o in offers if o.category not in sales_cats]
    sales_offers = [o for o in offers if o.category in sales_cats]

    # Prepara datos para la vista
    profile_data = {
        "id": prof.id,
        "type": prof.profile_type,
        "desc": prof.description,
        "available": prof.available_now,
        "user_name": user_owner.name if user_owner else "Usuario",
        "user_photo": prof.photo if prof.photo else "https://via.placeholder.com/80", # Ahora leemos de la DB
        "photo": prof.photo, # Raw photo path
        "phone": prof.phone,
        "lat": prof.lat,
        "lon": prof.lon,
        "address": prof.address
    }

    return templates.TemplateResponse(
        "ui_profile.html",
        {
            "request": request,
            "title": f"Ofrezco · {profile_data['user_name']}",
            "page_title": "Perfil",
            "back_url": "javascript:history.back()",
            "p": profile_data,
            "service_offers": service_offers,
            "sales_offers": sales_offers,
            "user": get_user_context(request),
            "is_me": "user_id" in request.session and request.session["user_id"] == prof.user_id 
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
            "offer_type": type, # Para que el frontend sepa qué modo es
        },
    )



# -------------------------
# WIZARD NUEVA OFERTA (4 pasos)
# -------------------------
@router.get("/ui/offers/new/1", response_class=HTMLResponse)
def ui_offer_w1(request: Request):
    if "user_id" not in request.session: return RedirectResponse("/ui")
    return templates.TemplateResponse("ui_offer_w1.html", {
        "request": request, 
        "title": "Nueva oferta (1/4)", 
        "page_title": "Paso 1: Info Básica",
        "back_url": "/ui/offers/new",
        "user": get_user_context(request),
        "categories": CATEGORIES,
        "sales_categories": get_sales_categories(),
    })


@router.get("/ui/offers/new/2", response_class=HTMLResponse)
def ui_offer_w2(request: Request):
    if "user_id" not in request.session: return RedirectResponse("/ui")
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
