from app.repositories.room_repository import RoomsRepository
from app.models.rooms import Rooms
from app.helpers.rooms.object_mapper import tipos_map, coluna_map

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