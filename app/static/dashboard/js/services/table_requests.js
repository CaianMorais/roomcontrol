

function carregaTabelaPedidos() {
    let table = $('#servicos').DataTable({
        destroy: true,
        responsive: true,
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.3.5/i18n/pt-BR.json',
        },
        order: [[
            5, 'desc'
        ]],
        ajax: {
            method: 'GET',
            url: `/internal_api/table_services_requests`,
            dataSrc: function (json) {
                if (json && json.length) return json;
                return [];
            },
        },
        columns: [
            {
                data: 'id',
                class: 'text-center',
            },
            {
                data: 'reservation.id',
                class: 'text-center'
            },
            {
                data: 'reservation.room.room_number',
                class: 'text-center'
            },
            {
                data: 'reservation.guest.name',
                class: 'text-center'
            },
            {
                data: 'status_table',
                class: 'text-center'
            },
            {
                data: 'request_date_table',
                class: 'text-center'
            },
            {
                title: 'Ações',
                data: 'id',
                className: 'text-center',
                class: 'text-center',
                render: function (data, type, full, meta) {
                    return `<a href="dashboard_services/pedido/${data}">Ver pedido</a>`
                }
            }
        ],
    });
}


let temporizador = null;
let tempo = 60;

function initTimer() {
  const count = document.getElementById('count');
  tempo = 60;
  count.textContent = tempo;

  if (temporizador) clearInterval(temporizador);

  temporizador = setInterval(() => {
    tempo -= 1;
    count.textContent = tempo;

    if (tempo <= 0) {
      clearInterval(temporizador);
      temporizador = null;

      carregaTabelaPedidos();
      initTimer();
    }
  }, 1000);
}

function reloadTable() {
  carregaTabelaPedidos();
  initTimer();
}

// inicial
carregaTabelaPedidos();
initTimer();
