from app.core.security import hash_password
from app.utils.flash import add_flash_message
from app.helpers.collaborators.format_username import format_username

def collaborator_updater(request, db, collaborator, change_password, firstname, lastname, username, is_active):
    # função que formata o username
    format_username(username, firstname, lastname)
    
    # se for redefinir senha define padrão o cpf
    if change_password:
        collaborator.password = hash_password(collaborator.cpf)
        add_flash_message(request, "Senha redefinida, e deverá ser trocada no próximo login.", "warning")

    collaborator.firstname = firstname
    collaborator.lastname = lastname
    collaborator.username = username
    collaborator.is_active = is_active
    collaborator.change_password = change_password

    db.commit()
    db.refresh(collaborator)

    add_flash_message(request, "Colaborador editado com sucesso", "success")