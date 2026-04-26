from typing import Optional
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.hotel import Hotel
from app.repositories.auth_hotel_repository import HotelRepository
from app.utils.brdocs import is_valid_cnpj, only_digits
from app.utils.cnpj_ws import CNPJWsError, fetch_cnpj_situacao

def valid_phone_number_on_create(phone_number):
    phone_number = "".join(filter(str.isdigit, phone_number))
    print(phone_number)
    if phone_number and len(phone_number) >= 10:
        return phone_number
    else:
        return None

class AuthHotelService:

    @staticmethod
    def check_registration(db: Session, email: str, cnpj: str):
        if not is_valid_cnpj(cnpj):
            return None, "CNPJ inválido"

        cnpj_digits = only_digits(cnpj)

        if HotelRepository.find_by_cnpj_and_email(db, cnpj_digits, email):
            return None, "CNPJ ou email já cadastrado"

        return cnpj_digits, None

    @staticmethod
    async def register(
        db: Session,
        sess_email: str,
        sess_cnpj: str,
        email: str,
        cnpj: str,
        name: str,
        login: str,
        ddd: str,
        phone_number: str,
        address: str,
        number: str,
        city: str,
        state: str,
        zip_code: str,
        password: str,
        confirm_password: str,
    ):
        cnpj_digits = only_digits(cnpj)

        if str(email).strip().lower() != str(sess_email).strip().lower() or cnpj_digits != sess_cnpj:
            return None, "Dados não foram validados, adulteração detectada."

        if not is_valid_cnpj(cnpj):
            return None, "CNPJ inválido"

        if HotelRepository.find_by_cnpj(db, cnpj_digits):
            return None, "O hotel já existe em nossos registros"

        if password != confirm_password:
            return None, "As senhas não conferem."

        try:
            situacao = await fetch_cnpj_situacao(cnpj_digits)
        except CNPJWsError as e:
            return None, str(e)

        if situacao.lower() != "ativa":
            return None, "CNPJ com situação irregular"

        new_hotel = Hotel(
            name=name,
            email=email,
            phone_number=ddd + phone_number,
            cnpj=cnpj_digits,
            login=login,
            address=address + ", " + number,
            city=city,
            state=state,
            zip_code=zip_code,
            password=hash_password(password),
        )

        return HotelRepository.create(db, new_hotel), None

    @staticmethod
    def login(db: Session, login: str, password: str):
        hotel = HotelRepository.find_by_login_or_cnpj(db, login)

        if not hotel:
            return None, "Login ou CNPJ não encontrado."

        if not verify_password(password, hotel.password):
            return None, "Senha incorreta."

        if not hotel.is_active:
            return None, "O hotel está desativado no sistema"

        return hotel, None

    @staticmethod
    def update_profile(
        db: Session,
        hotel_id: int,
        name: str,
        email: str,
        login: str,
        phone_number: str,
        zip_code: str,
        address: str,
        number: str,
        city: str,
        state: str,
        password: Optional[str] = None,
        confirm_password: Optional[str] = None,
    ):
        hotel = HotelRepository.find_by_id(db, hotel_id)
        if not hotel:
            return None, "Hotel não encontrado."

        # Validações de campos únicos se mudarem
        if email != hotel.email:
            if HotelRepository.find_by_email(db, email):
                return None, "Este email já está sendo usado por outro hotel."
        
        if login and login != hotel.login:
            if HotelRepository.find_by_login(db, login):
                return None, "Este login já está sendo usado por outro hotel."

        phone_number = valid_phone_number_on_create(phone_number)

        if not phone_number:
            return None, "Número de telefone inválido."

        # Validação de senha
        if password:
            if password != confirm_password:
                return None, "As senhas não conferem."
            hotel.password = hash_password(password)

        # Atualização dos campos
        hotel.name = name
        hotel.email = email
        hotel.login = login
        hotel.phone_number = phone_number
        hotel.zip_code = zip_code
        hotel.address = address + ", " + number
        hotel.city = city
        hotel.state = state

        return HotelRepository.update(db, hotel), None
    
class ApiAuthHotelService:

    @staticmethod
    def list_hotels(db: Session, cnpj: Optional[str] = None, name: Optional[str] = None):
        query = HotelRepository.base_query(db)
        query = HotelRepository.apply_filters(query, cnpj, name)
        return query.all()