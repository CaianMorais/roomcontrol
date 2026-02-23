from app.utils.flash import add_flash_message
from sqlalchemy.exc import IntegrityError

def update_key(db, key, request):
    try:
        if key.is_active:
            key.is_active = False
        else:
            key.is_active = True

        db.commit()
        db.refresh(key)
        add_flash_message(request, "Chave atualizada com sucesso", "success")
    except IntegrityError:
        db.rollback()
        add_flash_message(request, "Erro ao atualizar o status da chave", "danger")
