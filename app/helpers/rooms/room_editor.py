from models.rooms import Rooms
from utils.flash import add_flash_message

def room_editor(request, room, room_number, room_type, capacity_adults, capacity_children, capacity_total, price, is_active, comments, db):
    room.room_number = room_number
    room.type = room_type
    room.capacity_adults = capacity_adults
    room.capacity_children = capacity_children
    room.capacity_total = capacity_total
    room.price = price
    room.is_active = is_active
    room.comments = comments

    db.commit()
    db.refresh(room)
    add_flash_message(request, f"Quarto {room.room_number} atualizado com sucesso.", "success")
    return room