from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.offer import Offer
from app.models.profile import Profile
from app.models.user import User
from app.core.data import CATEGORIES

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

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
    db: Session = Depends(get_db)  # Inyección de DB
):
    from app.models.product import Product
    from app.core.data import get_flattened_categories
    
    view_mode = "list"
    
    # 1. Determinar si es búsqueda de productos (Mercadillo)
    is_product_search = False
    if cat in ["Mercadillo y Segunda Mano", "Venta de cosas", "Ropa y Accesorios", "Muebles y Deco", "Electrónica"]:
        is_product_search = True
        view_mode = "mosaic"

    results = []
    
    if is_product_search:
        # QUERY PRODUCTS
        query = select(Product).where(Product.status == "PUBLISHED").order_by(Product.id.desc())
        if cat and cat != "Mercadillo y Segunda Mano": # Si es subcategoría
            query = query.where(Product.category == cat)
        if q:
            query = query.where(Product.title.contains(q))
            
        products = db.execute(query).scalars().all()
        
        for p in products:
            results.append({
                "id": p.profile_id, # Link al perfil
                "title": p.title,
                "category": p.category,
                "price": p.price or 0,
                "video": p.video_path or "", # Path al video
                "photo": "", # Podríamos sacar frame del video o placeholder
                "desc": p.description or ""
            })
            
    else:
        # QUERY SERVICES (Offers)
        query = select(Offer).where(Offer.status == "PUBLISHED").order_by(Offer.id.desc())
        
        # Excluir ofertas que sean de tipo PRODUCTO (legacy cleaning)
        query = query.where(Offer.offer_kind.notin_(["PRODUCTO", "VENTA"]))

        if cat and cat != "Todas":
            query = query.where(Offer.category == cat)
        if q:
            query = query.where(Offer.title.contains(q))

        offers = db.execute(query).scalars().all()

        for o in offers:
            prof = db.get(Profile, o.profile_id)
            u = db.get(User, prof.user_id) if prof else None
            
            results.append({
                "id": o.profile_id,
                "name": u.name if u else "Usuario",
                "role": o.title,
                "photo": "https://via.placeholder.com/56",
                "distance_km": 1.2,
                "status": "Disponible" if o.available_now else "Consultar",
                "offer_cat": o.category,
                "desc": o.description or ""
            })

    return templates.TemplateResponse(
        "ui_results.html",
        {
            "request": request,
            "title": "Ofrezco · Resultados",
            "page_title": "Resultados",
            "back_url": "/ui/need/new",

            "results": results, 
            "flat_categories": get_flattened_categories(),
            "q": q, "cat": cat,
            "view_mode": view_mode
        },
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
        "photo": prof.photo # Raw photo path
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
        "back_url": "/ui/offers/new",
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
