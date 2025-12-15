from models.rooms import Rooms

def tipos_map():
# mapeia flags -> tipos
    return {
        "solteiro": ["1"],
        "duplo": ["2", "3"],
        "casal": ["4"],
        "triplo": ["5", "6", "7"],
        "triplo_com_casal": ["8"],
        "personalizado": ["9"],
    }

def coluna_map():
# mapeia criteria -> coluna
    return {
        "room_number": Rooms.room_number,
        "capacity_total": Rooms.capacity_total,
        "capacity_adults": Rooms.capacity_adults,
        "capacity_children": Rooms.capacity_children,
        "price": Rooms.price,
    }

def room_capacities_map():
    return {
        "1": [1, 0],
        "2": [1, 1],
        "3": [2, 0],
        "4": [2, 0],
        "5": [1, 2],
        "6": [2, 1],
        "7": [3, 0],
        "8": [2, 1],
    }