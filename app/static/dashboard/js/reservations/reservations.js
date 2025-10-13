import { showAlert } from '../alerts.js';
import { checkoutButton, reservationButton } from './change_buttons.js';


document.addEventListener("DOMContentLoaded", function () {
    // função que anexa os listeners no botao
    function attachReservationButtons() {
        const btnRes = document.querySelectorAll(".btn-res-1");
        btnRes.forEach(link => {
            // remove os listeners duplicados
            link.removeEventListener("click", handleClick);
            link.addEventListener("click", handleClick);
        });
    }
    
    async function handleClick(e) {
        //evita que a pagina recarregue
        e.preventDefault();

        // captura os dados para o alert e para o fetch
        const link = this;
        const reservationId = link.dataset.id;
        const name = link.dataset.name;
        const check = link.dataset.text;

        showAlert(
            `Confirmar check-${check} de ${name}?`,
            `Não há como desfazer o check-${check}.`,
            'warning'
        )
        .then(async (result) => {
            if (result.isConfirmed) {
                try {
                    const res = await fetch(`/dashboard_reservations/update/${reservationId}`, {
                        method: "POST",
                        headers: { "X-Requested-With": "XMLHttpRequest" }
                    });

                    const data = await res.json();

                    if (data.status) {
                        // se tiver o data.status, significa que a reserva foi atualizada
                        // muda a tabela dinamicamente
                        const status = link.closest('tr').querySelector(".status-cell p");
                        changeTable(link, status, reservationId, name, data.guest, data.status, handleClick)
                        // se der tudo certo, alerta com timer
                        showAlert(
                            `Sucesso`,
                            data.message,
                            'success',
                            true
                        )
                    // alerta com timer dando erro: caiu na condicional no back-end
                    } else {
                        showAlert(
                            `Erro`,
                            data.message,
                            'error',
                            true
                        )
                    }
                // alerta sem timer dando erro: problema ao fazer a requisição
                } catch (err) {
                    showAlert(
                        `Erro ao atualizar a reserva`,
                        `${err}`,
                        'error'
                    );
                }
            }
        });
    }
    // anexa os listeners ao carregar a página
    attachReservationButtons();
});

// FUNÇÃO DE ATUALIZAR QUARTOS DO FILTRO UTILIZANDO A API
const roomInput = document.getElementById("room");
async function updateRooms(hotel_id) {

    try {
        const url = `/api/get_rooms?hotel_id=${hotel_id}`;
        const res = await fetch(url);
        const data = await res.json();

        roomInput.innerHTML = `<option value="" selected>Selecione o quarto</option>`;
        data.forEach(r => {
            roomInput.innerHTML += `<option value="${r.id}">${r.room_number} - ${r.capacity_adults} adultos, ${r.capacity_children} crianças - R$ ${r.price.toFixed(2).replace('.', ',')}</option>`;
        });
    } catch (err) {
        console.error("Erro ao verificar disponibilidade:", err);
    }
}

roomInput.addEventListener("focus", function () {
    updateRooms(hotel_id);
});

// FUNÇÃO DE ALTERAR A TABELA AO ATUALIZAR A RESERVA
function changeTable(link, status, reservationId, name, guest, reservationStatus, handleClick) {
    if (reservationStatus === "checked_in") {
        checkoutButton(status, reservationId, name, link, handleClick);
    } else if (reservationStatus === "checked_out") {
        reservationButton(status, name, guest, link);
    }
}
