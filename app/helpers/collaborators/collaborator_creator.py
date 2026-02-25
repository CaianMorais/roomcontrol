from app.models.collaborator import Collaborator
from app.core.security import hash_password
from app.utils.flash import add_flash_message
from app.helpers.collaborators.format_username import format_username

def collaborator_creator(request, db, firstname, lastname, username, cpf, hotel_id):
    # função que formata o username
    format_username(username, firstname, lastname)
    
    new_collaborator = Collaborator(
        firstname = firstname,
        lastname = lastname,
        username = username,
        cpf = cpf,
        hotel_id = hotel_id,
        password = hash_password(cpf),
        change_password = True
    )

    db.add(new_collaborator)
    db.commit()
    db.refresh(new_collaborator)
    add_flash_message(request, "Colaborador cadastrado, no primeiro acesso a senha é o CPF.", "success")
