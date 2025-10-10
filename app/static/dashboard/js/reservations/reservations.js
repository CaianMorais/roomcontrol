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

        Swal.fire({
            title: `Confirmar check-${check} de ${name}?`,
            text: `Não há como desfazer o check-${check}.`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: "#3085d6",
            cancelButtonColor: "#d33",
            confirmButtonText: "Confirmar",
            cancelButtonText: "Não"
        }).then(async (result) => {
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
                        const row = link.closest('tr');
                        // captura o elemento <p> na 6º coluna da tabela
                        const statusCell = link.closest('tr').querySelector("td:nth-child(6) p");
                        // se foi feito check-in:
                        if (data.status === "checked_in") {
                            statusCell.textContent = "Entrada";
                            statusCell.className = "mb-0 fw-normal text-success";

                            // cria o botão do check-out
                            const newBtn = document.createElement("a");
                            newBtn.href = "#";
                            newBtn.className = "text-danger btn-res-1";
                            newBtn.dataset.id = reservationId;
                            newBtn.dataset.name = name;
                            newBtn.dataset.text = "out";
                            newBtn.dataset.bsToggle = "tooltip";
                            newBtn.dataset.bsPlacement = "bottom";
                            newBtn.dataset.bsTitle = "Fazer check-out";
                            newBtn.setAttribute("aria-label", "Fazer check-out");
                            newBtn.innerHTML = '<i class="ti ti-door-exit"></i>';

                            link.replaceWith(newBtn);
                            
                            // inicia o tooltip com o bootstrap
                            new bootstrap.Tooltip(newBtn);

                            // reanexa o listener no novo botão
                            attachReservationButtons();
                        }
                        // se foi feito check-out:
                        else if (data.status === "checked_out") {
                            statusCell.textContent = "Saída";
                            statusCell.className = "mb-0 fw-normal text-danger";

                            // remove botão antigo
                            link.remove();
                            // cria botão de reservar novamente
                            const repeatBtn = document.createElement("a");
                            repeatBtn.href = `/dashboard_reservations/new?guest_id=${data.guest}`;
                            repeatBtn.className = "text-success";
                            repeatBtn.dataset.name = name;
                            repeatBtn.dataset.guestId = data.guest;
                            repeatBtn.dataset.bsToggle = "tooltip";
                            repeatBtn.dataset.bsPlacement = "bottom";
                            repeatBtn.dataset.bsTitle = "Reservar este hóspede novamente";
                            repeatBtn.setAttribute("aria-label", "Reservar este hóspede novamente");
                            repeatBtn.innerHTML = '<i class="ti ti-calendar-plus"></i>';

                            // anexa o botao na tabela e ajusta a posição dele
                            const actionsDiv = row.querySelector("td:last-child .d-flex") || row.querySelector("td:last-child");
                            const manageBtn = actionsDiv.querySelector("a:last-child");
                            actionsDiv.insertBefore(repeatBtn, manageBtn);

                            // inicia o tooltip
                            new bootstrap.Tooltip(repeatBtn);
                        }
                        // se der tudo certo, alerta com timer
                        Swal.fire({
                            title: "Sucesso",
                            text: data.message,
                            icon: "success",
                            timer: 1000,
                            timerProgressBar: true,
                            didOpen: () => {
                                Swal.showLoading();
                                const timer = Swal.getPopup().querySelector("b");
                                timerInterval = setInterval(() => {
                                    timer.textContent = `${Swal.getTimerLeft()}`;
                                }, 100);
                            },
                            willClose: () => {
                                clearInterval(timerInterval);
                            }
                        });
                        // alerta com timer dando erro: caiu na condicional no back-end
                    } else {
                        Swal.fire({
                            title: "Erro",
                            text: data.message,
                            icon: "error",
                            timer: 1000,
                            timerProgressBar: true,
                            didOpen: () => {
                                Swal.showLoading();
                                const timer = Swal.getPopup().querySelector("b");
                                timerInterval = setInterval(() => {
                                    timer.textContent = `${Swal.getTimerLeft()}`;
                                }, 100);
                            },
                            willClose: () => {
                                clearInterval(timerInterval);
                            }
                        });
                    }
                // alerta sem timer dando erro: problema ao fazer a requisição
                } catch (err) {
                    Swal.fire("Erro", "Não foi possível atualizar a reserva.", "error");
                    console.error(err);
                }
            }
        });
    }
    // anexa os listeners ao carregar a página
    attachReservationButtons();
});