from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from app.db.init_db import init_db, reset_db_completely

from app.db.session import get_db
from app.models.offer import Offer
from app.models.profile import Profile
from app.models.user import User
from app.models.rating import Rating
from app.core.data import CATEGORIES, get_sales_categories

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
# Force Reload Trigger

def get_user_context(request: Request, db: Session = None):
    user_id = request.session.get("user_id")
    profile_id = request.session.get("profile_id")
    
    # Si hay sesión pero no hay DB (raro), devolvemos lo que hay
    if not db:
        return {
            "id": user_id,
            "name": request.session.get("user_name"),
            "email": request.session.get("user_email"),
            "picture": request.session.get("user_picture"),
            "profile_id": profile_id,
        }

    # 1. VERIFICAR USUARIO
    if user_id:
        user_exists = db.execute(select(User.id).where(User.id == user_id)).scalar()
        if not user_exists:
            print(f"DEBUG: Usuario {user_id} no existe en DB. Limpiando sesión.")
            request.session.clear()
            return {"id": None, "name": None, "email": None, "picture": None, "profile_id": None}

    # 2. VERIFICAR PERFIL
    if profile_id:
        p_exists = db.execute(select(Profile.id).where(Profile.id == profile_id)).scalar()
        if not p_exists:
            print(f"DEBUG: Perfil {profile_id} no encontrado en DB. Limpiando profile_id.")
            request.session.pop("profile_id", None)
            profile_id = None

    return {
        "id": user_id,
        "name": request.session.get("user_name"),
        "email": request.session.get("user_email"),
        "picture": request.session.get("user_picture"),
        "profile_id": profile_id,
    }




# -------------------------
# HOME (usa home.html)
# -------------------------
@router.get("/", response_class=HTMLResponse)
@router.get("/ui", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "title": "Ofrezco",
            "page_title": "Inicio",
            "user": get_user_context(request, db),
            "categories": CATEGORIES,
        },
    )


# -------------------------
# PUBLICAR NECESIDAD
# -------------------------
@router.get("/ui/need/new", response_class=HTMLResponse)
def ui_need_new(request: Request, db: Session = Depends(get_db), mode: str = ""):
    return templates.TemplateResponse(
        "ui_need_new.html",
        {
            "request": request,
            "title": "Ofrezco · Publicar necesidad",
            "page_title": "Publicar Necesidad",
            "back_url": "/ui",
            "user": get_user_context(request, db),
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
def ui_results(request: Request, db: Session = Depends(get_db), cat: str = None, q: str = None, mode: str = "service", exclude_cat: str = None, exclude_cat2: str = None):
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

    if exclude_cat:
        query = query.where(Offer.category != exclude_cat)
    if exclude_cat2:
        query = query.where(Offer.category != exclude_cat2)

    # Filtro por modo (Venta vs Servicio)
    sales_cats = get_sales_categories()
    if mode == "sales":
        query = query.where(Offer.category.in_(sales_cats))
    elif mode == "service":
        query = query.where(~Offer.category.in_(sales_cats))

    try:
        offers = db.execute(query).scalars().all()
    except Exception as e:
        print(f"ERROR query offers: {str(e)}")
        offers = []

    # Formatear para la vista "ui_results.html" (espera objetos 'p')
    results = []
    for o in offers:
        try:
            prof = db.get(Profile, o.profile_id)
            u = db.get(User, prof.user_id) if prof else None
            
            # Calcular valoración
            stmt_rating = select(func.count(Rating.id), func.avg(Rating.score)).where(Rating.profile_id == o.profile_id)
            res_rating = db.execute(stmt_rating).one()
            r_count = res_rating[0] or 0
            r_avg = res_rating[1] or 0
            
            results.append({
                "id": o.profile_id,
                "offer_id": o.id,
                "name": u.name if u else "Usuario",
                "role": o.title,
                "title": o.title,
                "category": o.category,
                "photo": getattr(o, "photo_path", None) or (prof.photo if prof and prof.photo else "https://via.placeholder.com/56"), 
                "video": getattr(o, "video_path", None) or (prof.video_url if prof else None),
                "distance_km": 1.2,
                "status": "Disponible" if o.available_now else "Consultar",
                "offer_cat": o.category,
                "price": o.price,
                "currency": o.currency,
                "extra_info": getattr(o, "extra_info", {}) or {},
                "rating_avg": round(r_avg, 1),
                "rating_count": r_count
            })
        except Exception as e:
            print(f"ERROR procesando oferta {getattr(o, 'id', '?')}: {str(e)}")
            continue # Ignorar ofertas corruptas para no romper el listado

    # Detectar modo de vista
    view_mode = "list"
    if cat and ("Venta" in cat or "Mercado" in cat or "mercadillo" in cat.lower()):
        view_mode = "mosaic"

    return templates.TemplateResponse(
        "ui_results.html",
        {
            "request": request,
            "title": "Resultados V4" if not cat else f"{cat} V4",
            "user": get_user_context(request, db),
            "categories": CATEGORIES,
            "page_title": "Resultados",
            "back_url": "/ui/need/new",

            "results": results, 
            "flat_categories": get_flattened_categories(), # Para filtros
            "q": q, "cat": cat, "mode": mode, "exclude_cat": exclude_cat, # Mantener filtros seleccionados
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
            "title": f"Perfil de {profile_data['user_name']}",
            "user": get_user_context(request, db),
            "p": profile_data,
            "service_offers": service_offers,
            "sales_offers": sales_offers,
            "is_me": request.session.get("profile_id") == profile_id
        }
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
            "back_url": f"/ui/profile/{profile_id}",
            "user": get_user_context(request, db),
        }
    )


# -------------------------
# PUBLICAR OFERTA
# -------------------------
@router.get("/ui/offers/new", response_class=HTMLResponse)
def ui_offer_new(request: Request, db: Session = Depends(get_db), type: str = ""):
    if "user_id" not in request.session:
        return RedirectResponse("/ui?login_required=true")
    
    # Validar que el user tiene perfil ANTES de pasar al wizard
    u_context = get_user_context(request, db)
    if not u_context["profile_id"]:
        return RedirectResponse("/ui?profile_required=true")
    
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
            "user": u_context,
            "categories": filtered_cats,
            "sales_categories": get_sales_categories(),
            "offer_type": type, # Para que el frontend sepa qué modo es
        },
    )



