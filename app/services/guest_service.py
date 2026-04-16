from app.repositories.guest_repository import GuestRepository
from app.models.guest import Guest

def valid_phone_number_on_create(phone_number):
    # validação do phone_number (não interrompe em caso não validação)
    if phone_number and len(phone_number) >= 10:
        return phone_number
    else:
        return None

def valid_phone_number_on_edit(phone_number):
    # validação do phone_number (cancela a operação em caso de número inválido)
    if phone_number and len(phone_number) < 10:
        return None, "Número de telefone inválido, operação cancelada"
    return phone_number, None

class GuestService:

    @staticmethod
    def list_guests(db, hotel_id):
        return GuestRepository.guests_with_active_reservations(db, hotel_id)
    
    @staticmethod
    def filter_guests(name, cpf, query):
        return GuestRepository.filter_guests_by_name_or_cpf(name, cpf, query)
    
    @staticmethod
    def get_guest(db, hotel_id, guest_id=None, cpf=None):
        guest = None
        
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
        
        phone_number = valid_phone_number_on_create(phone_number)

        if email == '':
            email = None

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
        phone_number, error = valid_phone_number_on_edit(phone_number)
        if error:
            return guest, error
        guest.email = email
        guest.phone_number = phone_number
        return GuestRepository.update(db, guest), None

    @staticmethod
    def delete_guest(db, guest):
        return GuestRepository.soft_delete(db, guest)
    
class ApiGuestService:

    @staticmethod
    def list_guests(db):
        return GuestRepository.base_query(db)
    
    @staticmethod
    def list_guests_by_hotel(db, hotel_id):
        return GuestRepository.list_guests_by_hotel(db, hotel_id)
    
    @staticmethod
    def filter_guests(name, cpf, query):
        return GuestRepository.filter_guests_by_name_or_cpf(name, cpf, query)
    
    @staticmethod
    def filter_guests_by_hotel(query, hotel_id: int = None, hotel_name: str = None):
        return GuestRepository.filter_guests_by_hotel(query, hotel_id, hotel_name)
