from app.models.guest import Guest
from app.utils.flash import add_flash_message

def filter_guests(request, name, cpf, query):
    if name:
        query = query.filter(Guest.name.ilike(f"%{name}%"))
        add_flash_message(request, f"Filtro aplicado", "success")
    if cpf:
        query = query.filter(Guest.cpf.like(f"%{cpf}%"))
        add_flash_message(request, f"Filtro aplicado", "success")
    return query