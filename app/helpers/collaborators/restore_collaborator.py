from app.core.security import hash_password
from app.utils.flash import add_flash_message
from app.helpers.collaborators.format_username import format_username

def restore_collaborator(request, db, collaborator, firstname, lastname, username):
    # função que formata o username
    format_username(username, firstname, lastname)

    collaborator.firstname = firstname
    collaborator.lastname = lastname
    collaborator.username = username
    collaborator.password = hash_password(collaborator.cpf),
    collaborator.change_password = True
    collaborator.is_deleted = False
    collaborator.is_active = True

    db.commit()
    db.refresh(collaborator)
    add_flash_message(request, "Colaborador cadastrado, no primeiro acesso a senha é o CPF.", "success")
