from unidecode import unidecode
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.collaborator import Collaborator
from app.repositories.collaborator_repository import CollaboratorRepository


def _format_username(username: str, firstname: str, lastname: str) -> str:
    if not username or username.strip() == "":
        return f"{unidecode(firstname.lower().strip().replace(' ', ''))}.{unidecode(lastname.lower().strip().replace(' ', ''))}"
    return unidecode(username.lower().strip().replace(" ", ""))


class CollaboratorService:

    @staticmethod
    def list_collaborators(db: Session, hotel_id: int):
        return CollaboratorRepository.base_query(db, hotel_id)

    @staticmethod
    def filter_collaborators(query, search: str = None, status: str = None):
        return CollaboratorRepository.apply_filters(query, search, status)

    @staticmethod
    def get_collaborator(db: Session, collaborator_id: int, hotel_id: int):
        collaborator = CollaboratorRepository.find_by_id(db, collaborator_id, hotel_id)
        if not collaborator:
            return None, "Colaborador não encontrado"
        return collaborator, None

    @staticmethod
    def create_collaborator(db: Session, hotel_id: int, firstname: str, lastname: str, username: str, cpf: str):
        existing = CollaboratorRepository.find_by_cpf(db, cpf, hotel_id)

        if existing and not existing.is_deleted:
            return None, "active", "Esse colaborador já está cadastrado no seu hotel."

        username = _format_username(username, firstname, lastname)

        # restaura se estava deletado
        if existing and existing.is_deleted:
            existing.firstname = firstname
            existing.lastname = lastname
            existing.username = username
            existing.password = hash_password(existing.cpf)
            existing.change_password = True
            existing.is_deleted = False
            existing.is_active = True
            CollaboratorRepository.update(db, existing)
            return existing, "restored", None

        # cria novo
        new_collaborator = Collaborator(
            firstname=firstname,
            lastname=lastname,
            username=username,
            cpf=cpf,
            hotel_id=hotel_id,
            password=hash_password(cpf),
            change_password=True
        )
        CollaboratorRepository.create(db, new_collaborator)
        return new_collaborator, "created", None

    @staticmethod
    def update_collaborator(db: Session, collaborator: Collaborator, firstname: str, lastname: str, username: str, is_active: bool, change_password: bool):
        username = _format_username(username, firstname, lastname)

        if change_password:
            collaborator.password = hash_password(collaborator.cpf)

        collaborator.firstname = firstname
        collaborator.lastname = lastname
        collaborator.username = username
        collaborator.is_active = is_active
        collaborator.change_password = change_password

        return CollaboratorRepository.update(db, collaborator), None

    @staticmethod
    def delete_collaborator(db: Session, collaborator_id: int, hotel_id: int):
        collaborator = CollaboratorRepository.find_by_id(db, collaborator_id, hotel_id)
        if not collaborator:
            return None, "Colaborador não encontrado"
        CollaboratorRepository.soft_delete(db, collaborator)
        return collaborator, None
    
class ApiCollaboratorService:

    @staticmethod
    def list_collaborators(db: Session):
        return CollaboratorRepository.find_all_global(db)
    
    @staticmethod
    def filter_collaborators(query, hotel_name: str = None, firstname: str = None, lastname: str = None, cpf: str = None):
        return CollaboratorRepository.apply_global_filters(query, hotel_name, firstname, lastname, cpf)