# -------------------------
# WIZARD NUEVA OFERTA (4 pasos)
# -------------------------
@router.get("/ui/offers/new/1", response_class=HTMLResponse)
def ui_offer_w1(request: Request, db: Session = Depends(get_db)):
    if "user_id" not in request.session: return RedirectResponse("/ui")
    return templates.TemplateResponse("ui_offer_w1.html", {
        "request": request, 
        "title": "Nueva oferta (1/4)", 
        "page_title": "Paso 1: Info Básica",
        "back_url": "/ui/offers/new",
        "user": get_user_context(request, db),
        "categories": CATEGORIES,
        "sales_categories": get_sales_categories(),
    })


@router.get("/ui/offers/new/2", response_class=HTMLResponse)
def ui_offer_w2(request: Request, db: Session = Depends(get_db)):
    if "user_id" not in request.session: return RedirectResponse("/ui")
    return templates.TemplateResponse("ui_offer_w2.html", {
        "request": request, 
        "title": "Nueva oferta (2/4)", 
        "page_title": "Paso 2: Ubicación",
        "back_url": "/ui/offers/new/1",
        "user": get_user_context(request, db),
        "sales_categories": get_sales_categories(),
    })


@router.get("/ui/offers/new/3", response_class=HTMLResponse)
def ui_offer_w3(request: Request, db: Session = Depends(get_db)):
    if "user_id" not in request.session: return RedirectResponse("/ui")
    return templates.TemplateResponse("ui_offer_w3.html", {
        "request": request, 
        "title": "Nueva oferta (3/4)", 
        "page_title": "Paso 3: Precio",
        "back_url": "/ui/offers/new/2",
        "user": get_user_context(request, db),
        "sales_categories": get_sales_categories(),
    })


@router.get("/ui/offers/new/4", response_class=HTMLResponse)
def ui_offer_w4(request: Request, db: Session = Depends(get_db)):
    if "user_id" not in request.session: return RedirectResponse("/ui")
    return templates.TemplateResponse("ui_offer_w4.html", {
        "request": request, 
        "title": "Nueva oferta (4/4)", 
        "page_title": "Paso 4: Finalizar",
        "back_url": "/ui/offers/new/3",
        "user": get_user_context(request, db)
    })

# -------------------------
# DETALLE DE OFERTA (IMMERSIVE) - Debe ir después de /new
# -------------------------
@router.get("/ui/offers/{offer_id}", response_class=HTMLResponse)
def ui_offer_detail(request: Request, offer_id: int, db: Session = Depends(get_db)):
    offer = db.execute(select(Offer).where(Offer.id == offer_id)).scalar_one_or_none()
    if not offer:
        return RedirectResponse("/ui")
    
    # Datos del dueño
    prof = offer.profile
    user_owner = prof.user if prof else None

    return templates.TemplateResponse(
        "ui_offer_detail.html",
        {
            "request": request,
            "title": offer.title,
            "user": get_user_context(request, db),
            "o": offer,
            "p": prof,
            "owner": user_owner,
            "is_mine": request.session.get("profile_id") == prof.id if prof else False
        }
    )

# -------------------------
# LISTADO DE OFERTAS
# -------------------------
@router.get("/ui/offers", response_class=HTMLResponse)
def ui_offers(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "ui_offers.html",
        {
            "request": request,
            "title": "Ofrezco · Ofertas",
            "user": get_user_context(request, db),
        },
    )


# -------------------------
# LISTADO DE OFERTAS
# -------------------------
@router.get("/ui/needs", response_class=HTMLResponse)
def ui_needs(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "ui_needs.html",
        {
            "request": request,
            "title": "Necesidades",
            "user": get_user_context(request, db),
        },
    )


# -------------------------
# ADMIN
# -------------------------
@router.get("/ui/admin", response_class=HTMLResponse)
def ui_admin(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "ui_admin.html",
        {
            "request": request,
            "title": "Admin",
            "user": get_user_context(request, db),
        },
    )

@router.get("/ui/admin/reset-db", response_class=HTMLResponse)
def ui_admin_reset_db(request: Request, db: Session = Depends(get_db)):
    # Solo permitir si el usuario es el dueño o vía URL secreta (demo)
    reset_db_completely()
    return HTMLResponse("<h1>Base de datos reiniciada con éxito en el servidor.</h1><p>Ahora puedes volver a <a href='/ui'>Inicio</a>, loguearte y crear tu anuncio con foto.</p>")
