from app.utils.flash import add_flash_message
from fastapi.responses import RedirectResponse

def valid_phone_number_on_create(request, phone_number):
    if phone_number and len(phone_number) >= 10:
        add_flash_message(request, "Hóspede criado com sucesso", "success")
    elif phone_number and len(phone_number) < 10:
        add_flash_message(request, "Hóspede criado, porém o telefone é inválido", "info")
    else:
        add_flash_message(request, "Hóspede criado com sucesso", "success")

def valid_phone_number_on_edit(request, phone_number, guest):
    if phone_number and len(phone_number) < 10:
        add_flash_message(request, "Número de telefone inválido, operação cancelada", "warning")
        return False
    return True