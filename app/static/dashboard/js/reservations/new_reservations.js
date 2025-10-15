import { showAlert } from "../alerts.js";
import Inputmask from "https://cdnjs.cloudflare.com/ajax/libs/jquery.inputmask/5.0.9/inputmask.es6.min.js";

// MASCARA DO INPUT CPF
Inputmask({
    mask: ['999.999.999-99'],
    keepStatic: true,
    rightAlign: false,
    removeMaskOnSubmit: true,
    unmaskAsNumber: true,
}).mask("#cpf");

const checkInInput = document.getElementById("check_in");
const checkOutInput = document.getElementById("check_out");
const roomSelect = document.getElementById("room_id");
const guestSelect = document.getElementById("name_select2");

async function updateAvailability() {
    const checkIn = checkInInput.value;
    const checkOut = checkOutInput.value;
    const guest_id = guestSelect ? guestSelect.value || GUEST_ID : GUEST_ID;

    if (!checkIn || !checkOut) return;

    if (checkIn > checkOut) {
        showAlert("Opa...", "O check-out deve ser posterior ao check-in", "error", true, 2000);
        checkInInput.value = ''; checkOutInput.value = '';
        return;
    }

    // calcula o número de dias da reserva (arredondando pra +)
    const daysReservation = new Date(checkOut) - new Date(checkIn)
    const totalDays = Math.ceil(daysReservation / (1000 * 60 * 60 * 24));

    try {
        const url = `/dashboard_reservations/check_availability?check_in=${checkIn}&check_out=${checkOut}${guest_id ? `&guest_id=${guest_id}` : ''}`;
        const res = await fetch(url);
        const data = await res.json();

        if (data.guest_conflict) {
            showAlert('Opa...', "Esse hóspede tem uma reserva ativa nesse período!", "error", true, 1500)
            checkInInput.value = ''; checkOutInput.value = '';
        }

        roomSelect.innerHTML = `<option value="" selected>Pesquise e selecione o quarto</option>`;
        data.available_rooms.forEach(r => {
            const totalPrice = r.price * totalDays;
            roomSelect.innerHTML += `<option value="${r.id}">Quarto: ${r.room_number} - ${r.capacity_adults} adultos, ${r.capacity_children} crianças - R$ ${r.price.toFixed(2).replace('.', ',')} / diária (Total: R$ ${totalPrice.toFixed(2).replace('.', ',')})</option>`;
        });

        if (guestSelect) {
            guestSelect.innerHTML = `<option value="" selected>Pesquise e selecione o hóspede</option>`;
            data.available_guests.forEach(g => {
                guestSelect.innerHTML += `<option value="${g.cpf}">${g.name} -> ${g.cpf.slice(0, 3)}.${g.cpf.slice(3, 6)}.${g.cpf.slice(6, 9)}.${g.cpf.slice(9,)}</option>`;
            });
        }

    } catch (err) {
        console.error("Erro ao verificar disponibilidade:", err);
    }
}

checkInInput.addEventListener("change", updateAvailability);
checkOutInput.addEventListener("change", updateAvailability);
//if (guestSelect) guestSelect.addEventListener("change", updateAvailability);