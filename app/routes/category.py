from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional

from app.db.session import get_db
from app.models.category import Category
from app.schemas.category import CategoryOut, CategoryTree

router = APIRouter()


def build_tree(categories: list[Category]) -> list[CategoryTree]:
    # Convertimos a dict de nodos
    nodes = {}
    for c in categories:
        nodes[c.id] = CategoryTree(
            id=c.id,
            slug=c.slug,
            name=c.name,
            parent_id=c.parent_id,
            active=c.active,
            children=[]
        )

    roots: list[CategoryTree] = []
    for c in categories:
        node = nodes[c.id]
        if c.parent_id and c.parent_id in nodes:
            nodes[c.parent_id].children.append(node)
        else:
            roots.append(node)

    # Opcional: ordenar por name
    def sort_node(n: CategoryTree):
        n.children.sort(key=lambda x: x.name.lower())
        for ch in n.children:
            sort_node(ch)

    roots.sort(key=lambda x: x.name.lower())
    for r in roots:
        sort_node(r)

    return roots


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    active: Optional[bool] = True,
):
    q = select(Category)
    if active is not None:
        q = q.where(Category.active == active)
    q = q.order_by(Category.parent_id().nullsfirst(), Category.name) if hasattr(Category, "parent_id") else q.order_by(Category.name)
    return db.execute(q).scalars().all()


@router.get("/categories/tree", response_model=list[CategoryTree])
def list_categories_tree(
    db: Session = Depends(get_db),
    active: Optional[bool] = True,
):
    q = select(Category)
    if active is not None:
        q = q.where(Category.active == active)
    categories = db.execute(q).scalars().all()
    return build_tree(categories)
