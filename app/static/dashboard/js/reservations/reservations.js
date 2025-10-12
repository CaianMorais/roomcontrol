// ATIVAÇÃO DO TOOLTIP
const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

// FUNÇÃO DE ATUALIZAR QUARTOS UTILIZANDO A API
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
    updateRooms("{{ request.session.get('hotel_id') }}");
});

function showAlert(title, text, icon, timer = false) {
    const options = {
        title: title,
        text: text,
        icon: icon
    };
    
    if (timer) {
        ;
        options.timer = 1000;
        options.timerProgressBar = true;
        options.didOpen = () => {
            Swal.showLoading();
        };
        options.willClose = () => {
            clearInterval(options.timerInterval);
        };
    } else {
        options.showCancelButton = true;
        options.confirmButtonColor = "#3085d6";
        options.cancelButtonColor = "#d33";
        options.confirmButtonText = "Confirmar";
        options.cancelButtonText = "Não";
    }

    return Swal.fire(options);
}

function changeTable(link, status, reservationId, name, guest, reservationStatus, handleClick) {
    if (reservationStatus === "checked_in") {
        status.textContent = "Entrada";
        status.className = "mb-0 fw-normal text-success";

        // cria o botão do check-out
        const checkoutButton = document.createElement("a");
        checkoutButton.href = "#";
        checkoutButton.className = "text-danger btn-res-1";
        checkoutButton.dataset.id = reservationId;
        checkoutButton.dataset.name = name;
        checkoutButton.dataset.text = "out";
        checkoutButton.dataset.bsToggle = "tooltip";
        checkoutButton.dataset.bsPlacement = "bottom";
        checkoutButton.dataset.bsTitle = "Fazer check-out";
        checkoutButton.setAttribute("aria-label", "Fazer check-out");
        checkoutButton.innerHTML = '<i class="ti ti-door-exit"></i>';

        link.replaceWith(checkoutButton);
        
        // inicia o tooltip com o bootstrap
        new bootstrap.Tooltip(checkoutButton);

        // adiciona o listener diretamente
        checkoutButton.addEventListener("click", handleClick);

    } else if (reservationStatus === "checked_out") {
        status.textContent = "Saída";
        status.className = "mb-0 fw-normal text-danger";

        // cria botão de reservar novamente
        const repeatBtn = document.createElement("a");
        repeatBtn.href = `/dashboard_reservations/new?guest_id=${guest}`;
        repeatBtn.className = "text-success";
        repeatBtn.dataset.name = name;
        repeatBtn.dataset.guestId = guest;
        repeatBtn.dataset.bsToggle = "tooltip";
        repeatBtn.dataset.bsPlacement = "bottom";
        repeatBtn.dataset.bsTitle = "Reservar este hóspede novamente";
        repeatBtn.setAttribute("aria-label", "Reservar este hóspede novamente");
        repeatBtn.innerHTML = '<i class="ti ti-calendar-plus"></i>';

        link.replaceWith(repeatBtn);

        // inicia o tooltip
        new bootstrap.Tooltip(repeatBtn);
    }
}

document.addEventListener("DOMContentLoaded", function () {
    // função que anexa os listeners no botao
    function attachReservationButtons() {
        const btnRes1 = document.querySelectorAll(".btn-res-1");
        btnRes1.forEach(link => {
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
                    // resposta do fetch

                    const data = await res.json();

                    if (data.status) {
                        // se tiver o data.status, significa que a reserva foi atualizada
                        // muda a tabela dinamicamente (sem recarregar a pagina)
                        // captura o elemento <p> na 6º coluna da tabela
                        const status = link.closest('tr').querySelector("td:nth-child(6) p");
                        changeTable(link, status, reservationId, name, data.guest, data.status, handleClick)
                        // se der tudo certo, alerta com timer
                        showAlert(
                            `Sucesso`,
                            data.message,
                            icon='success',
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
                        `Erro`,
                        "Não foi possível atualizar aa reserva.",
                        icon='error'
                    );
                }
            }
        });
    }
    // anexa os listeners ao carregar a página
    attachReservationButtons();
});