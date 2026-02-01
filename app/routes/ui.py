from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/ui", tags=["ui"])
templates = Jinja2Templates(directory="app/templates")

# --- Datos MOCK para Resultados ---
MOCK_PROS = [
    {
        "id": 1,
        "name": "Carlos",
        "role": "Electricista",
        "category": "Electricidad",
        "distance_km": 1.2,
        "status": "Disponible ahora",
        "photo": "/static/mock/carlos.jpg",
    },
    {
        "id": 2,
        "name": "Laura",
        "role": "Técnico Multiservicio",
        "category": "Multiservicio",
        "distance_km": 0.8,
        "status": "Libre ahora",
        "photo": "/static/mock/laura.jpg",
    },
    {
        "id": 3,
        "name": "Juan",
        "role": "Fontanero",
        "category": "Fontanería",
        "distance_km": 1.5,
        "status": "Disponible hoy",
        "photo": "/static/mock/juan.jpg",
    },
]

@router.get("")
@router.get("/")
def ui_root(request: Request):
    # Por si entras en /ui
    return templates.TemplateResponse("home.html", {"request": request})

@router.get("/need/new")
def ui_need_new(request: Request):
    return templates.TemplateResponse("ui_need_new.html", {"request": request})

@router.get("/results")
def ui_results(request: Request):
    q = (request.query_params.get("q") or "").strip().lower()
    cat = (request.query_params.get("cat") or "").strip().lower()

    results = MOCK_PROS

    if cat:
        results = [p for p in results if p["category"].lower() == cat]

    if q:
        def haystack(p):
            return f'{p["name"]} {p["role"]} {p["category"]}'.lower()
        results = [p for p in results if q in haystack(p)]

    return templates.TemplateResponse(
        "ui_results.html",
        {"request": request, "results": results, "q": q, "cat": cat},
    )

@router.get("/profile/{pro_id}")
def ui_profile_mock(request: Request, pro_id: int):
    # Mock simple para que "Ver perfil" no falle
    pro = next((p for p in MOCK_PROS if p["id"] == pro_id), None)
    if not pro:
        pro = MOCK_PROS[0]
    return templates.TemplateResponse(
        "ui_profile_mock.html",
        {"request": request, "pro": pro},
    )
