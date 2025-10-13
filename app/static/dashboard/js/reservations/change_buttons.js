export function checkoutButton(status, reservationId, name, link, handleClick){
    // muda a coluna status
    status.textContent = 'Entrada';
    status.className = "mb-0 fw-normal text-success";

    //cria o botao de check-out
    const checkoutButton = document.createElement("a");
    checkoutButton.href = '#';
    checkoutButton.className = "text-danger btn-res-1";
    checkoutButton.dataset.id = reservationId;
    checkoutButton.dataset.name = name;
    checkoutButton.dataset.text = "out";
    checkoutButton.dataset.bsToggle = "tooltip";
    checkoutButton.dataset.bsPlacement = "bottom";
    checkoutButton.dataset.bsTitle = "Fazer check-out";
    checkoutButton.setAttribute("aria-label", "Fazer check-out");
    checkoutButton.innerHTML = '<i class="ti ti-door-exit"></i>';

    // subtituição
    link.replaceWith(checkoutButton);

    // inicia o tooltip com o bootstrap
    new bootstrap.Tooltip(checkoutButton);

    // adiciona o listener diretamente
    checkoutButton.addEventListener("click", handleClick);
}

export function reservationButton(status, name, guest, link) {
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