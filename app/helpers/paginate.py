from math import ceil

def paginate(query, page: int, per_page: int):
    total = query.order_by(None).count()
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    pages = ceil(total / per_page) if per_page else 1
    return items, {"page": page, "per_page": per_page, "total": total, "pages": pages}