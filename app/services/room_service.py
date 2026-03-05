from decimal import Decimal

from app.repositories.room_repository import RoomsRepository
from app.models.rooms import Rooms
from app.helpers.rooms.object_mapper import room_capacities_map, tipos_map, coluna_map

class RoomsService:

    @staticmethod
    def list_rooms(db, hotel_id):
        return RoomsRepository.get_rooms(db, hotel_id)
    
    @staticmethod
    def filter_rooms(query, solteiro, duplo, casal, triplo, triplo_com_casal, personalizado, available, occupied, maintenance, criteria, order):
        ROOM_TYPE_MAP = tipos_map()
        ORDER_MAP = coluna_map()

        # MARCA AS FLAGS COM TRUE OU FALSE QUE FORAM MARCADAS NO FILTRO
        selected_type_flags = {
            "solteiro": solteiro,
            "duplo": duplo,
            "casal": casal,
            "triplo": triplo,
            "triplo_com_casal": triplo_com_casal,
            "personalizado": personalizado,
        }

        # ITERA SOBRE AS FLAGS PARA ADICIONAR RESGATAR O 
        # VALOR DOS SELECIONADOS (TRUE) NA LISTA TOOM_TYPE_MAP
        room_types = [t for flag, on in selected_type_flags.items() if on for t in ROOM_TYPE_MAP[flag]]
        if room_types:
            query = RoomsRepository.filter_rooms_by_types(query, room_types)

        # MARCA AS FLAGS QUE FORAM MARCADAS NO FILTRO
        status_flags = {
            "available": available,
            "occupied": occupied,
            "maintenance": maintenance,
        }

        #ITERA SOBRE AS FLAGS PARA FAZER A LISTA DE STATUS SELECIONADOS NO FILTRO
        statuses = [name for name, on in status_flags.items() if on]
        if statuses:
            query = RoomsRepository.filter_rooms_by_status(query, statuses)

        # ORDENAÇÃO DOS QUARTOS, PRIORIZANDO OS ATIVOS ACIMA
        order_cols = [Rooms.is_active.desc()]

        # PEGA O CRITERIO DE ORDENAÇÃO NO FILTRO E BUSCA ELE NO MAPPING
        col = ORDER_MAP.get(criteria or "")
        if col is not None:
            # SE HOVER CRITERIO DE ORDENAÇÃO, PEGA A ORDENAÇÃO
            if order == "decres":
                order_cols.append(col.desc())
            else:
                # SENAO O PADRAO É ASC
                order_cols.append(col.asc())
        else:
            # SE NAO HOUVER CRITERIO DE ORDENAÇÃO
            # O PADRÃO SERÁ PELO NUMERO DO QUARTO CRESCENTE
            order_cols.append(Rooms.room_number.asc())

        query = query.order_by(*order_cols)

        has_filter = bool(
            room_types or statuses or (criteria in ORDER_MAP)
        )
        
        return query, has_filter
    
    @staticmethod
    def create_room(db, hotel_id, room_number, room_type, capacity_adults, capacity_children, capacity_total, price, is_active, comments):

        existing = RoomsRepository.find_by_room_number(db, room_number, hotel_id)

        if existing and not existing.is_deleted:
            return None, "Número de quarto já cadastrado no seu hotel"
        
        room_capacities = room_capacities_map()

        if room_type in room_capacities:
            # pega as capacidades do quarto no map
            capacity_adults, capacity_children = room_capacities[room_type]
        elif room_type == "9":
            # se o tipo for personalizado, depende dos dados do form
            if capacity_adults is None or capacity_children is None:
                return None, "Capacidades de adultos e crianças são obrigatórias para quartos personalizados"
        else:
            return None, "Tipo de quarto é inválido."
        
        # calcula a capacidade total após definir a capacidade
        capacity_total = capacity_adults + capacity_children

        # formata o preço pra decimal
        price = Decimal(price)

        new_room = Rooms(
            hotel_id=hotel_id,
            room_number=room_number,
            type=room_type,
            capacity_adults=capacity_adults,
            capacity_children=capacity_children,
            capacity_total=capacity_total,
            price=price,
            status='available',
            is_active=is_active,
            comments=comments
        )

        return RoomsRepository.create(db, new_room), None

    @staticmethod
    def get_room(db, room_id, hotel_id):
        room = RoomsRepository.find_by_id(db, room_id, hotel_id)
        if room:
            return room, None
        else:
            return None, "Quarto não encontrado"

    @staticmethod
    def update_room(db, room, room_number, room_type, capacity_adults, capacity_children, capacity_total, price, is_active, comments):
        if room.is_active == True and room.is_active != is_active:
            # consulta se há alguma reserva ativa para esse quarto
            reservations = RoomsRepository.check_active_reservations(db, room)
            for r in reservations:
                if r.status in ['booked', 'checked_in']:
                    return None, "O quarto não pode ser desativado pois possui reservas ativas."
        
        # define a capacidade com base no tipo do quarto (pra não depender dos dados do form)
        room_capacities = room_capacities_map()
        
        if room_type in room_capacities:
            # pega as capacidades do quarto no map
            capacity_adults, capacity_children = room_capacities[room_type]
        elif room_type == "9":
            # se o tipo for personalizado, depende dos dados do form
            if capacity_adults is None or capacity_children is None:
                return None, "É necessário preencher a capacidade de adultos e crianças."
        else:
            return None, "Tipo de quarto é inválido."
        
        # calcula a capacidade total após definir a capacidade
        capacity_total = capacity_adults + capacity_children
        
        # formata o preço pra decimal
        price = Decimal(price)

        room.room_number = room_number
        room.type = room_type
        room.capacity_adults = capacity_adults
        room.capacity_children = capacity_children
        room.capacity_total = capacity_total
        room.price = price
        room.is_active = is_active
        room.comments = comments

        return RoomsRepository.update(db, room), None

    @staticmethod
    def delete_room(db, room):
        if room.status == 'occupied':
            return None, "O quarto não pode ser modificado enquanto ele estiver ocupado"
        
        reservations = RoomsRepository.check_active_reservations(db, room)
        for r in reservations:
            if r.status in ['booked', 'checked_in']:
                return None, "O quarto não pode ser removido pois possui reservas ativas."
            
        return RoomsRepository.soft_delete(db, room), None