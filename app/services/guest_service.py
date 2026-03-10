from app.repositories.guest_repository import GuestRepository
from app.models.guest import Guest

class GuestService:

    @staticmethod
    def list_guests(db, hotel_id):
        return GuestRepository.guests_with_active_reservations(db, hotel_id)
    
    @staticmethod
    def filter_guests(db, name, cpf, query):
        return GuestRepository.filter_guests_by_name_or_cpf(db, name, cpf, query)
    
    @staticmethod
    def get_guest(db, hotel_id, guest_id=None, cpf=None):
        guest = None
        print(f"Buscando guest com guest_id={guest_id}, cpf={cpf}, hotel_id={hotel_id}")
        if guest_id:
            guest = GuestRepository.find_by_id(db, guest_id, hotel_id)
        if not guest and cpf:
            guest = GuestRepository.find_by_cpf(db, cpf, hotel_id)
        if guest:
            return guest
        else:
            return None

    @staticmethod
    def create_guest(db, hotel_id, name, cpf, email, phone_number):
        # usa o repository para consultar se o hospede existe
        existing = GuestRepository.find_by_cpf(db, cpf, hotel_id)

        # se existir e não estiver deletado, dispara error
        if existing and not existing.is_deleted:
            return None, "CPF já cadastrado no seu hotel"
        
        if phone_number and len(phone_number) < 10:
            phone_number = None

        if email == '':
            email = None
        if phone_number == '':
            phone_number = None

        # se existir e estiver como deletado, restaura atualizando os dados
        if existing and existing.is_deleted:
            existing.name = name
            existing.email = email
            existing.phone_number = phone_number
            existing.is_deleted = False
            db.commit()
            db.refresh(existing)
            return existing, None

        # se não existir, cria um novo
        guest = Guest(
            name=name,
            cpf=cpf,
            email=email,
            phone_number=phone_number,
            hotel_id=hotel_id
        )

        # manda o novo guest pro create no repository
        return GuestRepository.create(db, guest), None

    @staticmethod
    def update_guest(db, guest, email, phone_number):
        guest.email = email
        guest.phone_number = phone_number
        return GuestRepository.update(db, guest)

    @staticmethod
    def delete_guest(db, guest):
        return GuestRepository.soft_delete(db, guest)