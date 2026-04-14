from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.repositories.auth_collaborator_repository import CollaboratorAuthRepository


class AuthCollaboratorService:

    @staticmethod
    def login(db: Session, username: str, password: str, hotel_id: int):
        """Autentica um colaborador e indica se precisa trocar a senha."""
        collaborator = CollaboratorAuthRepository.find_active_by_username_and_hotel(
            db, username, hotel_id
        )

        if not collaborator:
            return None, False, "Usuário não encontrado"

        if not verify_password(password, collaborator.password):
            return None, False, "Credenciais inválidas"

        return collaborator, collaborator.change_password, None

    @staticmethod
    def change_password(db: Session, collaborator_id: int, new_password: str, confirm_password: str):
        """Valida e aplica a nova senha do colaborador."""
        if new_password != confirm_password:
            return None, "As senhas não coincidem"

        collaborator = CollaboratorAuthRepository.find_active_by_id(db, collaborator_id)

        if not collaborator:
            return None, "Colaborador não encontrado ou inativo"

        CollaboratorAuthRepository.update_password(db, collaborator, hash_password(new_password))

        return collaborator, None