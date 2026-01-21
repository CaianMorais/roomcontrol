from app.models.rooms import Rooms
from app.utils.flash import add_flash_message

def room_creator(request, hotel_id, room_number, room_type, capacity_adults, capacity_children,capacity_total, price, db):
    new_room = Rooms(
        hotel_id=hotel_id,
        room_number=room_number,
        type=room_type,
        capacity_adults=capacity_adults,
        capacity_children=capacity_children,
        capacity_total=capacity_total,
        price=price,
        status='available',
        is_active=True
    )

    # salva no banco
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    add_flash_message(request, f"Quarto {room_number} criado com sucesso. Clique <a href='/dashboard_rooms/edit/{new_room.id}'>aqui</a> para editá-lo.", "success")
    return new_room