(function () {
    const servicesUrl = "/internal_api/dashboard/services";
    const checkinsUrl = "/internal_api/dashboard/upcoming_checkins";

    const servicesPendingCount = document.getElementById("services-pending-count");
    const servicesProgressCount = document.getElementById("services-progress-count");
    const servicesList = document.getElementById("services-list");
    const servicesLoading = document.getElementById("services-loading");
    const servicesError = document.getElementById("services-error");
    const servicesEmpty = document.getElementById("services-empty");
    const refreshServicesBtn = document.getElementById("refresh-services-btn");

    const checkinsList = document.getElementById("checkins-list");
    const checkinsLoading = document.getElementById("checkins-loading");
    const checkinsError = document.getElementById("checkins-error");
    const checkinsEmpty = document.getElementById("checkins-empty");
    const refreshCheckinsBtn = document.getElementById("refresh-checkins-btn");

    function escapeHtml(value) {
        if (value === null || value === undefined) return "";
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function getServiceBadge(status) {
        const normalized = (status || "").toLowerCase();

        if (normalized === "pending") {
            return '<span class="badge bg-warning-subtle text-warning-emphasis">Pendente</span>';
        }

        if (normalized === "in_progress") {
            return '<span class="badge bg-info-subtle text-info-emphasis">Em andamento</span>';
        }

        return `<span class="badge bg-secondary-subtle text-secondary-emphasis">${escapeHtml(status)}</span>`;
    }

    async function fetchJson(url) {
        const response = await fetch(url, {
            method: "GET",
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            },
            credentials: "same-origin"
        });

        let data = null;
        try {
            data = await response.json();
        } catch (_) {
            data = null;
        }

        if (!response.ok) {
            const detail =
                data?.detail ||
                data?.message ||
                "Falha ao carregar os dados do dashboard.";
            throw new Error(detail);
        }

        return data;
    }

    function renderServices(data) {
        const summary = data?.summary || {};
        const requests = data?.requests || [];

        servicesPendingCount.textContent = summary.pending ?? 0;
        servicesProgressCount.textContent = summary.in_progress ?? 0;

        servicesList.innerHTML = "";

        if (!requests.length) {
            servicesEmpty.classList.remove("d-none");
            return;
        }

        servicesEmpty.classList.add("d-none");

        const html = requests.map((item) => {
            return `
                <div class="list-group-item px-0">
                    <div class="d-flex justify-content-between align-items-start gap-3">
                        <div class="min-w-0">
                            <div class="fw-semibold mb-1">
                              <a href="/dashboard_services/pedido/${escapeHtml(item.service_id)}" rel="noopener noreferrer">
                                ${escapeHtml(item.request.substring(0, 35))}
                              </a>
                            </div>
                            <div class="small text-muted">
                                Hóspede: <strong>${escapeHtml(item.guest_name)}</strong> ·
                                Quarto: <strong>${escapeHtml(item.room_number)}</strong>
                            </div>
                        </div>
                        <div class="text-end">
                            <div class="mb-1">${getServiceBadge(item.status)}</div>
                            <small class="text-muted">${escapeHtml(item.created_at)}</small>
                        </div>
                    </div>
                </div>
            `;
        }).join("");

        servicesList.innerHTML = html;
    }

    function renderCheckins(data) {
        const checkins = data?.checkins || [];

        checkinsList.innerHTML = "";

        if (!checkins.length) {
            checkinsEmpty.classList.remove("d-none");
            return;
        }

        checkinsEmpty.classList.add("d-none");

        const html = checkins.map((item) => {
            return `
                <div class="list-group-item px-0">
                    <div class="d-flex justify-content-between align-items-start gap-3">
                        <div>
                            <div class="fw-semibold mb-1">${escapeHtml(item.guest_name)}</div>
                            <div class="small text-muted">
                                Quarto <strong>${escapeHtml(item.room_number)}</strong>
                                · ${escapeHtml(item.room_type)}
                            </div>
                        </div>
                        <div class="text-end">
                            <div class="fw-semibold">${escapeHtml(item.check_in)}</div>
                            <small class="text-muted">Reserva #${escapeHtml(item.reservation_id)}</small>
                        </div>
                    </div>
                </div>
            `;
        }).join("");

        checkinsList.innerHTML = html;
    }

    async function loadServices() {
        servicesLoading.classList.remove("d-none");
        servicesError.classList.add("d-none");
        servicesEmpty.classList.add("d-none");

        try {
            const data = await fetchJson(servicesUrl);
            renderServices(data);
        } catch (error) {
            servicesList.innerHTML = "";
            servicesPendingCount.textContent = "--";
            servicesProgressCount.textContent = "--";
            servicesError.textContent = error.message || "Não foi possível carregar os pedidos de serviço.";
            servicesError.classList.remove("d-none");
        } finally {
            servicesLoading.classList.add("d-none");
        }
    }

    async function loadCheckins() {
        checkinsLoading.classList.remove("d-none");
        checkinsError.classList.add("d-none");
        checkinsEmpty.classList.add("d-none");

        try {
            const data = await fetchJson(checkinsUrl);
            renderCheckins(data);
        } catch (error) {
            checkinsList.innerHTML = "";
            checkinsError.textContent = error.message || "Não foi possível carregar os próximos check-ins.";
            checkinsError.classList.remove("d-none");
        } finally {
            checkinsLoading.classList.add("d-none");
        }
    }

    if (refreshServicesBtn) {
        refreshServicesBtn.addEventListener("click", loadServices);
    }

    if (refreshCheckinsBtn) {
        refreshCheckinsBtn.addEventListener("click", loadCheckins);
    }

    loadServices();
    loadCheckins();

    setInterval(loadServices, 180000);
    setInterval(loadCheckins, 180000);
})();